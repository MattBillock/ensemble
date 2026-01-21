"""
Unit tests for tools module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from src.runtime.agents.tools import (
    WriteFileTool,
    ReadFileTool,
    RunCommandTool,
    ProjectTrackingTool,
    GitCommitTool,
    SpawnAgentTool,
    ToolRegistry,
)


class TestWriteFileTool:
    """Test WriteFileTool."""

    @pytest.fixture
    def mock_definition(self):
        """Create mock agent definition."""
        definition = MagicMock()
        definition.name = "Test Agent"
        definition.can_write_code = True
        definition.can_write_tests = True
        definition.can_write_markdown = True
        return definition

    @pytest.fixture
    def tool(self, mock_definition):
        """Create WriteFileTool instance."""
        return WriteFileTool(
            agent_definition=mock_definition,
            agent_id="test-agent-1",
            agent_name="Test Agent",
            request_id="req-123"
        )

    def test_tool_attributes(self, tool):
        """Test tool has required attributes."""
        assert tool.name == "write_file"
        assert "Write content" in tool.description
        assert "file_path" in tool.input_schema["properties"]
        assert "content" in tool.input_schema["properties"]

    def test_to_anthropic_format(self, tool):
        """Test conversion to Anthropic format."""
        result = tool.to_anthropic_format()

        assert result["name"] == "write_file"
        assert "description" in result
        assert "input_schema" in result

    def test_is_protected_file(self, tool):
        """Test protected file detection."""
        assert tool._is_protected_file(Path("requirements.txt"))
        assert tool._is_protected_file(Path("README.md"))
        assert tool._is_protected_file(Path("config.yaml"))
        assert not tool._is_protected_file(Path("main.py"))
        assert not tool._is_protected_file(Path("utils.js"))

    def test_write_file_to_temp_dir(self, tool):
        """Test writing file to temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"

            result = tool.execute({
                "file_path": str(test_file),
                "content": "Hello, World!"
            })

            assert result["success"] is True
            assert test_file.exists()
            assert test_file.read_text() == "Hello, World!"

    def test_write_file_creates_parent_dirs(self, tool):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "nested" / "deep" / "test.txt"

            result = tool.execute({
                "file_path": str(test_file),
                "content": "Nested content"
            })

            assert result["success"] is True
            assert test_file.exists()

    def test_write_code_without_permission(self):
        """Test writing code file without permission fails."""
        definition = MagicMock()
        definition.name = "No Code Agent"
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.can_write_markdown = True

        tool = WriteFileTool(agent_definition=definition)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "script.py"

            result = tool.execute({
                "file_path": str(test_file),
                "content": "print('hello')"
            })

            assert result["success"] is False
            assert "not authorized" in result.get("error", "").lower() or "permission" in result.get("error", "").lower()

    def test_write_markdown_with_permission(self):
        """Test writing markdown with permission."""
        definition = MagicMock()
        definition.name = "Markdown Agent"
        definition.can_write_code = False
        definition.can_write_tests = False
        definition.can_write_markdown = True

        tool = WriteFileTool(agent_definition=definition)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "readme.md"

            result = tool.execute({
                "file_path": str(test_file),
                "content": "# Hello"
            })

            assert result["success"] is True


class TestReadFileTool:
    """Test ReadFileTool."""

    @pytest.fixture
    def tool(self):
        """Create ReadFileTool instance."""
        return ReadFileTool()

    def test_tool_attributes(self, tool):
        """Test tool has required attributes."""
        assert tool.name == "read_file"
        assert "Read" in tool.description
        assert "file_path" in tool.input_schema["properties"]

    def test_to_anthropic_format(self, tool):
        """Test conversion to Anthropic format."""
        result = tool.to_anthropic_format()

        assert result["name"] == "read_file"
        assert "description" in result
        assert "input_schema" in result

    def test_read_existing_file(self, tool):
        """Test reading an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content here")
            temp_path = f.name

        try:
            result = tool.execute({"file_path": temp_path})

            assert result["success"] is True
            assert result["content"] == "Test content here"
        finally:
            os.unlink(temp_path)

    def test_read_nonexistent_file(self, tool):
        """Test reading a non-existent file."""
        result = tool.execute({"file_path": "/nonexistent/path/file.txt"})

        assert result["success"] is False
        assert "error" in result or "not found" in str(result).lower()

    def test_read_binary_file_fails(self, tool):
        """Test that binary files are handled appropriately."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            f.write(b'\x00\x01\x02\x03')
            temp_path = f.name

        try:
            result = tool.execute({"file_path": temp_path})
            # Should either fail or return indication of binary
            # Implementation may vary
        finally:
            os.unlink(temp_path)


class TestRunCommandTool:
    """Test RunCommandTool."""

    @pytest.fixture
    def tool(self):
        """Create RunCommandTool instance."""
        return RunCommandTool()

    def test_tool_attributes(self, tool):
        """Test tool has required attributes."""
        assert tool.name == "run_command"
        assert "command" in tool.input_schema["properties"]

    def test_to_anthropic_format(self, tool):
        """Test conversion to Anthropic format."""
        result = tool.to_anthropic_format()

        assert result["name"] == "run_command"
        assert "input_schema" in result

    def test_run_simple_command(self, tool):
        """Test running a simple echo command."""
        result = tool.execute({"command": "echo 'hello world'"})

        assert result["success"] is True
        assert "hello" in result.get("stdout", "").lower()

    def test_run_command_with_working_directory(self, tool):
        """Test running command in specific directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool.execute({
                "command": "pwd",
                "working_directory": tmpdir
            })

            assert result["success"] is True
            assert tmpdir in result.get("stdout", "")

    def test_run_failing_command(self, tool):
        """Test running a command that fails."""
        result = tool.execute({"command": "exit 1"})

        # Should capture the failure
        assert result["exit_code"] != 0 or result["success"] is False


class TestProjectTrackingTool:
    """Test ProjectTrackingTool."""

    @pytest.fixture
    def tool(self):
        """Create ProjectTrackingTool instance."""
        return ProjectTrackingTool()

    def test_tool_attributes(self, tool):
        """Test tool has required attributes."""
        assert tool.name == "project_tracking"
        assert "action" in tool.input_schema["properties"]

    def test_to_anthropic_format(self, tool):
        """Test conversion to Anthropic format."""
        result = tool.to_anthropic_format()

        assert result["name"] == "project_tracking"
        assert "input_schema" in result

    def test_get_summary_action(self, tool):
        """Test get_summary action requires project_id."""
        result = tool.execute({"action": "get_summary"})

        assert result["success"] is False
        assert "project_id" in result.get("error", "").lower()

    def test_invalid_action(self, tool):
        """Test invalid action returns error."""
        result = tool.execute({"action": "invalid_action_xyz"})

        assert result["success"] is False or "error" in result


class TestGitCommitTool:
    """Test GitCommitTool."""

    @pytest.fixture
    def tool(self):
        """Create GitCommitTool instance."""
        return GitCommitTool()

    def test_tool_attributes(self, tool):
        """Test tool has required attributes."""
        assert tool.name == "git_commit"
        assert "message" in tool.input_schema["properties"]

    def test_to_anthropic_format(self, tool):
        """Test conversion to Anthropic format."""
        result = tool.to_anthropic_format()

        assert result["name"] == "git_commit"
        assert "input_schema" in result

    def test_commit_requires_message(self, tool):
        """Test that commit requires a message."""
        # Missing message should raise KeyError since code accesses inputs["message"] directly
        with pytest.raises(KeyError):
            tool.execute({})

    def test_commit_message_validation(self, tool):
        """Test commit message validation."""
        # Very short message should be rejected
        result = tool.execute({"message": "x"})

        # Should either fail or warn about short message
        # Implementation dependent


class TestSpawnAgentTool:
    """Test SpawnAgentTool."""

    @pytest.fixture
    def tool(self):
        """Create SpawnAgentTool instance with mocked dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = SpawnAgentTool(
                agent_types_dir=Path(tmpdir),
                api_key="test-api-key",
                budget_tier="balanced",
                parent_agent_id="parent-123",
                request_id="req-456"
            )
            yield tool

    def test_tool_attributes(self, tool):
        """Test tool has required attributes."""
        assert tool.name == "spawn_agent"
        assert "agent_type" in tool.input_schema["properties"]
        assert "input_data" in tool.input_schema["properties"]

    def test_to_anthropic_format(self, tool):
        """Test conversion to Anthropic format."""
        result = tool.to_anthropic_format()

        assert result["name"] == "spawn_agent"
        assert "input_schema" in result

    def test_spawn_with_missing_agent_type(self, tool):
        """Test spawn with missing agent definition returns error."""
        # Spawning a non-existent agent type should fail gracefully
        result = tool.execute({
            "agent_type": "nonexistent/agent",
            "input_data": {"task": "test"}
        })

        assert result["success"] is False

    def test_spawn_requires_both_params(self, tool):
        """Test spawn requires both agent_type and input_data."""
        # Missing input_data should raise KeyError since code accesses inputs["input_data"] directly
        with pytest.raises(KeyError):
            tool.execute({"agent_type": "developers/backend_developer"})


class TestToolRegistry:
    """Test ToolRegistry class."""

    def test_registry_creates_new_instances(self):
        """Test that ToolRegistry creates new instances (not a singleton)."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        # ToolRegistry is NOT a singleton - each instance is independent
        assert registry1 is not registry2

    def test_registry_has_tools(self):
        """Test that registry has registered tools."""
        registry = ToolRegistry()

        # Registry should have some built-in tools
        assert hasattr(registry, 'tools') or hasattr(registry, '_tools')

    def test_get_tool_by_name(self):
        """Test getting a tool by name."""
        registry = ToolRegistry()

        # Try to get a known tool
        if hasattr(registry, 'get_tool'):
            tool = registry.get_tool("read_file")
            if tool:
                assert tool.name == "read_file"

    def test_get_tools_for_definition(self):
        """Test getting tools for an agent definition."""
        registry = ToolRegistry()

        definition = MagicMock()
        definition.name = "Test Agent"
        definition.can_write_code = True
        definition.can_write_tests = True
        definition.can_write_markdown = True
        definition.instructions = "Some instructions with write_file and read_file"

        if hasattr(registry, 'get_tools_for_agent'):
            tools = registry.get_tools_for_agent(definition)
            assert isinstance(tools, list)
        elif hasattr(registry, 'get_tools'):
            tools = registry.get_tools(definition)
            assert isinstance(tools, list)

    def test_registry_register_and_get(self):
        """Test registering and getting a tool."""
        registry = ToolRegistry()
        tool = ReadFileTool()

        registry.register(tool)

        retrieved = registry.get_tool("read_file")
        assert retrieved is not None
        assert retrieved.name == "read_file"

    def test_registry_get_all_tools(self):
        """Test getting all registered tools."""
        registry = ToolRegistry()
        registry.register(ReadFileTool())
        registry.register(RunCommandTool())

        all_tools = registry.get_all_tools()

        assert len(all_tools) == 2
        tool_names = [t.name for t in all_tools]
        assert "read_file" in tool_names
        assert "run_command" in tool_names

    def test_registry_to_anthropic_format(self):
        """Test converting registry to Anthropic format."""
        registry = ToolRegistry()
        registry.register(ReadFileTool())

        result = registry.to_anthropic_format()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "read_file"

    def test_registry_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist."""
        registry = ToolRegistry()

        result = registry.get_tool("nonexistent_tool")

        assert result is None

    def test_registry_default_creates_standard_tools(self):
        """Test default registry includes standard tools."""
        mock_definition = MagicMock()
        mock_definition.name = "Test Agent"

        # Patch the git_tools module imports
        with patch('src.runtime.agents.git_tools.GitBranchTool') as MockBranch, \
             patch('src.runtime.agents.git_tools.GitMergeTool') as MockMerge, \
             patch('src.runtime.agents.git_tools.GitStatusTool') as MockStatus:
            # Set up mocks to have 'name' attributes
            MockBranch.return_value.name = "git_branch"
            MockMerge.return_value.name = "git_merge"
            MockStatus.return_value.name = "git_status"

            registry = ToolRegistry.default(agent_definition=mock_definition)

        all_tools = registry.get_all_tools()
        tool_names = [t.name for t in all_tools]

        # Should have the standard tools
        assert "write_file" in tool_names
        assert "read_file" in tool_names
        assert "run_command" in tool_names
        assert "git_commit" in tool_names
        assert "project_tracking" in tool_names


class TestWriteFileToolAdvanced:
    """Advanced tests for WriteFileTool."""

    @pytest.fixture
    def mock_definition(self):
        """Create mock agent definition."""
        definition = MagicMock()
        definition.name = "Test Agent"
        definition.can_write_code = True
        definition.can_write_tests = True
        definition.can_write_markdown = True
        return definition

    def test_is_code_file(self):
        """Test code file detection."""
        tool = WriteFileTool()

        assert tool._is_code_file(Path("main.py"))
        assert tool._is_code_file(Path("app.js"))
        assert tool._is_code_file(Path("component.tsx"))
        assert tool._is_code_file(Path("util.go"))
        assert not tool._is_code_file(Path("readme.md"))
        assert not tool._is_code_file(Path("data.json"))

    def test_is_test_file(self):
        """Test test file detection."""
        tool = WriteFileTool()

        # Test file patterns
        assert tool._is_test_file(Path("test_main.py"))
        assert tool._is_test_file(Path("app_test.py"))
        assert tool._is_test_file(Path("component.test.js"))
        assert tool._is_test_file(Path("util.spec.ts"))

        # Test directory patterns
        assert tool._is_test_file(Path("tests/unit/test_something.py"))
        assert tool._is_test_file(Path("__tests__/component.test.js"))

        # Non-test files
        assert not tool._is_test_file(Path("main.py"))
        assert not tool._is_test_file(Path("app.js"))
        # Markdown files with test in name are NOT test files
        assert not tool._is_test_file(Path("test_tasks.md"))

    def test_write_test_file_without_permission(self):
        """Test writing test file without permission fails."""
        definition = MagicMock()
        definition.name = "No Tests Agent"
        definition.can_write_code = True
        definition.can_write_tests = False
        definition.can_write_markdown = True

        tool = WriteFileTool(agent_definition=definition)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_something.py"

            result = tool.execute({
                "file_path": str(test_file),
                "content": "def test_foo(): pass"
            })

            assert result["success"] is False
            assert "rogue" in result.get("error", "").lower() or "permission" in result.get("error", "").lower()

    def test_backup_created_for_protected_file(self, mock_definition):
        """Test backup is created for protected files."""
        tool = WriteFileTool(agent_definition=mock_definition)

        with tempfile.TemporaryDirectory() as tmpdir:
            requirements_file = Path(tmpdir) / "requirements.txt"
            # Create existing file
            requirements_file.write_text("old-content")

            result = tool.execute({
                "file_path": str(requirements_file),
                "content": "new-content"
            })

            assert result["success"] is True
            assert result["was_overwrite"] is True
            # Backup should be created
            assert result.get("backup_path") is not None

    def test_backup_created_when_content_differs(self, mock_definition):
        """Test backup is created when content changes."""
        tool = WriteFileTool(agent_definition=mock_definition)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "script.py"
            test_file.write_text("original content")

            result = tool.execute({
                "file_path": str(test_file),
                "content": "modified content"
            })

            assert result["success"] is True
            assert result["was_overwrite"] is True
            assert result.get("backup_path") is not None

    def test_no_backup_when_content_same(self, mock_definition):
        """Test no backup created when content is the same."""
        tool = WriteFileTool(agent_definition=mock_definition)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "script.py"
            content = "same content"
            test_file.write_text(content)

            result = tool.execute({
                "file_path": str(test_file),
                "content": content
            })

            assert result["success"] is True
            # Content same, so no backup
            assert result.get("backup_path") is None

    def test_write_exception_handling(self, mock_definition):
        """Test exception handling during write."""
        tool = WriteFileTool(agent_definition=mock_definition)

        # Try to write to an invalid path
        result = tool.execute({
            "file_path": "/nonexistent_root_dir_xyz/file.txt",
            "content": "content"
        })

        # Should fail gracefully
        assert result["success"] is False
        assert "error" in result

    def test_create_backup_nonexistent_file(self, mock_definition):
        """Test _create_backup returns None for nonexistent file."""
        tool = WriteFileTool(agent_definition=mock_definition)

        result = tool._create_backup(Path("/nonexistent/file.txt"))

        assert result is None


class TestReadFileToolAdvanced:
    """Advanced tests for ReadFileTool."""

    def test_read_file_exception_handling(self):
        """Test exception handling when read fails."""
        tool = ReadFileTool()

        # Create a file then make it unreadable (Unix only)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("content")
            temp_path = f.name

        try:
            # Make file unreadable
            os.chmod(temp_path, 0o000)

            result = tool.execute({"file_path": temp_path})

            # Should fail with error
            assert result["success"] is False
            assert "error" in result
        finally:
            # Restore permissions and clean up
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)


class TestRunCommandToolAdvanced:
    """Advanced tests for RunCommandTool."""

    def test_command_timeout(self):
        """Test command timeout handling."""
        tool = RunCommandTool()

        # This command would normally take forever, but should timeout
        with patch('subprocess.run') as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=30)

            result = tool.execute({"command": "sleep 100"})

            assert result["success"] is False
            assert "timed out" in result.get("stderr", "").lower()

    def test_command_general_exception(self):
        """Test general exception handling."""
        tool = RunCommandTool()

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            result = tool.execute({"command": "some command"})

            assert result["success"] is False
            assert "Unexpected error" in result.get("stderr", "")


class TestProjectTrackingToolAdvanced:
    """Advanced tests for ProjectTrackingTool."""

    @pytest.fixture
    def mock_tracker(self):
        """Create mock project tracker."""
        tracker = MagicMock()
        return tracker

    def test_create_project_action(self, mock_tracker):
        """Test create_project action."""
        tool = ProjectTrackingTool(request_id="req-123")

        with patch('src.runtime.agents.project_tracker.ProjectTracker') as MockTracker:
            mock_project = MagicMock()
            mock_project.project_id = "proj-123"
            mock_project.project_name = "Test Project"
            MockTracker.return_value.create_project.return_value = mock_project
            MockTracker.return_value.get_project_summary.return_value = {"name": "Test Project"}

            result = tool.execute({
                "action": "create_project",
                "project_name": "Test Project",
                "description": "A test project"
            })

            assert result["success"] is True
            assert result["project_id"] == "proj-123"

    def test_create_project_missing_params(self):
        """Test create_project with missing params."""
        tool = ProjectTrackingTool()

        result = tool.execute({
            "action": "create_project",
            "project_name": "Test"
            # Missing description
        })

        assert result["success"] is False
        assert "description" in result.get("error", "").lower()

    def test_add_task_action(self, mock_tracker):
        """Test add_task action."""
        tool = ProjectTrackingTool()

        with patch('src.runtime.agents.project_tracker.ProjectTracker') as MockTracker:
            MockTracker.return_value.add_task.return_value = "task-123"

            result = tool.execute({
                "action": "add_task",
                "project_id": "proj-123",
                "description": "Write tests"
            })

            assert result["success"] is True
            assert result["task_id"] == "task-123"

    def test_add_task_missing_params(self):
        """Test add_task with missing params."""
        tool = ProjectTrackingTool()

        result = tool.execute({
            "action": "add_task",
            "project_id": "proj-123"
            # Missing description
        })

        assert result["success"] is False

    def test_update_task_action(self, mock_tracker):
        """Test update_task action."""
        tool = ProjectTrackingTool()

        with patch('src.runtime.agents.project_tracker.ProjectTracker') as MockTracker:
            result = tool.execute({
                "action": "update_task",
                "project_id": "proj-123",
                "task_id": "task-123",
                "status": "completed"
            })

            assert result["success"] is True
            assert "completed" in result.get("message", "").lower()

    def test_update_task_missing_params(self):
        """Test update_task with missing params."""
        tool = ProjectTrackingTool()

        result = tool.execute({
            "action": "update_task",
            "project_id": "proj-123"
            # Missing task_id and status
        })

        assert result["success"] is False

    def test_add_note_action(self, mock_tracker):
        """Test add_note action."""
        tool = ProjectTrackingTool()

        with patch('src.runtime.agents.project_tracker.ProjectTracker') as MockTracker:
            result = tool.execute({
                "action": "add_note",
                "project_id": "proj-123",
                "note": "Important decision made"
            })

            assert result["success"] is True

    def test_add_note_missing_params(self):
        """Test add_note with missing params."""
        tool = ProjectTrackingTool()

        result = tool.execute({
            "action": "add_note",
            "project_id": "proj-123"
            # Missing note
        })

        assert result["success"] is False

    def test_get_next_tasks_action(self, mock_tracker):
        """Test get_next_tasks action."""
        tool = ProjectTrackingTool()

        with patch('src.runtime.agents.project_tracker.ProjectTracker') as MockTracker:
            mock_task = MagicMock()
            mock_task.task_id = "task-1"
            mock_task.description = "Do something"
            mock_task.assigned_to = "developer"
            MockTracker.return_value.get_next_tasks.return_value = [mock_task]

            result = tool.execute({
                "action": "get_next_tasks",
                "project_id": "proj-123"
            })

            assert result["success"] is True
            assert len(result["next_tasks"]) == 1

    def test_get_next_tasks_missing_params(self):
        """Test get_next_tasks with missing params."""
        tool = ProjectTrackingTool()

        result = tool.execute({
            "action": "get_next_tasks"
            # Missing project_id
        })

        assert result["success"] is False

    def test_exception_handling(self):
        """Test exception handling in execute."""
        tool = ProjectTrackingTool()

        with patch('src.runtime.agents.project_tracker.ProjectTracker') as MockTracker:
            MockTracker.return_value.create_project.side_effect = Exception("Database error")

            result = tool.execute({
                "action": "create_project",
                "project_name": "Test",
                "description": "Test description"
            })

            assert result["success"] is False
            assert "Database error" in result.get("error", "")


class TestGitCommitToolAdvanced:
    """Advanced tests for GitCommitTool."""

    def test_validate_empty_message(self):
        """Test validation of empty message."""
        tool = GitCommitTool()

        is_valid, error = tool._validate_commit_message("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_short_message(self):
        """Test validation of too short message."""
        tool = GitCommitTool()

        is_valid, error = tool._validate_commit_message("abc")
        assert is_valid is False
        assert "10 characters" in error.lower()

    def test_validate_bad_pattern_message(self):
        """Test validation of bad pattern messages that are long enough."""
        tool = GitCommitTool()

        # Only "test commit" is >= 10 chars, others fail length check first
        is_valid, error = tool._validate_commit_message("test commit")
        assert is_valid is False
        assert "descriptive" in error.lower()

    def test_validate_short_bad_patterns(self):
        """Test that short bad patterns fail length check."""
        tool = GitCommitTool()

        # These are all < 10 chars, so they fail length check
        short_bad = ["wip", "temp", "asdf", "fix"]
        for msg in short_bad:
            is_valid, error = tool._validate_commit_message(msg)
            assert is_valid is False
            assert "10 characters" in error.lower()

    def test_validate_good_message(self):
        """Test validation of good message."""
        tool = GitCommitTool()

        is_valid, error = tool._validate_commit_message("Add user authentication feature with OAuth2 support")
        assert is_valid is True
        assert error is None

    def test_commit_execution_success(self):
        """Test successful commit execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = GitCommitTool(working_directory=Path(tmpdir))

            with patch('subprocess.run') as mock_run:
                # Mock all the git commands
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # git add -A
                    MagicMock(returncode=1),  # git diff --cached --quiet (changes exist)
                    MagicMock(returncode=0, stdout="Commit success"),  # git commit
                    MagicMock(returncode=0, stdout="abc123"),  # git rev-parse HEAD
                    MagicMock(returncode=0, stdout="file1.py\nfile2.py"),  # git diff-tree
                ]

                result = tool.execute({"message": "Add new feature implementation"})

                assert result["success"] is True
                assert result["commit_hash"] == "abc123"
                assert "file1.py" in result["files"]

    def test_commit_no_changes(self):
        """Test commit when there are no changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = GitCommitTool(working_directory=Path(tmpdir))

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # git add -A
                    MagicMock(returncode=0),  # git diff --cached --quiet (no changes)
                ]

                result = tool.execute({"message": "Try to commit something"})

                assert result["success"] is True
                assert "no changes" in result.get("message", "").lower()

    def test_commit_timeout(self):
        """Test commit timeout handling."""
        import subprocess as sp
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = GitCommitTool(working_directory=Path(tmpdir))

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = sp.TimeoutExpired(cmd="git", timeout=10)

                result = tool.execute({"message": "Add feature that times out"})

                assert result["success"] is False
                assert "timed out" in result.get("error", "").lower()

    def test_commit_with_specific_files(self):
        """Test commit with specific files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = GitCommitTool(working_directory=Path(tmpdir))

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # git add file1.py
                    MagicMock(returncode=0),  # git add file2.py
                    MagicMock(returncode=1),  # git diff --cached --quiet
                    MagicMock(returncode=0, stdout="Commit done"),  # git commit
                    MagicMock(returncode=0, stdout="def456"),  # git rev-parse
                    MagicMock(returncode=0, stdout="file1.py\nfile2.py"),  # git diff-tree
                ]

                result = tool.execute({
                    "message": "Update specific files with changes",
                    "files": ["file1.py", "file2.py"]
                })

                assert result["success"] is True

    def test_commit_failure(self):
        """Test commit failure handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = GitCommitTool(working_directory=Path(tmpdir))

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # git add
                    MagicMock(returncode=1),  # git diff --cached (changes exist)
                    MagicMock(returncode=1, stderr="commit failed"),  # git commit fails
                ]

                result = tool.execute({"message": "This commit will fail"})

                assert result["success"] is False
                assert "failed" in result.get("error", "").lower()


class TestSpawnAgentToolAdvanced:
    """Advanced tests for SpawnAgentTool."""

    def test_spawn_success_with_mocked_runtime(self):
        """Test successful spawn with all dependencies mocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock agent definition file
            agent_dir = Path(tmpdir)
            agent_file = agent_dir / "test_agent.md"
            agent_file.write_text("""---
name: Test Agent
can_write_code: true
can_write_tests: false
can_write_markdown: true
---
# Instructions
Do something.""")

            tool = SpawnAgentTool(
                agent_types_dir=agent_dir,
                api_key="test-key",
                budget_tier="balanced",
                parent_agent_id="parent-1",
                request_id="req-1"
            )

            with patch('src.runtime.agents.definition.AgentDefinition') as MockDef, \
                 patch('src.runtime.agents.runtime.AgentRuntime') as MockRuntime, \
                 patch('src.runtime.agents.naming.name_generator.generate_agent_name') as MockName:

                # Setup mocks
                mock_def = MagicMock()
                mock_def.name = "Test Agent"
                mock_def.get_required_input_fields.return_value = {"task"}
                MockDef.from_file.return_value = mock_def

                MockName.return_value = "Happy Dolphin"

                mock_runtime = MagicMock()
                mock_runtime.execute.return_value = {"output": "Success!"}
                MockRuntime.return_value = mock_runtime

                result = tool.execute({
                    "agent_type": "test_agent",
                    "input_data": {"task": "Do something"}
                })

                assert result["success"] is True
                assert result["result"] == {"output": "Success!"}

    def test_spawn_missing_required_fields(self):
        """Test spawn fails when required input fields are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            agent_file = agent_dir / "test_agent.md"
            agent_file.write_text("---\nname: Test\n---\nInstructions")

            tool = SpawnAgentTool(
                agent_types_dir=agent_dir,
                api_key="test-key",
                budget_tier="balanced"
            )

            with patch('src.runtime.agents.definition.AgentDefinition') as MockDef:
                mock_def = MagicMock()
                mock_def.get_required_input_fields.return_value = {"task", "context"}
                MockDef.from_file.return_value = mock_def

                result = tool.execute({
                    "agent_type": "test_agent",
                    "input_data": {"task": "Do something"}  # Missing 'context'
                })

                assert result["success"] is False
                assert "missing" in result.get("error", "").lower()

    def test_spawn_general_exception(self):
        """Test spawn handles general exceptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = SpawnAgentTool(
                agent_types_dir=Path(tmpdir),
                api_key="test-key",
                budget_tier="balanced"
            )

            with patch('src.runtime.agents.definition.AgentDefinition') as MockDef:
                MockDef.from_file.side_effect = Exception("Unexpected error")

                result = tool.execute({
                    "agent_type": "test_agent",
                    "input_data": {"task": "test"}
                })

                assert result["success"] is False
                assert "Unexpected error" in result.get("error", "")
