"""Configuration module for GitHub Bots."""

from .settings import BotConfig, load_config, save_config, get_default_config

__all__ = ["BotConfig", "load_config", "save_config", "get_default_config"]
