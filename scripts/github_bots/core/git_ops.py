"""
Git Operations Wrapper

Provides a unified interface for Git operations using both GitPython
and subprocess for CLI operations.
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class GitResult:
    """Result of a Git operation."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    
    @property
    def output(self) -> str:
        """Get combined output."""
        return self.stdout if self.success else self.stderr


class GitOperations:
    """
    Wrapper for Git operations.
    
    Uses subprocess for direct Git CLI operations, providing better
    compatibility and control than GitPython for complex operations.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize Git operations.
        
        Args:
            repo_path: Path to repository. Defaults to current directory.
        """
        self.repo_path = repo_path or Path.cwd()
        self._validate_repo()
    
    def _validate_repo(self) -> None:
        """Validate that repo_path is a Git repository."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"Not a Git repository: {self.repo_path}")
    
    def _run(self, *args: str, capture: bool = True) -> GitResult:
        """
        Run a Git command.
        
        Args:
            *args: Git command and arguments
            capture: Whether to capture output
        
        Returns:
            GitResult with command output
        """
        cmd = ["git", *args]
        logger.debug(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=capture,
                text=True,
                timeout=60
            )
            return GitResult(
                success=result.returncode == 0,
                stdout=result.stdout.strip() if result.stdout else "",
                stderr=result.stderr.strip() if result.stderr else "",
                return_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return GitResult(
                success=False,
                stdout="",
                stderr="Command timed out",
                return_code=-1
            )
        except Exception as e:
            return GitResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1
            )
    
    # Status operations
    def status(self, short: bool = False) -> GitResult:
        """Get repository status."""
        args = ["status"]
        if short:
            args.append("--short")
        return self._run(*args)
    
    def is_clean(self) -> bool:
        """Check if working directory is clean."""
        result = self._run("status", "--porcelain")
        return result.success and not result.stdout
    
    def has_uncommitted_changes(self) -> bool:
        """Check for uncommitted changes."""
        return not self.is_clean()
    
    def get_current_branch(self) -> Optional[str]:
        """Get name of current branch."""
        result = self._run("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout if result.success else None
    
    def get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        result = self._run("diff", "--cached", "--name-only")
        if result.success and result.stdout:
            return result.stdout.split("\n")
        return []
    
    def get_modified_files(self) -> List[str]:
        """Get list of modified files (not staged)."""
        result = self._run("diff", "--name-only")
        if result.success and result.stdout:
            return result.stdout.split("\n")
        return []
    
    def get_untracked_files(self) -> List[str]:
        """Get list of untracked files."""
        result = self._run("ls-files", "--others", "--exclude-standard")
        if result.success and result.stdout:
            return result.stdout.split("\n")
        return []
    
    # Remote operations
    def fetch(self, remote: str = "origin", prune: bool = True) -> GitResult:
        """Fetch from remote."""
        args = ["fetch", remote]
        if prune:
            args.append("--prune")
        return self._run(*args)
    
    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> GitResult:
        """Pull from remote."""
        args = ["pull", remote]
        if branch:
            args.append(branch)
        return self._run(*args)
    
    def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        force_with_lease: bool = False,
        set_upstream: bool = False
    ) -> GitResult:
        """Push to remote."""
        args = ["push", remote]
        if branch:
            args.append(branch)
        if force_with_lease:
            args.append("--force-with-lease")
        elif force:
            args.append("--force")
        if set_upstream:
            args.append("--set-upstream")
        return self._run(*args)
    
    def get_remotes(self) -> List[str]:
        """Get list of remotes."""
        result = self._run("remote")
        if result.success and result.stdout:
            return result.stdout.split("\n")
        return []
    
    # Rebase operations
    def rebase(self, upstream: str, interactive: bool = False) -> GitResult:
        """Rebase onto upstream."""
        args = ["rebase"]
        if interactive:
            args.append("-i")
        args.append(upstream)
        return self._run(*args)
    
    def rebase_abort(self) -> GitResult:
        """Abort ongoing rebase."""
        return self._run("rebase", "--abort")
    
    def rebase_continue(self) -> GitResult:
        """Continue rebase after resolving conflicts."""
        return self._run("rebase", "--continue")
    
    # Stash operations
    def stash(self, message: Optional[str] = None) -> GitResult:
        """Stash changes."""
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])
        return self._run(*args)
    
    def stash_pop(self, index: int = 0) -> GitResult:
        """Pop stash."""
        return self._run("stash", "pop", f"stash@{{{index}}}")
    
    def stash_list(self) -> List[str]:
        """List stashes."""
        result = self._run("stash", "list")
        if result.success and result.stdout:
            return result.stdout.split("\n")
        return []
    
    def stash_drop(self, index: int = 0) -> GitResult:
        """Drop a stash entry."""
        return self._run("stash", "drop", f"stash@{{{index}}}")
    
    # Commit operations
    def add(self, *files: str) -> GitResult:
        """Stage files."""
        if not files:
            return self._run("add", "-A")
        return self._run("add", *files)
    
    def commit(
        self,
        message: str,
        amend: bool = False,
        sign: bool = False,
        no_verify: bool = False
    ) -> GitResult:
        """Create a commit."""
        args = ["commit", "-m", message]
        if amend:
            args.append("--amend")
        if sign:
            args.append("-S")
        if no_verify:
            args.append("--no-verify")
        return self._run(*args)
    
    def reset(self, mode: str = "mixed", ref: str = "HEAD") -> GitResult:
        """Reset to ref."""
        return self._run("reset", f"--{mode}", ref)
    
    # Diff operations
    def diff(
        self,
        staged: bool = False,
        stat: bool = False,
        name_only: bool = False
    ) -> GitResult:
        """Get diff."""
        args = ["diff"]
        if staged:
            args.append("--cached")
        if stat:
            args.append("--stat")
        if name_only:
            args.append("--name-only")
        return self._run(*args)
    
    # Log operations
    def log(
        self,
        count: int = 10,
        oneline: bool = True,
        since: Optional[str] = None
    ) -> GitResult:
        """Get commit log."""
        args = ["log", f"-{count}"]
        if oneline:
            args.append("--oneline")
        if since:
            args.extend(["--since", since])
        return self._run(*args)
    
    def get_unpushed_commits(self, remote: str = "origin") -> List[str]:
        """Get list of commits not yet pushed to remote."""
        branch = self.get_current_branch()
        if not branch:
            return []
        
        result = self._run("log", f"{remote}/{branch}..HEAD", "--oneline")
        if result.success and result.stdout:
            return result.stdout.split("\n")
        return []
    
    # Branch operations
    def checkout(self, branch: str, create: bool = False) -> GitResult:
        """Checkout branch."""
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch)
        return self._run(*args)
    
    def branch(self, name: Optional[str] = None, delete: bool = False) -> GitResult:
        """Branch operations."""
        args = ["branch"]
        if delete and name:
            args.extend(["-d", name])
        elif name:
            args.append(name)
        return self._run(*args)
    
    def get_branches(self, remote: bool = False, all: bool = False) -> List[str]:
        """Get list of branches."""
        args = ["branch"]
        if all:
            args.append("-a")
        elif remote:
            args.append("-r")
        result = self._run(*args)
        if result.success and result.stdout:
            branches = []
            for line in result.stdout.split("\n"):
                branch = line.strip().lstrip("* ")
                if branch:
                    branches.append(branch)
            return branches
        return []
