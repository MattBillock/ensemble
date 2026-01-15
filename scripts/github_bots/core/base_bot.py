"""
Base Bot Class

Provides common functionality for all GitHub automation bots.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..config import BotConfig, load_config
from .git_ops import GitOperations


class BaseBot(ABC):
    """
    Abstract base class for all GitHub bots.
    
    Provides common functionality like configuration loading,
    logging setup, and Git operations access.
    """
    
    # Bot name (override in subclasses)
    name: str = "base_bot"
    
    def __init__(
        self,
        repo_path: Optional[Path] = None,
        config: Optional[BotConfig] = None,
        config_path: Optional[Path] = None
    ):
        """
        Initialize the bot.
        
        Args:
            repo_path: Path to Git repository
            config: Bot configuration (if None, loads from file)
            config_path: Path to config file (if config is None)
        """
        self.repo_path = repo_path or Path.cwd()
        self.config = config or load_config(config_path)
        self.git = GitOperations(self.repo_path)
        self.logger = logging.getLogger(f"github_bots.{self.name}")
        
        # Execution state
        self._last_run: Optional[datetime] = None
        self._run_count: int = 0
        self._error_count: int = 0
    
    @property
    @abstractmethod
    def bot_config(self) -> Any:
        """Get bot-specific configuration section."""
        pass
    
    @property
    def is_enabled(self) -> bool:
        """Check if bot is enabled in configuration."""
        return getattr(self.bot_config, "enabled", True)
    
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an operation for audit trail.
        
        Args:
            operation: Name of the operation
            details: Additional details to log
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "bot": self.name,
            "operation": operation,
            "details": details or {}
        }
        self.logger.info(f"[{self.name}] {operation}: {details or 'OK'}")
    
    def log_error(self, operation: str, error: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error.
        
        Args:
            operation: Name of the operation that failed
            error: Error message
            details: Additional details
        """
        self._error_count += 1
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "bot": self.name,
            "operation": operation,
            "error": error,
            "details": details or {}
        }
        self.logger.error(f"[{self.name}] {operation} failed: {error}")
    
    @abstractmethod
    def run(self) -> bool:
        """
        Execute the bot's main operation.
        
        Returns:
            True if operation was successful, False otherwise
        """
        pass
    
    def execute(self) -> bool:
        """
        Execute the bot with state tracking.
        
        Returns:
            True if operation was successful, False otherwise
        """
        if not self.is_enabled:
            self.logger.info(f"[{self.name}] Bot is disabled, skipping")
            return True
        
        self._run_count += 1
        self._last_run = datetime.now()
        
        try:
            self.log_operation("start")
            result = self.run()
            self.log_operation("complete", {"success": result})
            return result
        except Exception as e:
            self.log_error("execute", str(e))
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            "name": self.name,
            "enabled": self.is_enabled,
            "run_count": self._run_count,
            "error_count": self._error_count,
            "last_run": self._last_run.isoformat() if self._last_run else None
        }
