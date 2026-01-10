"""Tests for agent tools."""
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import pytest

from agents.tools import Tool, WriteFileTool, ReadFileTool, RunCommandTool, SpawnAgentTool, ToolRegistry


class TestTool:
    """Test base tool functionality."""

    def test_tool_has_required_attributes(self):
        """Test that Tool defines required interface."""
        # WriteFileTool should have name, description, and schema
        tool = WriteFileTool()

        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "input_schema")
        assert callable(tool.execute)

    def test_tool_to_anthropic_format(self):
        """Test converting tool to Anthropic API format."""
        tool = WriteFileTool()

        anthropic_format = tool.to_anthropic_format()

        assert anthropic_format["name"] == tool.name
        assert anthropic_format["description"] == tool.description
        assert anthropic_format["input_schema"] == tool.input_schema


class TestWriteFileTool:
    """Test file writing tool."""

    def test_write_file_schema(self):
        """Test WriteFileTool has correct schema."""
        tool = WriteFileTool()

        assert tool.name == "write_file"
        assert "file_path" in tool.input_schema["properties"]
        assert "content" in tool.input_schema["properties"]
        assert tool.input_schema["required"] == ["file_path", "content"]

    def test_write_file_execution(self):
        """Test writing a file."""
        tool = WriteFileTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"

            result = tool.execute({
                "file_path": str(file_path),
                "content": "Hello, World!"
            })

            assert result["success"] is True
            assert file_path.exists()
            assert file_path.read_text() == "Hello, World!"

    def test_write_file_creates_parent_directories(self):
        """Test that write_file creates parent directories if needed."""
        tool = WriteFileTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "test.txt"

            result = tool.execute({
                "file_path": str(file_path),
                "content": "test content"
            })

            assert result["success"] is True
            assert file_path.exists()

    def test_write_file_error_handling(self):
        """Test write_file handles errors gracefully."""
        tool = WriteFileTool()

        # Try to write to invalid path
        result = tool.execute({
            "file_path": "/invalid/path/that/cannot/exist/file.txt",
            "content": "test"
        })

        assert result["success"] is False
        assert "error" in result


class TestReadFileTool:
    """Test file reading tool."""

    def test_read_file_schema(self):
        """Test ReadFileTool has correct schema."""
        tool = ReadFileTool()

        assert tool.name == "read_file"
        assert "file_path" in tool.input_schema["properties"]
        assert tool.input_schema["required"] == ["file_path"]

    def test_read_file_execution(self):
        """Test reading a file."""
        tool = ReadFileTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            file_path.write_text("Test content")

            result = tool.execute({
                "file_path": str(file_path)
            })

            assert result["success"] is True
            assert result["content"] == "Test content"

    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        tool = ReadFileTool()

        result = tool.execute({
            "file_path": "/nonexistent/file.txt"
        })

        assert result["success"] is False
        assert "error" in result


class TestToolRegistry:
    """Test tool registry for managing available tools."""

    def test_register_and_get_tool(self):
        """Test registering and retrieving tools."""
        registry = ToolRegistry()
        tool = WriteFileTool()

        registry.register(tool)

        retrieved = registry.get_tool("write_file")
        assert retrieved is not None
        assert retrieved.name == "write_file"

    def test_get_all_tools(self):
        """Test getting all registered tools."""
        registry = ToolRegistry()
        registry.register(WriteFileTool())
        registry.register(ReadFileTool())

        tools = registry.get_all_tools()

        assert len(tools) == 2
        assert any(t.name == "write_file" for t in tools)
        assert any(t.name == "read_file" for t in tools)

    def test_to_anthropic_format(self):
        """Test converting all tools to Anthropic format."""
        registry = ToolRegistry()
        registry.register(WriteFileTool())
        registry.register(ReadFileTool())

        anthropic_tools = registry.to_anthropic_format()

        assert len(anthropic_tools) == 2
        assert all("name" in t for t in anthropic_tools)
        assert all("description" in t for t in anthropic_tools)
        assert all("input_schema" in t for t in anthropic_tools)

    def test_default_registry(self):
        """Test that default registry includes standard tools."""
        registry = ToolRegistry.default()

        tools = registry.get_all_tools()

        # Should have at least write_file, read_file, and run_command
        assert len(tools) >= 3
        assert registry.get_tool("write_file") is not None
        assert registry.get_tool("read_file") is not None
        assert registry.get_tool("run_command") is not None


class TestRunCommandTool:
    """Test command execution tool."""

    def test_run_command_schema(self):
        """Test RunCommandTool has correct schema."""
        tool = RunCommandTool()

        assert tool.name == "run_command"
        assert "command" in tool.input_schema["properties"]
        assert "working_directory" in tool.input_schema["properties"]
        assert tool.input_schema["required"] == ["command"]

    def test_run_command_execution_success(self):
        """Test executing a simple command."""
        tool = RunCommandTool()

        result = tool.execute({
            "command": "echo 'Hello, World!'"
        })

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "Hello, World!" in result["stdout"]

    def test_run_command_with_working_directory(self):
        """Test executing command in specific directory."""
        tool = RunCommandTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool.execute({
                "command": "pwd",
                "working_directory": tmpdir
            })

            assert result["success"] is True
            assert tmpdir in result["stdout"]

    def test_run_command_handles_failure(self):
        """Test command that fails returns appropriate result."""
        tool = RunCommandTool()

        result = tool.execute({
            "command": "exit 1"
        })

        assert result["success"] is False
        assert result["exit_code"] == 1

    def test_run_command_captures_stderr(self):
        """Test that stderr is captured."""
        tool = RunCommandTool()

        # Command that outputs to stderr
        result = tool.execute({
            "command": "python3 -c 'import sys; sys.stderr.write(\"error message\")'"
        })

        assert "error message" in result["stderr"]

    @patch('subprocess.run')
    def test_run_command_security_basic(self, mock_run):
        """Test that dangerous commands are handled (basic check)."""
        tool = RunCommandTool()

        # This test just verifies the command is passed through correctly
        # In a real implementation, you might want command validation
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        tool.execute({"command": "ls"})

        assert mock_run.called


class TestSpawnAgentTool:
    """Test agent spawning tool."""

    def test_spawn_agent_schema(self):
        """Test SpawnAgentTool has correct schema."""
        tool = SpawnAgentTool(
            agent_types_dir=Path("agent_types"),
            api_key="test-key"
        )

        assert tool.name == "spawn_agent"
        assert "agent_type" in tool.input_schema["properties"]
        assert "input_data" in tool.input_schema["properties"]
        assert tool.input_schema["required"] == ["agent_type", "input_data"]

    @patch('agents.definition.AgentDefinition')
    @patch('agents.runtime.AgentRuntime')
    def test_spawn_agent_execution_success(self, mock_runtime_class, mock_def_class):
        """Test successfully spawning and executing an agent."""
        # Mock agent definition
        mock_definition = Mock()
        mock_definition.name = "Code Writer"
        mock_def_class.from_file.return_value = mock_definition

        # Mock runtime execution
        mock_runtime = Mock()
        mock_runtime.execute.return_value = {
            "status": "success",
            "output_file": "test.py",
            "message": "Done"
        }
        mock_runtime_class.return_value = mock_runtime

        # Create tool
        tool = SpawnAgentTool(
            agent_types_dir=Path("agent_types"),
            api_key="test-key"
        )

        # Execute
        result = tool.execute({
            "agent_type": "code_writer",
            "input_data": {"problem_description": "Test", "output_file": "test.py"}
        })

        assert result["success"] is True
        assert result["result"]["status"] == "success"
        assert mock_runtime.execute.called

    @patch('agents.definition.AgentDefinition')
    def test_spawn_agent_unknown_agent_type(self, mock_def_class):
        """Test handling of unknown agent type."""
        # Mock file not found
        mock_def_class.from_file.side_effect = FileNotFoundError("Agent not found")

        tool = SpawnAgentTool(
            agent_types_dir=Path("agent_types"),
            api_key="test-key"
        )

        result = tool.execute({
            "agent_type": "unknown_agent",
            "input_data": {}
        })

        assert result["success"] is False
        assert "error" in result

    @patch('agents.definition.AgentDefinition')
    @patch('agents.runtime.AgentRuntime')
    def test_spawn_agent_execution_failure(self, mock_runtime_class, mock_def_class):
        """Test handling agent execution errors."""
        mock_definition = Mock()
        mock_def_class.from_file.return_value = mock_definition

        # Mock runtime throwing exception
        mock_runtime = Mock()
        mock_runtime.execute.side_effect = Exception("Agent failed")
        mock_runtime_class.return_value = mock_runtime

        tool = SpawnAgentTool(
            agent_types_dir=Path("agent_types"),
            api_key="test-key"
        )

        result = tool.execute({
            "agent_type": "code_writer",
            "input_data": {}
        })

        assert result["success"] is False
        assert "Agent failed" in result["error"]

    @patch('agents.definition.AgentDefinition')
    @patch('agents.runtime.AgentRuntime')
    def test_spawn_agent_includes_tools(self, mock_runtime_class, mock_def_class):
        """Test that spawned agents get tools registry."""
        mock_definition = Mock()
        mock_def_class.from_file.return_value = mock_definition

        mock_runtime = Mock()
        mock_runtime.execute.return_value = {"status": "success"}
        mock_runtime_class.return_value = mock_runtime

        # Create tool with tools registry
        tools = ToolRegistry.default()
        tool = SpawnAgentTool(
            agent_types_dir=Path("agent_types"),
            api_key="test-key",
            tools=tools
        )

        tool.execute({
            "agent_type": "code_writer",
            "input_data": {}
        })

        # Verify runtime was created with tools
        call_args = mock_runtime_class.call_args
        assert call_args.kwargs.get("tools") == tools
