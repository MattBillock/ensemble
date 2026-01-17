"""
Unit tests for git_tools module.

Tests the git branch and merge tools for coordinated development.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess


class TestBranchInfo:
    """Test BranchInfo dataclass."""

    def test_branch_info_creation(self):
        """Test creating a BranchInfo instance."""
        from src.runtime.agents.git_tools import BranchInfo

        info = BranchInfo(
            name="feature-branch",
            is_current=True,
            last_commit="abc123",
            last_commit_message="Fix bug",
            ahead=2,
            behind=1
        )

        assert info.name == "feature-branch"
        assert info.is_current is True
        assert info.last_commit == "abc123"
        assert info.ahead == 2
        assert info.behind == 1


class TestGitBranchTool:
    """Test GitBranchTool class."""

    @pytest.fixture
    def branch_tool(self):
        """Create a GitBranchTool instance."""
        from src.runtime.agents.git_tools import GitBranchTool
        return GitBranchTool(
            working_directory=Path("/test"),
            agent_id="test-agent",
            session_id="test-session"
        )

    def test_tool_attributes(self, branch_tool):
        """Test tool name and description."""
        assert branch_tool.name == "git_branch"
        assert branch_tool.description is not None

    def test_input_schema(self, branch_tool):
        """Test input schema structure."""
        schema = branch_tool.input_schema
        assert schema["type"] == "object"
        assert "action" in schema["properties"]
        assert "branch_name" in schema["properties"]

    def test_to_anthropic_format(self, branch_tool):
        """Test conversion to Anthropic API format."""
        format = branch_tool.to_anthropic_format()

        assert format["name"] == "git_branch"
        assert "description" in format
        assert "input_schema" in format

    def test_run_git_success(self, branch_tool):
        """Test successful git command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            success, stdout, stderr = branch_tool._run_git(["status"])

            assert success is True
            assert stdout == "output"
            assert stderr == ""

    def test_run_git_failure(self, branch_tool):
        """Test failed git command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"

        with patch('subprocess.run', return_value=mock_result):
            success, stdout, stderr = branch_tool._run_git(["status"])

            assert success is False
            assert stderr == "error message"

    def test_run_git_timeout(self, branch_tool):
        """Test git command timeout handling."""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("git", 30)):
            success, stdout, stderr = branch_tool._run_git(["status"])

            assert success is False
            assert "timed out" in stderr.lower()

    def test_create_branch_success(self, branch_tool):
        """Test successful branch creation."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            with patch.object(branch_tool, '_emit_branch_event'):
                result = branch_tool.execute({
                    "action": "create",
                    "branch_name": "feature-new"
                })

                assert result["success"] is True
                assert result["branch"] == "feature-new"

    def test_create_branch_no_name(self, branch_tool):
        """Test branch creation without name fails."""
        result = branch_tool.execute({
            "action": "create"
        })

        assert result["success"] is False
        assert "branch_name required" in result["error"]

    def test_create_branch_invalid_name(self, branch_tool):
        """Test branch creation with invalid name fails."""
        result = branch_tool.execute({
            "action": "create",
            "branch_name": "branch with spaces"
        })

        assert result["success"] is False
        assert "Invalid branch name" in result["error"]

    def test_switch_branch_success(self, branch_tool):
        """Test successful branch switch."""
        # First call for status (clean), second for checkout
        mock_results = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="Switched", stderr="")
        ]

        with patch('subprocess.run', side_effect=mock_results):
            result = branch_tool.execute({
                "action": "switch",
                "branch_name": "main"
            })

            assert result["success"] is True

    def test_switch_branch_uncommitted_changes(self, branch_tool):
        """Test branch switch fails with uncommitted changes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "M file.py\n"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = branch_tool.execute({
                "action": "switch",
                "branch_name": "main"
            })

            assert result["success"] is False
            assert "uncommitted changes" in result["error"].lower()

    def test_list_branches(self, branch_tool):
        """Test listing branches."""
        mock_results = [
            MagicMock(returncode=0, stdout="main|*|abc123|Initial commit\nfeature| |def456|Add feature", stderr=""),
            MagicMock(returncode=0, stdout="main", stderr="")
        ]

        with patch('subprocess.run', side_effect=mock_results):
            result = branch_tool.execute({"action": "list"})

            assert result["success"] is True
            assert "branches" in result
            assert result["count"] == 2

    def test_delete_branch_success(self, branch_tool):
        """Test successful branch deletion."""
        mock_results = [
            MagicMock(returncode=0, stdout="main", stderr=""),  # Get current branch
            MagicMock(returncode=0, stdout="Deleted", stderr="")  # Delete branch
        ]

        with patch('subprocess.run', side_effect=mock_results):
            with patch.object(branch_tool, '_emit_branch_event'):
                result = branch_tool.execute({
                    "action": "delete",
                    "branch_name": "old-feature"
                })

                assert result["success"] is True

    def test_delete_branch_protected(self, branch_tool):
        """Test deleting protected branch fails."""
        result = branch_tool.execute({
            "action": "delete",
            "branch_name": "main"
        })

        assert result["success"] is False
        assert "protected" in result["error"].lower()

    def test_delete_current_branch_fails(self, branch_tool):
        """Test deleting current branch fails."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "feature-branch"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = branch_tool.execute({
                "action": "delete",
                "branch_name": "feature-branch"
            })

            assert result["success"] is False
            assert "current branch" in result["error"].lower()

    def test_get_current_branch(self, branch_tool):
        """Test getting current branch."""
        mock_results = [
            MagicMock(returncode=0, stdout="feature-branch", stderr=""),
            MagicMock(returncode=0, stdout="## feature-branch...origin/feature-branch [ahead 2]", stderr="")
        ]

        with patch('subprocess.run', side_effect=mock_results):
            result = branch_tool.execute({"action": "current"})

            assert result["success"] is True
            assert result["branch"] == "feature-branch"
            assert result["ahead"] == 2

    def test_is_valid_branch_name(self, branch_tool):
        """Test branch name validation."""
        valid_names = ["feature-branch", "fix/bug-123", "release-1.0"]
        invalid_names = ["", "-starts-with-dash", "has spaces", "has..dots", "has//slashes"]

        for name in valid_names:
            assert branch_tool._is_valid_branch_name(name) is True, f"{name} should be valid"

        for name in invalid_names:
            assert branch_tool._is_valid_branch_name(name) is False, f"{name} should be invalid"

    def test_unknown_action(self, branch_tool):
        """Test unknown action returns error."""
        result = branch_tool.execute({"action": "unknown"})

        assert result["success"] is False
        assert "Unknown action" in result["error"]


class TestGitMergeTool:
    """Test GitMergeTool class."""

    @pytest.fixture
    def merge_tool(self):
        """Create a GitMergeTool instance."""
        from src.runtime.agents.git_tools import GitMergeTool
        return GitMergeTool(
            working_directory=Path("/test"),
            agent_id="test-agent",
            session_id="test-session"
        )

    def test_tool_attributes(self, merge_tool):
        """Test tool name and description."""
        assert merge_tool.name == "git_merge"
        assert merge_tool.description is not None

    def test_preview_merge(self, merge_tool):
        """Test merge preview."""
        mock_results = [
            MagicMock(returncode=0, stdout="main", stderr=""),
            MagicMock(returncode=0, stdout="file1.py | 10 +++++\n", stderr=""),
            MagicMock(returncode=0, stdout="abc123 Fix bug\ndef456 Add feature", stderr=""),
            MagicMock(returncode=0, stdout="merge-base-hash", stderr=""),
            MagicMock(returncode=0, stdout="", stderr="")
        ]

        with patch('subprocess.run', side_effect=mock_results):
            result = merge_tool.execute({
                "action": "preview",
                "source_branch": "feature-branch"
            })

            assert result["success"] is True
            assert "diff_stat" in result
            assert "commits" in result

    def test_merge_success(self, merge_tool):
        """Test successful merge."""
        mock_results = [
            MagicMock(returncode=0, stdout="main", stderr=""),  # Get current branch
            MagicMock(returncode=0, stdout="Merge made", stderr=""),  # Merge
            MagicMock(returncode=0, stdout="abc123def", stderr="")  # Get commit hash
        ]

        with patch('subprocess.run', side_effect=mock_results):
            with patch.object(merge_tool, '_emit_merge_event'):
                result = merge_tool.execute({
                    "action": "merge",
                    "source_branch": "feature-branch"
                })

                assert result["success"] is True
                assert result["source_branch"] == "feature-branch"

    def test_merge_no_source(self, merge_tool):
        """Test merge without source branch fails."""
        result = merge_tool.execute({"action": "merge"})

        assert result["success"] is False
        assert "source_branch required" in result["error"]

    def test_merge_conflict(self, merge_tool):
        """Test merge with conflict."""
        mock_results = [
            MagicMock(returncode=0, stdout="main", stderr=""),
            MagicMock(returncode=1, stdout="CONFLICT in file.py", stderr=""),
            MagicMock(returncode=0, stdout="UU file.py", stderr="")
        ]

        with patch('subprocess.run', side_effect=mock_results):
            result = merge_tool.execute({
                "action": "merge",
                "source_branch": "feature-branch"
            })

            assert result["success"] is False
            assert "conflict" in result["error"].lower()
            assert "conflict_files" in result

    def test_abort_merge(self, merge_tool):
        """Test aborting a merge."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = merge_tool.execute({"action": "abort"})

            assert result["success"] is True

    def test_squash_merge(self, merge_tool):
        """Test squash merge strategy."""
        mock_results = [
            MagicMock(returncode=0, stdout="main", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),  # Squash
            MagicMock(returncode=0, stdout="", stderr=""),  # Commit
            MagicMock(returncode=0, stdout="abc123", stderr="")
        ]

        with patch('subprocess.run', side_effect=mock_results):
            with patch.object(merge_tool, '_emit_merge_event'):
                result = merge_tool.execute({
                    "action": "merge",
                    "source_branch": "feature",
                    "strategy": "squash"
                })

                assert result["success"] is True
                assert result["strategy"] == "squash"

    def test_to_anthropic_format(self, merge_tool):
        """Test conversion to Anthropic API format."""
        format = merge_tool.to_anthropic_format()

        assert format["name"] == "git_merge"
        assert "description" in format
        assert "input_schema" in format


class TestGitStatusTool:
    """Test GitStatusTool class."""

    @pytest.fixture
    def status_tool(self):
        """Create a GitStatusTool instance."""
        from src.runtime.agents.git_tools import GitStatusTool
        return GitStatusTool(working_directory=Path("/test"))

    def test_tool_attributes(self, status_tool):
        """Test tool name and description."""
        assert status_tool.name == "git_status"
        assert status_tool.description is not None

    def test_execute_basic(self, status_tool):
        """Test basic status execution."""
        mock_results = [
            MagicMock(returncode=0, stdout="main", stderr=""),  # Current branch
            MagicMock(returncode=0, stdout="?? new.py\nA  staged.py", stderr=""),  # Status (untracked and staged)
            MagicMock(returncode=0, stdout="## main", stderr=""),  # Tracking
            MagicMock(returncode=0, stdout="abc123|Fix bug|Author|2 hours ago", stderr=""),  # Last commit
            MagicMock(returncode=0, stdout="", stderr="")  # Stash
        ]

        with patch('subprocess.run', side_effect=mock_results):
            result = status_tool.execute({})

            assert result["success"] is True
            assert result["current_branch"] == "main"
            assert "changes" in result
            assert len(result["changes"]["untracked"]) > 0
            assert len(result["changes"]["staged"]) > 0

    def test_execute_with_history(self, status_tool):
        """Test status with history included."""
        mock_results = [
            MagicMock(returncode=0, stdout="main", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="## main", stderr=""),
            MagicMock(returncode=0, stdout="abc123|Commit 1|Author|1 hour ago", stderr=""),
            MagicMock(returncode=0, stdout="abc123|Commit 1|Author|1 hour ago\ndef456|Commit 2|Author|2 hours ago", stderr=""),
            MagicMock(returncode=0, stdout="", stderr="")
        ]

        with patch('subprocess.run', side_effect=mock_results):
            result = status_tool.execute({
                "include_history": True,
                "history_count": 5
            })

            assert result["success"] is True
            assert "history" in result
            assert len(result["history"]) == 2

    def test_to_anthropic_format(self, status_tool):
        """Test conversion to Anthropic API format."""
        format = status_tool.to_anthropic_format()

        assert format["name"] == "git_status"
        assert "description" in format
        assert "input_schema" in format
