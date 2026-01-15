"""
Configuration settings for GitHub Bots.

Provides YAML-based configuration with sensible defaults.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


@dataclass
class SyncBotConfig:
    """Configuration for Sync Bot."""
    enabled: bool = True
    strategy: str = "rebase"  # or "merge"
    remote: str = "origin"
    auto_stash: bool = True
    schedule: str = "*/30 * * * *"  # Every 30 minutes


@dataclass
class DocumentationBotConfig:
    """Configuration for Documentation Bot."""
    enabled: bool = True
    format: str = "conventional_commits"
    include_scope: bool = True
    max_subject_length: int = 50
    body_wrap_length: int = 72


@dataclass
class CommitBotConfig:
    """Configuration for Commit Bot."""
    enabled: bool = True
    gpg_sign: bool = False
    validate_message: bool = True
    auto_stage: bool = True


@dataclass
class PushBotConfig:
    """Configuration for Push Bot."""
    enabled: bool = True
    remote: str = "origin"
    schedule: str = "*/5 * * * *"  # Every 5 minutes
    strategy: str = "batch"  # or "immediate"
    force_push: str = "never"  # or "with_lease", "allowed"


@dataclass
class BotConfig:
    """Main configuration container for all bots."""
    sync_bot: SyncBotConfig = field(default_factory=SyncBotConfig)
    documentation_bot: DocumentationBotConfig = field(default_factory=DocumentationBotConfig)
    commit_bot: CommitBotConfig = field(default_factory=CommitBotConfig)
    push_bot: PushBotConfig = field(default_factory=PushBotConfig)
    
    # Global settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "sync_bot": asdict(self.sync_bot),
            "documentation_bot": asdict(self.documentation_bot),
            "commit_bot": asdict(self.commit_bot),
            "push_bot": asdict(self.push_bot),
            "log_level": self.log_level,
            "log_file": self.log_file,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BotConfig":
        """Create config from dictionary."""
        return cls(
            sync_bot=SyncBotConfig(**data.get("sync_bot", {})),
            documentation_bot=DocumentationBotConfig(**data.get("documentation_bot", {})),
            commit_bot=CommitBotConfig(**data.get("commit_bot", {})),
            push_bot=PushBotConfig(**data.get("push_bot", {})),
            log_level=data.get("log_level", "INFO"),
            log_file=data.get("log_file"),
        )


def get_default_config() -> BotConfig:
    """Get default configuration."""
    return BotConfig()


def load_config(config_path: Optional[Path] = None) -> BotConfig:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, searches for .github-bots.yml
                    in current directory and parent directories.
    
    Returns:
        BotConfig instance
    """
    if config_path is None:
        # Search for config file
        search_paths = [
            Path.cwd() / ".github-bots.yml",
            Path.cwd() / ".github-bots.yaml",
            Path.home() / ".config" / "github-bots" / "config.yml",
        ]
        for path in search_paths:
            if path.exists():
                config_path = path
                break
    
    if config_path is None or not config_path.exists():
        return get_default_config()
    
    with open(config_path, "r") as f:
        data = yaml.safe_load(f) or {}
    
    return BotConfig.from_dict(data)


def save_config(config: BotConfig, config_path: Path) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: BotConfig instance to save
        config_path: Path to save config file
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)
