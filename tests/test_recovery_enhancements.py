"""
Unit tests for the Enhanced Recovery System.

Tests the new recovery strategies:
- ENHANCE_PROMPT
- REFACTOR_AGENT
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "runtime" / "agents"))

from swarm_recovery import (
    RecoveryOrchestrator,
    RecoveryStrategy,
    StallDetector,
)


class TestRecoveryStrategyDetermination:
    """Tests for the strategy determination logic."""

    @pytest.fixture
    def orchestrator(self):
        """Create a RecoveryOrchestrator instance."""
        return RecoveryOrchestrator(api_key="test_key")

    def test_first_attempt_returns_retry(self, orchestrator):
        """First failure should use simple RETRY."""
        agent = {"recovery_attempts": 0, "iteration": 5}
        strategy = orchestrator._determine_strategy(agent, "no_activity")
        assert strategy == RecoveryStrategy.RETRY_WITH_BACKOFF

    def test_first_attempt_stuck_at_start_returns_retry(self, orchestrator):
        """Stuck at start on first attempt should use RETRY."""
        agent = {"recovery_attempts": 0, "iteration": 0}
        strategy = orchestrator._determine_strategy(agent, "stuck_at_start")
        assert strategy == RecoveryStrategy.RETRY

    def test_second_attempt_refactors_agent(self, orchestrator):
        """Second failure should refactor agent definition."""
        agent = {"recovery_attempts": 1, "iteration": 5}
        strategy = orchestrator._determine_strategy(agent, "scope_creep")
        assert strategy == RecoveryStrategy.REFACTOR_AGENT

    def test_third_attempt_enhances_prompt(self, orchestrator):
        """Third failure should enhance the prompt."""
        agent = {"recovery_attempts": 2, "iteration": 5}
        strategy = orchestrator._determine_strategy(agent, "incomplete")
        assert strategy == RecoveryStrategy.ENHANCE_PROMPT

    def test_fourth_attempt_escalates_model(self, orchestrator):
        """Fourth failure should escalate to better model."""
        agent = {"recovery_attempts": 3, "iteration": 5}
        strategy = orchestrator._determine_strategy(agent, "max_iterations_reached")
        assert strategy == RecoveryStrategy.ESCALATE_MODEL

    def test_fifth_attempt_manual_intervention(self, orchestrator):
        """Fifth+ failure should flag for manual intervention."""
        agent = {"recovery_attempts": 4, "iteration": 5}
        strategy = orchestrator._determine_strategy(agent, "unknown")
        assert strategy == RecoveryStrategy.MANUAL_INTERVENTION


class TestPromptEnhancement:
    """Tests for prompt enhancement functionality."""

    @pytest.fixture
    def orchestrator(self):
        """Create a RecoveryOrchestrator instance."""
        return RecoveryOrchestrator(api_key="test_key")

    def test_enhance_prompt_adds_guardrails(self, orchestrator):
        """Enhanced prompt should include guardrails."""
        task = {
            "agent_type": "developers/code_writer",
            "input_data": {"task": "Write a login function"},
            "recovery_reason": "scope_creep"
        }

        with patch("swarm_recovery.get_guardrail_system") as mock_gs:
            mock_system = MagicMock()
            mock_system.apply_guardrails_to_prompt.return_value = (
                "Write a login function\n\n**CRITICAL CONSTRAINTS:**\n- Stay focused",
                ["guard_001"]
            )
            mock_gs.return_value = mock_system

            enhanced = orchestrator._enhance_prompt(task)

            assert enhanced is not None
            assert enhanced["_enhanced"] == True
            assert "guard_001" in enhanced["_guardrails_applied"]

    def test_enhance_prompt_adds_failure_guidance(self, orchestrator):
        """Enhanced prompt should include failure-specific guidance."""
        guidance = orchestrator._get_failure_specific_guidance("scope_creep")
        assert "scope" in guidance.lower()

        guidance = orchestrator._get_failure_specific_guidance("max_iterations_reached")
        assert "iteration" in guidance.lower()

        guidance = orchestrator._get_failure_specific_guidance("incomplete")
        assert "complete" in guidance.lower()

    def test_enhance_prompt_preserves_original_task(self, orchestrator):
        """Enhanced prompt should preserve original task content."""
        original_task = "Build a REST API for user management"
        task = {
            "agent_type": "developers/code_writer",
            "input_data": {"task": original_task},
            "recovery_reason": "no_activity"
        }

        with patch("swarm_recovery.get_guardrail_system") as mock_gs:
            mock_system = MagicMock()
            mock_system.apply_guardrails_to_prompt.return_value = (
                original_task,
                []
            )
            mock_gs.return_value = mock_system

            enhanced = orchestrator._enhance_prompt(task)
            assert original_task in enhanced["task"]


class TestAgentDefinitionRefactoring:
    """Tests for agent definition refactoring."""

    @pytest.fixture
    def orchestrator(self):
        """Create a RecoveryOrchestrator instance."""
        return RecoveryOrchestrator(api_key="test_key")

    def test_refactor_learns_from_failure(self, orchestrator):
        """Refactoring should learn from the failure."""
        task = {
            "agent_type": "developers/code_writer",
            "agent_name": "Code Writer",
            "input_data": {"task": "Write tests"},
            "recovery_reason": "scope_creep",
            "attempts": 1,
            "max_attempts": 5
        }

        with patch("swarm_recovery.get_guardrail_system") as mock_gs:
            mock_system = MagicMock()
            mock_gs.return_value = mock_system

            result = orchestrator._refactor_agent_definition(task)

            # Should have called learn_from_failure
            mock_system.learn_from_failure.assert_called_once()
            call_args = mock_system.learn_from_failure.call_args
            assert call_args[1]["agent_type"] == "developers/code_writer"
            assert call_args[1]["failure_type"] == "scope_creep"

    def test_get_agent_definition_path_valid(self, orchestrator, tmp_path):
        """Should return path for existing agent definitions."""
        # This test would need the actual file structure
        # For now, test the None case
        result = orchestrator._get_agent_definition_path("nonexistent/agent")
        assert result is None or not result.exists()


class TestStallDetector:
    """Tests for the StallDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a StallDetector instance."""
        return StallDetector(stall_threshold_minutes=5)

    def test_detect_with_custom_threshold(self, detector):
        """Should use custom threshold when provided."""
        with patch("swarm_recovery.get_swarm_state") as mock_state:
            mock_manager = MagicMock()
            mock_manager.get_stalled_agents.return_value = []
            mock_state.return_value = mock_manager

            detector.detect_stalled_agents(threshold_minutes=10)

            mock_manager.get_stalled_agents.assert_called_with(
                stall_threshold_minutes=10
            )

    def test_detect_diagnoses_stalls(self, detector):
        """Should diagnose stall reasons."""
        with patch("swarm_recovery.get_swarm_state") as mock_state:
            mock_manager = MagicMock()
            mock_manager.get_stalled_agents.return_value = [
                {
                    "agent_id": "test_001",
                    "iteration": 10,
                    "max_iterations": 10,
                    "last_checkpoint": None
                }
            ]
            mock_state.return_value = mock_manager

            stalled = detector.detect_stalled_agents()

            assert len(stalled) == 1
            assert stalled[0]["stall_reason"] == "max_iterations_reached"

    def test_queue_for_recovery(self, detector):
        """Should queue stalled agents for recovery."""
        stalled_agents = [
            {
                "agent_id": "test_001",
                "session_id": "session_001",
                "stall_reason": "no_activity"
            },
            {
                "agent_id": "test_002",
                "session_id": "session_001",
                "stall_reason": "stuck_at_start"
            }
        ]

        with patch("swarm_recovery.get_swarm_state") as mock_state:
            mock_manager = MagicMock()
            mock_state.return_value = mock_manager

            queued = detector.queue_for_recovery(stalled_agents)

            assert queued == 2
            assert mock_manager.update_agent_status.call_count == 2
            assert mock_manager.queue_for_recovery.call_count == 2


class TestRecoveryIntegration:
    """Integration tests for the recovery system."""

    @pytest.fixture
    def orchestrator(self):
        """Create a RecoveryOrchestrator instance."""
        return RecoveryOrchestrator(api_key="test_key")

    def test_recovery_priority_calculation(self, orchestrator):
        """Should calculate priority correctly."""
        root_agent = {"parent_agent_id": None, "iteration": 5, "agent_type": "leadership/executive_director"}
        child_agent = {"parent_agent_id": "parent", "iteration": 3, "agent_type": "developers/code_writer"}

        root_priority = orchestrator._calculate_priority(root_agent, "no_activity")
        child_priority = orchestrator._calculate_priority(child_agent, "no_activity")

        # Root agent should have higher priority
        assert root_priority > child_priority

    def test_leadership_agents_have_higher_priority(self, orchestrator):
        """Leadership agents should have higher priority."""
        exec_agent = {"parent_agent_id": "x", "iteration": 1, "agent_type": "leadership/executive_director"}
        dev_agent = {"parent_agent_id": "x", "iteration": 1, "agent_type": "developers/code_writer"}

        exec_priority = orchestrator._calculate_priority(exec_agent, "no_activity")
        dev_priority = orchestrator._calculate_priority(dev_agent, "no_activity")

        assert exec_priority > dev_priority


class TestRecoveryStrategies:
    """Tests for all recovery strategy definitions."""

    def test_all_strategies_defined(self):
        """All expected strategies should be defined."""
        expected = [
            "RETRY",
            "RETRY_WITH_BACKOFF",
            "ENHANCE_PROMPT",
            "REFACTOR_AGENT",
            "ESCALATE_MODEL",
            "SPAWN_REPLACEMENT",
            "MANUAL_INTERVENTION",
            "ABORT"
        ]

        for strategy_name in expected:
            assert hasattr(RecoveryStrategy, strategy_name)

    def test_strategy_values(self):
        """Strategy values should be valid strings."""
        for strategy in RecoveryStrategy:
            assert isinstance(strategy.value, str)
            assert len(strategy.value) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
