"""
Push Bot

Regularly pushes repository changes to GitHub.
"""

from typing import Any, List
import time

from ..core.base_bot import BaseBot


class PushBot(BaseBot):
    """
    Push Bot implementation.
    
    Features:
    - Monitor for unpushed commits
    - Push to configured remote
    - Multiple push strategies (immediate, batch)
    - Retry logic with backoff
    - Force push with safety checks
    """
    
    name = "push_bot"
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [5, 15, 60]  # seconds
    
    @property
    def bot_config(self) -> Any:
        """Get Push Bot configuration."""
        return self.config.push_bot
    
    def get_unpushed_count(self) -> int:
        """Get count of unpushed commits."""
        unpushed = self.git.get_unpushed_commits(self.bot_config.remote)
        return len(unpushed)
    
    def push_with_retry(self, force: bool = False) -> bool:
        """
        Push to remote with retry logic.
        
        Args:
            force: Whether to force push
        
        Returns:
            True if push was successful
        """
        remote = self.bot_config.remote
        force_config = self.bot_config.force_push
        
        # Determine push mode
        use_force_with_lease = force and force_config == "with_lease"
        use_force = force and force_config == "allowed"
        
        if force and force_config == "never":
            self.log_error("push", "Force push requested but disabled in config")
            return False
        
        for attempt in range(self.MAX_RETRIES):
            result = self.git.push(
                remote=remote,
                force=use_force,
                force_with_lease=use_force_with_lease
            )
            
            if result.success:
                return True
            
            # Check if it's a non-retryable error
            if "non-fast-forward" in result.stderr:
                self.log_error("push", "Remote has new commits. Sync first.")
                return False
            
            if "protected branch" in result.stderr.lower():
                self.log_error("push", "Cannot push to protected branch")
                return False
            
            # Retry with delay
            if attempt < self.MAX_RETRIES - 1:
                delay = self.RETRY_DELAYS[attempt]
                self.log_operation("retry", {"attempt": attempt + 1, "delay": delay})
                time.sleep(delay)
        
        self.log_error("push", f"Failed after {self.MAX_RETRIES} attempts")
        return False
    
    def run(self, force: bool = False) -> bool:
        """
        Execute push operation.
        
        Args:
            force: Whether to force push (subject to config)
        
        Returns:
            True if push was successful or nothing to push
        """
        # Check for unpushed commits
        unpushed = self.get_unpushed_count()
        
        if unpushed == 0:
            self.log_operation("skip", {"reason": "no unpushed commits"})
            return True
        
        self.log_operation("push", {"commits": unpushed, "remote": self.bot_config.remote})
        
        success = self.push_with_retry(force=force)
        
        if success:
            self.log_operation("push_complete", {"commits": unpushed})
        
        return success
