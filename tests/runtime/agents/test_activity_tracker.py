"""
Unit tests for activity_tracker module.

Tests the agent activity tracking system, focusing on completion data capture.
"""

import pytest
from datetime import datetime
from src.runtime.agents.activity_tracker import (
    AgentActivityTracker,
    Activity,
    ActivityType
)


class TestAgentActivityTracker:
    """Test AgentActivityTracker class."""

    def test_tracker_initialization(self):
        """Test basic initialization."""
        # Disable persistence to avoid loading state from previous runs
        tracker = AgentActivityTracker(enable_persistence=False)
        assert len(tracker.activities) == 0
        assert len(tracker.agent_hierarchy) == 0
        assert len(tracker.agent_states) == 0
        assert tracker.max_activities == 10000

    def test_record_agent_started(self):
        """Test recording agent start."""
        # Disable persistence to avoid loading state from previous runs
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="test-agent-1",
            agent_name="Test Agent",
            agent_type="Test Type",
            request_id="req-123",
            parent_agent_id=None,
            input_data={"task": "test task"},
            model="claude-3-5-sonnet-20241022"
        )

        assert len(tracker.activities) == 1
        assert tracker.activities[0].activity_type == ActivityType.AGENT_STARTED
        assert tracker.activities[0].agent_id == "test-agent-1"

        # Check hierarchy
        assert "test-agent-1" in tracker.agent_hierarchy
        assert tracker.agent_hierarchy["test-agent-1"]["status"] == "running"

        # Check state
        assert "test-agent-1" in tracker.agent_states
        assert tracker.agent_states["test-agent-1"]["status"] == "running"


class TestAgentCompletionDataCapture:
    """Test agent completion data capture functionality."""

    def test_record_agent_completed_with_summary(self):
        """Test recording agent completion with summary."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Start agent first
        tracker.record_agent_started(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_type="Developer",
            request_id="req-123"
        )

        # Complete agent with result containing summary
        result = {
            "status": "success",
            "summary": "Successfully implemented user authentication feature",
            "self_analysis": "Implementation follows best practices",
            "deliverables": ["auth.py", "test_auth.py"]
        }

        tracker.record_agent_completed(
            agent_id="agent-1",
            agent_name="Test Agent",
            request_id="req-123",
            result=result
        )

        # Verify activity recorded
        assert len(tracker.activities) == 2
        completed_activity = tracker.activities[1]
        assert completed_activity.activity_type == ActivityType.AGENT_COMPLETED

        # Verify state updated with completion data
        agent_state = tracker.agent_states["agent-1"]
        assert agent_state["status"] == "completed"
        assert agent_state["summary"] == "Successfully implemented user authentication feature"
        assert agent_state["self_analysis"] == "Implementation follows best practices"
        assert agent_state["deliverables"] == ["auth.py", "test_auth.py"]

    def test_record_agent_completed_without_summary(self):
        """Test recording agent completion without summary (backward compatibility)."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Start agent
        tracker.record_agent_started(
            agent_id="agent-2",
            agent_name="Test Agent 2",
            agent_type="Developer",
            request_id="req-456"
        )

        # Complete without summary (old format)
        result = {
            "status": "success",
            "files": ["output.txt"]
        }

        tracker.record_agent_completed(
            agent_id="agent-2",
            agent_name="Test Agent 2",
            request_id="req-456",
            result=result
        )

        # Verify graceful handling - empty strings/lists
        agent_state = tracker.agent_states["agent-2"]
        assert agent_state["status"] == "completed"
        assert agent_state["summary"] == ""
        assert agent_state["self_analysis"] == ""
        assert agent_state["deliverables"] == []

    def test_record_agent_completed_with_none_result(self):
        """Test recording agent completion with None result."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Start agent
        tracker.record_agent_started(
            agent_id="agent-3",
            agent_name="Test Agent 3",
            agent_type="Developer",
            request_id="req-789"
        )

        # Complete with None result
        tracker.record_agent_completed(
            agent_id="agent-3",
            agent_name="Test Agent 3",
            request_id="req-789",
            result=None
        )

        # Verify graceful handling - empty strings/lists
        agent_state = tracker.agent_states["agent-3"]
        assert agent_state["status"] == "completed"
        assert agent_state["summary"] == ""
        assert agent_state["self_analysis"] == ""
        assert agent_state["deliverables"] == []

    def test_record_agent_completed_with_partial_data(self):
        """Test recording agent completion with partial completion data."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Start agent
        tracker.record_agent_started(
            agent_id="agent-4",
            agent_name="Test Agent 4",
            agent_type="Developer",
            request_id="req-101"
        )

        # Complete with only summary, no deliverables
        result = {
            "status": "success",
            "summary": "Task completed successfully"
        }

        tracker.record_agent_completed(
            agent_id="agent-4",
            agent_name="Test Agent 4",
            request_id="req-101",
            result=result
        )

        # Verify partial data handled correctly
        agent_state = tracker.agent_states["agent-4"]
        assert agent_state["summary"] == "Task completed successfully"
        assert agent_state["self_analysis"] == ""  # Missing field defaults to empty
        assert agent_state["deliverables"] == []  # Missing field defaults to empty list

    def test_record_agent_completed_with_multiple_deliverables(self):
        """Test recording agent completion with multiple deliverables."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Start agent
        tracker.record_agent_started(
            agent_id="agent-5",
            agent_name="Test Agent 5",
            agent_type="Developer",
            request_id="req-202"
        )

        # Complete with multiple deliverables
        result = {
            "status": "success",
            "summary": "Implemented complete feature with tests",
            "deliverables": [
                "src/feature.py",
                "src/utils.py",
                "tests/test_feature.py",
                "tests/test_utils.py",
                "docs/feature.md"
            ]
        }

        tracker.record_agent_completed(
            agent_id="agent-5",
            agent_name="Test Agent 5",
            request_id="req-202",
            result=result
        )

        # Verify all deliverables captured
        agent_state = tracker.agent_states["agent-5"]
        assert len(agent_state["deliverables"]) == 5
        assert "src/feature.py" in agent_state["deliverables"]
        assert "docs/feature.md" in agent_state["deliverables"]


class TestAgentStateRetrieval:
    """Test agent state retrieval with completion data."""

    def test_get_agent_state_with_completion_data(self):
        """Test retrieving agent state includes completion data."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Start and complete agent
        tracker.record_agent_started(
            agent_id="agent-6",
            agent_name="Test Agent 6",
            agent_type="Developer",
            request_id="req-303"
        )

        result = {
            "summary": "Feature implemented successfully",
            "self_analysis": "Code quality is good",
            "deliverables": ["feature.py"]
        }

        tracker.record_agent_completed(
            agent_id="agent-6",
            agent_name="Test Agent 6",
            request_id="req-303",
            result=result
        )

        # Get agent state
        state = tracker.get_agent_state("agent-6")

        assert state is not None
        assert state["status"] == "completed"
        assert "summary" in state
        assert "self_analysis" in state
        assert "deliverables" in state

    def test_get_all_agent_states_includes_completion_data(self):
        """Test retrieving all agent states includes completion data."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Create multiple completed agents
        for i in range(3):
            agent_id = f"agent-{i}"
            tracker.record_agent_started(
                agent_id=agent_id,
                agent_name=f"Agent {i}",
                agent_type="Developer",
                request_id="req-404"
            )

            result = {
                "summary": f"Agent {i} completed task",
                "deliverables": [f"file{i}.py"]
            }

            tracker.record_agent_completed(
                agent_id=agent_id,
                agent_name=f"Agent {i}",
                request_id="req-404",
                result=result
            )

        # Get all states
        all_states = tracker.get_all_agent_states()

        assert len(all_states) == 3
        for i in range(3):
            agent_id = f"agent-{i}"
            assert agent_id in all_states
            assert "summary" in all_states[agent_id]
            assert all_states[agent_id]["summary"] == f"Agent {i} completed task"


class TestAgentCompletionActivity:
    """Test agent completion activity data."""

    def test_completion_activity_includes_result(self):
        """Test completion activity includes full result in data."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent-7",
            agent_name="Test Agent 7",
            agent_type="Developer",
            request_id="req-505"
        )

        result = {
            "summary": "Task completed",
            "deliverables": ["file.py"]
        }

        tracker.record_agent_completed(
            agent_id="agent-7",
            agent_name="Test Agent 7",
            request_id="req-505",
            result=result
        )

        # Get completion activity
        activities = tracker.get_activities(
            agent_id="agent-7",
            activity_types=[ActivityType.AGENT_COMPLETED]
        )

        assert len(activities) == 1
        assert activities[0]["data"]["result"] == result

    def test_multiple_agents_completion_data_isolated(self):
        """Test completion data is isolated between agents."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Create two agents with different results
        for i in [1, 2]:
            agent_id = f"agent-isolated-{i}"
            tracker.record_agent_started(
                agent_id=agent_id,
                agent_name=f"Agent {i}",
                agent_type="Developer",
                request_id="req-606"
            )

            result = {
                "summary": f"Agent {i} unique summary",
                "deliverables": [f"agent{i}_file.py"]
            }

            tracker.record_agent_completed(
                agent_id=agent_id,
                agent_name=f"Agent {i}",
                request_id="req-606",
                result=result
            )

        # Verify isolation
        state1 = tracker.get_agent_state("agent-isolated-1")
        state2 = tracker.get_agent_state("agent-isolated-2")

        assert state1["summary"] == "Agent 1 unique summary"
        assert state2["summary"] == "Agent 2 unique summary"
        assert state1["deliverables"] == ["agent1_file.py"]
        assert state2["deliverables"] == ["agent2_file.py"]


class TestCallbacks:
    """Test activity callbacks with completion data."""

    def test_completion_callback_receives_activity(self):
        """Test callbacks receive agent completion activities."""
        tracker = AgentActivityTracker(enable_persistence=False)
        received_activities = []

        def callback(activity):
            received_activities.append(activity)

        tracker.register_callback(callback)

        tracker.record_agent_started(
            agent_id="agent-8",
            agent_name="Test Agent 8",
            agent_type="Developer",
            request_id="req-707"
        )

        result = {
            "summary": "Callback test completed",
            "deliverables": ["test.py"]
        }

        tracker.record_agent_completed(
            agent_id="agent-8",
            agent_name="Test Agent 8",
            request_id="req-707",
            result=result
        )

        # Verify callback received activities
        assert len(received_activities) == 2  # started + completed

        completion_activity = received_activities[1]
        assert completion_activity.activity_type == ActivityType.AGENT_COMPLETED
        assert completion_activity.data["result"]["summary"] == "Callback test completed"
