"""Agent performance metrics tracking and analytics."""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AgentMetricsTracker:
    """Tracks and analyzes agent performance metrics."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize metrics tracker.

        Args:
            db_path: Path to SQLite database. If None, uses default location.
        """
        if db_path is None:
            db_path = Path.home() / ".ensemble" / "metrics.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        logger.info(f"Initialized metrics tracker at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Agent executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    task_complexity TEXT,
                    budget_tier TEXT,
                    success BOOLEAN NOT NULL,
                    error_type TEXT,
                    duration_ms INTEGER,
                    iterations INTEGER,
                    tokens_used INTEGER,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    request_id TEXT,
                    parent_agent_id TEXT,
                    spawned_agents_count INTEGER DEFAULT 0,
                    task_description TEXT,
                    self_analysis TEXT,
                    performance_analysis TEXT
                )
            """)

            # Indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_type
                ON agent_executions(agent_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_used
                ON agent_executions(model_used)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_success
                ON agent_executions(success)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON agent_executions(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_request_id
                ON agent_executions(request_id)
            """)

    def record_execution(
        self,
        agent_id: str,
        agent_type: str,
        agent_name: str,
        model_used: str,
        task_complexity: str,
        budget_tier: str,
        success: bool,
        duration_ms: int,
        iterations: int,
        created_at: str,
        completed_at: str,
        request_id: str,
        parent_agent_id: Optional[str] = None,
        spawned_agents_count: int = 0,
        error_type: Optional[str] = None,
        tokens_used: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        estimated_cost: Optional[float] = None,
        task_description: Optional[str] = None,
        self_analysis: Optional[str] = None,
        performance_analysis: Optional[str] = None
    ) -> int:
        """
        Record an agent execution.

        Args:
            agent_id: Unique agent execution ID
            agent_type: Type of agent (e.g., "leadership", "coordinator")
            agent_name: Agent name (e.g., "executive_director")
            model_used: Model ID used (e.g., "claude-sonnet-4-5-20250929")
            task_complexity: Task complexity level (simple, creative, strategic)
            budget_tier: Budget tier (economical, balanced, full_firepower)
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds
            iterations: Number of iterations/turns
            created_at: ISO timestamp when started
            completed_at: ISO timestamp when completed
            request_id: Request ID for tracing
            parent_agent_id: Parent agent if spawned by another
            spawned_agents_count: Number of agents this agent spawned
            error_type: Type of error if failed
            tokens_used: Estimated tokens used
            task_description: Brief task description
            self_analysis: Agent's self-performance analysis
            performance_analysis: Supervisor's analysis of dependencies

        Returns:
            Execution record ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_executions (
                    agent_id, agent_type, agent_name, model_used,
                    task_complexity, budget_tier, success, error_type,
                    duration_ms, iterations, tokens_used,
                    input_tokens, output_tokens, estimated_cost,
                    created_at, completed_at, request_id, parent_agent_id,
                    spawned_agents_count, task_description,
                    self_analysis, performance_analysis
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, agent_type, agent_name, model_used,
                task_complexity, budget_tier, success, error_type,
                duration_ms, iterations, tokens_used,
                input_tokens, output_tokens, estimated_cost,
                created_at, completed_at, request_id, parent_agent_id,
                spawned_agents_count, task_description,
                self_analysis, performance_analysis
            ))

            record_id = cursor.lastrowid
            logger.info(f"Recorded execution for {agent_name} (ID: {record_id})")
            return record_id

    def get_success_rate_by_agent(self, agent_name: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get success rate grouped by agent type."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    agent_name,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms,
                    ROUND(AVG(iterations), 1) as avg_iterations
                FROM agent_executions
                WHERE created_at >= ?
            """

            params = [cutoff_date]
            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)

            query += " GROUP BY agent_name ORDER BY total_executions DESC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            return {
                "period_days": days,
                "agents": [dict(row) for row in results]
            }

    def get_success_rate_by_model(self, days: int = 30) -> Dict[str, Any]:
        """Get success rate grouped by model."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    model_used,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms,
                    ROUND(AVG(iterations), 1) as avg_iterations
                FROM agent_executions
                WHERE created_at >= ?
                GROUP BY model_used
                ORDER BY total_executions DESC
            """, (cutoff_date,))

            results = cursor.fetchall()

            return {
                "period_days": days,
                "models": [dict(row) for row in results]
            }

    def get_success_rate_by_complexity(self, days: int = 30) -> Dict[str, Any]:
        """Get success rate grouped by task complexity."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    task_complexity,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms
                FROM agent_executions
                WHERE created_at >= ?
                GROUP BY task_complexity
                ORDER BY
                    CASE task_complexity
                        WHEN 'simple' THEN 1
                        WHEN 'creative' THEN 2
                        WHEN 'strategic' THEN 3
                        ELSE 4
                    END
            """, (cutoff_date,))

            results = cursor.fetchall()

            return {
                "period_days": days,
                "complexities": [dict(row) for row in results]
            }

    def get_agent_model_correlation(self, agent_name: str, days: int = 30) -> Dict[str, Any]:
        """Get success rate for a specific agent across different models."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    model_used,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms,
                    ROUND(AVG(iterations), 1) as avg_iterations
                FROM agent_executions
                WHERE agent_name = ? AND created_at >= ?
                GROUP BY model_used
                ORDER BY total_executions DESC
            """, (agent_name, cutoff_date))

            results = cursor.fetchall()

            return {
                "agent_name": agent_name,
                "period_days": days,
                "model_performance": [dict(row) for row in results]
            }

    def get_error_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze common error types."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    error_type,
                    agent_name,
                    COUNT(*) as occurrences,
                    ROUND(AVG(duration_ms), 0) as avg_duration_before_failure
                FROM agent_executions
                WHERE success = 0 AND error_type IS NOT NULL
                  AND created_at >= ?
                GROUP BY error_type, agent_name
                ORDER BY occurrences DESC
                LIMIT 20
            """, (cutoff_date,))

            results = cursor.fetchall()

            return {
                "period_days": days,
                "errors": [dict(row) for row in results]
            }

    def get_performance_trends(self, agent_name: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms
                FROM agent_executions
                WHERE created_at >= ?
            """

            params = [cutoff_date]
            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)

            query += " GROUP BY DATE(created_at) ORDER BY date DESC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            return {
                "agent_name": agent_name or "all",
                "period_days": days,
                "daily_trends": [dict(row) for row in results]
            }

    def get_self_analyses(self, agent_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent self-analyses from agents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    agent_name,
                    agent_id,
                    created_at,
                    success,
                    duration_ms,
                    self_analysis,
                    performance_analysis
                FROM agent_executions
                WHERE (self_analysis IS NOT NULL OR performance_analysis IS NOT NULL)
            """

            params = []
            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [dict(row) for row in results]

    def get_summary_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get overall summary statistics."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Overall stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms,
                    ROUND(AVG(iterations), 1) as avg_iterations,
                    COUNT(DISTINCT agent_name) as unique_agents,
                    COUNT(DISTINCT model_used) as models_used,
                    SUM(spawned_agents_count) as total_spawned_agents
                FROM agent_executions
                WHERE created_at >= ?
            """, (cutoff_date,))

            overall = dict(cursor.fetchone())

            # Most active agents
            cursor.execute("""
                SELECT agent_name, COUNT(*) as executions
                FROM agent_executions
                WHERE created_at >= ?
                GROUP BY agent_name
                ORDER BY executions DESC
                LIMIT 5
            """, (cutoff_date,))

            most_active = [dict(row) for row in cursor.fetchall()]

            # Best performing agents
            cursor.execute("""
                SELECT
                    agent_name,
                    COUNT(*) as executions,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate
                FROM agent_executions
                WHERE created_at >= ?
                GROUP BY agent_name
                HAVING COUNT(*) >= 3
                ORDER BY success_rate DESC, executions DESC
                LIMIT 5
            """, (cutoff_date,))

            best_performing = [dict(row) for row in cursor.fetchall()]

            return {
                "period_days": days,
                "overall": overall,
                "most_active_agents": most_active,
                "best_performing_agents": best_performing
            }

    def get_recent_executions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent agent executions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    agent_id,
                    agent_name,
                    model_used,
                    success,
                    duration_ms,
                    iterations,
                    created_at,
                    error_type
                FROM agent_executions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            results = cursor.fetchall()
            return [dict(row) for row in results]
