"""
CLI Interface for GitHub Bots

Provides command-line interface to run all bots.
"""

import argparse
import sys
from pathlib import Path

from .config import load_config, get_default_config, save_config
from .core import GitOperations
from .bots import SyncBot, DocumentationBot, CommitBot, PushBot
from .utils import setup_logging


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GitHub Bots - Automated Git workflow tools"
    )

    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--repo", "-r",
        type=Path,
        default=Path.cwd(),
        help="Path to Git repository (default: current directory)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Bot commands")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync with upstream")

    # Doc command
    doc_parser = subparsers.add_parser("doc", help="Generate commit message")

    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Create commit")
    commit_parser.add_argument(
        "-m", "--message",
        help="Commit message (or use generated)"
    )

    # Push command
    push_parser = subparsers.add_parser("push", help="Push to remote")
    push_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force push (if allowed by config)"
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument(
        "--init",
        action="store_true",
        help="Create default config file"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show bot status")

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)

    # Load config
    config = load_config(args.config)

    # Handle commands
    if args.command == "config":
        if args.init:
            config_path = args.config or Path.cwd() / ".github-bots.yml"
            save_config(get_default_config(), config_path)
            print(f"Created config file: {config_path}")
            return 0

    elif args.command == "sync":
        bot = SyncBot(repo_path=args.repo, config=config)
        success = bot.execute()
        return 0 if success else 1

    elif args.command == "doc":
        bot = DocumentationBot(repo_path=args.repo, config=config)
        success = bot.execute()
        if success:
            message = bot.get_message()
            if message:
                print("Generated commit message:")
                print("-" * 40)
                print(message)
                print("-" * 40)
        return 0 if success else 1

    elif args.command == "commit":
        # First generate message if not provided
        message = args.message
        if not message:
            doc_bot = DocumentationBot(repo_path=args.repo, config=config)
            doc_bot.execute()
            message = doc_bot.get_message()

        if not message:
            print("Error: No commit message provided and generation failed")
            return 1

        bot = CommitBot(repo_path=args.repo, config=config)
        success = bot.run(message=message)
        return 0 if success else 1

    elif args.command == "push":
        bot = PushBot(repo_path=args.repo, config=config)
        success = bot.run(force=args.force)
        return 0 if success else 1

    elif args.command == "status":
        try:
            git = GitOperations(args.repo)
            print(f"Repository: {args.repo}")
            print(f"Branch: {git.get_current_branch()}")
            print(f"Clean: {git.is_clean()}")
            print(f"Staged files: {len(git.get_staged_files())}")
            print(f"Modified files: {len(git.get_modified_files())}")
            print(f"Untracked files: {len(git.get_untracked_files())}")
            print(f"Unpushed commits: {len(git.get_unpushed_commits())}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    else:
        parser.print_help()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
