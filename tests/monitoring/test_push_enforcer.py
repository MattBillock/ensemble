"""
Unit tests for push_enforcer.py

Tests the push enforcement bot that monitors unpushed commits.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add scripts/monitoring to path
scripts_path = Path(__file__).parent.parent.parent / "scripts" / "monitoring"
sys.path.insert(0, str(scripts_path))

import push_enforcer


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

            code, stdout, stderr = push_enforcer.run_git_command(['branch'])

            assert code == 0
            assert stdout == "main\n"
            assert stderr == ""

    def test_run_git_command_failure(self):
        """Test failed git command execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=128,
                stdout="",
                stderr="fatal: not a git repository"
            )

            code, stdout, stderr = push_enforcer.run_git_command(['status'])

            assert code == 128
            assert stderr == "fatal: not a git repository"


class TestGetCurrentBranch:
    """Test current branch detection."""

    def test_get_current_branch_main(self):
        """Test getting main branch."""
        with patch.object(push_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (0, "main\n", "")

            branch = push_enforcer.get_current_branch()

            assert branch == "main"

    def test_get_current_branch_feature(self):
        """Test getting feature branch."""
        with patch.object(push_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (0, "feature/add-tests\n", "")

            branch = push_enforcer.get_current_branch()

            assert branch == "feature/add-tests"

    def test_get_current_branch_error(self):
        """Test error handling."""
        with patch.object(push_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (128, "", "error")

            branch = push_enforcer.get_current_branch()

            assert branch is None


class TestGetRemoteBranch:
    """Test remote tracking branch detection."""

    def test_get_remote_branch_exists(self):
        """Test getting remote tracking branch."""
        with patch.object(push_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (0, "origin/main\n", "")

            remote = push_enforcer.get_remote_branch("main")

            assert remote == "origin/main"

    def test_get_remote_branch_none(self):
        """Test when no remote tracking branch exists."""
        with patch.object(push_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (128, "", "no upstream configured")

            remote = push_enforcer.get_remote_branch("feature-branch")

            assert remote is None


class TestGetUnpushedCommits:
    """Test detection of unpushed commits."""

    def test_get_unpushed_commits_none(self):
        """Test when all commits are pushed."""
        with patch.object(push_enforcer, 'get_current_branch', return_value='main'):
            with patch.object(push_enforcer, 'get_remote_branch', return_value='origin/main'):
                with patch.object(push_enforcer, 'run_git_command') as mock_git:
                    # Mock git log (empty - all pushed)
                    mock_git.side_effect = [
                        (0, "", ""),  # log
                        (0, "1234567890", "")  # log -1 --format=%ct
                    ]

                    status = push_enforcer.get_unpushed_commits()

                    assert status['has_unpushed'] is False
                    assert status['has_remote'] is True
                    assert status['commit_count'] == 0

    def test_get_unpushed_commits_some(self):
        """Test when unpushed commits exist."""
        with patch.object(push_enforcer, 'get_current_branch', return_value='main'):
            with patch.object(push_enforcer, 'get_remote_branch', return_value='origin/main'):
                with patch.object(push_enforcer, 'run_git_command') as mock_git:
                    # Mock git log (3 unpushed commits)
                    mock_git.side_effect = [
                        (0, "abc1234 Add feature X\ndef5678 Fix bug Y\nghi9012 Update docs\n", ""),  # log
                        (0, "1234567890", "")  # log -1 --format=%ct
                    ]

                    status = push_enforcer.get_unpushed_commits()

                    assert status['has_unpushed'] is True
                    assert status['commit_count'] == 3
                    assert len(status['commits']) == 3
                    assert status['commits'][0]['hash'] == 'abc1234'
                    assert status['commits'][0]['message'] == 'Add feature X'

    def test_get_unpushed_commits_no_remote(self):
        """Test when branch has no remote tracking branch."""
        with patch.object(push_enforcer, 'get_current_branch', return_value='local-branch'):
            with patch.object(push_enforcer, 'get_remote_branch', return_value=None):
                status = push_enforcer.get_unpushed_commits()

                assert 'error' in status
                assert status['has_remote'] is False
                assert status['branch'] == 'local-branch'

    def test_get_unpushed_commits_no_branch(self):
        """Test when current branch cannot be determined."""
        with patch.object(push_enforcer, 'get_current_branch', return_value=None):
            status = push_enforcer.get_unpushed_commits()

            assert 'error' in status
            assert status['has_unpushed'] is False

    def test_get_unpushed_commits_with_time(self):
        """Test unpushed commits with last push time calculation."""
        import time

        current_time = int(time.time())
        thirty_mins_ago = current_time - 1800

        with patch.object(push_enforcer, 'get_current_branch', return_value='main'):
            with patch.object(push_enforcer, 'get_remote_branch', return_value='origin/main'):
                with patch.object(push_enforcer, 'run_git_command') as mock_git:
                    mock_git.side_effect = [
                        (0, "abc1234 Recent commit\n", ""),  # log
                        (0, str(thirty_mins_ago), "")  # log -1 --format=%ct
                    ]

                    with patch('time.time', return_value=current_time):
                        status = push_enforcer.get_unpushed_commits()

                        assert status['last_push_minutes'] == 30


class TestCheckThresholds:
    """Test threshold checking logic."""

    def test_check_thresholds_no_unpushed(self):
        """Test when no unpushed commits exist."""
        status = {'has_unpushed': False, 'commit_count': 0}

        warnings = push_enforcer.check_thresholds(status)

        assert len(warnings) == 0

    def test_check_thresholds_within_limits(self):
        """Test when unpushed commits are within thresholds."""
        status = {'has_unpushed': True, 'commit_count': 3, 'last_push_minutes': 30}

        warnings = push_enforcer.check_thresholds(status)

        assert len(warnings) == 0

    def test_check_thresholds_too_many_commits(self):
        """Test warning when too many unpushed commits."""
        status = {'has_unpushed': True, 'commit_count': 10, 'last_push_minutes': 30}

        warnings = push_enforcer.check_thresholds(status)

        assert len(warnings) >= 1
        assert any('commits' in w for w in warnings)

    def test_check_thresholds_too_long_since_push(self):
        """Test warning when too long since last push."""
        status = {'has_unpushed': True, 'commit_count': 3, 'last_push_minutes': 90}

        warnings = push_enforcer.check_thresholds(status)

        assert len(warnings) >= 1
        assert any('since last push' in w for w in warnings)

    def test_check_thresholds_all_exceeded(self):
        """Test multiple warnings when all thresholds exceeded."""
        status = {'has_unpushed': True, 'commit_count': 10, 'last_push_minutes': 90}

        warnings = push_enforcer.check_thresholds(status)

        assert len(warnings) == 2


class TestAutoPush:
    """Test automatic push functionality."""

    def test_auto_push_no_commits(self):
        """Test auto-push when no unpushed commits exist."""
        status = {'has_unpushed': False}

        result = push_enforcer.auto_push_commits(status)

        assert result is True

    def test_auto_push_no_remote(self):
        """Test auto-push when no remote configured."""
        status = {'has_unpushed': True, 'has_remote': False}

        result = push_enforcer.auto_push_commits(status)

        assert result is False

    def test_auto_push_success(self):
        """Test successful auto-push."""
        status = {
            'has_unpushed': True,
            'has_remote': True,
            'branch': 'main',
            'commit_count': 3
        }

        with patch.object(push_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (0, "Successfully pushed", "")

            result = push_enforcer.auto_push_commits(status)

            assert result is True
            mock_git.assert_called_once_with(['push'])

    def test_auto_push_fails(self):
        """Test auto-push when push command fails."""
        status = {
            'has_unpushed': True,
            'has_remote': True,
            'branch': 'main',
            'commit_count': 3
        }

        with patch.object(push_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (1, "", "error: failed to push")

            result = push_enforcer.auto_push_commits(status)

            assert result is False

    def test_auto_push_rejected_non_fast_forward(self):
        """Test auto-push when remote has diverged."""
        status = {
            'has_unpushed': True,
            'has_remote': True,
            'branch': 'main',
            'commit_count': 3
        }

        with patch.object(push_enforcer, 'run_git_command') as mock_git:
            mock_git.return_value = (1, "", "rejected non-fast-forward")

            result = push_enforcer.auto_push_commits(status)

            assert result is False


class TestPrintStatus:
    """Test status printing (visual output)."""

    def test_print_status_no_unpushed(self, capsys):
        """Test printing status with no unpushed commits."""
        status = {
            'has_unpushed': False,
            'has_remote': True,
            'branch': 'main',
            'remote_branch': 'origin/main'
        }
        warnings = []

        push_enforcer.print_status(status, warnings)

        captured = capsys.readouterr()
        assert "All commits pushed" in captured.out

    def test_print_status_with_unpushed(self, capsys):
        """Test printing status with unpushed commits."""
        status = {
            'has_unpushed': True,
            'has_remote': True,
            'branch': 'main',
            'remote_branch': 'origin/main',
            'commit_count': 3,
            'commits': [
                {'hash': 'abc1234', 'message': 'Add feature'},
                {'hash': 'def5678', 'message': 'Fix bug'},
                {'hash': 'ghi9012', 'message': 'Update docs'}
            ],
            'last_push_minutes': 45
        }
        warnings = []

        push_enforcer.print_status(status, warnings)

        captured = capsys.readouterr()
        assert "Unpushed Commits: 3" in captured.out
        assert "abc1234" in captured.out
        assert "Add feature" in captured.out

    def test_print_status_with_warnings(self, capsys):
        """Test printing status with warnings."""
        status = {
            'has_unpushed': True,
            'has_remote': True,
            'branch': 'main',
            'remote_branch': 'origin/main',
            'commit_count': 10,
            'commits': [],
            'last_push_minutes': 90
        }
        warnings = ["Too many unpushed commits", "Too long since last push"]

        push_enforcer.print_status(status, warnings)

        captured = capsys.readouterr()
        assert "WARNINGS" in captured.out
        assert "Too many unpushed commits" in captured.out

    def test_print_status_no_remote(self, capsys):
        """Test printing status when no remote configured."""
        status = {
            'has_remote': False,
            'branch': 'local-branch'
        }
        warnings = []

        push_enforcer.print_status(status, warnings)

        captured = capsys.readouterr()
        assert "No remote tracking branch" in captured.out

    def test_print_status_error(self, capsys):
        """Test printing status with error."""
        status = {
            'error': 'Could not determine current branch'
        }
        warnings = []

        push_enforcer.print_status(status, warnings)

        captured = capsys.readouterr()
        assert "Error:" in captured.out
