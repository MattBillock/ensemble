"""
Comprehensive tests for activity_tracker module.

Tests additional methods not covered by existing tests to achieve 90%+ coverage.
"""

import pytest
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

from src.runtime.agents.activity_tracker import (
    ActivityTracker,
    AgentActivityTracker,
    Activity,
    ActivityType,
)


class TestSimpleActivityTracker:
    """Test the simple ActivityTracker class (request lifecycle)."""

    def test_init(self):
        """Test basic initialization."""
        tracker = ActivityTracker()
        assert hasattr(tracker, '_active_requests')
        assert hasattr(tracker, '_completed_requests')
        assert tracker._active_requests == {}
        assert tracker._completed_requests == {}

    def test_cleanup_empty(self):
        """Test cleanup on empty tracker."""
        tracker = ActivityTracker()
        tracker.cleanup()  # Should not raise
        assert tracker._active_requests == {}

    def test_cleanup_removes_completed_requests(self):
        """Test cleanup removes completed requests."""
        tracker = ActivityTracker()

        class MockRequest:
            is_completed = True
            is_stale = False

        tracker._active_requests['req1'] = MockRequest()
        tracker.cleanup()
        assert 'req1' not in tracker._active_requests

    def test_cleanup_removes_stale_requests(self):
        """Test cleanup removes stale requests."""
        tracker = ActivityTracker()

        class MockRequest:
            is_completed = False
            is_stale = True

        tracker._active_requests['req1'] = MockRequest()
        tracker.cleanup()
        assert 'req1' not in tracker._active_requests

    def test_cleanup_with_max_age(self):
        """Test cleanup with max_age removes old requests."""
        tracker = ActivityTracker()

        class OldRequest:
            is_completed = False
            is_stale = False
            timestamp = time.time() - 100  # 100 seconds old

        tracker._active_requests['old_req'] = OldRequest()
        tracker.cleanup(max_age=50)  # Remove requests older than 50 seconds
        assert 'old_req' not in tracker._active_requests

    def test_cleanup_keeps_recent_requests(self):
        """Test cleanup keeps recent requests when max_age specified."""
        tracker = ActivityTracker()

        class RecentRequest:
            is_completed = False
            is_stale = False
            timestamp = time.time()  # Just created

        tracker._active_requests['recent'] = RecentRequest()
        tracker.cleanup(max_age=50)
        assert 'recent' in tracker._active_requests

    def test_cleanup_calls_cleanup_method(self):
        """Test cleanup calls cleanup method on request if available."""
        tracker = ActivityTracker()

        cleanup_called = []

        class RequestWithCleanup:
            is_completed = True
            is_stale = False

            def cleanup(self):
                cleanup_called.append(True)

        tracker._active_requests['req1'] = RequestWithCleanup()
        tracker.cleanup()
        assert len(cleanup_called) == 1

    def test_cleanup_handles_cleanup_failure(self):
        """Test cleanup continues if request cleanup raises."""
        tracker = ActivityTracker()

        class RequestWithFailingCleanup:
            is_completed = True
            is_stale = False

            def cleanup(self):
                raise Exception("Cleanup failed")

        tracker._active_requests['req1'] = RequestWithFailingCleanup()
        tracker.cleanup()  # Should not raise
        assert 'req1' not in tracker._active_requests

    @pytest.mark.asyncio
    async def test_cleanup_async(self):
        """Test async cleanup wrapper."""
        tracker = ActivityTracker()

        class MockRequest:
            is_completed = True
            is_stale = False

        tracker._active_requests['req1'] = MockRequest()
        await tracker.cleanup_async()
        assert 'req1' not in tracker._active_requests


class TestAgentActivityTrackerPersistence:
    """Test persistence (_save_state, _load_state) functionality."""

    def test_save_and_load_state(self):
        """Test that state is saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = AgentActivityTracker(state_dir=tmpdir, enable_persistence=True)

            # Record some activities
            tracker.record_agent_started(
                agent_id="agent1",
                agent_name="Test Agent",
                agent_type="leadership",
                request_id="req1"
            )
            tracker.record_request_started(
                request_id="req1",
                prompt="Test prompt",
                budget_tier="balanced"
            )

            # Force save
            tracker._save_state()

            # Create new tracker with same state dir
            tracker2 = AgentActivityTracker(state_dir=tmpdir, enable_persistence=True)

            # Verify state was loaded
            assert "agent1" in tracker2.agent_states
            assert "req1" in tracker2.requests

    def test_persistence_disabled(self):
        """Test that persistence can be disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = AgentActivityTracker(state_dir=tmpdir, enable_persistence=False)

            tracker.record_agent_started(
                agent_id="agent1",
                agent_name="Test Agent",
                agent_type="leadership",
                request_id="req1"
            )

            # Should not create state file
            state_file = Path(tmpdir) / AgentActivityTracker.STATE_FILENAME
            assert not state_file.exists()

    def test_load_state_with_invalid_version(self):
        """Test loading state with unknown version is skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / AgentActivityTracker.STATE_FILENAME
            state_file.parent.mkdir(parents=True, exist_ok=True)

            # Write state with invalid version
            import json
            with open(state_file, 'w') as f:
                json.dump({"version": 999}, f)

            tracker = AgentActivityTracker(state_dir=tmpdir, enable_persistence=True)
            assert len(tracker.activities) == 0

    def test_load_state_marks_running_as_recovered(self):
        """Test that running agents are marked as recovered on load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First tracker creates running agent
            tracker1 = AgentActivityTracker(state_dir=tmpdir, enable_persistence=True)
            tracker1.record_agent_started(
                agent_id="agent1",
                agent_name="Test Agent",
                agent_type="leadership",
                request_id="req1"
            )
            tracker1._save_state()

            # Second tracker loads and should mark as recovered
            tracker2 = AgentActivityTracker(state_dir=tmpdir, enable_persistence=True)
            state = tracker2.get_agent_state("agent1")
            assert state["status"] == "recovered"


class TestRecordIterationStarted:
    """Test record_iteration_started method."""

    def test_record_iteration_started(self):
        """Test recording iteration start."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_iteration_started(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            iteration=1,
            max_iterations=10
        )

        state = tracker.get_agent_state("agent1")
        assert state is not None
        assert state.get("current_iteration") == 1

    def test_iteration_updates_agent_state(self):
        """Test that iterations update agent state correctly."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        # Record multiple iterations
        for i in range(1, 4):
            tracker.record_iteration_started(
                agent_id="agent1",
                agent_name="Test Agent",
                request_id="req1",
                iteration=i,
                max_iterations=10
            )

        state = tracker.get_agent_state("agent1")
        assert state["current_iteration"] == 3
        assert state["max_iterations"] == 10

    def test_iteration_with_prompt(self):
        """Test recording iteration with prompt."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_iteration_started(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            iteration=1,
            max_iterations=10,
            prompt="Long prompt text..." * 50  # Should be truncated
        )

        activities = tracker.get_activities(agent_id="agent1")
        # Find iteration activity
        iter_activity = [a for a in activities if a["activity_type"] == "iteration_started"]
        assert len(iter_activity) == 1


class TestRecordToolUse:
    """Test record_tool_use method."""

    def test_record_tool_use_started(self):
        """Test recording tool use start."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_tool_use(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            iteration=1,
            tool_name="read_file",
            tool_inputs={"path": "/test/file.txt"},
            status="started"
        )

        activities = tracker.get_activities(
            agent_id="agent1",
            activity_types=[ActivityType.TOOL_USE_STARTED]
        )
        assert len(activities) == 1
        assert activities[0]["data"]["tool_name"] == "read_file"
        assert activities[0]["data"]["status"] == "started"

    def test_record_tool_use_completed(self):
        """Test recording tool use completion."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_tool_use(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            iteration=1,
            tool_name="write_file",
            tool_inputs={"path": "/test/output.txt"},
            status="completed"
        )

        activities = tracker.get_activities(
            agent_id="agent1",
            activity_types=[ActivityType.TOOL_USE_COMPLETED]
        )
        assert len(activities) == 1
        assert activities[0]["data"]["status"] == "completed"

    def test_record_tool_use_failed(self):
        """Test recording tool use failure."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_tool_use(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            iteration=1,
            tool_name="spawn_agent",
            tool_inputs={"agent_type": "invalid"},
            status="failed"
        )

        activities = tracker.get_activities(
            agent_id="agent1",
            activity_types=[ActivityType.TOOL_USE_FAILED]
        )
        assert len(activities) == 1
        assert activities[0]["data"]["status"] == "failed"


class TestRecordAgentSpawned:
    """Test record_agent_spawned method."""

    def test_record_agent_spawned(self):
        """Test recording agent spawn."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="parent1",
            agent_name="Parent Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_agent_spawned(
            parent_agent_id="parent1",
            parent_agent_name="Parent Agent",
            spawned_agent_id="child1",
            spawned_agent_name="Child Agent",
            request_id="req1"
        )

        activities = tracker.get_activities(
            activity_types=[ActivityType.AGENT_SPAWNED]
        )
        assert len(activities) == 1
        assert activities[0]["data"]["spawned_agent_id"] == "child1"


class TestRecordMessage:
    """Test record_message method."""

    def test_record_message(self):
        """Test recording a message."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_message(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            message="Processing task...",
            message_type="info"
        )

        activities = tracker.get_activities(
            agent_id="agent1",
            activity_types=[ActivityType.MESSAGE]
        )
        assert len(activities) == 1
        assert activities[0]["data"]["message"] == "Processing task..."


class TestRecordQuestionAnswer:
    """Test record_question and record_answer methods."""

    def test_record_question(self):
        """Test recording a question."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_question(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            question_id="q1",
            question="What should I do next?"
        )

        pending = tracker.get_pending_questions()
        assert "q1" in pending
        assert pending["q1"]["question"] == "What should I do next?"

        # Check agent state
        state = tracker.get_agent_state("agent1")
        assert state["status"] == "awaiting_user_input"

    def test_record_question_with_options(self):
        """Test recording a question with options."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_question(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            question_id="q1",
            question="Which approach?",
            options=["Option A", "Option B"]
        )

        pending = tracker.get_pending_questions()
        assert pending["q1"]["options"] == ["Option A", "Option B"]

    def test_record_answer(self):
        """Test recording an answer to a question."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_question(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            question_id="q1",
            question="What should I do next?"
        )

        tracker.record_answer(
            question_id="q1",
            answer="Continue with the implementation"
        )

        pending = tracker.get_pending_questions()
        assert "q1" not in pending  # Should be removed from pending

        # Check agent state is back to running
        state = tracker.get_agent_state("agent1")
        assert state["status"] == "running"

    def test_record_answer_unknown_question(self):
        """Test recording answer for unknown question."""
        tracker = AgentActivityTracker(enable_persistence=False)

        # Should not raise, just log warning
        tracker.record_answer(
            question_id="unknown",
            answer="Some answer"
        )


class TestRecordFileGenerated:
    """Test record_file_generated method."""

    def test_record_file_generated(self):
        """Test recording file generation."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced"
        )

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="developers",
            request_id="req1"
        )

        tracker.record_file_generated(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            file_path="/output/test.py",
            file_size=1024,
            file_type="code"
        )

        activities = tracker.get_activities(
            agent_id="agent1",
            activity_types=[ActivityType.FILE_GENERATED]
        )
        assert len(activities) == 1
        assert activities[0]["data"]["file_path"] == "/output/test.py"

        # Check request counts incremented
        request = tracker.get_request("req1")
        assert request["file_count"] == 1


class TestRecordGitCommit:
    """Test record_git_commit method."""

    def test_record_git_commit(self):
        """Test recording git commit."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced"
        )

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="developers",
            request_id="req1"
        )

        tracker.record_git_commit(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            commit_hash="abc123",
            commit_message="Add new feature",
            files=["src/main.py", "tests/test_main.py"]
        )

        activities = tracker.get_activities(
            agent_id="agent1",
            activity_types=[ActivityType.GIT_COMMIT]
        )
        assert len(activities) == 1
        assert activities[0]["data"]["commit_hash"] == "abc123"

        # Check request counts incremented
        request = tracker.get_request("req1")
        assert request["commit_count"] == 1


class TestRecordAgentCompleted:
    """Test record_agent_completed method."""

    def test_record_agent_completed_basic(self):
        """Test recording agent completion."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_agent_completed(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            result={"status": "success", "summary": "Task completed"}
        )

        state = tracker.get_agent_state("agent1")
        assert state["status"] == "completed"
        assert state["summary"] == "Task completed"

    def test_record_agent_completed_with_metrics(self):
        """Test recording agent completion with cost metrics."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_agent_completed(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            result={"status": "success"},
            started_at="2024-01-01T00:00:00",
            completed_at="2024-01-01T00:01:00",
            duration_ms=60000,
            model_used="claude-sonnet-4-5-20250929",
            cost_estimate=0.05,
            input_tokens=1000,
            output_tokens=500
        )

        state = tracker.get_agent_state("agent1")
        assert state["duration_ms"] == 60000
        assert state["cost_estimate"] == 0.05


class TestRecordAgentFailed:
    """Test record_agent_failed method."""

    def test_record_agent_failed(self):
        """Test recording agent failure."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_agent_failed(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            error="Something went wrong",
            traceback="Traceback: ..."
        )

        state = tracker.get_agent_state("agent1")
        assert state["status"] == "failed"
        assert "Something went wrong" in state["current_task"]


class TestGetActivitiesFiltering:
    """Test get_activities with various filters."""

    def test_filter_by_request_id(self):
        """Test filtering activities by request_id."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Agent 1",
            agent_type="leadership",
            request_id="req1"
        )
        tracker.record_agent_started(
            agent_id="agent2",
            agent_name="Agent 2",
            agent_type="leadership",
            request_id="req2"
        )

        activities = tracker.get_activities(request_id="req1")
        assert all(a.get("request_id") == "req1" for a in activities)

    def test_filter_by_activity_types(self):
        """Test filtering by multiple activity types."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )
        tracker.record_message(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            message="Test message"
        )

        activities = tracker.get_activities(
            activity_types=[ActivityType.AGENT_STARTED, ActivityType.MESSAGE]
        )
        assert len(activities) == 2

    def test_filter_by_limit(self):
        """Test limiting number of activities."""
        tracker = AgentActivityTracker(enable_persistence=False)

        for i in range(10):
            tracker.record_agent_started(
                agent_id=f"agent{i}",
                agent_name=f"Agent {i}",
                agent_type="leadership",
                request_id="req1"
            )

        activities = tracker.get_activities(limit=5)
        assert len(activities) == 5


class TestGetAgentHierarchy:
    """Test get_agent_hierarchy method."""

    def test_get_hierarchy_all(self):
        """Test getting full hierarchy."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        hierarchy = tracker.get_agent_hierarchy()
        assert "agent1" in hierarchy

    def test_get_hierarchy_by_request_id(self):
        """Test hierarchy filtered by request_id."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Agent 1",
            agent_type="leadership",
            request_id="req1"
        )
        tracker.record_agent_started(
            agent_id="agent2",
            agent_name="Agent 2",
            agent_type="leadership",
            request_id="req2"
        )

        hierarchy = tracker.get_agent_hierarchy(request_id="req1")
        assert "agent1" in hierarchy
        assert "agent2" not in hierarchy

    def test_get_hierarchy_with_children(self):
        """Test hierarchy with parent-child relationship."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="parent1",
            agent_name="Parent",
            agent_type="leadership",
            request_id="req1"
        )
        tracker.record_agent_started(
            agent_id="child1",
            agent_name="Child",
            agent_type="developers",
            request_id="req1",
            parent_agent_id="parent1"
        )

        hierarchy = tracker.get_agent_hierarchy()
        assert "child1" in hierarchy["parent1"]["children"]


class TestClearMethods:
    """Test clear_request, clear_all, clear_agents_by_status."""

    def test_clear_request(self):
        """Test clearing a specific request."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced"
        )
        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.clear_request("req1")

        assert "req1" not in tracker.requests
        assert "agent1" not in tracker.agent_states

    def test_clear_all(self):
        """Test clearing all data."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        result = tracker.clear_all(include_activities=True, include_agents=True)

        assert result["activities"] >= 0
        assert result["agents"] >= 0
        assert len(tracker.activities) == 0
        assert len(tracker.agent_states) == 0

    def test_clear_agents_by_status(self):
        """Test clearing agents by status."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Agent 1",
            agent_type="leadership",
            request_id="req1"
        )
        tracker.record_agent_completed(
            agent_id="agent1",
            agent_name="Agent 1",
            request_id="req1",
            result={"status": "success"}
        )

        tracker.record_agent_started(
            agent_id="agent2",
            agent_name="Agent 2",
            agent_type="leadership",
            request_id="req1"
        )

        result = tracker.clear_agents_by_status(["completed"])

        # Agent1 was completed, so it should be cleared
        assert result["agents"] >= 1
        assert "agent1" not in tracker.agent_states
        assert "agent2" in tracker.agent_states  # Still running


class TestRequestTracking:
    """Test request tracking methods."""

    def test_record_request_started(self):
        """Test recording request start."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Build a web app",
            budget_tier="balanced"
        )

        request = tracker.get_request("req1")
        assert request is not None
        assert request["prompt"] == "Build a web app"
        assert request["status"] == "running"

    def test_record_request_with_github_url(self):
        """Test recording request with GitHub URL."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced",
            github_repo_url="https://github.com/user/repo"
        )

        request = tracker.get_request("req1")
        assert request["github_repo_url"] == "https://github.com/user/repo"

    def test_update_request_title(self):
        """Test updating request title."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced"
        )
        tracker.update_request_title("req1", "New Title")

        request = tracker.get_request("req1")
        assert request["title"] == "New Title"
        assert request["title_status"] == "completed"

    def test_update_request_root_agent(self):
        """Test updating request root agent."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced"
        )
        tracker.update_request_root_agent("req1", "agent1")

        request = tracker.get_request("req1")
        assert request["root_agent_id"] == "agent1"

    def test_update_request_status(self):
        """Test updating request status."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced"
        )
        tracker.update_request_status("req1", "completed")

        request = tracker.get_request("req1")
        assert request["status"] == "completed"
        assert request["completed_at"] is not None

    def test_increment_request_counts(self):
        """Test incrementing request counts."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced"
        )

        tracker.increment_request_counts("req1", agents=2, files=3, commits=1)

        request = tracker.get_request("req1")
        assert request["agent_count"] == 2
        assert request["file_count"] == 3
        assert request["commit_count"] == 1

    def test_get_requests(self):
        """Test getting all requests."""
        tracker = AgentActivityTracker(enable_persistence=False)

        for i in range(5):
            tracker.record_request_started(
                request_id=f"req{i}",
                prompt=f"Task {i}",
                budget_tier="balanced"
            )

        requests = tracker.get_requests(limit=3)
        assert len(requests) == 3

    def test_get_request_timeline(self):
        """Test getting request timeline."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Test",
            budget_tier="balanced"
        )
        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        timeline = tracker.get_request_timeline("req1")
        assert timeline is not None
        assert "request" in timeline
        assert "agents" in timeline
        assert "timeline" in timeline

    def test_get_request_timeline_not_found(self):
        """Test getting timeline for nonexistent request."""
        tracker = AgentActivityTracker(enable_persistence=False)

        timeline = tracker.get_request_timeline("nonexistent")
        assert "error" in timeline


class TestLineageTracking:
    """Test lineage tracking methods."""

    def test_record_task_spawned_from_report(self):
        """Test recording task spawned from report."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req2",
            prompt="Continue work",
            budget_tier="balanced"
        )

        tracker.record_task_spawned_from_report(
            report_id="report1",
            report_title="Initial Report",
            new_request_id="req2",
            problem_description="Continue from previous work"
        )

        # Check lineage stored in request
        request = tracker.get_request("req2")
        assert request["lineage"]["source_id"] == "report1"
        assert request["lineage"]["source_title"] == "Initial Report"

    def test_get_tasks_spawned_from_report(self):
        """Test getting tasks spawned from report."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req2",
            prompt="Continue",
            budget_tier="balanced"
        )
        tracker.record_task_spawned_from_report(
            report_id="report1",
            report_title="Report",
            new_request_id="req2",
            problem_description="Follow-up"
        )

        spawned = tracker.get_tasks_spawned_from_report("report1")
        assert len(spawned) == 1
        assert spawned[0]["request_id"] == "req2"

    def test_get_report_lineage(self):
        """Test getting report lineage."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Original",
            budget_tier="balanced"
        )
        tracker.record_task_spawned_from_report(
            report_id="report1",
            report_title="Report",
            new_request_id="req1",
            problem_description="Follow-up"
        )

        lineage = tracker.get_report_lineage("req1")
        assert lineage is not None
        assert lineage["source_id"] == "report1"

    def test_get_report_lineage_none(self):
        """Test getting lineage for request without source."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_request_started(
            request_id="req1",
            prompt="Original",
            budget_tier="balanced"
        )

        lineage = tracker.get_report_lineage("req1")
        assert lineage is None


class TestCallbackRegistration:
    """Test callback registration and unregistration."""

    def test_register_and_trigger_callback(self):
        """Test that registered callbacks are triggered."""
        tracker = AgentActivityTracker(enable_persistence=False)
        received_activities = []

        def callback(activity):
            received_activities.append(activity)

        tracker.register_callback(callback)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        assert len(received_activities) == 1

    def test_unregister_callback(self):
        """Test that unregistered callbacks are not triggered."""
        tracker = AgentActivityTracker(enable_persistence=False)
        received_activities = []

        def callback(activity):
            received_activities.append(activity)

        tracker.register_callback(callback)
        tracker.unregister_callback(callback)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        assert len(received_activities) == 0

    def test_callback_error_handling(self):
        """Test that callback errors don't break tracking."""
        tracker = AgentActivityTracker(enable_persistence=False)

        def bad_callback(activity):
            raise Exception("Callback error")

        tracker.register_callback(bad_callback)

        # Should not raise
        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        # Activity should still be recorded
        assert len(tracker.activities) == 1


class TestActivityDataclass:
    """Test the Activity dataclass."""

    def test_activity_to_dict(self):
        """Test Activity.to_dict() conversion."""
        activity = Activity(
            activity_type=ActivityType.AGENT_STARTED,
            agent_id="agent1",
            agent_name="Test Agent",
            timestamp="2024-01-01T00:00:00",
            data={"key": "value"},
            request_id="req1",
            parent_agent_id="parent1",
            iteration=1
        )

        result = activity.to_dict()

        assert result["activity_type"] == "agent_started"  # String value
        assert result["agent_id"] == "agent1"
        assert result["data"] == {"key": "value"}


class TestActivityType:
    """Test ActivityType enum."""

    def test_activity_types_are_strings(self):
        """Test that ActivityType values are strings."""
        assert ActivityType.AGENT_STARTED.value == "agent_started"
        assert ActivityType.AGENT_COMPLETED.value == "agent_completed"
        assert ActivityType.TOOL_USE_STARTED.value == "tool_use_started"


class TestMaxActivities:
    """Test activity list trimming."""

    def test_activities_trimmed_at_max(self):
        """Test that activities are trimmed when exceeding max."""
        tracker = AgentActivityTracker(enable_persistence=False)
        tracker.max_activities = 5  # Set low limit for testing

        for i in range(10):
            tracker.record_message(
                agent_id="agent1",
                agent_name="Test",
                request_id="req1",
                message=f"Message {i}"
            )

        assert len(tracker.activities) == 5
        # Should have the last 5 messages
        assert tracker.activities[-1].data["message"] == "Message 9"


class TestRecordTaskUpdate:
    """Test record_task_update method."""

    def test_record_task_update(self):
        """Test recording task update."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Test Agent",
            agent_type="leadership",
            request_id="req1"
        )

        tracker.record_task_update(
            agent_id="agent1",
            agent_name="Test Agent",
            request_id="req1",
            task_description="Working on implementation"
        )

        state = tracker.get_agent_state("agent1")
        assert state["current_task"] == "Working on implementation"


class TestGetAllAgentStates:
    """Test get_all_agent_states method."""

    def test_get_all_agent_states(self):
        """Test getting all agent states."""
        tracker = AgentActivityTracker(enable_persistence=False)

        tracker.record_agent_started(
            agent_id="agent1",
            agent_name="Agent 1",
            agent_type="leadership",
            request_id="req1"
        )
        tracker.record_agent_started(
            agent_id="agent2",
            agent_name="Agent 2",
            agent_type="developers",
            request_id="req1"
        )

        states = tracker.get_all_agent_states()

        assert "agent1" in states
        assert "agent2" in states
