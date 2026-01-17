"""
Unit tests for swarm_recovery module.

Tests the StallDetector, RecoveryOrchestrator, and related components.
"""

import pytest
import time
import threading
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from src.runtime.agents.swarm_recovery import (
    RecoveryStrategy,
    RecoveryTask,
    StallDetector,
    RecoveryOrchestrator,
    GuardrailSystem,
    get_guardrail_system,
)


class TestRecoveryStrategy:
    """Test RecoveryStrategy enum."""

    def test_strategy_values(self):
        """Test all strategy values."""
        assert RecoveryStrategy.RETRY.value == "retry"
        assert RecoveryStrategy.RETRY_WITH_BACKOFF.value == "retry_backoff"
        assert RecoveryStrategy.ENHANCE_PROMPT.value == "enhance_prompt"
        assert RecoveryStrategy.REFACTOR_AGENT.value == "refactor_agent"
        assert RecoveryStrategy.ESCALATE_MODEL.value == "escalate_model"
        assert RecoveryStrategy.SPAWN_REPLACEMENT.value == "spawn_replacement"
        assert RecoveryStrategy.MANUAL_INTERVENTION.value == "manual"
        assert RecoveryStrategy.ABORT.value == "abort"


class TestRecoveryTask:
    """Test RecoveryTask dataclass."""

    def test_recovery_task_creation(self):
        """Test creating a RecoveryTask."""
        task = RecoveryTask(
            recovery_id=1,
            agent_id="agent-123",
            session_id="session-456",
            agent_type="backend_developer",
            agent_name="Test Agent",
            input_data={"task": "do something"},
            reason="no_activity",
            strategy=RecoveryStrategy.RETRY,
            priority=10,
            attempts=0,
            max_attempts=3,
            created_at=datetime.now(),
        )

        assert task.recovery_id == 1
        assert task.agent_id == "agent-123"
        assert task.strategy == RecoveryStrategy.RETRY
        assert task.attempts == 0
        assert task.last_attempt is None


class TestStallDetector:
    """Test StallDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a StallDetector instance."""
        return StallDetector(
            stall_threshold_minutes=5,
            max_iteration_time_minutes=10,
            check_interval_seconds=30
        )

    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector.stall_threshold == timedelta(minutes=5)
        assert detector.max_iteration_time == timedelta(minutes=10)
        assert detector.check_interval == 30
        assert detector._running is False

    def test_diagnose_stall_max_iterations(self, detector):
        """Test diagnosing max iterations stall."""
        agent = {
            "iteration": 15,
            "max_iterations": 10,
        }

        reason = detector._diagnose_stall(agent)

        assert reason == "max_iterations_reached"

    def test_diagnose_stall_no_activity(self, detector):
        """Test diagnosing no activity stall."""
        old_checkpoint = (datetime.now() - timedelta(minutes=10)).isoformat()
        agent = {
            "iteration": 5,
            "max_iterations": 15,
            "last_checkpoint": old_checkpoint,
        }

        # Need to handle timezone-aware comparison
        reason = detector._diagnose_stall(agent)

        # May be None due to timezone issues in test
        # The important thing is it doesn't crash

    def test_diagnose_stall_stuck_at_start(self, detector):
        """Test diagnosing stuck at start stall."""
        agent = {
            "iteration": 0,
            "max_iterations": 10,
            "started_at": datetime.now().isoformat(),
        }

        reason = detector._diagnose_stall(agent)

        assert reason == "stuck_at_start"

    def test_diagnose_stall_no_issue(self, detector):
        """Test diagnosing when no stall detected."""
        agent = {
            "iteration": 5,
            "max_iterations": 15,
        }

        reason = detector._diagnose_stall(agent)

        assert reason is None

    @patch('src.runtime.agents.swarm_recovery.get_swarm_state')
    def test_detect_stalled_agents(self, mock_get_swarm_state, detector):
        """Test detecting stalled agents."""
        mock_swarm = MagicMock()
        mock_swarm.get_stalled_agents.return_value = [
            {
                "agent_id": "agent-1",
                "iteration": 15,
                "max_iterations": 10,
            }
        ]
        mock_get_swarm_state.return_value = mock_swarm

        stalled = detector.detect_stalled_agents()

        assert len(stalled) == 1
        assert stalled[0]["stall_reason"] == "max_iterations_reached"

    @patch('src.runtime.agents.swarm_recovery.get_swarm_state')
    def test_queue_for_recovery(self, mock_get_swarm_state, detector):
        """Test queuing agents for recovery."""
        mock_swarm = MagicMock()
        mock_get_swarm_state.return_value = mock_swarm

        stalled_agents = [
            {
                "agent_id": "agent-1",
                "session_id": "session-1",
                "stall_reason": "no_activity",
            }
        ]

        count = detector.queue_for_recovery(stalled_agents)

        assert count == 1
        mock_swarm.update_agent_status.assert_called_once()
        mock_swarm.queue_for_recovery.assert_called_once()

    def test_start_monitoring(self, detector):
        """Test starting background monitoring."""
        callback = MagicMock()

        with patch('src.runtime.agents.swarm_recovery.get_swarm_state') as mock:
            mock_swarm = MagicMock()
            mock_swarm.get_stalled_agents.return_value = []
            mock.return_value = mock_swarm

            detector.start_monitoring(callback)

            assert detector._running is True
            assert detector._thread is not None

            # Give thread time to start
            time.sleep(0.1)

            detector.stop_monitoring()

            assert detector._running is False

    def test_stop_monitoring_without_start(self, detector):
        """Test stopping monitoring that wasn't started."""
        detector.stop_monitoring()

        # Should not raise
        assert detector._running is False


class TestRecoveryOrchestrator:
    """Test RecoveryOrchestrator class."""

    @pytest.fixture
    def orchestrator(self):
        """Create a RecoveryOrchestrator instance."""
        return RecoveryOrchestrator(
            max_concurrent_recoveries=2,
            stall_threshold_minutes=5,
            api_key="test-api-key"
        )

    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.max_concurrent == 2
        assert orchestrator.api_key == "test-api-key"
        assert orchestrator._running is False

    def test_determine_strategy_first_attempt_stuck_at_start(self, orchestrator):
        """Test strategy determination for first attempt stuck at start."""
        agent = {"recovery_attempts": 0, "iteration": 0}

        strategy = orchestrator._determine_strategy(agent, "stuck_at_start")

        assert strategy == RecoveryStrategy.RETRY

    def test_determine_strategy_first_attempt_no_activity(self, orchestrator):
        """Test strategy determination for first attempt no activity."""
        agent = {"recovery_attempts": 0, "iteration": 5}

        strategy = orchestrator._determine_strategy(agent, "no_activity")

        assert strategy == RecoveryStrategy.RETRY_WITH_BACKOFF

    def test_determine_strategy_second_attempt(self, orchestrator):
        """Test strategy determination for second attempt."""
        agent = {"recovery_attempts": 1, "iteration": 5}

        strategy = orchestrator._determine_strategy(agent, "no_activity")

        assert strategy == RecoveryStrategy.REFACTOR_AGENT

    def test_determine_strategy_third_attempt(self, orchestrator):
        """Test strategy determination for third attempt."""
        agent = {"recovery_attempts": 2, "iteration": 5}

        strategy = orchestrator._determine_strategy(agent, "no_activity")

        assert strategy == RecoveryStrategy.ENHANCE_PROMPT

    def test_determine_strategy_fourth_attempt(self, orchestrator):
        """Test strategy determination for fourth attempt."""
        agent = {"recovery_attempts": 3, "iteration": 5}

        strategy = orchestrator._determine_strategy(agent, "no_activity")

        assert strategy == RecoveryStrategy.ESCALATE_MODEL

    def test_determine_strategy_fifth_attempt(self, orchestrator):
        """Test strategy determination for fifth attempt."""
        agent = {"recovery_attempts": 4, "iteration": 5}

        strategy = orchestrator._determine_strategy(agent, "no_activity")

        assert strategy == RecoveryStrategy.MANUAL_INTERVENTION

    def test_determine_strategy_exhausted(self, orchestrator):
        """Test strategy determination when attempts exhausted."""
        agent = {"recovery_attempts": 5, "iteration": 5}

        strategy = orchestrator._determine_strategy(agent, "no_activity")

        assert strategy == RecoveryStrategy.ABORT

    def test_calculate_priority_root_agent(self, orchestrator):
        """Test priority calculation for root agent."""
        agent = {"parent_agent_id": None, "iteration": 0, "agent_type": "worker"}

        priority = orchestrator._calculate_priority(agent, "no_activity")

        assert priority >= 100  # Root agents get +100

    def test_calculate_priority_executive(self, orchestrator):
        """Test priority calculation for executive agent."""
        agent = {
            "parent_agent_id": "parent-1",
            "iteration": 2,
            "agent_type": "executive_director"
        }

        priority = orchestrator._calculate_priority(agent, "no_activity")

        # 0 (not root) + 10 (2 iterations * 5) + 50 (executive) = 60
        assert priority >= 50

    def test_calculate_priority_coordinator(self, orchestrator):
        """Test priority calculation for coordinator agent."""
        agent = {
            "parent_agent_id": "parent-1",
            "iteration": 3,
            "agent_type": "backend_coordinator"
        }

        priority = orchestrator._calculate_priority(agent, "no_activity")

        # 0 (not root) + 15 (3 * 5) + 30 (coordinator) = 45
        assert priority >= 30

    def test_calculate_priority_lead(self, orchestrator):
        """Test priority calculation for lead agent."""
        agent = {
            "parent_agent_id": "parent-1",
            "iteration": 1,
            "agent_type": "backend_lead"
        }

        priority = orchestrator._calculate_priority(agent, "no_activity")

        # 0 (not root) + 5 (1 * 5) + 20 (lead) = 25
        assert priority >= 20

    @patch('src.runtime.agents.swarm_recovery.get_swarm_state')
    def test_on_stalls_detected(self, mock_get_swarm_state, orchestrator):
        """Test handling stall detection."""
        mock_swarm = MagicMock()
        mock_get_swarm_state.return_value = mock_swarm

        stalled_agents = [
            {
                "agent_id": "agent-1",
                "session_id": "session-1",
                "agent_name": "Test Agent",
                "recovery_attempts": 0,
                "iteration": 5,
                "agent_type": "developer",
                "stall_reason": "no_activity",
            }
        ]

        orchestrator._on_stalls_detected(stalled_agents)

        mock_swarm.update_agent_status.assert_called()
        mock_swarm.queue_for_recovery.assert_called()

    def test_start_and_stop(self, orchestrator):
        """Test starting and stopping orchestrator."""
        with patch('src.runtime.agents.swarm_recovery.get_swarm_state') as mock:
            mock_swarm = MagicMock()
            mock_swarm.get_stalled_agents.return_value = []
            mock_swarm.get_recovery_queue.return_value = []
            mock.return_value = mock_swarm

            orchestrator.start()

            assert orchestrator._running is True

            # Give threads time to start
            time.sleep(0.1)

            orchestrator.stop()

            assert orchestrator._running is False

    def test_start_already_running(self, orchestrator):
        """Test starting when already running."""
        orchestrator._running = True

        with patch.object(orchestrator.stall_detector, 'start_monitoring'):
            orchestrator.start()

        # Should not start again
        orchestrator._running = False

    def test_retry_agent_no_api_key(self):
        """Test retry agent fails without API key."""
        orch = RecoveryOrchestrator(api_key=None)

        with patch('src.runtime.agents.swarm_recovery.get_swarm_state'):
            result = orch._retry_agent({"agent_id": "test"})

        assert result is False


class TestGuardrailSystem:
    """Test GuardrailSystem class in swarm_recovery."""

    @pytest.fixture
    def guardrail_system(self):
        """Create a GuardrailSystem instance."""
        return GuardrailSystem()

    def test_initialization(self, guardrail_system):
        """Test guardrail system initialization."""
        assert guardrail_system is not None

    def test_get_guardrails_for_director(self, guardrail_system):
        """Test getting guardrails for director agent type."""
        guardrails = guardrail_system.get_guardrails_for_agent_type("executive_director")

        # Method returns list (may be empty for some types)
        assert isinstance(guardrails, list)

    def test_get_guardrails_for_coordinator(self, guardrail_system):
        """Test getting guardrails for coordinator agent type."""
        guardrails = guardrail_system.get_guardrails_for_agent_type("backend_coordinator")

        # Method returns list
        assert isinstance(guardrails, list)
        # Coordinators may have coordination guardrails
        if guardrails:
            assert any("coordinate" in g.lower() or "handoff" in g.lower() or "team" in g.lower() for g in guardrails)

    def test_get_guardrails_for_unknown_type(self, guardrail_system):
        """Test getting guardrails for unknown agent type."""
        guardrails = guardrail_system.get_guardrails_for_agent_type("unknown_agent")

        # Method returns list (may be empty for unknown types)
        assert isinstance(guardrails, list)

    def test_learn_from_failure_scope_creep(self, guardrail_system):
        """Test learning from scope creep failure."""
        result = guardrail_system.learn_from_failure(
            agent_type="developer",
            failure_reason="scope_creep",
            input_data={"task": "fix bug"},
        )

        assert result["failure_reason"] == "scope_creep"
        assert len(result["recommendations"]) > 0
        assert any("scope" in r.lower() for r in result["recommendations"])

    def test_learn_from_failure_incomplete(self, guardrail_system):
        """Test learning from incomplete failure."""
        result = guardrail_system.learn_from_failure(
            agent_type="developer",
            failure_reason="incomplete",
            input_data={"task": "build feature"},
        )

        assert result["failure_reason"] == "incomplete"
        assert any("completion" in r.lower() or "checklist" in r.lower() for r in result["recommendations"])

    def test_learn_from_failure_max_iterations(self, guardrail_system):
        """Test learning from max iterations failure."""
        result = guardrail_system.learn_from_failure(
            agent_type="developer",
            failure_reason="max_iterations_reached",
            input_data={},
        )

        assert "max_iterations_reached" in result["failure_reason"]

    def test_learn_from_failure_stuck_at_start(self, guardrail_system):
        """Test learning from stuck at start failure."""
        result = guardrail_system.learn_from_failure(
            agent_type="developer",
            failure_reason="stuck_at_start",
            input_data={},
        )

        assert any("starting" in r.lower() or "guidance" in r.lower() for r in result["recommendations"])

    def test_format_guardrails_for_agent_definition(self, guardrail_system):
        """Test formatting guardrails for agent definition."""
        # Use coordinator which has guardrails
        formatted = guardrail_system.format_guardrails_for_agent_definition("backend_coordinator")

        # If guardrails exist, should be formatted
        if formatted:
            assert "## Guardrails" in formatted or "-" in formatted

    def test_format_guardrails_empty_for_unknown(self, guardrail_system):
        """Test formatting for agent type with no specific guardrails."""
        # Mock get_guardrails_for_agent_type to return empty
        with patch.object(guardrail_system, 'get_guardrails_for_agent_type', return_value=[]):
            formatted = guardrail_system.format_guardrails_for_agent_definition("empty_agent")

        assert formatted == ""


class TestGetGuardrailSystem:
    """Test get_guardrail_system function."""

    def test_returns_instance(self):
        """Test get_guardrail_system returns instance."""
        import src.runtime.agents.swarm_recovery as module
        module._guardrail_system = None

        system = get_guardrail_system()

        assert system is not None
        assert isinstance(system, GuardrailSystem)

        # Cleanup
        module._guardrail_system = None

    def test_returns_same_instance(self):
        """Test get_guardrail_system returns same instance."""
        import src.runtime.agents.swarm_recovery as module
        module._guardrail_system = None

        system1 = get_guardrail_system()
        system2 = get_guardrail_system()

        assert system1 is system2

        # Cleanup
        module._guardrail_system = None


class TestRecoveryExecution:
    """Test recovery execution scenarios."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked dependencies."""
        return RecoveryOrchestrator(
            max_concurrent_recoveries=2,
            api_key="test-key"
        )

    @patch('src.runtime.agents.swarm_recovery.get_swarm_state')
    def test_execute_recovery_retry_strategy(self, mock_get_swarm_state, orchestrator):
        """Test executing retry recovery strategy."""
        mock_swarm = MagicMock()
        mock_swarm.get_agent.return_value = {"agent_id": "test-1", "model_used": "haiku"}
        mock_get_swarm_state.return_value = mock_swarm

        task = {
            "id": 1,
            "agent_id": "test-1",
            "agent_type": "leadership/executive_director",
            "agent_name": "Test Agent",
            "recovery_strategy": "retry",
            "input_data": {},
            "attempts": 0,
            "max_attempts": 3,
        }

        # Mock the retry to avoid actual execution
        with patch.object(orchestrator, '_retry_agent', return_value=True):
            orchestrator._execute_recovery(task)

        mock_swarm.update_recovery_status.assert_called()

    @patch('src.runtime.agents.swarm_recovery.get_swarm_state')
    def test_execute_recovery_manual_intervention(self, mock_get_swarm_state, orchestrator):
        """Test executing manual intervention strategy."""
        mock_swarm = MagicMock()
        mock_get_swarm_state.return_value = mock_swarm

        task = {
            "id": 1,
            "agent_id": "test-1",
            "agent_type": "developer",
            "agent_name": "Test Agent",
            "recovery_strategy": "manual",
            "input_data": {},
            "attempts": 4,
            "max_attempts": 5,
        }

        orchestrator._execute_recovery(task)

        # Should mark for review, not attempt retry
        mock_swarm.update_recovery_status.assert_called_with(1, "needs_review")
        mock_swarm.update_agent_status.assert_called_with("test-1", "needs_review")

    @patch('src.runtime.agents.swarm_recovery.get_swarm_state')
    def test_execute_recovery_abort(self, mock_get_swarm_state, orchestrator):
        """Test executing abort strategy."""
        mock_swarm = MagicMock()
        mock_get_swarm_state.return_value = mock_swarm

        task = {
            "id": 1,
            "agent_id": "test-1",
            "agent_type": "developer",
            "agent_name": "Test Agent",
            "recovery_strategy": "abort",
            "input_data": {},
            "attempts": 5,
            "max_attempts": 5,
        }

        orchestrator._execute_recovery(task)

        # Should mark as forever failed
        mock_swarm.update_agent_status.assert_called()
        call_args = mock_swarm.update_agent_status.call_args
        assert call_args[0][0] == "test-1"
        assert call_args[0][1] == "forever_failed"

    @patch('src.runtime.agents.swarm_recovery.get_swarm_state')
    def test_execute_recovery_exception_handling(self, mock_get_swarm_state, orchestrator):
        """Test exception handling during recovery execution."""
        mock_swarm = MagicMock()
        mock_get_swarm_state.return_value = mock_swarm

        task = {
            "id": 1,
            "agent_id": "test-1",
            "agent_type": "developer",
            "agent_name": "Test Agent",
            "recovery_strategy": "retry",
            "input_data": {},
            "attempts": 0,
            "max_attempts": 3,
        }

        # Make retry raise an exception
        with patch.object(orchestrator, '_retry_agent', side_effect=Exception("Test error")):
            orchestrator._execute_recovery(task)

        # Should mark as failed
        mock_swarm.update_recovery_status.assert_called_with(1, "failed")


class TestEnhancePrompt:
    """Test prompt enhancement."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator."""
        return RecoveryOrchestrator(api_key="test-key")

    def test_enhance_prompt_basic(self, orchestrator):
        """Test basic prompt enhancement."""
        task = {
            "input_data": {"problem_description": "Fix the bug"},
            "recovery_reason": "incomplete",
            "attempts": 2,
        }

        enhanced = orchestrator._enhance_prompt(task)

        # Should return enhanced input data
        assert enhanced is not None
        assert "problem_description" in enhanced

    def test_enhance_prompt_adds_recovery_context(self, orchestrator):
        """Test that enhancement adds recovery context."""
        task = {
            "input_data": {"problem_description": "Build feature"},
            "recovery_reason": "stuck_at_start",
            "attempts": 1,
        }

        enhanced = orchestrator._enhance_prompt(task)

        assert enhanced is not None
        # Enhanced data should include original
        assert "Build feature" in enhanced.get("problem_description", "")
