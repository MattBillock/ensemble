"""
Swarm State Manager - Central SQLite-backed state for all agents.

Solves the memory crash problem by persisting all state to SQLite instead of
keeping everything in memory. Provides swarm-wide visibility and recovery.
"""
import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STALLED = "stalled"
    RECOVERED = "recovered"


class SwarmStateManager:
    """
    Central SQLite-backed state manager for the entire agent swarm.

    Replaces in-memory state with persistent SQLite storage to prevent
    memory-related crashes and enable swarm recovery.
    """

    _instance: Optional["SwarmStateManager"] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[Path] = None):
        """Singleton pattern to ensure single database connection."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize swarm state manager with SQLite backend."""
        if self._initialized:
            return

        self.db_path = db_path or Path.home() / ".ensemble" / "swarm_state.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._local = threading.local()
        self._init_database()
        self._initialized = True

        logger.info(f"SwarmStateManager initialized with database: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")

        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            raise e

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Swarm sessions table - top level tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS swarm_sessions (
                    session_id TEXT PRIMARY KEY,
                    request_id TEXT,
                    user_prompt TEXT,
                    title TEXT,
                    status TEXT DEFAULT 'running',
                    budget_tier TEXT DEFAULT 'balanced',
                    root_agent_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    error_message TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Agents table - all spawned agents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    request_id TEXT,
                    agent_type TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    parent_agent_id TEXT,
                    status TEXT DEFAULT 'pending',
                    iteration INTEGER DEFAULT 0,
                    max_iterations INTEGER DEFAULT 10,
                    model_used TEXT,
                    input_data TEXT,
                    output_data TEXT,
                    error_message TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    last_checkpoint TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES swarm_sessions(session_id),
                    FOREIGN KEY (parent_agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Agent messages - conversation history (chunked to avoid memory issues)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    iteration INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Tool executions - all tool calls
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    inputs TEXT,
                    result TEXT,
                    success INTEGER DEFAULT 1,
                    duration_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Deliverables - files and commits created
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deliverables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    deliverable_type TEXT NOT NULL,
                    file_path TEXT,
                    commit_hash TEXT,
                    description TEXT,
                    content_preview TEXT,
                    github_url TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES swarm_sessions(session_id),
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Events table - for event bus
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    session_id TEXT,
                    agent_id TEXT,
                    payload TEXT,
                    processed INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Recovery queue - for stalled agent recovery
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recovery_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    recovery_reason TEXT,
                    recovery_strategy TEXT,
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_attempt TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_session ON agents(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_parent ON agents(parent_agent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_agent ON agent_messages(agent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_agent ON tool_executions(agent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_unprocessed ON events(processed, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliverables_session ON deliverables(session_id)")

            # Pending reviews table - files awaiting human review
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    request_id TEXT,
                    agent_id TEXT,
                    agent_name TEXT,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    detection_method TEXT NOT NULL,
                    review_type TEXT,
                    action TEXT,
                    action_params TEXT,
                    content_preview TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    reviewed_by TEXT,
                    execution_result TEXT,
                    FOREIGN KEY (session_id) REFERENCES swarm_sessions(session_id),
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Agent improvement reports - track agents that need improvement
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_improvement_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    session_id TEXT,
                    request_id TEXT,
                    issue_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    detection_method TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    recommendation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged INTEGER DEFAULT 0,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pending_reviews_status ON pending_reviews(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pending_reviews_file_path ON pending_reviews(file_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_improvement_reports_agent ON agent_improvement_reports(agent_id)")

            conn.commit()
            logger.info("Database schema initialized")

    # ===================
    # Session Management
    # ===================

    def create_session(
        self,
        request_id: str,
        user_prompt: str,
        budget_tier: str = "balanced",
        title: Optional[str] = None
    ) -> str:
        """Create a new swarm session."""
        import uuid
        session_id = str(uuid.uuid4())[:8]

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO swarm_sessions
                (session_id, request_id, user_prompt, title, budget_tier, status)
                VALUES (?, ?, ?, ?, ?, 'running')
            """, (session_id, request_id, user_prompt, title, budget_tier))
            conn.commit()

        # Emit event
        self.emit_event("session_created", session_id=session_id, payload={
            "request_id": request_id,
            "user_prompt": user_prompt[:200],
            "budget_tier": budget_tier
        })

        logger.info(f"Created swarm session: {session_id}")
        return session_id

    def update_session_title(self, session_id: str, title: str):
        """Update session title (from AI generation)."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE swarm_sessions
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (title, session_id))
            conn.commit()

    def update_session_status(
        self,
        session_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update session status."""
        with self._get_connection() as conn:
            if status in ("completed", "failed"):
                conn.execute("""
                    UPDATE swarm_sessions
                    SET status = ?, error_message = ?,
                        completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (status, error_message, session_id))
            else:
                conn.execute("""
                    UPDATE swarm_sessions
                    SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (status, error_message, session_id))
            conn.commit()

        self.emit_event("session_status_changed", session_id=session_id, payload={
            "status": status,
            "error_message": error_message
        })

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM swarm_sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()

            if row:
                return dict(row)
        return None

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active (running) sessions."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM swarm_sessions
                WHERE status = 'running'
                ORDER BY created_at DESC
            """).fetchall()
            return [dict(row) for row in rows]

    def get_stalled_sessions(self, stall_threshold_minutes: int = 10) -> List[Dict[str, Any]]:
        """Get sessions that appear stalled."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT s.*,
                       COUNT(a.agent_id) as total_agents,
                       SUM(CASE WHEN a.status = 'running' THEN 1 ELSE 0 END) as running_agents
                FROM swarm_sessions s
                LEFT JOIN agents a ON s.session_id = a.session_id
                WHERE s.status = 'running'
                AND datetime(s.updated_at) < datetime('now', ?)
                GROUP BY s.session_id
            """, (f'-{stall_threshold_minutes} minutes',)).fetchall()
            return [dict(row) for row in rows]

    # ===================
    # Agent Management
    # ===================

    def register_agent(
        self,
        agent_id: str,
        session_id: str,
        agent_type: str,
        agent_name: str,
        request_id: Optional[str] = None,
        parent_agent_id: Optional[str] = None,
        input_data: Optional[Dict] = None,
        max_iterations: int = 10,
        model_used: Optional[str] = None
    ):
        """Register a new agent in the swarm."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO agents
                (agent_id, session_id, request_id, agent_type, agent_name,
                 parent_agent_id, input_data, max_iterations, model_used, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                agent_id, session_id, request_id, agent_type, agent_name,
                parent_agent_id, json.dumps(input_data or {}), max_iterations, model_used
            ))

            # Update session's root agent if this is the first
            if parent_agent_id is None:
                conn.execute("""
                    UPDATE swarm_sessions
                    SET root_agent_id = ?
                    WHERE session_id = ? AND root_agent_id IS NULL
                """, (agent_id, session_id))

            conn.commit()

        self.emit_event("agent_registered", session_id=session_id, agent_id=agent_id, payload={
            "agent_type": agent_type,
            "agent_name": agent_name,
            "parent_agent_id": parent_agent_id
        })

        logger.info(f"Registered agent: {agent_id} ({agent_name})")

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        iteration: Optional[int] = None,
        error_message: Optional[str] = None,
        output_data: Optional[Dict] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None
    ):
        """Update agent status and metrics."""
        updates = ["status = ?", "last_checkpoint = CURRENT_TIMESTAMP"]
        params = [status]

        if iteration is not None:
            updates.append("iteration = ?")
            params.append(iteration)

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if output_data is not None:
            updates.append("output_data = ?")
            params.append(json.dumps(output_data))

        if tokens_used is not None:
            updates.append("tokens_used = tokens_used + ?")
            params.append(tokens_used)

        if cost is not None:
            updates.append("cost = cost + ?")
            params.append(cost)

        if status == "running":
            updates.append("started_at = COALESCE(started_at, CURRENT_TIMESTAMP)")
        elif status in ("completed", "failed"):
            updates.append("completed_at = CURRENT_TIMESTAMP")

        params.append(agent_id)

        with self._get_connection() as conn:
            conn.execute(f"""
                UPDATE agents
                SET {', '.join(updates)}
                WHERE agent_id = ?
            """, params)

            # Update session updated_at
            conn.execute("""
                UPDATE swarm_sessions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE session_id = (SELECT session_id FROM agents WHERE agent_id = ?)
            """, (agent_id,))

            conn.commit()

        self.emit_event("agent_status_changed", agent_id=agent_id, payload={
            "status": status,
            "iteration": iteration,
            "error_message": error_message
        })

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM agents WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()

            if row:
                result = dict(row)
                # Parse JSON fields
                if result.get('input_data'):
                    result['input_data'] = json.loads(result['input_data'])
                if result.get('output_data'):
                    result['output_data'] = json.loads(result['output_data'])
                return result
        return None

    def get_session_agents(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all agents for a session."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM agents
                WHERE session_id = ?
                ORDER BY created_at ASC
            """, (session_id,)).fetchall()

            results = []
            for row in rows:
                result = dict(row)
                if result.get('input_data'):
                    result['input_data'] = json.loads(result['input_data'])
                if result.get('output_data'):
                    result['output_data'] = json.loads(result['output_data'])
                results.append(result)
            return results

    def get_running_agents(self) -> List[Dict[str, Any]]:
        """Get all currently running agents."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT a.*, s.user_prompt, s.title as session_title
                FROM agents a
                JOIN swarm_sessions s ON a.session_id = s.session_id
                WHERE a.status = 'running'
                ORDER BY a.started_at DESC
            """).fetchall()
            return [dict(row) for row in rows]

    def get_stalled_agents(self, stall_threshold_minutes: int = 5) -> List[Dict[str, Any]]:
        """Get agents that appear stalled (running but no updates)."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM agents
                WHERE status = 'running'
                AND datetime(last_checkpoint) < datetime('now', ?)
            """, (f'-{stall_threshold_minutes} minutes',)).fetchall()
            return [dict(row) for row in rows]

    # ===================
    # Message History (Chunked)
    # ===================

    def record_message(
        self,
        agent_id: str,
        iteration: int,
        role: str,
        content: Any
    ):
        """Record a message in the conversation history."""
        # Serialize content if needed
        if not isinstance(content, str):
            content = json.dumps(content, default=str)

        # Truncate very long messages to prevent database bloat
        max_content_length = 50000  # 50KB max per message
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n[TRUNCATED]"

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO agent_messages (agent_id, iteration, role, content)
                VALUES (?, ?, ?, ?)
            """, (agent_id, iteration, role, content))
            conn.commit()

    def get_agent_messages(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for an agent."""
        with self._get_connection() as conn:
            query = """
                SELECT * FROM agent_messages
                WHERE agent_id = ?
                ORDER BY iteration ASC, id ASC
            """
            params = [agent_id]

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_resumable_messages(self, agent_id: str, max_messages: int = 50) -> List[Dict[str, Any]]:
        """Get messages for resuming an agent, with smart truncation."""
        with self._get_connection() as conn:
            # Get total count
            count = conn.execute(
                "SELECT COUNT(*) FROM agent_messages WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()[0]

            if count <= max_messages:
                # Return all messages
                rows = conn.execute("""
                    SELECT * FROM agent_messages
                    WHERE agent_id = ?
                    ORDER BY iteration ASC, id ASC
                """, (agent_id,)).fetchall()
            else:
                # Return first message + last (max_messages - 1)
                rows = conn.execute("""
                    SELECT * FROM agent_messages
                    WHERE agent_id = ?
                    ORDER BY iteration ASC, id ASC
                    LIMIT 1
                """, (agent_id,)).fetchall()

                rows += conn.execute("""
                    SELECT * FROM agent_messages
                    WHERE agent_id = ?
                    ORDER BY iteration DESC, id DESC
                    LIMIT ?
                """, (agent_id, max_messages - 1)).fetchall()[::-1]

            return [dict(row) for row in rows]

    # ===================
    # Tool Executions
    # ===================

    def record_tool_execution(
        self,
        agent_id: str,
        tool_name: str,
        inputs: Dict[str, Any],
        result: Dict[str, Any],
        success: bool,
        duration_ms: Optional[int] = None
    ):
        """Record a tool execution."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO tool_executions
                (agent_id, tool_name, inputs, result, success, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                agent_id, tool_name,
                json.dumps(inputs, default=str),
                json.dumps(result, default=str),
                1 if success else 0,
                duration_ms
            ))
            conn.commit()

    # ===================
    # Deliverables
    # ===================

    def record_deliverable(
        self,
        session_id: str,
        agent_id: str,
        deliverable_type: str,
        file_path: Optional[str] = None,
        commit_hash: Optional[str] = None,
        description: Optional[str] = None,
        content_preview: Optional[str] = None,
        github_url: Optional[str] = None
    ):
        """Record a deliverable (file or commit)."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO deliverables
                (session_id, agent_id, deliverable_type, file_path, commit_hash,
                 description, content_preview, github_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, agent_id, deliverable_type, file_path, commit_hash,
                description, content_preview, github_url
            ))
            conn.commit()

        self.emit_event("deliverable_created", session_id=session_id, agent_id=agent_id, payload={
            "type": deliverable_type,
            "file_path": file_path,
            "commit_hash": commit_hash
        })

    def get_session_deliverables(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all deliverables for a session."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT d.*, a.agent_name
                FROM deliverables d
                JOIN agents a ON d.agent_id = a.agent_id
                WHERE d.session_id = ?
                ORDER BY d.timestamp ASC
            """, (session_id,)).fetchall()
            return [dict(row) for row in rows]

    # ===================
    # Event Bus
    # ===================

    def emit_event(
        self,
        event_type: str,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        payload: Optional[Dict] = None
    ):
        """Emit an event to the event bus."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO events (event_type, session_id, agent_id, payload)
                VALUES (?, ?, ?, ?)
            """, (event_type, session_id, agent_id, json.dumps(payload or {})))
            conn.commit()

    def get_unprocessed_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get unprocessed events for broadcasting."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM events
                WHERE processed = 0
                ORDER BY timestamp ASC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def mark_events_processed(self, event_ids: List[int]):
        """Mark events as processed."""
        if not event_ids:
            return

        with self._get_connection() as conn:
            placeholders = ','.join('?' * len(event_ids))
            conn.execute(f"""
                UPDATE events SET processed = 1 WHERE id IN ({placeholders})
            """, event_ids)
            conn.commit()

    def subscribe_events(
        self,
        event_types: Optional[List[str]] = None,
        since_id: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Subscribe to events (for polling-based consumption)."""
        with self._get_connection() as conn:
            query = "SELECT * FROM events WHERE id > ?"
            params = [since_id]

            if event_types:
                placeholders = ','.join('?' * len(event_types))
                query += f" AND event_type IN ({placeholders})"
                params.extend(event_types)

            query += " ORDER BY timestamp ASC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                result = dict(row)
                if result.get('payload'):
                    result['payload'] = json.loads(result['payload'])
                results.append(result)
            return results

    # ===================
    # Recovery Queue
    # ===================

    def queue_for_recovery(
        self,
        agent_id: str,
        session_id: str,
        reason: str,
        strategy: str = "retry",
        priority: int = 0
    ):
        """Add an agent to the recovery queue."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO recovery_queue
                (agent_id, session_id, recovery_reason, recovery_strategy, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, session_id, reason, strategy, priority))
            conn.commit()

        logger.info(f"Queued agent {agent_id} for recovery: {reason}")

    def get_recovery_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending recovery tasks."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT r.*, a.agent_type, a.agent_name, a.input_data
                FROM recovery_queue r
                JOIN agents a ON r.agent_id = a.agent_id
                WHERE r.status = 'pending' AND r.attempts < r.max_attempts
                ORDER BY r.priority DESC, r.created_at ASC
                LIMIT ?
            """, (limit,)).fetchall()

            results = []
            for row in rows:
                result = dict(row)
                if result.get('input_data'):
                    result['input_data'] = json.loads(result['input_data'])
                results.append(result)
            return results

    def update_recovery_status(
        self,
        recovery_id: int,
        status: str,
        increment_attempts: bool = False
    ):
        """Update recovery task status."""
        with self._get_connection() as conn:
            if increment_attempts:
                conn.execute("""
                    UPDATE recovery_queue
                    SET status = ?, attempts = attempts + 1, last_attempt = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, recovery_id))
            else:
                conn.execute("""
                    UPDATE recovery_queue
                    SET status = ?
                    WHERE id = ?
                """, (status, recovery_id))
            conn.commit()

    # ===================
    # Query Methods (for API)
    # ===================

    def get_sessions(
        self,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get sessions with optional filters."""
        with self._get_connection() as conn:
            query = "SELECT * FROM swarm_sessions"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_agents(
        self,
        session_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get agents with optional filters."""
        with self._get_connection() as conn:
            query = "SELECT * FROM agents WHERE 1=1"
            params = []

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                result = dict(row)
                if result.get('input_data'):
                    try:
                        result['input_data'] = json.loads(result['input_data'])
                    except:
                        pass
                if result.get('output_data'):
                    try:
                        result['output_data'] = json.loads(result['output_data'])
                    except:
                        pass
                results.append(result)
            return results

    def get_agent_tool_executions(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get tool executions for an agent."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM tool_executions
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_id, limit)).fetchall()

            results = []
            for row in rows:
                result = dict(row)
                if result.get('inputs'):
                    try:
                        result['inputs'] = json.loads(result['inputs'])
                    except:
                        pass
                if result.get('result'):
                    try:
                        result['result'] = json.loads(result['result'])
                    except:
                        pass
                results.append(result)
            return results

    def get_events(
        self,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get events with optional filters."""
        with self._get_connection() as conn:
            query = "SELECT * FROM events WHERE 1=1"
            params = []

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                result = dict(row)
                if result.get('payload'):
                    try:
                        result['payload'] = json.loads(result['payload'])
                    except:
                        pass
                results.append(result)
            return results

    def get_stats(self) -> Dict[str, Any]:
        """Alias for get_swarm_stats (for API compatibility)."""
        return self.get_swarm_stats()

    # ===================
    # Statistics
    # ===================

    def get_swarm_stats(self) -> Dict[str, Any]:
        """Get overall swarm statistics."""
        with self._get_connection() as conn:
            stats = {}

            # Session stats
            stats['sessions'] = dict(conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM swarm_sessions
            """).fetchone())

            # Agent stats
            stats['agents'] = dict(conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'stalled' THEN 1 ELSE 0 END) as stalled,
                    SUM(tokens_used) as total_tokens,
                    SUM(cost) as total_cost
                FROM agents
            """).fetchone())

            # Recent activity
            stats['recent_events'] = conn.execute("""
                SELECT COUNT(*) FROM events
                WHERE timestamp > datetime('now', '-1 hour')
            """).fetchone()[0]

            # Recovery queue
            stats['recovery_pending'] = conn.execute("""
                SELECT COUNT(*) FROM recovery_queue WHERE status = 'pending'
            """).fetchone()[0]

            return stats

    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to prevent database bloat."""
        with self._get_connection() as conn:
            # Clean old processed events
            conn.execute("""
                DELETE FROM events
                WHERE processed = 1 AND timestamp < datetime('now', ?)
            """, (f'-{days} days',))

            # Clean old completed recovery tasks
            conn.execute("""
                DELETE FROM recovery_queue
                WHERE status IN ('completed', 'failed')
                AND last_attempt < datetime('now', ?)
            """, (f'-{days} days',))

            conn.commit()

            # Vacuum to reclaim space
            conn.execute("VACUUM")

            logger.info(f"Cleaned up data older than {days} days")

    # ===================
    # Pending Reviews
    # ===================

    def add_pending_review(
        self,
        file_path: str,
        file_type: str,
        detection_method: str,
        review_type: str = None,
        action: str = None,
        action_params: Dict = None,
        content_preview: str = None,
        session_id: str = None,
        request_id: str = None,
        agent_id: str = None,
        agent_name: str = None
    ) -> int:
        """Add a file to the pending review queue."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO pending_reviews
                (file_path, file_type, detection_method, review_type, action,
                 action_params, content_preview, session_id, request_id, agent_id, agent_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path, file_type, detection_method, review_type, action,
                json.dumps(action_params) if action_params else None, content_preview,
                session_id, request_id, agent_id, agent_name
            ))
            conn.commit()
            return cursor.lastrowid

    def is_file_tracked_for_review(self, file_path: str) -> bool:
        """Check if a file is already in the review queue."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM pending_reviews WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            return row is not None

    def get_pending_reviews(
        self,
        status: str = "pending",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get pending reviews with optional filtering."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM pending_reviews
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (status, limit, offset)).fetchall()

            results = []
            for row in rows:
                result = dict(row)
                if result.get('action_params'):
                    try:
                        result['action_params'] = json.loads(result['action_params'])
                    except json.JSONDecodeError:
                        result['action_params'] = {}
                results.append(result)
            return results

    def get_pending_review(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Get a single pending review by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM pending_reviews WHERE id = ?",
                (review_id,)
            ).fetchone()

            if row:
                result = dict(row)
                if result.get('action_params'):
                    try:
                        result['action_params'] = json.loads(result['action_params'])
                    except json.JSONDecodeError:
                        result['action_params'] = {}
                return result
            return None

    def update_pending_review(
        self,
        review_id: int,
        status: str = None,
        execution_result: Dict = None
    ):
        """Update a pending review status."""
        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)
            if status in ("approved", "rejected"):
                updates.append("reviewed_at = CURRENT_TIMESTAMP")
                updates.append("reviewed_by = 'user'")

        if execution_result is not None:
            updates.append("execution_result = ?")
            params.append(json.dumps(execution_result))

        if not updates:
            return

        params.append(review_id)

        with self._get_connection() as conn:
            conn.execute(f"""
                UPDATE pending_reviews
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()

    # ===================
    # Agent Improvement Reports
    # ===================

    def add_improvement_report(
        self,
        agent_id: str,
        agent_name: str,
        issue_type: str,
        file_path: str,
        detection_method: str,
        severity: str = "warning",
        recommendation: str = None,
        session_id: str = None,
        request_id: str = None
    ) -> int:
        """Add an agent improvement report."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO agent_improvement_reports
                (agent_id, agent_name, session_id, request_id, issue_type,
                 file_path, detection_method, severity, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, agent_name, session_id, request_id, issue_type,
                file_path, detection_method, severity, recommendation
            ))
            conn.commit()
            return cursor.lastrowid

    def get_improvement_reports(
        self,
        agent_id: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get agent improvement reports."""
        with self._get_connection() as conn:
            query = "SELECT * FROM agent_improvement_reports WHERE 1=1"
            params = []

            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    # ===================
    # Agent Stats
    # ===================

    def get_agents_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all agent classes with activity counts."""
        with self._get_connection() as conn:
            # Get counts grouped by agent_name from agents table
            rows = conn.execute("""
                SELECT
                    agent_name,
                    COUNT(*) as count,
                    MAX(created_at) as last_activity,
                    status
                FROM agents
                GROUP BY agent_name
                ORDER BY count DESC
            """).fetchall()
            return [dict(row) for row in rows]


# Singleton accessor
_swarm_state_manager: Optional[SwarmStateManager] = None


def get_swarm_state() -> SwarmStateManager:
    """Get the global swarm state manager instance."""
    global _swarm_state_manager
    if _swarm_state_manager is None:
        _swarm_state_manager = SwarmStateManager()
    return _swarm_state_manager
