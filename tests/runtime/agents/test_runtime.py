"""
Unit tests for runtime module.

Tests the AgentRuntime class with mocked Anthropic API.
"""

import pytest
import json
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
from pathlib import Path
from src.runtime.agents.runtime import (
    TokenUsage,
    AgentRuntime,
)


class TestTokenUsage:
    """Test TokenUsage class."""

    def test_initialization_default(self):
        """Test default initialization."""
        usage = TokenUsage()

        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_initialization_with_values(self):
        """Test initialization with values."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_initialization_negative_raises(self):
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            TokenUsage(prompt_tokens=-1)

        with pytest.raises(ValueError, match="cannot be negative"):
            TokenUsage(completion_tokens=-1)

    def test_add_tokens(self):
        """Test adding tokens."""
        usage = TokenUsage()

        usage.add_tokens(prompt_tokens=50, completion_tokens=25)

        assert usage.prompt_tokens == 50
        assert usage.completion_tokens == 25
        assert usage.total_tokens == 75

    def test_add_tokens_cumulative(self):
        """Test adding tokens cumulatively."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)

        usage.add_tokens(prompt_tokens=50, completion_tokens=25)

        assert usage.prompt_tokens == 150
        assert usage.completion_tokens == 75
        assert usage.total_tokens == 225

    def test_add_tokens_negative_raises(self):
        """Test that adding negative tokens raises ValueError."""
        usage = TokenUsage()

        with pytest.raises(ValueError, match="cannot be negative"):
            usage.add_tokens(prompt_tokens=-1)

        with pytest.raises(ValueError, match="cannot be negative"):
            usage.add_tokens(completion_tokens=-1)

    def test_to_dict(self):
        """Test converting to dictionary."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)

        result = usage.to_dict()

        assert result == {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }


class TestAgentRuntimeClassMethods:
    """Test AgentRuntime class methods."""

    def setup_method(self):
        """Reset class-level state before each test."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

    def test_get_metrics_tracker_creates_singleton(self):
        """Test get_metrics_tracker creates singleton."""
        tracker1 = AgentRuntime.get_metrics_tracker()
        tracker2 = AgentRuntime.get_metrics_tracker()

        assert tracker1 is tracker2

    def test_get_activity_tracker_creates_singleton(self):
        """Test get_activity_tracker creates singleton."""
        tracker1 = AgentRuntime.get_activity_tracker()
        tracker2 = AgentRuntime.get_activity_tracker()

        assert tracker1 is tracker2

    def test_get_circuit_breaker_creates_singleton(self):
        """Test get_circuit_breaker creates singleton."""
        breaker1 = AgentRuntime.get_circuit_breaker()
        breaker2 = AgentRuntime.get_circuit_breaker()

        assert breaker1 is breaker2

    @patch('src.runtime.agents.runtime.get_swarm_state')
    def test_get_swarm_state(self, mock_get_swarm_state):
        """Test get_swarm_state class method."""
        mock_state = MagicMock()
        mock_get_swarm_state.return_value = mock_state

        result = AgentRuntime.get_swarm_state()

        assert result is mock_state

    @patch('src.runtime.agents.runtime.get_event_bus')
    def test_get_event_bus(self, mock_get_event_bus):
        """Test get_event_bus class method."""
        mock_bus = MagicMock()
        mock_get_event_bus.return_value = mock_bus

        result = AgentRuntime.get_event_bus()

        assert result is mock_bus


class TestAgentRuntimeInitialization:
    """Test AgentRuntime initialization."""

    @pytest.fixture
    def mock_definition(self):
        """Create a mock agent definition."""
        definition = MagicMock()
        definition.name = "Test Agent"
        definition.purpose = "Testing"
        definition.instructions = "Do testing"
        definition.input_format = '{"task": "string"}'
        definition.output_format = '{"result": "string"}'
        definition.max_iterations = 10
        definition.task_complexity = "routine"
        definition.category = "testing"
        definition.model_preference = "haiku"
        definition.instantiation_conditions = []
        definition.termination_conditions = []
        definition.clarification_conditions = []
        definition.can_write_code = False
        definition.can_write_tests = False
        return definition

    @pytest.fixture
    def mock_anthropic(self):
        """Mock the Anthropic client."""
        with patch('src.runtime.agents.runtime.Anthropic') as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('src.runtime.agents.runtime.get_swarm_state') as mock_swarm, \
             patch('src.runtime.agents.runtime.get_event_bus') as mock_bus, \
             patch('src.runtime.agents.runtime.get_iteration_tuner') as mock_tuner, \
             patch('src.runtime.agents.runtime.generate_agent_name') as mock_name, \
             patch('src.runtime.agents.runtime.generate_family_name') as mock_family:

            mock_swarm_instance = MagicMock()
            mock_swarm.return_value = mock_swarm_instance

            mock_bus_instance = MagicMock()
            mock_bus.return_value = mock_bus_instance

            mock_tuner_instance = MagicMock()
            mock_tuner_instance.get_effective_max_iterations.return_value = 10
            mock_tuner.return_value = mock_tuner_instance

            mock_name.return_value = "Test Agent-1234"
            mock_family.return_value = "TestFamily"

            yield {
                'swarm_state': mock_swarm_instance,
                'event_bus': mock_bus_instance,
                'tuner': mock_tuner_instance,
            }

    def test_initialization_basic(self, mock_definition, mock_anthropic, mock_dependencies):
        """Test basic initialization."""
        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
        )

        assert runtime.definition is mock_definition
        assert runtime.api_key == "test-api-key"
        assert runtime.iteration_count == 0

    def test_initialization_with_agent_id(self, mock_definition, mock_anthropic, mock_dependencies):
        """Test initialization with custom agent_id."""
        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
            agent_id="custom-agent-id",
        )

        assert runtime.agent_id == "custom-agent-id"

    def test_initialization_with_session_id_registers(self, mock_definition, mock_anthropic, mock_dependencies):
        """Test that session_id triggers swarm state registration."""
        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
            session_id="test-session",
        )

        mock_dependencies['swarm_state'].register_agent.assert_called_once()

    def test_initialization_generates_family_name_for_root(self, mock_definition, mock_anthropic, mock_dependencies):
        """Test that root agents get a generated family name."""
        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
            parent_agent_id=None,  # Root agent
        )

        assert runtime.family_name == "TestFamily"

    def test_initialization_uses_provided_family_name(self, mock_definition, mock_anthropic, mock_dependencies):
        """Test that provided family name is used."""
        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
            family_name="ProvidedFamily",
        )

        assert runtime.family_name == "ProvidedFamily"

    def test_initialization_with_tuned_iterations(self, mock_definition, mock_anthropic, mock_dependencies):
        """Test that iteration tuner adjusts max_iterations."""
        mock_dependencies['tuner'].get_effective_max_iterations.return_value = 15

        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
        )

        # Should use tuned value
        assert mock_definition.max_iterations == 15

    def test_set_user_answer(self, mock_definition, mock_anthropic, mock_dependencies):
        """Test setting user answer."""
        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
        )

        runtime.set_user_answer("This is my answer")

        assert runtime.user_answer == "This is my answer"


class TestAgentRuntimeExecution:
    """Test AgentRuntime execution."""

    @pytest.fixture
    def mock_definition(self):
        """Create a mock agent definition."""
        definition = MagicMock()
        definition.name = "Test Agent"
        definition.purpose = "Testing purpose"
        definition.instructions = "Test instructions"
        definition.input_format = '{"task": {"type": "string"}}'
        definition.output_format = '{"result": {"type": "string"}}'
        definition.max_iterations = 5
        definition.task_complexity = "routine"
        definition.category = "testing"
        definition.model_preference = "haiku"
        definition.instantiation_conditions = ["When testing"]
        definition.termination_conditions = ["When done"]
        definition.clarification_conditions = []
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.get_required_input_fields.return_value = set()
        return definition

    @pytest.fixture
    def mock_response(self):
        """Create a mock Anthropic API response."""
        response = MagicMock()
        response.stop_reason = "end_turn"
        response.content = [
            MagicMock(
                type="text",
                text='{"status": "success", "output": "test completed"}'
            )
        ]
        response.usage = MagicMock()
        response.usage.input_tokens = 100
        response.usage.output_tokens = 50
        return response

    @pytest.fixture
    def mock_anthropic_client(self, mock_response):
        """Mock the Anthropic client with response."""
        with patch('src.runtime.agents.runtime.Anthropic') as mock_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_class.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_all_dependencies(self):
        """Mock all external dependencies for execution."""
        with patch('src.runtime.agents.runtime.get_swarm_state') as mock_swarm, \
             patch('src.runtime.agents.runtime.get_event_bus') as mock_bus, \
             patch('src.runtime.agents.runtime.get_iteration_tuner') as mock_tuner, \
             patch('src.runtime.agents.runtime.get_global_rate_limiter') as mock_limiter, \
             patch('src.runtime.agents.runtime.generate_agent_name') as mock_name, \
             patch('src.runtime.agents.runtime.generate_family_name') as mock_family, \
             patch('src.runtime.agents.runtime.get_improvement_loop') as mock_improve, \
             patch('src.runtime.agents.runtime.get_achievement_tracker') as mock_achieve:

            mock_swarm_instance = MagicMock()
            mock_swarm.return_value = mock_swarm_instance

            mock_bus_instance = MagicMock()
            mock_bus.return_value = mock_bus_instance

            mock_tuner_instance = MagicMock()
            mock_tuner_instance.get_effective_max_iterations.return_value = 5
            mock_tuner_instance.record_execution_result.return_value = MagicMock()
            mock_tuner.return_value = mock_tuner_instance

            mock_limiter_instance = MagicMock()
            mock_limiter_instance.wait_time_needed.return_value = 0
            mock_limiter.return_value = mock_limiter_instance

            mock_name.return_value = "Test Agent-1234"
            mock_family.return_value = "TestFamily"

            mock_improve_instance = MagicMock()
            mock_improve_instance.check_and_recommend.return_value = []
            mock_improve.return_value = mock_improve_instance

            mock_achieve_instance = MagicMock()
            mock_achieve_instance.check_and_award.return_value = []
            mock_achieve.return_value = mock_achieve_instance

            yield {
                'swarm_state': mock_swarm_instance,
                'event_bus': mock_bus_instance,
                'tuner': mock_tuner_instance,
                'rate_limiter': mock_limiter_instance,
                'improvement_loop': mock_improve_instance,
                'achievement_tracker': mock_achieve_instance,
            }

    def test_execute_success(self, mock_definition, mock_anthropic_client, mock_all_dependencies):
        """Test successful execution."""
        # Reset class-level state
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
        )

        result = runtime.execute({"task": "test task"})

        assert result["status"] == "success"
        assert "output" in result
        mock_anthropic_client.messages.create.assert_called()

    def test_execute_tracks_tokens(self, mock_definition, mock_anthropic_client, mock_all_dependencies):
        """Test that execution tracks token usage."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
        )

        runtime.execute({"task": "test"})

        assert runtime.total_input_tokens > 0
        assert runtime.total_output_tokens > 0

    def test_execute_with_model_preference(self, mock_definition, mock_anthropic_client, mock_all_dependencies):
        """Test execution with model preference override."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        mock_definition.model_preference = "sonnet"

        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
        )

        runtime.execute({"task": "test"})

        # Check that the call used sonnet model
        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert "sonnet" in call_kwargs["model"]

    def test_execute_updates_swarm_state(self, mock_definition, mock_anthropic_client, mock_all_dependencies):
        """Test that execution updates swarm state."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        runtime = AgentRuntime(
            definition=mock_definition,
            api_key="test-api-key",
            session_id="test-session",
        )

        runtime.execute({"task": "test"})

        mock_all_dependencies['swarm_state'].update_agent_status.assert_called()


class TestAgentRuntimeToolExecution:
    """Test AgentRuntime with tool execution."""

    @pytest.fixture
    def mock_definition(self):
        """Create a mock agent definition."""
        definition = MagicMock()
        definition.name = "Tool Agent"
        definition.purpose = "Testing tools"
        definition.instructions = "Use tools"
        definition.input_format = '{"task": {"type": "string"}}'
        definition.output_format = '{"result": {"type": "string"}}'
        definition.max_iterations = 5
        definition.task_complexity = "routine"
        definition.category = "testing"
        definition.model_preference = "haiku"
        definition.instantiation_conditions = []
        definition.termination_conditions = []
        definition.clarification_conditions = []
        definition.can_write_code = True
        definition.can_write_tests = False
        definition.get_required_input_fields.return_value = set()
        return definition

    @pytest.fixture
    def mock_tool_use_response(self):
        """Create a mock response with tool use."""
        response = MagicMock()
        response.stop_reason = "tool_use"
        response.content = [
            MagicMock(
                type="tool_use",
                id="tool_call_1",
                name="write_file",
                input={"path": "test.py", "content": "# test"}
            )
        ]
        response.usage = MagicMock()
        response.usage.input_tokens = 100
        response.usage.output_tokens = 50
        return response

    @pytest.fixture
    def mock_final_response(self):
        """Create a mock final response with explicit completion."""
        response = MagicMock()
        response.stop_reason = "end_turn"
        response.content = [
            MagicMock(
                type="text",
                # Must include BOTH status="success" AND phase="complete" for explicit completion
                text='{"status": "success", "phase": "complete", "output": "done"}'
            )
        ]
        response.usage = MagicMock()
        response.usage.input_tokens = 50
        response.usage.output_tokens = 30
        return response

    @pytest.fixture
    def mock_tools(self):
        """Create mock tool registry."""
        tools = MagicMock()
        tools.to_anthropic_format.return_value = [
            {
                "name": "write_file",
                "description": "Write a file",
                "input_schema": {"type": "object"}
            }
        ]
        tools.has_tool.return_value = True
        tools.get_tool.return_value = MagicMock(
            execute=MagicMock(return_value={"success": True})
        )
        return tools

    @pytest.fixture
    def mock_all_dependencies_for_tools(self):
        """Mock all dependencies for tool tests."""
        with patch('src.runtime.agents.runtime.get_swarm_state') as mock_swarm, \
             patch('src.runtime.agents.runtime.get_event_bus') as mock_bus, \
             patch('src.runtime.agents.runtime.get_iteration_tuner') as mock_tuner, \
             patch('src.runtime.agents.runtime.get_global_rate_limiter') as mock_limiter, \
             patch('src.runtime.agents.runtime.generate_agent_name') as mock_name, \
             patch('src.runtime.agents.runtime.generate_family_name') as mock_family, \
             patch('src.runtime.agents.runtime.get_improvement_loop') as mock_improve, \
             patch('src.runtime.agents.runtime.get_achievement_tracker') as mock_achieve:

            mock_swarm.return_value = MagicMock()
            mock_bus.return_value = MagicMock()

            mock_tuner_instance = MagicMock()
            mock_tuner_instance.get_effective_max_iterations.return_value = 5
            mock_tuner_instance.record_execution_result.return_value = MagicMock()
            mock_tuner.return_value = mock_tuner_instance

            mock_limiter_instance = MagicMock()
            mock_limiter_instance.wait_time_needed.return_value = 0
            mock_limiter.return_value = mock_limiter_instance

            mock_name.return_value = "Tool Agent-1234"
            mock_family.return_value = "TestFamily"

            mock_improve.return_value = MagicMock(check_and_recommend=MagicMock(return_value=[]))
            mock_achieve.return_value = MagicMock(check_and_award=MagicMock(return_value=[]))

            yield

    def test_execute_with_tools(
        self,
        mock_definition,
        mock_tool_use_response,
        mock_final_response,
        mock_tools,
        mock_all_dependencies_for_tools
    ):
        """Test execution with tool use."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic') as mock_class:
            mock_client = MagicMock()
            # First call returns tool use, second returns final
            mock_client.messages.create.side_effect = [
                mock_tool_use_response,
                mock_final_response,
            ]
            mock_class.return_value = mock_client

            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
                tools=mock_tools,
            )

            result = runtime.execute({"task": "use tools"})

            assert result["status"] == "success"
            # Should have called API twice (tool use + final)
            assert mock_client.messages.create.call_count >= 1


class TestAgentRuntimeErrorHandling:
    """Test AgentRuntime error handling."""

    @pytest.fixture
    def mock_definition(self):
        """Create a mock agent definition."""
        definition = MagicMock()
        definition.name = "Error Agent"
        definition.purpose = "Testing errors"
        definition.instructions = "Handle errors"
        definition.input_format = '{"task": {"type": "string"}}'
        definition.output_format = '{"result": {"type": "string"}}'
        definition.max_iterations = 3
        definition.task_complexity = "routine"
        definition.category = "testing"
        definition.model_preference = "haiku"
        definition.instantiation_conditions = []
        definition.termination_conditions = []
        definition.clarification_conditions = []
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.get_required_input_fields.return_value = set()
        return definition

    @pytest.fixture
    def mock_all_dependencies_for_errors(self):
        """Mock all dependencies for error tests."""
        with patch('src.runtime.agents.runtime.get_swarm_state') as mock_swarm, \
             patch('src.runtime.agents.runtime.get_event_bus') as mock_bus, \
             patch('src.runtime.agents.runtime.get_iteration_tuner') as mock_tuner, \
             patch('src.runtime.agents.runtime.get_global_rate_limiter') as mock_limiter, \
             patch('src.runtime.agents.runtime.generate_agent_name') as mock_name, \
             patch('src.runtime.agents.runtime.generate_family_name') as mock_family, \
             patch('src.runtime.agents.runtime.get_improvement_loop') as mock_improve, \
             patch('src.runtime.agents.runtime.get_achievement_tracker') as mock_achieve:

            mock_swarm.return_value = MagicMock()
            mock_bus.return_value = MagicMock()

            mock_tuner_instance = MagicMock()
            mock_tuner_instance.get_effective_max_iterations.return_value = 3
            mock_tuner_instance.record_execution_result.return_value = MagicMock()
            mock_tuner.return_value = mock_tuner_instance

            mock_limiter_instance = MagicMock()
            mock_limiter_instance.wait_time_needed.return_value = 0
            mock_limiter.return_value = mock_limiter_instance

            mock_name.return_value = "Error Agent-1234"
            mock_family.return_value = "TestFamily"

            mock_improve.return_value = MagicMock(check_and_recommend=MagicMock(return_value=[]))
            mock_achieve.return_value = MagicMock(check_and_award=MagicMock(return_value=[]))

            yield

    def test_execute_max_iterations_reached(self, mock_definition, mock_all_dependencies_for_errors):
        """Test that max iterations returns appropriate status."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic') as mock_class:
            mock_client = MagicMock()

            # Response that indicates agent is still working (status=in_progress)
            # This will cause the loop to continue with auto_continue=True
            response = MagicMock()
            response.stop_reason = "end_turn"
            response.content = [MagicMock(type="text", text='{"status": "in_progress", "phase": "working"}')]
            response.usage = MagicMock()
            response.usage.input_tokens = 100
            response.usage.output_tokens = 50

            mock_client.messages.create.return_value = response
            mock_class.return_value = mock_client

            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
                auto_continue=True,  # Enable auto-continue to keep looping
            )

            result = runtime.execute({"task": "test"})

            # Should have iterated max_iterations times
            assert runtime.iteration_count == mock_definition.max_iterations


class TestAgentRuntimeModelSelection:
    """Test AgentRuntime model selection."""

    @pytest.fixture
    def mock_definition(self):
        """Create a mock agent definition."""
        definition = MagicMock()
        definition.name = "Model Agent"
        definition.purpose = "Testing model selection"
        definition.instructions = "Test"
        definition.input_format = '{"task": {"type": "string"}}'
        definition.output_format = '{"result": {"type": "string"}}'
        definition.max_iterations = 5
        definition.task_complexity = "strategic"
        definition.category = "leadership"
        definition.model_preference = "default"
        definition.instantiation_conditions = []
        definition.termination_conditions = []
        definition.clarification_conditions = []
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.get_required_input_fields.return_value = set()
        return definition

    @pytest.fixture
    def mock_all_dependencies_for_model(self):
        """Mock all dependencies for model tests."""
        with patch('src.runtime.agents.runtime.get_swarm_state') as mock_swarm, \
             patch('src.runtime.agents.runtime.get_event_bus') as mock_bus, \
             patch('src.runtime.agents.runtime.get_iteration_tuner') as mock_tuner, \
             patch('src.runtime.agents.runtime.get_global_rate_limiter') as mock_limiter, \
             patch('src.runtime.agents.runtime.generate_agent_name') as mock_name, \
             patch('src.runtime.agents.runtime.generate_family_name') as mock_family, \
             patch('src.runtime.agents.runtime.get_model_router') as mock_router, \
             patch('src.runtime.agents.runtime.get_improvement_loop') as mock_improve, \
             patch('src.runtime.agents.runtime.get_achievement_tracker') as mock_achieve:

            mock_swarm.return_value = MagicMock()
            mock_bus.return_value = MagicMock()

            mock_tuner_instance = MagicMock()
            mock_tuner_instance.get_effective_max_iterations.return_value = 5
            mock_tuner_instance.record_execution_result.return_value = MagicMock()
            mock_tuner.return_value = mock_tuner_instance

            mock_limiter_instance = MagicMock()
            mock_limiter_instance.wait_time_needed.return_value = 0
            mock_limiter.return_value = mock_limiter_instance

            mock_name.return_value = "Model Agent-1234"
            mock_family.return_value = "TestFamily"

            # Mock router for dynamic selection
            mock_router_instance = MagicMock()
            mock_router_instance.analyze_task_profile.return_value = MagicMock()
            mock_router_instance.select_model.return_value = MagicMock(
                model_id="claude-sonnet-4-5-20250929",
                selection_reason="Dynamic selection"
            )
            mock_router.return_value = mock_router_instance

            mock_improve.return_value = MagicMock(check_and_recommend=MagicMock(return_value=[]))
            mock_achieve.return_value = MagicMock(check_and_award=MagicMock(return_value=[]))

            yield {'router': mock_router_instance}

    def test_dynamic_model_selection(self, mock_definition, mock_all_dependencies_for_model):
        """Test dynamic model selection."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic') as mock_class:
            mock_client = MagicMock()
            response = MagicMock()
            response.stop_reason = "end_turn"
            response.content = [MagicMock(type="text", text='{"result": "ok"}')]
            response.usage = MagicMock(input_tokens=50, output_tokens=25)
            mock_client.messages.create.return_value = response
            mock_class.return_value = mock_client

            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
                budget_tier="balanced",
                use_dynamic_model_selection=True,
            )

            runtime.execute({"task": "test"})

            # Router should have been called
            mock_all_dependencies_for_model['router'].analyze_task_profile.assert_called()

    def test_static_model_selection_full_firepower(self, mock_definition, mock_all_dependencies_for_model):
        """Test static model selection with full_firepower tier."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic') as mock_class:
            mock_client = MagicMock()
            response = MagicMock()
            response.stop_reason = "end_turn"
            response.content = [MagicMock(type="text", text='{"result": "ok"}')]
            response.usage = MagicMock(input_tokens=50, output_tokens=25)
            mock_client.messages.create.return_value = response
            mock_class.return_value = mock_client

            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
                budget_tier="full_firepower",  # Should use static selection
            )

            runtime.execute({"task": "test"})

            # Check that opus was used
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "opus" in call_kwargs["model"]

    def test_model_preference_override(self, mock_definition, mock_all_dependencies_for_model):
        """Test that explicit model_preference overrides other selection."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        mock_definition.model_preference = "opus"

        with patch('src.runtime.agents.runtime.Anthropic') as mock_class:
            mock_client = MagicMock()
            response = MagicMock()
            response.stop_reason = "end_turn"
            response.content = [MagicMock(type="text", text='{"result": "ok"}')]
            response.usage = MagicMock(input_tokens=50, output_tokens=25)
            mock_client.messages.create.return_value = response
            mock_class.return_value = mock_client

            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
                budget_tier="economical",  # Would normally use haiku
            )

            runtime.execute({"task": "test"})

            # Should use opus due to model_preference override
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "opus" in call_kwargs["model"]


class TestAgentRuntimePromptBuilding:
    """Test AgentRuntime prompt building methods."""

    @pytest.fixture
    def mock_definition(self):
        """Create a mock agent definition."""
        definition = MagicMock()
        definition.name = "Prompt Agent"
        definition.purpose = "Testing prompts"
        definition.instructions = "Build prompts correctly"
        definition.input_format = '{"task": "description"}'
        definition.output_format = '{"result": "output"}'
        definition.max_iterations = 5
        definition.task_complexity = "routine"
        definition.category = "testing"
        definition.model_preference = "haiku"
        definition.instantiation_conditions = ["When testing prompts"]
        definition.termination_conditions = ["When prompts are built"]
        definition.clarification_conditions = ["When input is unclear"]
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.get_required_input_fields.return_value = set()
        return definition

    @pytest.fixture
    def mock_dependencies_for_prompts(self):
        """Mock dependencies for prompt tests."""
        with patch('src.runtime.agents.runtime.get_swarm_state') as mock_swarm, \
             patch('src.runtime.agents.runtime.get_event_bus') as mock_bus, \
             patch('src.runtime.agents.runtime.get_iteration_tuner') as mock_tuner, \
             patch('src.runtime.agents.runtime.generate_agent_name') as mock_name, \
             patch('src.runtime.agents.runtime.generate_family_name') as mock_family:

            mock_swarm.return_value = MagicMock()
            mock_bus.return_value = MagicMock()

            mock_tuner_instance = MagicMock()
            mock_tuner_instance.get_effective_max_iterations.return_value = 5
            mock_tuner.return_value = mock_tuner_instance

            mock_name.return_value = "Prompt Agent-1234"
            mock_family.return_value = "TestFamily"

            yield

    def test_build_system_prompt(self, mock_definition, mock_dependencies_for_prompts):
        """Test building system prompt."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            system_prompt = runtime._build_system_prompt()

            assert mock_definition.purpose in system_prompt
            assert mock_definition.instructions in system_prompt

    def test_build_user_prompt(self, mock_definition, mock_dependencies_for_prompts):
        """Test building user prompt."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            user_prompt = runtime._build_user_prompt({"task": "do something"})

            assert "do something" in user_prompt


class TestAgentRuntimeInputValidation:
    """Test AgentRuntime input validation."""

    @pytest.fixture
    def mock_definition(self):
        """Create a mock agent definition."""
        definition = MagicMock()
        definition.name = "Validation Agent"
        definition.purpose = "Testing validation"
        definition.instructions = "Validate inputs"
        definition.input_format = '{"task": "string - the task to perform", "priority": "string (optional)"}'
        definition.output_format = '{"result": "string"}'
        definition.max_iterations = 5
        definition.task_complexity = "routine"
        definition.category = "testing"
        definition.model_preference = "haiku"
        definition.instantiation_conditions = []
        definition.termination_conditions = []
        definition.clarification_conditions = []
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.get_required_input_fields.return_value = set()
        return definition

    @pytest.fixture
    def mock_dependencies_for_validation(self):
        """Mock dependencies for validation tests."""
        with patch('src.runtime.agents.runtime.get_swarm_state') as mock_swarm, \
             patch('src.runtime.agents.runtime.get_event_bus') as mock_bus, \
             patch('src.runtime.agents.runtime.get_iteration_tuner') as mock_tuner, \
             patch('src.runtime.agents.runtime.generate_agent_name') as mock_name, \
             patch('src.runtime.agents.runtime.generate_family_name') as mock_family:

            mock_swarm.return_value = MagicMock()
            mock_bus.return_value = MagicMock()

            mock_tuner_instance = MagicMock()
            mock_tuner_instance.get_effective_max_iterations.return_value = 5
            mock_tuner.return_value = mock_tuner_instance

            mock_name.return_value = "Validation Agent-1234"
            mock_family.return_value = "TestFamily"

            yield

    def test_validate_input_with_required_field(self, mock_definition, mock_dependencies_for_validation):
        """Test validation with required field present."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            # Should not raise - required field present
            runtime._validate_input({"task": "test task"})

    def test_validate_input_missing_required_field(self, mock_definition, mock_dependencies_for_validation):
        """Test validation raises when required field missing."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            with pytest.raises(ValueError, match="Missing required input field"):
                runtime._validate_input({})

    def test_validate_input_with_optional_field(self, mock_definition, mock_dependencies_for_validation):
        """Test validation allows missing optional fields."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            # Should not raise - priority is optional
            runtime._validate_input({"task": "test"})

    def test_validate_input_with_invalid_json_schema(self, mock_definition, mock_dependencies_for_validation):
        """Test validation skips when schema can't be parsed."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        mock_definition.input_format = "not valid json"

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            # Should not raise - invalid schema is skipped
            runtime._validate_input({"anything": "goes"})

    def test_validate_input_with_json_schema_dict_format(self, mock_dependencies_for_validation):
        """Test validation with JSON schema dict format."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        definition = MagicMock()
        definition.name = "Schema Agent"
        definition.purpose = "Testing"
        definition.instructions = "Test"
        definition.input_format = '{"task": {"type": "string", "description": "Required task"}}'
        definition.output_format = '{}'
        definition.max_iterations = 5
        definition.task_complexity = "routine"
        definition.category = "testing"
        definition.model_preference = "haiku"
        definition.instantiation_conditions = []
        definition.termination_conditions = []
        definition.clarification_conditions = []
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.get_required_input_fields.return_value = set()

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=definition,
                api_key="test-api-key",
            )

            # Should raise - required field missing
            with pytest.raises(ValueError, match="Missing required input field"):
                runtime._validate_input({})


class TestAgentRuntimeResponseExtraction:
    """Test AgentRuntime response extraction."""

    @pytest.fixture
    def mock_definition(self):
        """Create a mock agent definition."""
        definition = MagicMock()
        definition.name = "Extract Agent"
        definition.purpose = "Testing extraction"
        definition.instructions = "Extract responses"
        definition.input_format = '{"task": "string"}'
        definition.output_format = '{"result": "string"}'
        definition.max_iterations = 5
        definition.task_complexity = "routine"
        definition.category = "testing"
        definition.model_preference = "haiku"
        definition.instantiation_conditions = []
        definition.termination_conditions = []
        definition.clarification_conditions = []
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.get_required_input_fields.return_value = set()
        return definition

    @pytest.fixture
    def mock_dependencies_for_extraction(self):
        """Mock dependencies for extraction tests."""
        with patch('src.runtime.agents.runtime.get_swarm_state') as mock_swarm, \
             patch('src.runtime.agents.runtime.get_event_bus') as mock_bus, \
             patch('src.runtime.agents.runtime.get_iteration_tuner') as mock_tuner, \
             patch('src.runtime.agents.runtime.generate_agent_name') as mock_name, \
             patch('src.runtime.agents.runtime.generate_family_name') as mock_family:

            mock_swarm.return_value = MagicMock()
            mock_bus.return_value = MagicMock()

            mock_tuner_instance = MagicMock()
            mock_tuner_instance.get_effective_max_iterations.return_value = 5
            mock_tuner.return_value = mock_tuner_instance

            mock_name.return_value = "Extract Agent-1234"
            mock_family.return_value = "TestFamily"

            yield

    def test_extract_json_from_code_block(self, mock_definition, mock_dependencies_for_extraction):
        """Test extracting JSON from markdown code block."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            text = '```json\n{"result": "extracted"}\n```'
            result = runtime._extract_json_from_response(text)

            assert result["result"] == "extracted"

    def test_extract_json_direct(self, mock_definition, mock_dependencies_for_extraction):
        """Test extracting direct JSON without code block."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            text = '{"result": "direct"}'
            result = runtime._extract_json_from_response(text)

            assert result["result"] == "direct"

    def test_extract_json_raises_on_invalid(self, mock_definition, mock_dependencies_for_extraction):
        """Test extraction raises on invalid JSON."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            text = 'This is not valid JSON at all'

            with pytest.raises(ValueError, match="does not contain valid JSON"):
                runtime._extract_json_from_response(text)

    def test_extract_final_response_with_text_type(self, mock_definition, mock_dependencies_for_extraction):
        """Test extracting final response from text content."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            response = MagicMock()
            response.content = [
                MagicMock(type="text", text='{"status": "success"}')
            ]

            result = runtime._extract_final_response(response)

            assert result["status"] == "success"

    def test_extract_final_response_conversational(self, mock_definition, mock_dependencies_for_extraction):
        """Test extracting conversational response."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            response = MagicMock()
            response.content = [
                MagicMock(type="text", text='Hello, this is a conversational response.')
            ]

            result = runtime._extract_final_response(response)

            assert result["response_type"] == "conversational"
            assert "Hello" in result["message"]

    def test_extract_final_response_empty(self, mock_definition, mock_dependencies_for_extraction):
        """Test extracting from response with no text content."""
        AgentRuntime._metrics_tracker = None
        AgentRuntime._activity_tracker = None
        AgentRuntime._circuit_breaker = None

        with patch('src.runtime.agents.runtime.Anthropic'):
            runtime = AgentRuntime(
                definition=mock_definition,
                api_key="test-api-key",
            )

            response = MagicMock()
            response.content = []

            result = runtime._extract_final_response(response)

            assert result == {}
