"""GitHub integration utilities for repository detection and URL generation."""
import subprocess
import re
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Utilities for GitHub repository integration."""

    # Cache for repo URL to avoid repeated git calls
    _cached_repo_url: Optional[str] = None
    _cached_branch: Optional[str] = None

    @classmethod
    def detect_repo_url(cls, working_directory: str = ".") -> Optional[str]:
        """
        Auto-detect GitHub repo URL from git config.

        Args:
            working_directory: Directory to run git commands in

        Returns:
            HTTPS GitHub URL or None if not detected
        """
        if cls._cached_repo_url is not None:
            return cls._cached_repo_url

        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                raw_url = result.stdout.strip()
                cls._cached_repo_url = cls.convert_to_https(raw_url)
                logger.info(f"Detected GitHub repo: {cls._cached_repo_url}")
                return cls._cached_repo_url
        except subprocess.TimeoutExpired:
            logger.warning("Git command timed out")
        except FileNotFoundError:
            logger.warning("Git not found in PATH")
        except Exception as e:
            logger.error(f"Error detecting repo URL: {e}")

        return None

    @staticmethod
    def convert_to_https(url: str) -> str:
        """
        Convert various git URL formats to HTTPS URL.

        Handles:
        - git@github.com:user/repo.git
        - git@github.com:user/repo
        - https://github.com/user/repo.git
        - https://github.com/user/repo

        Args:
            url: Git remote URL

        Returns:
            HTTPS GitHub URL
        """
        # Handle SSH format: git@github.com:user/repo.git
        ssh_pattern = r'^git@github\.com:(.+?)(?:\.git)?$'
        match = re.match(ssh_pattern, url)
        if match:
            return f"https://github.com/{match.group(1)}"

        # Handle HTTPS with .git suffix
        if url.endswith('.git'):
            url = url[:-4]

        return url

    @classmethod
    def get_current_branch(cls, working_directory: str = ".") -> str:
        """
        Get current git branch name.

        Args:
            working_directory: Directory to run git commands in

        Returns:
            Branch name or "main" as fallback
        """
        if cls._cached_branch is not None:
            return cls._cached_branch

        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                cls._cached_branch = result.stdout.strip()
                return cls._cached_branch
        except Exception as e:
            logger.warning(f"Error getting current branch: {e}")

        return "main"

    @staticmethod
    def get_commit_url(repo_url: str, commit_hash: str) -> str:
        """
        Generate GitHub commit page URL.

        Args:
            repo_url: Base GitHub repo URL (https://github.com/user/repo)
            commit_hash: Full or short commit hash

        Returns:
            GitHub commit URL
        """
        return f"{repo_url}/commit/{commit_hash}"

    @staticmethod
    def get_file_url(repo_url: str, file_path: str, branch: str = "main") -> str:
        """
        Generate GitHub blob URL for viewing a file.

        Args:
            repo_url: Base GitHub repo URL
            file_path: Relative path to file
            branch: Branch name (defaults to main)

        Returns:
            GitHub blob URL
        """
        # Clean up file path - remove leading slashes or ./
        clean_path = file_path.lstrip('./')
        return f"{repo_url}/blob/{branch}/{clean_path}"

    @staticmethod
    def get_file_history_url(repo_url: str, file_path: str) -> str:
        """
        Generate GitHub URL for file commit history.

        Args:
            repo_url: Base GitHub repo URL
            file_path: Relative path to file

        Returns:
            GitHub file history URL
        """
        clean_path = file_path.lstrip('./')
        return f"{repo_url}/commits/main/{clean_path}"

    @classmethod
    def clear_cache(cls):
        """Clear cached values (useful for testing or when repo changes)."""
        cls._cached_repo_url = None
        cls._cached_branch = None

    @classmethod
    def get_repo_info(cls, working_directory: str = ".") -> dict:
        """
        Get comprehensive repo information.

        Args:
            working_directory: Directory to run git commands in

        Returns:
            Dict with repo_url, branch, and status
        """
        repo_url = cls.detect_repo_url(working_directory)
        branch = cls.get_current_branch(working_directory)

        return {
            "repo_url": repo_url,
            "branch": branch,
            "detected": repo_url is not None,
            "github_base": repo_url if repo_url else None
        }
