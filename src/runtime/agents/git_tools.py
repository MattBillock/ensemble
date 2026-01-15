"""
Git Tools - Branch-based development tools for agents.

Provides git branch, merge, and enhanced commit tools for coordinated
multi-agent development with proper isolation and collaboration.
"""
import logging
import subprocess
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BranchInfo:
    """Information about a git branch."""
    name: str
    is_current: bool
    last_commit: str
    last_commit_message: str
    ahead: int = 0
    behind: int = 0


class GitBranchTool:
    """Tool for managing git branches."""

    name = "git_branch"
    description = "Create, switch, list, or delete git branches for coordinated development"
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "switch", "list", "delete", "current"],
                "description": "Action to perform: create new branch, switch to existing, list all, delete, or get current"
            },
            "branch_name": {
                "type": "string",
                "description": "Name of the branch (for create, switch, delete)"
            },
            "from_branch": {
                "type": "string",
                "description": "Base branch to create from (for create, defaults to current branch)"
            },
            "force": {
                "type": "boolean",
                "description": "Force the operation (for delete unmerged branches)",
                "default": False
            }
        },
        "required": ["action"]
    }

    def __init__(
        self,
        working_directory: Optional[Path] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.working_directory = working_directory or Path.cwd()
        self.agent_id = agent_id
        self.session_id = session_id

    def _run_git(self, args: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Run a git command and return (success, stdout, stderr)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute git branch operation."""
        action = inputs["action"]
        branch_name = inputs.get("branch_name")
        from_branch = inputs.get("from_branch")
        force = inputs.get("force", False)

        try:
            if action == "create":
                return self._create_branch(branch_name, from_branch)
            elif action == "switch":
                return self._switch_branch(branch_name)
            elif action == "list":
                return self._list_branches()
            elif action == "delete":
                return self._delete_branch(branch_name, force)
            elif action == "current":
                return self._get_current_branch()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Git branch error: {e}")
            return {"success": False, "error": str(e)}

    def _create_branch(
        self,
        branch_name: Optional[str],
        from_branch: Optional[str]
    ) -> Dict[str, Any]:
        """Create a new branch."""
        if not branch_name:
            return {"success": False, "error": "branch_name required for create"}

        # Validate branch name
        if not self._is_valid_branch_name(branch_name):
            return {"success": False, "error": f"Invalid branch name: {branch_name}"}

        # Check if branch exists
        success, stdout, _ = self._run_git(["branch", "--list", branch_name])
        if stdout:
            return {"success": False, "error": f"Branch '{branch_name}' already exists"}

        # Create branch
        args = ["checkout", "-b", branch_name]
        if from_branch:
            args.append(from_branch)

        success, stdout, stderr = self._run_git(args)

        if success:
            # Emit event
            self._emit_branch_event("created", branch_name, from_branch)

            return {
                "success": True,
                "message": f"Created and switched to branch '{branch_name}'",
                "branch": branch_name,
                "from_branch": from_branch
            }
        else:
            return {"success": False, "error": stderr or "Failed to create branch"}

    def _switch_branch(self, branch_name: Optional[str]) -> Dict[str, Any]:
        """Switch to an existing branch."""
        if not branch_name:
            return {"success": False, "error": "branch_name required for switch"}

        # Check for uncommitted changes
        success, stdout, _ = self._run_git(["status", "--porcelain"])
        if stdout:
            return {
                "success": False,
                "error": "Cannot switch branches with uncommitted changes. Commit or stash first.",
                "uncommitted_files": stdout.split('\n')
            }

        success, stdout, stderr = self._run_git(["checkout", branch_name])

        if success:
            return {
                "success": True,
                "message": f"Switched to branch '{branch_name}'",
                "branch": branch_name
            }
        else:
            return {"success": False, "error": stderr or f"Failed to switch to branch '{branch_name}'"}

    def _list_branches(self) -> Dict[str, Any]:
        """List all branches with their status."""
        success, stdout, stderr = self._run_git([
            "branch", "-v", "--format=%(refname:short)|%(HEAD)|%(objectname:short)|%(subject)"
        ])

        if not success:
            return {"success": False, "error": stderr}

        branches = []
        for line in stdout.split('\n'):
            if not line.strip():
                continue
            parts = line.split('|')
            if len(parts) >= 4:
                branches.append({
                    "name": parts[0],
                    "is_current": parts[1] == '*',
                    "last_commit": parts[2],
                    "last_commit_message": parts[3]
                })

        # Get current branch
        _, current, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])

        return {
            "success": True,
            "current_branch": current,
            "branches": branches,
            "count": len(branches)
        }

    def _delete_branch(self, branch_name: Optional[str], force: bool) -> Dict[str, Any]:
        """Delete a branch."""
        if not branch_name:
            return {"success": False, "error": "branch_name required for delete"}

        # Check if it's the current branch
        _, current, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if branch_name == current:
            return {"success": False, "error": "Cannot delete the current branch. Switch to another branch first."}

        # Prevent deleting main/master
        if branch_name in ("main", "master"):
            return {"success": False, "error": f"Cannot delete protected branch '{branch_name}'"}

        flag = "-D" if force else "-d"
        success, stdout, stderr = self._run_git(["branch", flag, branch_name])

        if success:
            self._emit_branch_event("deleted", branch_name)
            return {
                "success": True,
                "message": f"Deleted branch '{branch_name}'",
                "branch": branch_name
            }
        else:
            return {"success": False, "error": stderr or f"Failed to delete branch '{branch_name}'"}

    def _get_current_branch(self) -> Dict[str, Any]:
        """Get the current branch name and status."""
        success, branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])

        if not success:
            return {"success": False, "error": "Failed to get current branch"}

        # Get ahead/behind count from remote
        _, status_output, _ = self._run_git(["status", "-sb"])

        ahead = behind = 0
        if '[' in status_output:
            match = re.search(r'ahead (\d+)', status_output)
            if match:
                ahead = int(match.group(1))
            match = re.search(r'behind (\d+)', status_output)
            if match:
                behind = int(match.group(1))

        return {
            "success": True,
            "branch": branch,
            "ahead": ahead,
            "behind": behind,
            "status": "up_to_date" if ahead == 0 and behind == 0 else "diverged"
        }

    def _is_valid_branch_name(self, name: str) -> bool:
        """Check if branch name is valid."""
        # Basic validation
        if not name or len(name) > 255:
            return False
        if name.startswith('-') or name.endswith('.'):
            return False
        if '..' in name or '//' in name:
            return False
        # Check for invalid characters
        invalid_chars = set(' ~^:?*[\\')
        if any(c in name for c in invalid_chars):
            return False
        return True

    def _emit_branch_event(
        self,
        action: str,
        branch_name: str,
        from_branch: Optional[str] = None
    ):
        """Emit a branch event to the event bus."""
        try:
            from .event_bus import get_event_bus, EventType

            event_type = EventType.GIT_BRANCH_CREATED if action == "created" else EventType.CUSTOM

            get_event_bus().publish(
                event_type.value,
                {
                    "action": action,
                    "branch_name": branch_name,
                    "from_branch": from_branch
                },
                session_id=self.session_id,
                agent_id=self.agent_id
            )
        except Exception as e:
            logger.warning(f"Failed to emit branch event: {e}")

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class GitMergeTool:
    """Tool for merging git branches."""

    name = "git_merge"
    description = "Merge branches or create pull requests for code review"
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["merge", "preview", "abort"],
                "description": "Action: merge branches, preview changes, or abort an in-progress merge"
            },
            "source_branch": {
                "type": "string",
                "description": "Branch to merge from"
            },
            "target_branch": {
                "type": "string",
                "description": "Branch to merge into (defaults to current branch)"
            },
            "strategy": {
                "type": "string",
                "enum": ["merge", "squash", "rebase"],
                "description": "Merge strategy (default: merge)",
                "default": "merge"
            },
            "message": {
                "type": "string",
                "description": "Custom merge commit message (optional)"
            },
            "no_ff": {
                "type": "boolean",
                "description": "Create merge commit even if fast-forward is possible",
                "default": True
            }
        },
        "required": ["action"]
    }

    def __init__(
        self,
        working_directory: Optional[Path] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.working_directory = working_directory or Path.cwd()
        self.agent_id = agent_id
        self.session_id = session_id

    def _run_git(self, args: List[str], timeout: int = 60) -> Tuple[bool, str, str]:
        """Run a git command and return (success, stdout, stderr)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute git merge operation."""
        action = inputs["action"]
        source_branch = inputs.get("source_branch")
        target_branch = inputs.get("target_branch")
        strategy = inputs.get("strategy", "merge")
        message = inputs.get("message")
        no_ff = inputs.get("no_ff", True)

        try:
            if action == "preview":
                return self._preview_merge(source_branch, target_branch)
            elif action == "merge":
                return self._merge_branches(source_branch, target_branch, strategy, message, no_ff)
            elif action == "abort":
                return self._abort_merge()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Git merge error: {e}")
            return {"success": False, "error": str(e)}

    def _preview_merge(
        self,
        source_branch: Optional[str],
        target_branch: Optional[str]
    ) -> Dict[str, Any]:
        """Preview what would be merged."""
        if not source_branch:
            return {"success": False, "error": "source_branch required for preview"}

        # Get current branch if target not specified
        if not target_branch:
            _, target_branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])

        # Get the diff between branches
        success, diff_stat, _ = self._run_git([
            "diff", "--stat", f"{target_branch}...{source_branch}"
        ])

        # Get commit list
        success, commits, _ = self._run_git([
            "log", "--oneline", f"{target_branch}..{source_branch}"
        ])

        # Check for conflicts
        success, merge_base, _ = self._run_git(["merge-base", target_branch, source_branch])
        _, tree_result, _ = self._run_git([
            "merge-tree", merge_base, target_branch, source_branch
        ])

        has_conflicts = "<<<<<<" in tree_result or "+<<<<<<" in tree_result

        return {
            "success": True,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "diff_stat": diff_stat,
            "commits": commits.split('\n') if commits else [],
            "commit_count": len(commits.split('\n')) if commits else 0,
            "potential_conflicts": has_conflicts,
            "conflict_preview": tree_result[:1000] if has_conflicts else None
        }

    def _merge_branches(
        self,
        source_branch: Optional[str],
        target_branch: Optional[str],
        strategy: str,
        message: Optional[str],
        no_ff: bool
    ) -> Dict[str, Any]:
        """Merge source branch into target branch."""
        if not source_branch:
            return {"success": False, "error": "source_branch required for merge"}

        # Get current branch
        _, current_branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])

        # Switch to target if specified and different
        if target_branch and target_branch != current_branch:
            success, _, stderr = self._run_git(["checkout", target_branch])
            if not success:
                return {"success": False, "error": f"Failed to checkout target branch: {stderr}"}
            current_branch = target_branch

        # Build merge command based on strategy
        if strategy == "squash":
            args = ["merge", "--squash", source_branch]
        elif strategy == "rebase":
            # For rebase, we actually rebase instead of merge
            success, _, stderr = self._run_git(["rebase", source_branch])
            if success:
                self._emit_merge_event(source_branch, current_branch, strategy)
                return {
                    "success": True,
                    "message": f"Rebased '{current_branch}' onto '{source_branch}'",
                    "source_branch": source_branch,
                    "target_branch": current_branch,
                    "strategy": strategy
                }
            else:
                return {"success": False, "error": f"Rebase failed: {stderr}"}
        else:
            # Regular merge
            args = ["merge"]
            if no_ff:
                args.append("--no-ff")
            if message:
                args.extend(["-m", message])
            args.append(source_branch)

        success, stdout, stderr = self._run_git(args)

        if success:
            # For squash, we need to commit
            if strategy == "squash":
                commit_msg = message or f"Squashed merge of '{source_branch}' into '{current_branch}'"
                success, _, stderr = self._run_git(["commit", "-m", commit_msg])
                if not success:
                    return {"success": False, "error": f"Squash commit failed: {stderr}"}

            # Get merge commit hash
            _, commit_hash, _ = self._run_git(["rev-parse", "HEAD"])

            self._emit_merge_event(source_branch, current_branch, strategy)

            return {
                "success": True,
                "message": f"Merged '{source_branch}' into '{current_branch}'",
                "source_branch": source_branch,
                "target_branch": current_branch,
                "strategy": strategy,
                "commit_hash": commit_hash
            }
        else:
            # Check if it's a conflict
            if "CONFLICT" in stderr or "CONFLICT" in stdout:
                # Get conflict files
                _, status, _ = self._run_git(["status", "--porcelain"])
                conflict_files = [
                    line[3:] for line in status.split('\n')
                    if line.startswith('UU') or line.startswith('AA')
                ]

                return {
                    "success": False,
                    "error": "Merge conflict detected",
                    "conflict_files": conflict_files,
                    "resolution_needed": True,
                    "abort_command": "git_merge with action='abort'"
                }
            else:
                return {"success": False, "error": stderr or stdout}

    def _abort_merge(self) -> Dict[str, Any]:
        """Abort an in-progress merge."""
        success, stdout, stderr = self._run_git(["merge", "--abort"])

        if success:
            return {
                "success": True,
                "message": "Merge aborted successfully"
            }
        else:
            # Try reset if merge abort fails
            success, _, stderr2 = self._run_git(["reset", "--hard", "HEAD"])
            if success:
                return {
                    "success": True,
                    "message": "Merge aborted via reset"
                }
            return {"success": False, "error": stderr or stderr2}

    def _emit_merge_event(
        self,
        source_branch: str,
        target_branch: str,
        strategy: str
    ):
        """Emit a merge event to the event bus."""
        try:
            from .event_bus import get_event_bus, EventType

            get_event_bus().publish(
                EventType.GIT_BRANCH_MERGED.value,
                {
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "strategy": strategy
                },
                session_id=self.session_id,
                agent_id=self.agent_id
            )
        except Exception as e:
            logger.warning(f"Failed to emit merge event: {e}")

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class GitStatusTool:
    """Tool for getting comprehensive git status."""

    name = "git_status"
    description = "Get comprehensive git repository status including branches, changes, and history"
    input_schema = {
        "type": "object",
        "properties": {
            "include_history": {
                "type": "boolean",
                "description": "Include recent commit history",
                "default": False
            },
            "history_count": {
                "type": "integer",
                "description": "Number of commits to include in history",
                "default": 10
            }
        },
        "required": []
    }

    def __init__(self, working_directory: Optional[Path] = None):
        self.working_directory = working_directory or Path.cwd()

    def _run_git(self, args: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Run a git command."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive git status."""
        include_history = inputs.get("include_history", False)
        history_count = inputs.get("history_count", 10)

        result = {"success": True}

        # Current branch
        success, branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        result["current_branch"] = branch if success else "unknown"

        # Working directory status
        success, status_output, _ = self._run_git(["status", "--porcelain"])
        changes = {
            "staged": [],
            "unstaged": [],
            "untracked": []
        }

        for line in status_output.split('\n'):
            if not line:
                continue
            index_status = line[0]
            worktree_status = line[1]
            filename = line[3:]

            if index_status == '?':
                changes["untracked"].append(filename)
            elif index_status != ' ':
                changes["staged"].append({"file": filename, "status": index_status})
            if worktree_status != ' ' and worktree_status != '?':
                changes["unstaged"].append({"file": filename, "status": worktree_status})

        result["changes"] = changes
        result["has_changes"] = bool(status_output)
        result["clean"] = not bool(status_output)

        # Remote tracking
        _, tracking_output, _ = self._run_git(["status", "-sb"])
        if '[' in tracking_output:
            match = re.search(r'ahead (\d+)', tracking_output)
            result["ahead"] = int(match.group(1)) if match else 0
            match = re.search(r'behind (\d+)', tracking_output)
            result["behind"] = int(match.group(1)) if match else 0
        else:
            result["ahead"] = 0
            result["behind"] = 0

        # Last commit
        success, last_commit, _ = self._run_git([
            "log", "-1", "--format=%H|%s|%an|%ar"
        ])
        if success and last_commit:
            parts = last_commit.split('|')
            result["last_commit"] = {
                "hash": parts[0],
                "message": parts[1],
                "author": parts[2],
                "when": parts[3]
            }

        # History if requested
        if include_history:
            success, history, _ = self._run_git([
                "log", f"-{history_count}", "--format=%H|%s|%an|%ar"
            ])
            if success:
                result["history"] = []
                for line in history.split('\n'):
                    if line:
                        parts = line.split('|')
                        result["history"].append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "when": parts[3]
                        })

        # Stash count
        success, stash, _ = self._run_git(["stash", "list"])
        result["stash_count"] = len(stash.split('\n')) if stash else 0

        return result

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }
