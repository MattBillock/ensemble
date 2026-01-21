"""
Unit tests for swarm_state module.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.runtime.agents.swarm_state import (
    AgentStatus,
    SwarmStateManager,
    get_swarm_state,
)


class TestAgentStatus:
    """Test AgentStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert AgentStatus.PENDING.value == "pending"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.STALLED.value == "stalled"
        assert AgentStatus.RECOVERED.value == "recovered"


class TestSwarmStateManager:
    """Test SwarmStateManager class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            yield db_path

    @pytest.fixture
    def manager(self, temp_db):
        """Create a SwarmStateManager with temp database."""
        return SwarmStateManager(db_path=temp_db)

    def test_singleton_pattern(self, temp_db):
        """Test that SwarmStateManager is a singleton."""
        manager1 = SwarmStateManager(db_path=temp_db)
        manager2 = SwarmStateManager(db_path=temp_db)
        assert manager1 is manager2

    def test_database_initialization(self, manager):
        """Test database tables are created."""
        with manager._get_connection() as conn:
            # Check that all expected tables exist
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]

            assert "swarm_sessions" in table_names
            assert "agents" in table_names
            assert "agent_messages" in table_names
            assert "tool_executions" in table_names
            assert "deliverables" in table_names
            assert "events" in table_names
            assert "recovery_queue" in table_names
            assert "pending_reviews" in table_names
            assert "agent_improvement_reports" in table_names


class TestSessionManagement:
    """Test session management methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_create_session(self, manager):
        """Test creating a new session."""
        session_id = manager.create_session(
            request_id="req-123",
            user_prompt="Build a web app",
            budget_tier="balanced"
        )

        assert session_id is not None
        assert len(session_id) == 8  # UUID truncated to 8 chars

        session = manager.get_session(session_id)
        assert session is not None
        assert session["request_id"] == "req-123"
        assert session["user_prompt"] == "Build a web app"
        assert session["budget_tier"] == "balanced"
        assert session["status"] == "running"

    def test_create_session_with_title(self, manager):
        """Test creating a session with a title."""
        session_id = manager.create_session(
            request_id="req-456",
            user_prompt="Create API",
            title="API Development Project"
        )

        session = manager.get_session(session_id)
        assert session["title"] == "API Development Project"

    def test_update_session_title(self, manager):
        """Test updating session title."""
        session_id = manager.create_session(
            request_id="req-789",
            user_prompt="Test prompt"
        )

        manager.update_session_title(session_id, "New Title")

        session = manager.get_session(session_id)
        assert session["title"] == "New Title"

    def test_update_session_status(self, manager):
        """Test updating session status."""
        session_id = manager.create_session(
            request_id="req-001",
            user_prompt="Test"
        )

        manager.update_session_status(session_id, "completed")

        session = manager.get_session(session_id)
        assert session["status"] == "completed"
        assert session["completed_at"] is not None

    def test_update_session_status_failed(self, manager):
        """Test updating session status to failed with error."""
        session_id = manager.create_session(
            request_id="req-002",
            user_prompt="Test"
        )

        manager.update_session_status(session_id, "failed", error_message="Something broke")

        session = manager.get_session(session_id)
        assert session["status"] == "failed"
        assert session["error_message"] == "Something broke"

    def test_get_active_sessions(self, manager):
        """Test getting active sessions."""
        # Create multiple sessions
        manager.create_session("req-1", "Prompt 1")
        manager.create_session("req-2", "Prompt 2")
        session3_id = manager.create_session("req-3", "Prompt 3")

        # Mark one as completed
        manager.update_session_status(session3_id, "completed")

        active = manager.get_active_sessions()
        assert len(active) == 2
        for session in active:
            assert session["status"] == "running"

    def test_get_nonexistent_session(self, manager):
        """Test getting a session that doesn't exist."""
        session = manager.get_session("nonexistent-id")
        assert session is None


class TestAgentManagement:
    """Test agent management methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    @pytest.fixture
    def session_id(self, manager):
        """Create a session and return its ID."""
        return manager.create_session("req-test", "Test prompt")

    def test_register_agent(self, manager, session_id):
        """Test registering a new agent."""
        manager.register_agent(
            agent_id="agent-001",
            session_id=session_id,
            agent_type="developers/backend_developer",
            agent_name="Backend Developer",
            request_id="req-test",
            input_data={"task": "Build API"}
        )

        agent = manager.get_agent("agent-001")
        assert agent is not None
        assert agent["agent_type"] == "developers/backend_developer"
        assert agent["agent_name"] == "Backend Developer"
        assert agent["status"] == "pending"
        assert agent["input_data"]["task"] == "Build API"

    def test_register_root_agent(self, manager, session_id):
        """Test registering a root agent updates session."""
        manager.register_agent(
            agent_id="root-agent",
            session_id=session_id,
            agent_type="leadership/executive_director",
            agent_name="Executive Director"
        )

        session = manager.get_session(session_id)
        assert session["root_agent_id"] == "root-agent"

    def test_update_agent_status(self, manager, session_id):
        """Test updating agent status."""
        manager.register_agent(
            agent_id="agent-002",
            session_id=session_id,
            agent_type="test",
            agent_name="Test Agent"
        )

        manager.update_agent_status("agent-002", "running", iteration=1)

        agent = manager.get_agent("agent-002")
        assert agent["status"] == "running"
        assert agent["iteration"] == 1
        assert agent["started_at"] is not None

    def test_update_agent_status_completed(self, manager, session_id):
        """Test updating agent to completed status."""
        manager.register_agent(
            agent_id="agent-003",
            session_id=session_id,
            agent_type="test",
            agent_name="Test Agent"
        )

        manager.update_agent_status(
            "agent-003",
            "completed",
            output_data={"result": "success"},
            tokens_used=100,
            cost=0.01
        )

        agent = manager.get_agent("agent-003")
        assert agent["status"] == "completed"
        assert agent["output_data"]["result"] == "success"
        assert agent["tokens_used"] == 100
        assert agent["completed_at"] is not None

    def test_get_session_agents(self, manager, session_id):
        """Test getting all agents for a session."""
        manager.register_agent("agent-a", session_id, "type-a", "Agent A")
        manager.register_agent("agent-b", session_id, "type-b", "Agent B")
        manager.register_agent("agent-c", session_id, "type-c", "Agent C")

        agents = manager.get_session_agents(session_id)
        assert len(agents) == 3

    def test_get_running_agents(self, manager, session_id):
        """Test getting running agents."""
        manager.register_agent("agent-x", session_id, "type-x", "Agent X")
        manager.register_agent("agent-y", session_id, "type-y", "Agent Y")

        manager.update_agent_status("agent-x", "running")
        manager.update_agent_status("agent-y", "completed")

        running = manager.get_running_agents()
        assert len(running) == 1
        assert running[0]["agent_id"] == "agent-x"

    def test_restart_agent(self, manager, session_id):
        """Test restarting a failed agent."""
        manager.register_agent("agent-restart", session_id, "test", "Restart Agent")
        manager.update_agent_status("agent-restart", "failed", error_message="Crashed")

        result = manager.restart_agent("agent-restart")

        assert result is True
        agent = manager.get_agent("agent-restart")
        assert agent["status"] == "pending"
        assert agent["iteration"] == 0
        assert agent["error_message"] is None

    def test_restart_nonexistent_agent(self, manager):
        """Test restarting an agent that doesn't exist."""
        result = manager.restart_agent("nonexistent-agent")
        assert result is False


class TestMessageHistory:
    """Test message history methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    @pytest.fixture
    def agent_id(self, manager):
        """Create a session and agent, return agent ID."""
        session_id = manager.create_session("req", "prompt")
        manager.register_agent("agent-msg", session_id, "test", "Test")
        return "agent-msg"

    def test_record_message(self, manager, agent_id):
        """Test recording a message."""
        manager.record_message(agent_id, iteration=1, role="user", content="Hello")
        manager.record_message(agent_id, iteration=1, role="assistant", content="Hi there")

        messages = manager.get_agent_messages(agent_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_record_message_with_json_content(self, manager, agent_id):
        """Test recording a message with dict content."""
        manager.record_message(agent_id, iteration=1, role="assistant", content={"key": "value"})

        messages = manager.get_agent_messages(agent_id)
        assert len(messages) == 1
        # Content is serialized to JSON string
        assert "key" in messages[0]["content"]

    def test_record_message_truncates_long_content(self, manager, agent_id):
        """Test that very long messages are truncated."""
        long_content = "x" * 60000  # > 50KB
        manager.record_message(agent_id, iteration=1, role="user", content=long_content)

        messages = manager.get_agent_messages(agent_id)
        assert "[TRUNCATED]" in messages[0]["content"]
        assert len(messages[0]["content"]) < 60000

    def test_get_agent_messages_with_limit(self, manager, agent_id):
        """Test getting messages with limit."""
        for i in range(10):
            manager.record_message(agent_id, iteration=i, role="user", content=f"Message {i}")

        messages = manager.get_agent_messages(agent_id, limit=5)
        assert len(messages) == 5

    def test_get_resumable_messages(self, manager, agent_id):
        """Test getting resumable messages with smart truncation."""
        for i in range(100):
            manager.record_message(agent_id, iteration=i, role="user", content=f"Message {i}")

        messages = manager.get_resumable_messages(agent_id, max_messages=10)
        # Should get first message + last 9
        assert len(messages) == 10


class TestToolExecutions:
    """Test tool execution recording."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    @pytest.fixture
    def agent_id(self, manager):
        """Create a session and agent, return agent ID."""
        session_id = manager.create_session("req", "prompt")
        manager.register_agent("agent-tool", session_id, "test", "Test")
        return "agent-tool"

    def test_record_tool_execution(self, manager, agent_id):
        """Test recording a tool execution."""
        manager.record_tool_execution(
            agent_id=agent_id,
            tool_name="write_file",
            inputs={"file_path": "/test.txt", "content": "hello"},
            result={"success": True},
            success=True,
            duration_ms=150
        )

        executions = manager.get_agent_tool_executions(agent_id)
        assert len(executions) == 1
        assert executions[0]["tool_name"] == "write_file"
        assert executions[0]["success"] == 1


class TestDeliverables:
    """Test deliverable recording."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    @pytest.fixture
    def session_and_agent(self, manager):
        """Create a session and agent, return both IDs."""
        session_id = manager.create_session("req", "prompt")
        manager.register_agent("agent-del", session_id, "test", "Test")
        return session_id, "agent-del"

    def test_record_deliverable_file(self, manager, session_and_agent):
        """Test recording a file deliverable."""
        session_id, agent_id = session_and_agent

        manager.record_deliverable(
            session_id=session_id,
            agent_id=agent_id,
            deliverable_type="file",
            file_path="/src/main.py",
            description="Main application file",
            content_preview="import os..."
        )

        deliverables = manager.get_session_deliverables(session_id)
        assert len(deliverables) == 1
        assert deliverables[0]["deliverable_type"] == "file"
        assert deliverables[0]["file_path"] == "/src/main.py"

    def test_record_deliverable_commit(self, manager, session_and_agent):
        """Test recording a commit deliverable."""
        session_id, agent_id = session_and_agent

        manager.record_deliverable(
            session_id=session_id,
            agent_id=agent_id,
            deliverable_type="commit",
            commit_hash="abc123",
            description="Initial commit"
        )

        deliverables = manager.get_session_deliverables(session_id)
        assert len(deliverables) == 1
        assert deliverables[0]["commit_hash"] == "abc123"


class TestEventBus:
    """Test event bus methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_emit_event(self, manager):
        """Test emitting an event."""
        manager.emit_event(
            event_type="agent_started",
            session_id="sess-1",
            agent_id="agent-1",
            payload={"key": "value"}
        )

        events = manager.get_unprocessed_events()
        assert len(events) >= 1
        # Find our event (there may be others from session creation)
        our_event = next((e for e in events if e["event_type"] == "agent_started"), None)
        assert our_event is not None

    def test_mark_events_processed(self, manager):
        """Test marking events as processed."""
        manager.emit_event("test_event", payload={"test": True})

        events = manager.get_unprocessed_events()
        event_ids = [e["id"] for e in events]

        manager.mark_events_processed(event_ids)

        # Should be no unprocessed events now
        remaining = manager.get_unprocessed_events()
        assert len(remaining) == 0

    def test_subscribe_events(self, manager):
        """Test subscribing to events."""
        manager.emit_event("type_a", payload={"a": 1})
        manager.emit_event("type_b", payload={"b": 2})
        manager.emit_event("type_a", payload={"a": 3})

        # Subscribe to only type_a events
        events = manager.subscribe_events(event_types=["type_a"])
        type_a_events = [e for e in events if e["event_type"] == "type_a"]
        assert len(type_a_events) == 2


class TestRecoveryQueue:
    """Test recovery queue methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    @pytest.fixture
    def failed_agent(self, manager):
        """Create a failed agent for recovery testing."""
        session_id = manager.create_session("req", "prompt")
        manager.register_agent("failed-agent", session_id, "test", "Failed Agent")
        manager.update_agent_status("failed-agent", "failed", error_message="Crashed")
        return "failed-agent", session_id

    def test_queue_for_recovery(self, manager, failed_agent):
        """Test queueing an agent for recovery."""
        agent_id, session_id = failed_agent

        manager.queue_for_recovery(
            agent_id=agent_id,
            session_id=session_id,
            reason="Agent crashed",
            strategy="retry"
        )

        queue = manager.get_recovery_queue()
        assert len(queue) == 1
        assert queue[0]["agent_id"] == agent_id
        assert queue[0]["recovery_reason"] == "Agent crashed"

    def test_queue_prevents_duplicates(self, manager, failed_agent):
        """Test that duplicate queue entries are prevented."""
        agent_id, session_id = failed_agent

        manager.queue_for_recovery(agent_id, session_id, "reason1")
        manager.queue_for_recovery(agent_id, session_id, "reason2")

        queue = manager.get_recovery_queue()
        agent_entries = [q for q in queue if q["agent_id"] == agent_id]
        assert len(agent_entries) == 1

    def test_update_recovery_status(self, manager, failed_agent):
        """Test updating recovery task status."""
        agent_id, session_id = failed_agent
        manager.queue_for_recovery(agent_id, session_id, "reason")

        queue = manager.get_recovery_queue()
        recovery_id = queue[0]["id"]

        manager.update_recovery_status(recovery_id, "completed")

        # Should no longer appear in pending queue
        queue = manager.get_recovery_queue()
        assert len(queue) == 0


class TestPendingReviews:
    """Test pending reviews methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_add_pending_review(self, manager):
        """Test adding a pending review."""
        review_id = manager.add_pending_review(
            file_path="/src/requirements.md",
            file_type="markdown",
            detection_method="file_write",
            review_type="approval",
            content_preview="# Requirements"
        )

        assert review_id > 0

        reviews = manager.get_pending_reviews()
        assert len(reviews) == 1
        assert reviews[0]["file_path"] == "/src/requirements.md"

    def test_is_file_tracked_for_review(self, manager):
        """Test checking if file is already tracked."""
        manager.add_pending_review("/src/test.py", "python", "write")

        assert manager.is_file_tracked_for_review("/src/test.py") is True
        assert manager.is_file_tracked_for_review("/src/other.py") is False

    def test_get_pending_review(self, manager):
        """Test getting a single pending review."""
        review_id = manager.add_pending_review("/file.txt", "text", "write")

        review = manager.get_pending_review(review_id)
        assert review is not None
        assert review["file_path"] == "/file.txt"

    def test_update_pending_review(self, manager):
        """Test updating a pending review."""
        review_id = manager.add_pending_review("/file.txt", "text", "write")

        manager.update_pending_review(
            review_id,
            status="approved",
            execution_result={"success": True}
        )

        review = manager.get_pending_review(review_id)
        assert review["status"] == "approved"
        assert review["reviewed_at"] is not None


class TestStatistics:
    """Test statistics methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_get_swarm_stats(self, manager):
        """Test getting swarm statistics."""
        # Create some test data
        session1 = manager.create_session("req1", "prompt1")
        session2 = manager.create_session("req2", "prompt2")
        manager.update_session_status(session2, "completed")

        manager.register_agent("a1", session1, "type", "Agent 1")
        manager.register_agent("a2", session1, "type", "Agent 2")
        manager.update_agent_status("a1", "running")
        manager.update_agent_status("a2", "completed")

        stats = manager.get_swarm_stats()

        assert "sessions" in stats
        assert "agents" in stats
        assert stats["sessions"]["total"] == 2
        assert stats["sessions"]["running"] == 1
        assert stats["sessions"]["completed"] == 1
        assert stats["agents"]["total"] == 2

    def test_get_stats_alias(self, manager):
        """Test get_stats is an alias for get_swarm_stats."""
        stats1 = manager.get_stats()
        stats2 = manager.get_swarm_stats()
        assert stats1 == stats2

    def test_get_agents_summary(self, manager):
        """Test getting agent summary."""
        session = manager.create_session("req", "prompt")
        manager.register_agent("a1", session, "type", "Backend Developer")
        manager.register_agent("a2", session, "type", "Backend Developer")
        manager.register_agent("a3", session, "type", "Frontend Developer")

        summary = manager.get_agents_summary()
        assert len(summary) >= 2


class TestStalledDetection:
    """Test stalled session and agent detection."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_get_stalled_agents(self, manager):
        """Test getting stalled agents."""
        session_id = manager.create_session("req", "prompt")
        manager.register_agent("stalled-agent", session_id, "test", "Test")

        # Manually update last_checkpoint to be old
        with manager._get_connection() as conn:
            conn.execute("""
                UPDATE agents
                SET status = 'running', last_checkpoint = datetime('now', '-10 minutes')
                WHERE agent_id = ?
            """, ("stalled-agent",))
            conn.commit()

        stalled = manager.get_stalled_agents(stall_threshold_minutes=5)
        assert len(stalled) == 1
        assert stalled[0]["agent_id"] == "stalled-agent"


class TestQueryMethods:
    """Test advanced query methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_get_sessions_with_status_filter(self, manager):
        """Test getting sessions filtered by status."""
        s1 = manager.create_session("r1", "p1")
        s2 = manager.create_session("r2", "p2")
        manager.update_session_status(s2, "completed")

        completed = manager.get_sessions(status="completed")
        assert len(completed) == 1
        assert completed[0]["session_id"] == s2

    def test_get_agents_with_filters(self, manager):
        """Test getting agents with filters."""
        session = manager.create_session("req", "prompt")
        manager.register_agent("a1", session, "type1", "Agent 1")
        manager.register_agent("a2", session, "type2", "Agent 2")
        manager.update_agent_status("a1", "running")
        manager.update_agent_status("a2", "completed")

        running = manager.get_agents(session_id=session, status="running")
        assert len(running) == 1
        assert running[0]["agent_id"] == "a1"

    def test_get_events_with_filters(self, manager):
        """Test getting events with filters."""
        session = manager.create_session("req", "prompt")
        manager.register_agent("ag1", session, "test", "Test Agent")

        manager.emit_event("type_a", session_id=session)
        manager.emit_event("type_b", agent_id="ag1")
        manager.emit_event("type_a", session_id=session, agent_id="ag1")

        # Filter by session
        session_events = manager.get_events(session_id=session)
        assert len([e for e in session_events if e["session_id"] == session]) >= 1

        # Filter by agent
        agent_events = manager.get_events(agent_id="ag1")
        assert len([e for e in agent_events if e["agent_id"] == "ag1"]) >= 1

        # Filter by event type
        type_events = manager.get_events(event_type="type_a")
        assert len([e for e in type_events if e["event_type"] == "type_a"]) >= 1


class TestCleanupAndMaintenance:
    """Test cleanup and maintenance methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_cleanup_old_data(self, manager):
        """Test cleaning up old data."""
        # Create some data
        manager.emit_event("old_event", payload={"test": True})
        manager.mark_events_processed([1])  # Mark as processed

        # Run cleanup (with a very short retention of 0 days for testing)
        manager.cleanup_old_data(days=0)

        # Should have cleaned up old processed events
        # (exact behavior depends on timing, just verify no crash)


class TestImprovementReports:
    """Test improvement reports methods."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_add_improvement_report(self, manager):
        """Test adding an improvement report."""
        session = manager.create_session("req", "prompt")
        manager.register_agent("agent-imp", session, "test", "Test Agent")

        report_id = manager.add_improvement_report(
            agent_id="agent-imp",
            agent_name="Test Agent",
            issue_type="model_recommendation",
            file_path="/path/to/agent.md",
            detection_method="self_improvement",
            severity="warning",
            recommendation="Upgrade model",
            session_id=session,
            request_id="req"
        )

        assert report_id > 0

    def test_get_improvement_reports(self, manager):
        """Test getting improvement reports."""
        session = manager.create_session("req", "prompt")
        manager.register_agent("agent-rep", session, "test", "Test Agent")

        manager.add_improvement_report(
            agent_id="agent-rep",
            agent_name="Test Agent",
            issue_type="performance",
            file_path="/path/to/file.md",
            detection_method="analysis"
        )

        reports = manager.get_improvement_reports(agent_id="agent-rep")
        assert len(reports) == 1
        assert reports[0]["issue_type"] == "performance"


class TestRestartAgentAdvanced:
    """Test advanced restart agent functionality."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_restart_agent_with_new_max_iterations(self, manager):
        """Test restarting agent with new max iterations."""
        session = manager.create_session("req", "prompt")
        manager.register_agent("agent-iter", session, "test", "Test", max_iterations=5)

        result = manager.restart_agent("agent-iter", new_max_iterations=20)

        assert result is True
        agent = manager.get_agent("agent-iter")
        assert agent["max_iterations"] == 20


class TestRecoveryStatusAdvanced:
    """Test advanced recovery status functionality."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_update_recovery_status_with_increment(self, manager):
        """Test updating recovery with attempts increment."""
        session = manager.create_session("req", "prompt")
        manager.register_agent("agent-rec", session, "test", "Test")
        manager.update_agent_status("agent-rec", "failed")
        manager.queue_for_recovery("agent-rec", session, "reason")

        queue = manager.get_recovery_queue()
        recovery_id = queue[0]["id"]
        initial_attempts = queue[0]["attempts"]

        manager.update_recovery_status(recovery_id, "in_progress", increment_attempts=True)

        # Verify attempts incremented
        with manager._get_connection() as conn:
            row = conn.execute(
                "SELECT attempts FROM recovery_queue WHERE id = ?",
                (recovery_id,)
            ).fetchone()
            assert row[0] == initial_attempts + 1


class TestPendingReviewAdvanced:
    """Test advanced pending review functionality."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        SwarmStateManager._instance = None
        yield
        SwarmStateManager._instance = None

    @pytest.fixture
    def manager(self):
        """Create a SwarmStateManager with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_swarm.db"
            manager = SwarmStateManager(db_path=db_path)
            yield manager

    def test_pending_review_with_action_params(self, manager):
        """Test pending review with action params."""
        review_id = manager.add_pending_review(
            file_path="/test.py",
            file_type="python",
            detection_method="write",
            action="create_file",
            action_params={"target": "/dest/test.py", "mode": "755"}
        )

        review = manager.get_pending_review(review_id)
        assert review["action_params"]["target"] == "/dest/test.py"
        assert review["action_params"]["mode"] == "755"

    def test_update_pending_review_no_changes(self, manager):
        """Test update_pending_review with no changes does nothing."""
        review_id = manager.add_pending_review("/file.txt", "text", "write")

        # Call with no changes
        manager.update_pending_review(review_id)

        # Verify no crash, status unchanged
        review = manager.get_pending_review(review_id)
        assert review["status"] == "pending"


class TestGlobalAccessor:
    """Test the global accessor function."""

    @pytest.fixture(autouse=True)
    def reset_singleton_and_global(self):
        """Reset the singleton and global for each test."""
        import src.runtime.agents.swarm_state as swarm_module
        SwarmStateManager._instance = None
        swarm_module._swarm_state_manager = None
        yield
        SwarmStateManager._instance = None
        swarm_module._swarm_state_manager = None

    def test_get_swarm_state_creates_singleton(self):
        """Test get_swarm_state creates singleton."""
        manager1 = get_swarm_state()
        manager2 = get_swarm_state()

        assert manager1 is manager2
        assert isinstance(manager1, SwarmStateManager)
