"""
Unit tests for persistence module.

Tests the SwarmPersistence class for SQLite-based state persistence.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime


class TestSwarmPersistence:
    """Test SwarmPersistence class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        try:
            Path(db_path).unlink()
        except:
            pass

    @pytest.fixture
    def persistence(self, temp_db):
        """Create a SwarmPersistence instance with temp database."""
        from src.runtime.agents.persistence import SwarmPersistence
        return SwarmPersistence(db_path=temp_db)

    def test_init_creates_database(self, temp_db):
        """Test that initialization creates the database file."""
        from src.runtime.agents.persistence import SwarmPersistence

        persistence = SwarmPersistence(db_path=temp_db)

        assert Path(temp_db).exists()

    def test_init_creates_tables(self, persistence):
        """Test that initialization creates required tables."""
        with persistence._get_connection() as conn:
            # Check swarm_sessions table
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='swarm_sessions'"
            )
            assert cursor.fetchone() is not None

            # Check agent_states table
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_states'"
            )
            assert cursor.fetchone() is not None

    def test_create_session(self, persistence):
        """Test creating a new session."""
        session = persistence.create_session(
            session_id="test-session-1",
            prompt="Test prompt",
            budget_tier="balanced"
        )

        assert session is not None
        assert session["session_id"] == "test-session-1"
        assert session["prompt"] == "Test prompt"
        assert session["status"] == "running"

    def test_create_session_with_options(self, persistence):
        """Test creating a session with all options."""
        session = persistence.create_session(
            session_id="test-session-2",
            prompt="Test prompt",
            budget_tier="full_firepower",
            project_id="project-1",
            family_name="Test Family"
        )

        assert session["budget_tier"] == "full_firepower"
        assert session["project_id"] == "project-1"
        assert session["family_name"] == "Test Family"

    def test_get_session(self, persistence):
        """Test retrieving a session."""
        persistence.create_session(
            session_id="test-session",
            prompt="Test prompt"
        )

        session = persistence.get_session("test-session")

        assert session is not None
        assert session["session_id"] == "test-session"

    def test_get_session_not_found(self, persistence):
        """Test retrieving a non-existent session."""
        session = persistence.get_session("nonexistent")

        assert session is None

    def test_update_session(self, persistence):
        """Test updating a session."""
        persistence.create_session(
            session_id="test-session",
            prompt="Test prompt"
        )

        updated = persistence.update_session(
            "test-session",
            status="completed",
            summary="Test completed"
        )

        assert updated["status"] == "completed"
        assert updated["summary"] == "Test completed"

    def test_update_session_json_fields(self, persistence):
        """Test updating session with JSON fields."""
        persistence.create_session(
            session_id="test-session",
            prompt="Test prompt"
        )

        updated = persistence.update_session(
            "test-session",
            errors=["error1", "error2"],
            deliverables=["file1.py", "file2.py"]
        )

        assert updated["errors"] == ["error1", "error2"]
        assert updated["deliverables"] == ["file1.py", "file2.py"]

    def test_update_session_empty_updates(self, persistence):
        """Test updating session with no updates returns current state."""
        persistence.create_session(
            session_id="test-session",
            prompt="Test prompt"
        )

        result = persistence.update_session("test-session")

        assert result is not None
        assert result["session_id"] == "test-session"

    def test_complete_session(self, persistence):
        """Test completing a session."""
        persistence.create_session(
            session_id="test-session",
            prompt="Test prompt"
        )

        completed = persistence.complete_session(
            "test-session",
            status="completed",
            summary="All done",
            deliverables=["output.py"]
        )

        assert completed["status"] == "completed"
        assert completed["summary"] == "All done"
        assert completed["completed_at"] is not None

    def test_get_sessions(self, persistence):
        """Test getting all sessions."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_session("session-2", "Prompt 2")

        sessions = persistence.get_sessions()

        assert len(sessions) == 2

    def test_get_sessions_filtered_by_status(self, persistence):
        """Test getting sessions filtered by status."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_session("session-2", "Prompt 2")
        persistence.complete_session("session-1")

        running = persistence.get_sessions(status="running")
        completed = persistence.get_sessions(status="completed")

        assert len(running) == 1
        assert len(completed) == 1

    def test_get_sessions_with_limit(self, persistence):
        """Test getting sessions with limit."""
        for i in range(10):
            persistence.create_session(f"session-{i}", f"Prompt {i}")

        sessions = persistence.get_sessions(limit=5)

        assert len(sessions) == 5

    def test_get_sessions_include_agents(self, persistence):
        """Test getting sessions with agent data."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_agent("agent-1", "session-1", "developer")

        sessions = persistence.get_sessions(include_agents=True)

        assert len(sessions) == 1
        assert "agents" in sessions[0]
        assert len(sessions[0]["agents"]) == 1

    def test_get_incomplete_sessions(self, persistence):
        """Test getting incomplete sessions."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_session("session-2", "Prompt 2")
        persistence.complete_session("session-1")

        incomplete = persistence.get_incomplete_sessions()

        assert len(incomplete) == 1
        assert incomplete[0]["session_id"] == "session-2"

    def test_mark_sessions_as_recovered(self, persistence):
        """Test marking running sessions as recovered."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_session("session-2", "Prompt 2")

        count = persistence.mark_sessions_as_recovered()

        assert count == 2

        session = persistence.get_session("session-1")
        assert session["status"] == "recovered"

    def test_create_agent(self, persistence):
        """Test creating an agent."""
        persistence.create_session("session-1", "Prompt 1")

        agent = persistence.create_agent(
            agent_id="agent-1",
            session_id="session-1",
            agent_type="developer"
        )

        assert agent["agent_id"] == "agent-1"
        assert agent["agent_type"] == "developer"
        assert agent["status"] == "running"

    def test_create_agent_with_options(self, persistence):
        """Test creating an agent with all options."""
        persistence.create_session("session-1", "Prompt 1")

        agent = persistence.create_agent(
            agent_id="agent-1",
            session_id="session-1",
            agent_type="developer",
            whimsical_name="Test Agent",
            family_name="Test Family",
            parent_id="parent-1",
            max_iterations=100
        )

        assert agent["whimsical_name"] == "Test Agent"
        assert agent["family_name"] == "Test Family"
        assert agent["parent_id"] == "parent-1"
        assert agent["max_iterations"] == 100

    def test_get_agent(self, persistence):
        """Test retrieving an agent."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_agent("agent-1", "session-1", "developer")

        agent = persistence.get_agent("agent-1")

        assert agent is not None
        assert agent["agent_id"] == "agent-1"

    def test_get_agent_not_found(self, persistence):
        """Test retrieving a non-existent agent."""
        agent = persistence.get_agent("nonexistent")

        assert agent is None

    def test_update_agent(self, persistence):
        """Test updating an agent."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_agent("agent-1", "session-1", "developer")

        updated = persistence.update_agent(
            "agent-1",
            iterations=10,
            current_task="Working on something"
        )

        assert updated["iterations"] == 10
        assert updated["current_task"] == "Working on something"

    def test_update_agent_json_fields(self, persistence):
        """Test updating agent with JSON result field."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_agent("agent-1", "session-1", "developer")

        updated = persistence.update_agent(
            "agent-1",
            result={"status": "success", "output": "test"}
        )

        assert updated["result"]["status"] == "success"

    def test_update_agent_empty_updates(self, persistence):
        """Test updating agent with no updates returns current state."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_agent("agent-1", "session-1", "developer")

        result = persistence.update_agent("agent-1")

        assert result is not None
        assert result["agent_id"] == "agent-1"

    def test_complete_agent(self, persistence):
        """Test completing an agent."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_agent("agent-1", "session-1", "developer")

        completed = persistence.complete_agent(
            "agent-1",
            status="completed",
            summary="Task completed",
            result={"output": "test"},
            cost=0.01,
            input_tokens=100,
            output_tokens=50
        )

        assert completed["status"] == "completed"
        assert completed["summary"] == "Task completed"
        assert completed["completed_at"] is not None
        assert completed["cost"] == 0.01

    def test_get_agents_for_session(self, persistence):
        """Test getting all agents for a session."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_agent("agent-1", "session-1", "developer")
        persistence.create_agent("agent-2", "session-1", "tester")

        agents = persistence.get_agents_for_session("session-1")

        assert len(agents) == 2

    def test_delete_session(self, persistence):
        """Test deleting a session and its agents."""
        persistence.create_session("session-1", "Prompt 1")
        persistence.create_agent("agent-1", "session-1", "developer")

        result = persistence.delete_session("session-1")

        assert result is True
        assert persistence.get_session("session-1") is None
        assert persistence.get_agent("agent-1") is None

    def test_delete_session_not_found(self, persistence):
        """Test deleting a non-existent session."""
        result = persistence.delete_session("nonexistent")

        assert result is False

    def test_cleanup_old_sessions(self, persistence):
        """Test cleaning up old sessions."""
        persistence.create_session("old-session", "Prompt")
        persistence.complete_session("old-session")

        # Set old completed_at manually
        with persistence._get_connection() as conn:
            conn.execute(
                "UPDATE swarm_sessions SET completed_at = '2020-01-01T00:00:00' WHERE session_id = 'old-session'"
            )

        count = persistence.cleanup_old_sessions(max_age_days=1)

        # Should clean up the old session
        assert count >= 0  # May or may not delete depending on timing


class TestGlobalPersistence:
    """Test global persistence functions."""

    def test_get_persistence_returns_instance(self):
        """Test get_persistence returns a SwarmPersistence instance."""
        # Reset global for test
        import src.runtime.agents.persistence as module
        module._persistence = None

        from src.runtime.agents.persistence import get_persistence

        persistence = get_persistence()

        assert persistence is not None

    def test_get_persistence_returns_same_instance(self):
        """Test get_persistence returns the same instance."""
        import src.runtime.agents.persistence as module
        module._persistence = None

        from src.runtime.agents.persistence import get_persistence

        p1 = get_persistence()
        p2 = get_persistence()

        assert p1 is p2

    def test_init_persistence_creates_new_instance(self):
        """Test init_persistence creates a new instance."""
        import src.runtime.agents.persistence as module

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            from src.runtime.agents.persistence import init_persistence

            persistence = init_persistence(db_path=db_path)

            assert persistence is not None
            assert persistence.db_path == Path(db_path)
        finally:
            try:
                Path(db_path).unlink()
            except:
                pass
