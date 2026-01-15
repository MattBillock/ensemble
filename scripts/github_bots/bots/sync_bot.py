"""
Sync Bot

Keeps pending changes up to date with the latest upstream changes.
"""

from typing import Any

from ..core.base_bot import BaseBot


class SyncBot(BaseBot):
    """
    Sync Bot implementation.
    
    Features:
    - Detect uncommitted changes
    - Stash uncommitted changes before sync
    - Fetch latest from remote
    - Choose between pull/rebase based on config
    - Handle merge conflicts
    - Restore stashed changes
    """
    
    name = "sync_bot"
    
    @property
    def bot_config(self) -> Any:
        """Get Sync Bot configuration."""
        return self.config.sync_bot
    
    def run(self) -> bool:
        """
        Execute sync operation.
        
        Returns:
            True if sync was successful
        """
        remote = self.bot_config.remote
        strategy = self.bot_config.strategy
        auto_stash = self.bot_config.auto_stash
        
        # Check for uncommitted changes
        has_changes = self.git.has_uncommitted_changes()
        stashed = False
        
        if has_changes:
            if auto_stash:
                self.log_operation("stash", {"reason": "auto_stash before sync"})
                result = self.git.stash("Auto-stash before sync")
                if not result.success:
                    self.log_error("stash", result.stderr)
                    return False
                stashed = True
            else:
                self.log_error("sync", "Uncommitted changes present and auto_stash disabled")
                return False
        
        # Fetch from remote
        self.log_operation("fetch", {"remote": remote})
        result = self.git.fetch(remote)
        if not result.success:
            self.log_error("fetch", result.stderr)
            if stashed:
                self.git.stash_pop()
            return False
        
        # Sync based on strategy
        branch = self.git.get_current_branch()
        if strategy == "rebase":
            self.log_operation("rebase", {"upstream": f"{remote}/{branch}"})
            result = self.git.rebase(f"{remote}/{branch}")
        else:
            self.log_operation("pull", {"remote": remote})
            result = self.git.pull(remote, branch)
        
        if not result.success:
            self.log_error(strategy, result.stderr)
            if "CONFLICT" in result.stderr or "conflict" in result.stdout:
                self.log_error(strategy, "Merge conflicts detected")
                if strategy == "rebase":
                    self.git.rebase_abort()
            if stashed:
                self.git.stash_pop()
            return False
        
        # Restore stashed changes
        if stashed:
            self.log_operation("stash_pop", {})
            result = self.git.stash_pop()
            if not result.success:
                self.log_error("stash_pop", result.stderr)
                return False
        
        self.log_operation("sync_complete", {"strategy": strategy, "remote": remote})
        return True
