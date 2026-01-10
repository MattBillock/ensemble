"""Tests for agent runtime core."""
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from agents.definition import AgentDefinition
from agents.runtime import AgentRuntime
from agents.tools import ToolRegistry, WriteFileTool


class TestAgentRuntime:
    """Test agent runtime execution."""

    @pytest.fixture
    def code_writer_def(self):
        """Load code_writer agent definition."""
        path = Path(__file__).parent.parent / "agent_types" / "code_writer.md"
        return AgentDefinition.from_file(path)

    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic API client."""
        with patch("agents.runtime.Anthropic") as mock:
            # Set up mock response
            mock_response = Mock()
            mock_response.content = [Mock(text=json.dumps({
                "status": "success",
                "output_file": "solution.py",
                "message": "Implemented solution using dynamic programming",
                "needs_clarification": False,
                "clarification_question": ""
            }))]

            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock.return_value = mock_client

            yield mock

    def test_runtime_initialization(self, code_writer_def):
        """Test creating an agent runtime."""
        runtime = AgentRuntime(code_writer_def, api_key="test-key")

        assert runtime.definition == code_writer_def
        assert runtime.iteration_count == 0

    def test_execute_agent(self, code_writer_def, mock_anthropic_client):
        """Test executing an agent with valid input."""
        runtime = AgentRuntime(code_writer_def, api_key="test-key")

        input_data = {
            "problem_description": "Find the sum of all multiples of 3 or 5 below 1000",
            "problem_number": 1,
            "output_file": "problems/problem_001.py"
        }

        result = runtime.execute(input_data)

        assert result["status"] == "success"
        assert result["output_file"] == "solution.py"
        assert result["needs_clarification"] is False
        assert runtime.iteration_count == 1

    def test_execute_validates_input_format(self, code_writer_def):
        """Test that execute validates input against agent's expected format."""
        runtime = AgentRuntime(code_writer_def, api_key="test-key")

        # Missing required field
        invalid_input = {
            "problem_number": 1
        }

        with pytest.raises(ValueError, match="problem_description"):
            runtime.execute(invalid_input)

    def test_execute_respects_max_iterations(self, code_writer_def, mock_anthropic_client):
        """Test that agent stops after max iterations."""
        runtime = AgentRuntime(code_writer_def, api_key="test-key")

        # Mock response that always asks for clarification (to keep iterating)
        mock_client = mock_anthropic_client.return_value
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "status": "success",
            "output_file": "",
            "message": "",
            "needs_clarification": True,
            "clarification_question": "Need more info"
        }))]
        mock_client.messages.create.return_value = mock_response

        input_data = {
            "problem_description": "Test problem",
            "output_file": "test.py"
        }

        result = runtime.execute(input_data)

        # Should stop at max_iterations (5 for code_writer)
        assert runtime.iteration_count == code_writer_def.max_iterations

    def test_build_system_prompt(self, code_writer_def):
        """Test building the system prompt from agent definition."""
        runtime = AgentRuntime(code_writer_def, api_key="test-key")

        system_prompt = runtime._build_system_prompt()

        # Should include key parts of the definition
        assert "Code Writer" in system_prompt
        assert code_writer_def.purpose in system_prompt
        assert code_writer_def.instructions in system_prompt
        assert "Input Format" in system_prompt
        assert "Output Format" in system_prompt

    def test_build_user_prompt(self, code_writer_def):
        """Test building user prompt with input data."""
        runtime = AgentRuntime(code_writer_def, api_key="test-key")

        input_data = {
            "problem_description": "Test problem",
            "output_file": "test.py"
        }

        user_prompt = runtime._build_user_prompt(input_data)

        assert "Test problem" in user_prompt
        assert "test.py" in user_prompt

    def test_uses_correct_model(self, code_writer_def, mock_anthropic_client):
        """Test that runtime uses the model specified in agent definition."""
        runtime = AgentRuntime(code_writer_def, api_key="test-key")

        input_data = {
            "problem_description": "Test",
            "output_file": "test.py"
        }

        runtime.execute(input_data)

        # Check that Anthropic client was called with haiku model
        mock_client = mock_anthropic_client.return_value
        call_args = mock_client.messages.create.call_args
        assert "claude-3-5-haiku" in call_args.kwargs["model"]


class TestAgentRuntimeWithTools:
    """Test agent runtime with tool use."""

    @pytest.fixture
    def code_writer_def(self):
        """Load code_writer agent definition."""
        path = Path(__file__).parent.parent / "agent_types" / "code_writer.md"
        return AgentDefinition.from_file(path)

    @pytest.fixture
    def tool_registry(self):
        """Create a tool registry with default tools."""
        return ToolRegistry.default()

    def test_runtime_accepts_tool_registry(self, code_writer_def, tool_registry):
        """Test that runtime can be initialized with tools."""
        runtime = AgentRuntime(code_writer_def, api_key="test-key", tools=tool_registry)

        assert runtime.tools == tool_registry

    def test_runtime_passes_tools_to_api(self, code_writer_def, tool_registry):
        """Test that runtime includes tools in API calls."""
        with patch("agents.runtime.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(text=json.dumps({
                "status": "success",
                "output_file": "test.py",
                "message": "Done",
                "needs_clarification": False
            }))]
            mock_response.stop_reason = "end_turn"
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            runtime = AgentRuntime(code_writer_def, api_key="test-key", tools=tool_registry)

            input_data = {
                "problem_description": "Test",
                "output_file": "test.py"
            }

            runtime.execute(input_data)

            # Verify tools were passed to API
            call_args = mock_client.messages.create.call_args
            assert "tools" in call_args.kwargs
            assert len(call_args.kwargs["tools"]) > 0

    def test_runtime_handles_tool_use(self, code_writer_def, tool_registry):
        """Test that runtime executes tools when agent requests them."""
        with patch("agents.runtime.Anthropic") as mock_anthropic:
            mock_client = Mock()

            # First response: agent wants to use write_file tool
            tool_use_response = Mock()
            tool_use_block = Mock()
            tool_use_block.type = "tool_use"
            tool_use_block.id = "tool_1"
            tool_use_block.name = "write_file"
            tool_use_block.input = {
                "file_path": "test.py",
                "content": "print('hello')"
            }
            tool_use_response.content = [tool_use_block]
            tool_use_response.stop_reason = "tool_use"

            # Second response: agent completes after tool use
            final_response = Mock()
            final_response.content = [Mock(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "output_file": "test.py",
                    "message": "Done",
                    "needs_clarification": False
                })
            )]
            final_response.stop_reason = "end_turn"

            mock_client.messages.create.side_effect = [tool_use_response, final_response]
            mock_anthropic.return_value = mock_client

            runtime = AgentRuntime(code_writer_def, api_key="test-key", tools=tool_registry)

            input_data = {
                "problem_description": "Test",
                "output_file": "test.py"
            }

            with patch.object(tool_registry.get_tool("write_file"), "execute") as mock_execute:
                mock_execute.return_value = {"success": True, "message": "File written"}

                result = runtime.execute(input_data)

                # Verify tool was executed
                assert mock_execute.called
                assert result["status"] == "success"

    def test_runtime_without_tools_still_works(self, code_writer_def):
        """Test that runtime works without tools (backward compatibility)."""
        with patch("agents.runtime.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "output_file": "test.py",
                    "message": "Done",
                    "needs_clarification": False
                })
            )]
            mock_response.stop_reason = "end_turn"
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            # Create runtime without tools
            runtime = AgentRuntime(code_writer_def, api_key="test-key")

            input_data = {
                "problem_description": "Test",
                "output_file": "test.py"
            }

            result = runtime.execute(input_data)

            # Should work fine without tools
            assert result["status"] == "success"

            # Verify no tools were passed to API
            call_args = mock_client.messages.create.call_args
            assert "tools" not in call_args.kwargs or call_args.kwargs["tools"] is None
