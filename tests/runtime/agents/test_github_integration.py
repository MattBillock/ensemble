"""
Unit tests for github_integration module.

Tests the GitHubIntegration class for repository detection and URL generation.
"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess


class TestGitHubIntegration:
    """Test GitHubIntegration class."""

    def setup_method(self):
        """Reset cache before each test."""
        from src.runtime.agents.github_integration import GitHubIntegration
        GitHubIntegration.clear_cache()

    def test_convert_to_https_ssh_format(self):
        """Test converting SSH URL to HTTPS."""
        from src.runtime.agents.github_integration import GitHubIntegration

        ssh_url = "git@github.com:user/repo.git"
        https_url = GitHubIntegration.convert_to_https(ssh_url)

        assert https_url == "https://github.com/user/repo"

    def test_convert_to_https_ssh_format_no_git_suffix(self):
        """Test converting SSH URL without .git suffix."""
        from src.runtime.agents.github_integration import GitHubIntegration

        ssh_url = "git@github.com:user/repo"
        https_url = GitHubIntegration.convert_to_https(ssh_url)

        assert https_url == "https://github.com/user/repo"

    def test_convert_to_https_already_https(self):
        """Test HTTPS URL passthrough."""
        from src.runtime.agents.github_integration import GitHubIntegration

        https_url = "https://github.com/user/repo"
        result = GitHubIntegration.convert_to_https(https_url)

        assert result == "https://github.com/user/repo"

    def test_convert_to_https_removes_git_suffix(self):
        """Test that .git suffix is removed from HTTPS URLs."""
        from src.runtime.agents.github_integration import GitHubIntegration

        url = "https://github.com/user/repo.git"
        result = GitHubIntegration.convert_to_https(url)

        assert result == "https://github.com/user/repo"

    def test_detect_repo_url_success(self):
        """Test successful repo URL detection."""
        from src.runtime.agents.github_integration import GitHubIntegration

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git@github.com:user/repo.git\n"

        with patch('subprocess.run', return_value=mock_result):
            url = GitHubIntegration.detect_repo_url(".")

            assert url == "https://github.com/user/repo"

    def test_detect_repo_url_caches_result(self):
        """Test that repo URL is cached."""
        from src.runtime.agents.github_integration import GitHubIntegration

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/user/repo\n"

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            url1 = GitHubIntegration.detect_repo_url(".")
            url2 = GitHubIntegration.detect_repo_url(".")

            # Should only call subprocess once due to caching
            assert mock_run.call_count == 1
            assert url1 == url2

    def test_detect_repo_url_failure(self):
        """Test repo URL detection failure returns None."""
        from src.runtime.agents.github_integration import GitHubIntegration

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch('subprocess.run', return_value=mock_result):
            url = GitHubIntegration.detect_repo_url(".")

            assert url is None

    def test_detect_repo_url_timeout(self):
        """Test repo URL detection handles timeout."""
        from src.runtime.agents.github_integration import GitHubIntegration

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='git', timeout=5)):
            url = GitHubIntegration.detect_repo_url(".")

            assert url is None

    def test_detect_repo_url_git_not_found(self):
        """Test repo URL detection handles missing git."""
        from src.runtime.agents.github_integration import GitHubIntegration

        with patch('subprocess.run', side_effect=FileNotFoundError()):
            url = GitHubIntegration.detect_repo_url(".")

            assert url is None

    def test_get_current_branch_success(self):
        """Test successful branch detection."""
        from src.runtime.agents.github_integration import GitHubIntegration

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "feature-branch\n"

        with patch('subprocess.run', return_value=mock_result):
            branch = GitHubIntegration.get_current_branch(".")

            assert branch == "feature-branch"

    def test_get_current_branch_caches_result(self):
        """Test that branch is cached."""
        from src.runtime.agents.github_integration import GitHubIntegration

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "main\n"

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            branch1 = GitHubIntegration.get_current_branch(".")
            branch2 = GitHubIntegration.get_current_branch(".")

            assert mock_run.call_count == 1
            assert branch1 == branch2

    def test_get_current_branch_fallback(self):
        """Test branch detection fallback to 'main'."""
        from src.runtime.agents.github_integration import GitHubIntegration

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch('subprocess.run', return_value=mock_result):
            branch = GitHubIntegration.get_current_branch(".")

            assert branch == "main"

    def test_get_commit_url(self):
        """Test commit URL generation."""
        from src.runtime.agents.github_integration import GitHubIntegration

        url = GitHubIntegration.get_commit_url(
            "https://github.com/user/repo",
            "abc123"
        )

        assert url == "https://github.com/user/repo/commit/abc123"

    def test_get_file_url(self):
        """Test file URL generation."""
        from src.runtime.agents.github_integration import GitHubIntegration

        url = GitHubIntegration.get_file_url(
            "https://github.com/user/repo",
            "src/main.py",
            "main"
        )

        assert url == "https://github.com/user/repo/blob/main/src/main.py"

    def test_get_file_url_cleans_path(self):
        """Test file URL cleans leading ./ from path."""
        from src.runtime.agents.github_integration import GitHubIntegration

        url = GitHubIntegration.get_file_url(
            "https://github.com/user/repo",
            "./src/main.py",
            "main"
        )

        assert url == "https://github.com/user/repo/blob/main/src/main.py"

    def test_get_file_url_default_branch(self):
        """Test file URL uses main as default branch."""
        from src.runtime.agents.github_integration import GitHubIntegration

        url = GitHubIntegration.get_file_url(
            "https://github.com/user/repo",
            "README.md"
        )

        assert url == "https://github.com/user/repo/blob/main/README.md"

    def test_get_file_history_url(self):
        """Test file history URL generation."""
        from src.runtime.agents.github_integration import GitHubIntegration

        url = GitHubIntegration.get_file_history_url(
            "https://github.com/user/repo",
            "src/main.py"
        )

        assert url == "https://github.com/user/repo/commits/main/src/main.py"

    def test_get_file_history_url_cleans_path(self):
        """Test file history URL cleans path."""
        from src.runtime.agents.github_integration import GitHubIntegration

        url = GitHubIntegration.get_file_history_url(
            "https://github.com/user/repo",
            "./src/main.py"
        )

        assert url == "https://github.com/user/repo/commits/main/src/main.py"

    def test_clear_cache(self):
        """Test cache clearing."""
        from src.runtime.agents.github_integration import GitHubIntegration

        # Set some cached values
        GitHubIntegration._cached_repo_url = "test"
        GitHubIntegration._cached_branch = "test"

        GitHubIntegration.clear_cache()

        assert GitHubIntegration._cached_repo_url is None
        assert GitHubIntegration._cached_branch is None

    def test_get_repo_info(self):
        """Test comprehensive repo info retrieval."""
        from src.runtime.agents.github_integration import GitHubIntegration

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/user/repo\n"

        with patch('subprocess.run', return_value=mock_result):
            info = GitHubIntegration.get_repo_info(".")

            assert info["detected"] is True
            assert info["repo_url"] == "https://github.com/user/repo"
            assert "branch" in info
            assert "github_base" in info

    def test_get_repo_info_not_detected(self):
        """Test repo info when not in a git repo."""
        from src.runtime.agents.github_integration import GitHubIntegration

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch('subprocess.run', return_value=mock_result):
            info = GitHubIntegration.get_repo_info(".")

            assert info["detected"] is False
            assert info["repo_url"] is None
            assert info["github_base"] is None
