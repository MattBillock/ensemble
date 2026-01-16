"""
Iteration Tuner - Automatic adjustment of agent iteration limits based on performance.

This module tracks success/failure rates per agent type and automatically adjusts
iteration limits to optimize performance. When tuned iterations reach 2x original,
agents are flagged for model escalation consideration.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TuningAction(Enum):
    """Action taken during tuning."""
    INCREASED = "increased"
    DECREASED = "decreased"
    UNCHANGED = "unchanged"
    ESCALATION_FLAGGED = "escalation_flagged"


@dataclass
class TunedIterationConfig:
    """Configuration for a tuned agent's iterations."""
    agent_name: str
    original_max_iterations: int
    current_tuned_iterations: int
    success_count: int
    failure_count: int
    escalation_flagged: bool
    last_adjustment_at: Optional[str]


class IterationTuner:
    """
    Automatic iteration tuning based on agent success/failure rates.

    Rules:
    - On success: reduce max_iterations by 1 (floor at original * 0.5 or 3, whichever is higher)
    - On failure: increase max_iterations by 1 (ceiling at original * 2)
    - When tuned >= original * 2: flag for model escalation consideration
    """

    _instance = None

    def __new__(cls, db_path: Optional[Path] = None):
        """Singleton pattern to ensure single instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the iteration tuner with SQLite storage."""
        if self._initialized:
            return

        self.db_path = db_path or Path.home() / ".ensemble" / "iteration_tuning.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        self._initialized = True

        logger.info(f"IterationTuner initialized with database: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tuned iterations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tuned_iterations (
                    agent_name TEXT PRIMARY KEY,
                    original_max_iterations INTEGER NOT NULL,
                    current_tuned_iterations INTEGER NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_adjustment_at TEXT,
                    escalation_flagged INTEGER DEFAULT 0,
                    escalation_flagged_at TEXT
                )
            """)

            # Tuning history table for audit
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tuning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value INTEGER,
                    new_value INTEGER,
                    reason TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def get_tuned_iterations(self, agent_name: str) -> Optional[TunedIterationConfig]:
        """Get current tuned iteration configuration for an agent."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tuned_iterations WHERE agent_name = ?",
                (agent_name,)
            )
            row = cursor.fetchone()

            if row:
                return TunedIterationConfig(
                    agent_name=row["agent_name"],
                    original_max_iterations=row["original_max_iterations"],
                    current_tuned_iterations=row["current_tuned_iterations"],
                    success_count=row["success_count"],
                    failure_count=row["failure_count"],
                    escalation_flagged=bool(row["escalation_flagged"]),
                    last_adjustment_at=row["last_adjustment_at"]
                )
            return None

    def get_effective_max_iterations(self, agent_name: str, original_max: int) -> int:
        """
        Get the effective max iterations for an agent.

        Returns tuned value if available, otherwise original.
        """
        config = self.get_tuned_iterations(agent_name)
        if config:
            return config.current_tuned_iterations
        return original_max

    def record_execution_result(
        self,
        agent_name: str,
        success: bool,
        original_max: int,
        actual_iterations: int
    ) -> TuningAction:
        """
        Process execution result and update tuning.

        Args:
            agent_name: Name of the agent
            success: Whether execution succeeded
            original_max: Original max iterations from agent definition
            actual_iterations: How many iterations were actually used

        Returns:
            TuningAction indicating what adjustment was made
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get or create tuning record
            cursor.execute(
                "SELECT * FROM tuned_iterations WHERE agent_name = ?",
                (agent_name,)
            )
            row = cursor.fetchone()

            if row:
                current = row["current_tuned_iterations"]
                success_count = row["success_count"]
                failure_count = row["failure_count"]
                escalation_flagged = bool(row["escalation_flagged"])
            else:
                # First time seeing this agent
                current = original_max
                success_count = 0
                failure_count = 0
                escalation_flagged = False

                cursor.execute("""
                    INSERT INTO tuned_iterations
                    (agent_name, original_max_iterations, current_tuned_iterations)
                    VALUES (?, ?, ?)
                """, (agent_name, original_max, current))

            # Calculate new value
            floor = max(int(original_max * 0.5), 3)  # Minimum 50% of original or 3
            ceiling = original_max * 2  # Maximum 2x original

            action = TuningAction.UNCHANGED
            new_value = current
            reason = ""

            if success:
                success_count += 1
                if current > floor:
                    new_value = current - 1
                    action = TuningAction.DECREASED
                    reason = f"Success - reduced from {current} to {new_value} (floor: {floor})"
            else:
                failure_count += 1
                if current < ceiling:
                    new_value = current + 1
                    action = TuningAction.INCREASED
                    reason = f"Failure - increased from {current} to {new_value} (ceiling: {ceiling})"

            # Check for escalation flag
            if new_value >= ceiling and not escalation_flagged:
                escalation_flagged = True
                action = TuningAction.ESCALATION_FLAGGED
                reason += f" - FLAGGED FOR MODEL ESCALATION (reached 2x original)"

                cursor.execute("""
                    UPDATE tuned_iterations
                    SET escalation_flagged = 1, escalation_flagged_at = ?
                    WHERE agent_name = ?
                """, (datetime.now().isoformat(), agent_name))

                logger.warning(
                    f"Agent {agent_name} flagged for model escalation - "
                    f"iterations reached {new_value} (2x original {original_max})"
                )

            # Update tuning record
            cursor.execute("""
                UPDATE tuned_iterations
                SET current_tuned_iterations = ?,
                    success_count = ?,
                    failure_count = ?,
                    last_adjustment_at = ?
                WHERE agent_name = ?
            """, (new_value, success_count, failure_count, datetime.now().isoformat(), agent_name))

            # Record history
            if action != TuningAction.UNCHANGED:
                cursor.execute("""
                    INSERT INTO tuning_history (agent_name, action, old_value, new_value, reason)
                    VALUES (?, ?, ?, ?, ?)
                """, (agent_name, action.value, current, new_value, reason))

                logger.info(f"Iteration tuning for {agent_name}: {reason}")

            conn.commit()

            return action

    def check_escalation_needed(self, agent_name: str) -> bool:
        """Check if agent is flagged for model escalation."""
        config = self.get_tuned_iterations(agent_name)
        return config.escalation_flagged if config else False

    def get_flagged_for_escalation(self) -> List[Dict[str, Any]]:
        """Get all agents flagged for model escalation."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT agent_name, original_max_iterations, current_tuned_iterations,
                       success_count, failure_count, escalation_flagged_at
                FROM tuned_iterations
                WHERE escalation_flagged = 1
                ORDER BY escalation_flagged_at DESC
            """)

            return [dict(row) for row in cursor.fetchall()]

    def get_all_tuned_agents(self) -> List[Dict[str, Any]]:
        """Get tuning status for all agents."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT agent_name, original_max_iterations, current_tuned_iterations,
                       success_count, failure_count, escalation_flagged, last_adjustment_at
                FROM tuned_iterations
                ORDER BY agent_name
            """)

            return [dict(row) for row in cursor.fetchall()]

    def get_tuning_history(self, agent_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tuning history, optionally filtered by agent."""
        with self._get_connection() as conn:
            if agent_name:
                cursor = conn.execute("""
                    SELECT * FROM tuning_history
                    WHERE agent_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (agent_name, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM tuning_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def reset_agent_tuning(self, agent_name: str) -> bool:
        """Reset tuning for a specific agent back to original values."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get original value
            cursor.execute(
                "SELECT original_max_iterations FROM tuned_iterations WHERE agent_name = ?",
                (agent_name,)
            )
            row = cursor.fetchone()

            if not row:
                return False

            original = row["original_max_iterations"]

            # Reset to original
            cursor.execute("""
                UPDATE tuned_iterations
                SET current_tuned_iterations = original_max_iterations,
                    success_count = 0,
                    failure_count = 0,
                    escalation_flagged = 0,
                    escalation_flagged_at = NULL,
                    last_adjustment_at = ?
                WHERE agent_name = ?
            """, (datetime.now().isoformat(), agent_name))

            # Record in history
            cursor.execute("""
                INSERT INTO tuning_history (agent_name, action, old_value, new_value, reason)
                VALUES (?, 'reset', NULL, ?, 'Manual reset to original value')
            """, (agent_name, original))

            conn.commit()

            logger.info(f"Reset tuning for {agent_name} to original {original} iterations")
            return True

    def reset_all_tuning(self) -> int:
        """Reset tuning for all agents. Returns number of agents reset."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get all agents
            cursor.execute("SELECT agent_name FROM tuned_iterations")
            agents = [row["agent_name"] for row in cursor.fetchall()]

            # Reset each
            for agent_name in agents:
                self.reset_agent_tuning(agent_name)

            return len(agents)


# Global singleton accessor
_tuner_instance: Optional[IterationTuner] = None


def get_iteration_tuner() -> IterationTuner:
    """Get the global IterationTuner instance."""
    global _tuner_instance
    if _tuner_instance is None:
        _tuner_instance = IterationTuner()
    return _tuner_instance
