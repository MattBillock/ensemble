"""
Unit tests for commit_enforcer.py

Tests the commit enforcement bot that monitors uncommitted changes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add scripts/monitoring to path
scripts_path = Path(__file__).parent.parent.parent / "scripts" / "monitoring"
sys.path.insert(0, str(scripts_path))

import commit_enforcer


class TestGitCommands:
    """Test git command execution wrapper."""

    def test_run_git_command_success(self):
        """Test successful git command execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="main\n",
                stderr=""
            )

            code, stdout, stderr = commit_enforcer.run_git_command(['branch'])

            assert code == 0
            assert stdout == "main\n"
            assert stderr == ""
            mock_run.assert_called_once()

    def test_run_git_command_failure(self):
        """Test failed git command execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=128,
                stdout="",
                stderr="fatal: not a git repository"
            )

            code, stdout, stderr = commit_enforcer.run_git_command(['status'])

            assert code == 128
            assert stderr == "fatal: not a git repository"

    def test_run_git_command_timeout(self):
        """Test git command timeout handling."""
        with patch('subprocess.run', side_effect=Exception("timeout")):
            code, stdout, stderr = commit_enforcer.run_git_command(['status'])

            assert code == 1
            assert "timeout" in stderr


class TestGetUncommittedChanges:
    """Test detection of uncommitted changes."""

    def test_get_uncommitted_changes_empty(self):
        """Test when no uncommitted changes exist."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            # Mock git status --porcelain (empty)
            mock_git.return_value = (0, "", "")

            changes = commit_enforcer.get_uncommitted_changes()

            assert changes['has_changes'] is False
            assert changes['total_files'] == 0
            assert len(changes['modified']) == 0
            assert len(changes['untracked']) == 0

    def test_get_uncommitted_changes_with_modified_files(self):
        """Test detection of modified files."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            # Mock git status --porcelain
            mock_git.side_effect = [
                (0, " M file1.py\n M file2.py\n", ""),  # status
                (0, "2 files changed, 10 insertions(+), 5 deletions(-)", "")  # diff --stat
            ]

            changes = commit_enforcer.get_uncommitted_changes()

            assert changes['has_changes'] is True
            assert changes['total_files'] == 2
            assert 'file1.py' in changes['modified']
            assert 'file2.py' in changes['modified']
            assert changes['lines_changed'] == 15  # 10 insertions + 5 deletions

    def test_get_uncommitted_changes_with_untracked_files(self):
        """Test detection of untracked files."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.side_effect = [
                (0, "?? new_file.py\n", ""),  # status
                (0, "", "")  # diff --stat
            ]

            changes = commit_enforcer.get_uncommitted_changes()

            assert changes['has_changes'] is True
            assert changes['total_files'] == 1
            assert 'new_file.py' in changes['untracked']

    def test_get_uncommitted_changes_with_all_types(self):
        """Test detection of all change types."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.side_effect = [
                (0, " M modified.py\nA  added.py\n D deleted.py\n?? untracked.py\n", ""),  # status
                (0, "4 files changed, 50 insertions(+), 20 deletions(-)", "")  # diff --stat
            ]

            changes = commit_enforcer.get_uncommitted_changes()

            assert changes['has_changes'] is True
            assert changes['total_files'] == 4
            assert 'modified.py' in changes['modified']
            assert 'added.py' in changes['added']
            assert 'deleted.py' in changes['deleted']
            assert 'untracked.py' in changes['untracked']
            assert changes['lines_changed'] == 70

    def test_get_uncommitted_changes_git_error(self):
        """Test handling of git command errors."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (128, "", "fatal: not a git repository")

            changes = commit_enforcer.get_uncommitted_changes()

            assert 'error' in changes
            assert changes['has_changes'] is False


class TestGetTimeSinceLastCommit:
    """Test calculation of time since last commit."""

    def test_get_time_since_last_commit_recent(self):
        """Test recent commit (5 minutes ago)."""
        import time

        current_time = int(time.time())
        five_mins_ago = current_time - 300

        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (0, str(five_mins_ago), "")

            with patch('time.time', return_value=current_time):
                minutes = commit_enforcer.get_time_since_last_commit()

                assert minutes == 5

    def test_get_time_since_last_commit_old(self):
        """Test old commit (2 hours ago)."""
        import time

        current_time = int(time.time())
        two_hours_ago = current_time - 7200

        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (0, str(two_hours_ago), "")

            with patch('time.time', return_value=current_time):
                minutes = commit_enforcer.get_time_since_last_commit()

                assert minutes == 120

    def test_get_time_since_last_commit_no_commits(self):
        """Test when no commits exist."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (128, "", "fatal: no commits")

            minutes = commit_enforcer.get_time_since_last_commit()

            assert minutes is None


class TestGetCurrentBranch:
    """Test current branch detection."""

    def test_get_current_branch_main(self):
        """Test getting main branch."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (0, "main\n", "")

            branch = commit_enforcer.get_current_branch()

            assert branch == "main"

    def test_get_current_branch_feature(self):
        """Test getting feature branch."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (0, "feature/test-branch\n", "")

            branch = commit_enforcer.get_current_branch()

            assert branch == "feature/test-branch"

    def test_get_current_branch_error(self):
        """Test error handling."""
        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (128, "", "not a git repo")

            branch = commit_enforcer.get_current_branch()

            assert branch == "unknown"


class TestCheckThresholds:
    """Test threshold checking logic."""

    def test_check_thresholds_no_changes(self):
        """Test when no changes exist."""
        changes = {'has_changes': False, 'total_files': 0, 'lines_changed': 0}

        warnings = commit_enforcer.check_thresholds(changes)

        assert len(warnings) == 0

    def test_check_thresholds_within_limits(self):
        """Test when changes are within thresholds."""
        changes = {'has_changes': True, 'total_files': 5, 'lines_changed': 100}

        with patch.object(commit_enforcer, 'get_time_since_last_commit', return_value=10):
            warnings = commit_enforcer.check_thresholds(changes)

            assert len(warnings) == 0

    def test_check_thresholds_too_many_files(self):
        """Test warning when too many files changed."""
        changes = {'has_changes': True, 'total_files': 15, 'lines_changed': 100}

        warnings = commit_enforcer.check_thresholds(changes)

        assert len(warnings) >= 1
        assert any('files' in w for w in warnings)

    def test_check_thresholds_too_many_lines(self):
        """Test warning when too many lines changed."""
        changes = {'has_changes': True, 'total_files': 5, 'lines_changed': 600}

        warnings = commit_enforcer.check_thresholds(changes)

        assert len(warnings) >= 1
        assert any('lines' in w for w in warnings)

    def test_check_thresholds_too_long_since_commit(self):
        """Test warning when too long since last commit."""
        changes = {'has_changes': True, 'total_files': 5, 'lines_changed': 100}

        with patch.object(commit_enforcer, 'get_time_since_last_commit', return_value=45):
            warnings = commit_enforcer.check_thresholds(changes)

            assert len(warnings) >= 1
            assert any('since last commit' in w for w in warnings)

    def test_check_thresholds_all_exceeded(self):
        """Test multiple warnings when all thresholds exceeded."""
        changes = {'has_changes': True, 'total_files': 15, 'lines_changed': 600}

        with patch.object(commit_enforcer, 'get_time_since_last_commit', return_value=45):
            warnings = commit_enforcer.check_thresholds(changes)

            assert len(warnings) == 3


class TestAutoCommit:
    """Test automatic commit functionality."""

    def test_auto_commit_no_changes(self):
        """Test auto-commit when no changes exist."""
        changes = {'has_changes': False}

        result = commit_enforcer.auto_commit_changes(changes)

        assert result is True

    def test_auto_commit_success(self):
        """Test successful auto-commit."""
        changes = {
            'has_changes': True,
            'total_files': 3,
            'modified': ['file1.py', 'file2.py'],
            'added': ['file3.py'],
            'deleted': [],
            'untracked': [],
            'lines_changed': 50
        }

        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            # Mock git add -A and git commit
            mock_git.side_effect = [
                (0, "", ""),  # git add
                (0, "", ""),  # git commit
                (0, "abc1234\n", "")  # git rev-parse
            ]

            result = commit_enforcer.auto_commit_changes(changes)

            assert result is True
            assert mock_git.call_count == 3

    def test_auto_commit_add_fails(self):
        """Test auto-commit when git add fails."""
        changes = {
            'has_changes': True,
            'total_files': 1,
            'modified': ['file1.py'],
            'added': [],
            'deleted': [],
            'untracked': [],
            'lines_changed': 10
        }

        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (1, "", "error adding files")

            result = commit_enforcer.auto_commit_changes(changes)

            assert result is False

    def test_auto_commit_commit_fails(self):
        """Test auto-commit when git commit fails."""
        changes = {
            'has_changes': True,
            'total_files': 1,
            'modified': ['file1.py'],
            'added': [],
            'deleted': [],
            'untracked': [],
            'lines_changed': 10
        }

        with patch.object(commit_enforcer, 'run_git_command') as mock_git:
            mock_git.side_effect = [
                (0, "", ""),  # git add succeeds
                (1, "", "nothing to commit")  # git commit fails
            ]

            result = commit_enforcer.auto_commit_changes(changes)

            assert result is False


class TestPrintStatus:
    """Test status printing (visual output)."""

    def test_print_status_no_changes(self, capsys):
        """Test printing status with no changes."""
        changes = {'has_changes': False}
        warnings = []

        with patch.object(commit_enforcer, 'get_current_branch', return_value='main'):
            commit_enforcer.print_status(changes, warnings)

            captured = capsys.readouterr()
            assert "No uncommitted changes" in captured.out

    def test_print_status_with_changes(self, capsys):
        """Test printing status with changes."""
        changes = {
            'has_changes': True,
            'total_files': 5,
            'lines_changed': 100,
            'modified': ['file1.py', 'file2.py'],
            'added': ['file3.py'],
            'deleted': [],
            'untracked': ['file4.py', 'file5.py']
        }
        warnings = []

        with patch.object(commit_enforcer, 'get_current_branch', return_value='main'):
            with patch.object(commit_enforcer, 'get_time_since_last_commit', return_value=15):
                commit_enforcer.print_status(changes, warnings)

                captured = capsys.readouterr()
                assert "Total files: 5" in captured.out
                assert "Lines changed: ~100" in captured.out

    def test_print_status_with_warnings(self, capsys):
        """Test printing status with warnings."""
        changes = {'has_changes': True, 'total_files': 15, 'lines_changed': 600}
        warnings = ["Too many files", "Too many lines"]

        with patch.object(commit_enforcer, 'get_current_branch', return_value='main'):
            commit_enforcer.print_status(changes, warnings)

            captured = capsys.readouterr()
            assert "WARNINGS" in captured.out
            assert "Too many files" in captured.out
            assert "Too many lines" in captured.out
