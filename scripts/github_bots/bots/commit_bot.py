"""
Commit Bot

Handles automated commits with proper formatting and validation.
"""

from typing import Any, Optional
import re

from ..core.base_bot import BaseBot


class CommitBot(BaseBot):
    """
    Commit Bot implementation.
    
    Features:
    - Accept message from Documentation Bot or manual input
    - Validate commit message format
    - Stage changes
    - Execute commit with author info
    - GPG signing support
    - Rollback capability
    """
    
    name = "commit_bot"
    
    @property
    def bot_config(self) -> Any:
        """Get Commit Bot configuration."""
        return self.config.commit_bot
    
    def validate_message(self, message: str) -> bool:
        """
        Validate commit message format.
        
        Args:
            message: Commit message to validate
        
        Returns:
            True if message is valid
        """
        if not self.bot_config.validate_message:
            return True
        
        # Check minimum length
        if len(message) < 10:
            self.log_error("validate", "Message too short")
            return False
        
        # Check Conventional Commits format
        # Pattern: type(scope)?: subject
        pattern = r"^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+"
        if not re.match(pattern, message.split("\n")[0]):
            self.log_error("validate", "Message does not follow Conventional Commits format")
            return False
        
        return True
    
    def stage_changes(self, files: Optional[list] = None) -> bool:
        """
        Stage changes for commit.
        
        Args:
            files: Specific files to stage, or None to stage all
        
        Returns:
            True if staging was successful
        """
        if files:
            result = self.git.add(*files)
        else:
            result = self.git.add()
        
        if not result.success:
            self.log_error("stage", result.stderr)
            return False
        
        return True
    
    def commit(self, message: str) -> bool:
        """
        Execute commit with the given message.
        
        Args:
            message: Commit message
        
        Returns:
            True if commit was successful
        """
        # Validate message
        if not self.validate_message(message):
            return False
        
        # Check for staged changes
        staged = self.git.get_staged_files()
        if not staged:
            self.log_error("commit", "No staged changes")
            return False
        
        # Execute commit
        result = self.git.commit(
            message=message,
            sign=self.bot_config.gpg_sign
        )
        
        if not result.success:
            self.log_error("commit", result.stderr)
            return False
        
        self.log_operation("commit", {"files": len(staged), "message_length": len(message)})
        return True
    
    def run(self, message: Optional[str] = None, files: Optional[list] = None) -> bool:
        """
        Execute commit operation.
        
        Args:
            message: Commit message (required)
            files: Specific files to commit, or None for all staged
        
        Returns:
            True if commit was successful
        """
        if not message:
            self.log_error("run", "No commit message provided")
            return False
        
        # Stage if auto_stage is enabled and we have specific files
        if self.bot_config.auto_stage and files:
            if not self.stage_changes(files):
                return False
        
        return self.commit(message)
