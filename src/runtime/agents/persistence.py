"""
Swarm State Persistence Layer

Provides SQLite-based persistence for swarm sessions and agent states,
enabling recovery after backend restarts or crashes.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from threading import Lock

logger = logging.getLogger(__name__)


class SwarmPersistence:
    """
    Persistent storage for swarm sessions and agent states.

    Uses SQLite for reliable, transactional storage of:
    - Swarm sessions (original prompts, status, metrics)
    - Agent states (status, iterations, results)
    - Activity history for recovery
    """

    DEFAULT_DB_PATH = os.path.expanduser("~/.ensemble/swarm_state.db")

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the persistence layer.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.ensemble/swarm_state.db
        """
        self.db_path = Path(db_path or self.DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_database()

    def _init_database(self):
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            conn.executescript("""
                -- Swarm sessions table
                CREATE TABLE IF NOT EXISTS swarm_sessions (
                    session_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    prompt TEXT NOT NULL,
                    budget_tier TEXT NOT NULL DEFAULT 'balanced',
                    status TEXT NOT NULL DEFAULT 'running',
                    project_id TEXT,
                    family_name TEXT,
                    total_cost REAL DEFAULT 0.0,
                    total_tokens INTEGER DEFAULT 0,
                    duration_ms INTEGER,
                    summary TEXT,
                    errors TEXT,  -- JSON array of error strings
                    deliverables TEXT,  -- JSON array of file paths
                    metadata TEXT  -- JSON object for extra data
                );

                -- Agent states table
                CREATE TABLE IF NOT EXISTS agent_states (
                    agent_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    whimsical_name TEXT,
                    family_name TEXT,
                    status TEXT NOT NULL DEFAULT 'running',
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    iterations INTEGER DEFAULT 0,
                    max_iterations INTEGER DEFAULT 50,
                    model_used TEXT,
                    cost REAL DEFAULT 0.0,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    current_task TEXT,
                    summary TEXT,
                    self_analysis TEXT,
                    parent_id TEXT,
                    result TEXT,  -- JSON object
                    error TEXT,
                    FOREIGN KEY (session_id) REFERENCES swarm_sessions(session_id)
                );

                -- Index for faster lookups
                CREATE INDEX IF NOT EXISTS idx_agent_session ON agent_states(session_id);
                CREATE INDEX IF NOT EXISTS idx_session_status ON swarm_sessions(status);
                CREATE INDEX IF NOT EXISTS idx_agent_status ON agent_states(status);
            """)
            logger.info(f"Initialized swarm persistence database at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper locking."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ========== Session Operations ==========

    def create_session(
        self,
        session_id: str,
        prompt: str,
        budget_tier: str = "balanced",
        project_id: Optional[str] = None,
        family_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new swarm session.

        Args:
            session_id: Unique session identifier
            prompt: Original user prompt
            budget_tier: Budget tier (economical/balanced/full_firepower)
            project_id: Optional project ID for grouping
            family_name: Optional family name for agent grouping

        Returns:
            Created session data
        """
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO swarm_sessions (
                    session_id, started_at, prompt, budget_tier,
                    status, project_id, family_name
                ) VALUES (?, ?, ?, ?, 'running', ?, ?)
            """, (session_id, now, prompt, budget_tier, project_id, family_name))

        logger.info(f"Created swarm session: {session_id}")
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM swarm_sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()

            if row:
                return self._row_to_session(row)
        return None

    def update_session(self, session_id: str, **updates) -> Optional[Dict[str, Any]]:
        """
        Update session fields.

        Args:
            session_id: Session to update
            **updates: Field-value pairs to update

        Returns:
            Updated session or None if not found
        """
        if not updates:
            return self.get_session(session_id)

        # Handle JSON fields
        json_fields = {'errors', 'deliverables', 'metadata'}
        for field in json_fields:
            if field in updates and not isinstance(updates[field], str):
                updates[field] = json.dumps(updates[field])

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [session_id]

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE swarm_sessions SET {set_clause} WHERE session_id = ?",
                values
            )

        return self.get_session(session_id)

    def complete_session(
        self,
        session_id: str,
        status: str = "completed",
        summary: Optional[str] = None,
        deliverables: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Mark a session as completed."""
        now = datetime.now().isoformat()
        return self.update_session(
            session_id,
            status=status,
            completed_at=now,
            summary=summary,
            deliverables=deliverables
        )

    def get_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        include_agents: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions, optionally filtered by status.

        Args:
            status: Filter by status (running/completed/failed/recovered)
            limit: Maximum number of sessions to return
            include_agents: Include agent data for each session

        Returns:
            List of session data
        """
        with self._get_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM swarm_sessions WHERE status = ? ORDER BY started_at DESC LIMIT ?",
                    (status, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM swarm_sessions ORDER BY started_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()

            sessions = [self._row_to_session(row) for row in rows]

            if include_agents:
                for session in sessions:
                    session['agents'] = self.get_agents_for_session(session['session_id'])

            return sessions

    def get_incomplete_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions that are not completed (for recovery)."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM swarm_sessions WHERE status NOT IN ('completed', 'abandoned') ORDER BY started_at DESC"
            ).fetchall()

            sessions = []
            for row in rows:
                session = self._row_to_session(row)
                session['agents'] = self.get_agents_for_session(session['session_id'])
                sessions.append(session)

            return sessions

    def mark_sessions_as_recovered(self) -> int:
        """Mark all running sessions as recovered (called on startup)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE swarm_sessions SET status = 'recovered' WHERE status = 'running'"
            )
            count = cursor.rowcount

        if count > 0:
            logger.info(f"Marked {count} sessions as recovered")
        return count

    # ========== Agent Operations ==========

    def create_agent(
        self,
        agent_id: str,
        session_id: str,
        agent_type: str,
        whimsical_name: Optional[str] = None,
        family_name: Optional[str] = None,
        parent_id: Optional[str] = None,
        max_iterations: int = 50
    ) -> Dict[str, Any]:
        """Create a new agent state."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO agent_states (
                    agent_id, session_id, agent_type, whimsical_name,
                    family_name, started_at, parent_id, max_iterations, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running')
            """, (agent_id, session_id, agent_type, whimsical_name,
                  family_name, now, parent_id, max_iterations))

        logger.debug(f"Created agent state: {agent_id} in session {session_id}")
        return self.get_agent(agent_id)

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM agent_states WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()

            if row:
                return self._row_to_agent(row)
        return None

    def update_agent(self, agent_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update agent fields."""
        if not updates:
            return self.get_agent(agent_id)

        # Handle JSON fields
        if 'result' in updates and not isinstance(updates['result'], str):
            updates['result'] = json.dumps(updates['result'])

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [agent_id]

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE agent_states SET {set_clause} WHERE agent_id = ?",
                values
            )

        return self.get_agent(agent_id)

    def complete_agent(
        self,
        agent_id: str,
        status: str = "completed",
        summary: Optional[str] = None,
        result: Optional[Dict] = None,
        cost: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Mark an agent as completed."""
        now = datetime.now().isoformat()
        return self.update_agent(
            agent_id,
            status=status,
            completed_at=now,
            summary=summary,
            result=result,
            cost=cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

    def get_agents_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all agents for a session."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM agent_states WHERE session_id = ? ORDER BY started_at",
                (session_id,)
            ).fetchall()

            return [self._row_to_agent(row) for row in rows]

    # ========== Cleanup Operations ==========

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its agents."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM agent_states WHERE session_id = ?", (session_id,))
            cursor = conn.execute("DELETE FROM swarm_sessions WHERE session_id = ?", (session_id,))
            return cursor.rowcount > 0

    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Delete sessions older than max_age_days."""
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()

        with self._get_connection() as conn:
            # Get session IDs to delete
            rows = conn.execute(
                "SELECT session_id FROM swarm_sessions WHERE started_at < ? AND status IN ('completed', 'abandoned')",
                (cutoff,)
            ).fetchall()

            count = 0
            for row in rows:
                conn.execute("DELETE FROM agent_states WHERE session_id = ?", (row['session_id'],))
                conn.execute("DELETE FROM swarm_sessions WHERE session_id = ?", (row['session_id'],))
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} old sessions")
        return count

    # ========== Helper Methods ==========

    def _row_to_session(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a session dict."""
        data = dict(row)
        # Parse JSON fields
        for field in ['errors', 'deliverables', 'metadata']:
            if data.get(field):
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return data

    def _row_to_agent(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to an agent dict."""
        data = dict(row)
        # Parse JSON fields
        if data.get('result'):
            try:
                data['result'] = json.loads(data['result'])
            except (json.JSONDecodeError, TypeError):
                pass
        return data


# Global instance
_persistence: Optional[SwarmPersistence] = None


def get_persistence() -> SwarmPersistence:
    """Get the global persistence instance."""
    global _persistence
    if _persistence is None:
        _persistence = SwarmPersistence()
    return _persistence


def init_persistence(db_path: Optional[str] = None) -> SwarmPersistence:
    """Initialize and return the global persistence instance."""
    global _persistence
    _persistence = SwarmPersistence(db_path)
    return _persistence
