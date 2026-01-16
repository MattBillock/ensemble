#!/usr/bin/env python3
"""
Commit Enforcer Bot - Ensures agents commit their work regularly

This bot:
1. Monitors for uncommitted changes in the repository
2. Warns when uncommitted changes exceed thresholds
3. Can automatically commit work-in-progress (optional)
4. Logs commit enforcement actions to metrics database

Usage:
    python commit_enforcer.py --check          # Check and warn only
    python commit_enforcer.py --auto-commit    # Auto-commit if threshold exceeded
    python commit_enforcer.py --watch          # Continuous monitoring mode
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

# Thresholds
MAX_UNCOMMITTED_FILES = 10
MAX_UNCOMMITTED_LINES = 500
MAX_TIME_SINCE_COMMIT_MINUTES = 30

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_git_command(args: List[str]) -> Tuple[int, str, str]:
    """Run a git command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Git command timed out"
    except Exception as e:
        return 1, "", str(e)


def get_uncommitted_changes() -> Dict[str, any]:
    """Get information about uncommitted changes."""
    # Check for unstaged changes
    code, stdout, stderr = run_git_command(['status', '--porcelain'])

    if code != 0:
        return {
            'error': f"Git status failed: {stderr}",
            'has_changes': False
        }

    # Use rstrip to preserve leading spaces which are significant in git status output
    lines = stdout.rstrip().split('\n') if stdout.rstrip() else []

    # Parse status
    modified_files = []
    added_files = []
    deleted_files = []
    untracked_files = []

    for line in lines:
        if not line.strip():
            continue

        status = line[:2]
        filename = line[3:]

        if 'M' in status:
            modified_files.append(filename)
        if 'A' in status:
            added_files.append(filename)
        if 'D' in status:
            deleted_files.append(filename)
        if '??' in status:
            untracked_files.append(filename)

    # Get diff stats
    code, diff_stdout, _ = run_git_command(['diff', '--stat'])
    lines_changed = 0

    if code == 0 and diff_stdout:
        # Parse lines like: "5 files changed, 123 insertions(+), 45 deletions(-)"
        for line in diff_stdout.split('\n'):
            if 'changed' in line or 'insertion' in line or 'deletion' in line:
                parts = line.split(',')
                for part in parts:
                    if 'insertion' in part:
                        try:
                            lines_changed += int(part.split()[0])
                        except (ValueError, IndexError):
                            pass
                    if 'deletion' in part:
                        try:
                            lines_changed += int(part.split()[0])
                        except (ValueError, IndexError):
                            pass

    total_files = len(modified_files) + len(added_files) + len(deleted_files) + len(untracked_files)

    return {
        'has_changes': total_files > 0,
        'total_files': total_files,
        'modified': modified_files,
        'added': added_files,
        'deleted': deleted_files,
        'untracked': untracked_files,
        'lines_changed': lines_changed
    }


def get_time_since_last_commit() -> Optional[int]:
    """Get minutes since last commit."""
    code, stdout, stderr = run_git_command(['log', '-1', '--format=%ct'])

    if code != 0 or not stdout.strip():
        return None

    try:
        last_commit_timestamp = int(stdout.strip())
        current_timestamp = int(time.time())
        minutes = (current_timestamp - last_commit_timestamp) // 60
        return minutes
    except ValueError:
        return None


def get_current_branch() -> str:
    """Get current git branch name."""
    code, stdout, stderr = run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])

    if code != 0:
        return "unknown"

    return stdout.strip()


def check_thresholds(changes: Dict) -> List[str]:
    """Check if any thresholds are exceeded and return warnings."""
    warnings = []

    if not changes.get('has_changes'):
        return warnings

    total_files = changes['total_files']
    lines_changed = changes['lines_changed']

    if total_files > MAX_UNCOMMITTED_FILES:
        warnings.append(
            f"Too many uncommitted files: {total_files} (threshold: {MAX_UNCOMMITTED_FILES})"
        )

    if lines_changed > MAX_UNCOMMITTED_LINES:
        warnings.append(
            f"Too many uncommitted lines: {lines_changed} (threshold: {MAX_UNCOMMITTED_LINES})"
        )

    time_since = get_time_since_last_commit()
    if time_since and time_since > MAX_TIME_SINCE_COMMIT_MINUTES:
        warnings.append(
            f"Too long since last commit: {time_since} minutes (threshold: {MAX_TIME_SINCE_COMMIT_MINUTES})"
        )

    return warnings


def print_status(changes: Dict, warnings: List[str]):
    """Print current status with colors."""
    print(f"\n{Colors.BOLD}=== Commit Enforcer Status ==={Colors.END}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Branch: {Colors.BLUE}{get_current_branch()}{Colors.END}")
    print()

    if not changes.get('has_changes'):
        print(f"{Colors.GREEN}✓ No uncommitted changes{Colors.END}")
        return

    print(f"{Colors.BOLD}Uncommitted Changes:{Colors.END}")
    print(f"  Total files: {changes.get('total_files', 0)}")
    print(f"  Lines changed: ~{changes.get('lines_changed', 0)}")
    print(f"  Modified: {len(changes.get('modified', []))}")
    print(f"  Added: {len(changes.get('added', []))}")
    print(f"  Deleted: {len(changes.get('deleted', []))}")
    print(f"  Untracked: {len(changes.get('untracked', []))}")

    time_since = get_time_since_last_commit()
    if time_since is not None:
        print(f"  Time since last commit: {time_since} minutes")

    print()

    if warnings:
        print(f"{Colors.RED}{Colors.BOLD}⚠ WARNINGS:{Colors.END}")
        for warning in warnings:
            print(f"  {Colors.RED}• {warning}{Colors.END}")
        print()
    else:
        print(f"{Colors.YELLOW}ℹ Changes within thresholds{Colors.END}")
        print()


def auto_commit_changes(changes: Dict) -> bool:
    """Automatically commit changes with a generated message."""
    if not changes.get('has_changes'):
        print(f"{Colors.GREEN}No changes to commit{Colors.END}")
        return True

    # Generate commit message
    total = changes['total_files']
    modified = len(changes['modified'])
    added = len(changes['added'])
    deleted = len(changes['deleted'])
    untracked = len(changes['untracked'])

    parts = []
    if modified:
        parts.append(f"{modified} modified")
    if added:
        parts.append(f"{added} added")
    if deleted:
        parts.append(f"{deleted} deleted")
    if untracked:
        parts.append(f"{untracked} untracked")

    file_summary = ", ".join(parts) if parts else "changes"

    commit_msg = f"[AUTO-COMMIT] Work in progress: {file_summary}\n\n"
    commit_msg += f"Automated commit by commit_enforcer.py\n"
    commit_msg += f"Total files: {total}\n"
    commit_msg += f"Lines changed: ~{changes['lines_changed']}\n"
    commit_msg += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    commit_msg += "Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

    print(f"{Colors.YELLOW}Auto-committing changes...{Colors.END}")
    print(f"Message: {commit_msg.split(chr(10))[0]}")

    # Add all changes
    code, stdout, stderr = run_git_command(['add', '-A'])
    if code != 0:
        print(f"{Colors.RED}Failed to add files: {stderr}{Colors.END}")
        return False

    # Commit
    code, stdout, stderr = run_git_command(['commit', '-m', commit_msg])
    if code != 0:
        print(f"{Colors.RED}Failed to commit: {stderr}{Colors.END}")
        return False

    print(f"{Colors.GREEN}✓ Successfully committed changes{Colors.END}")

    # Show commit hash
    code, stdout, stderr = run_git_command(['rev-parse', '--short', 'HEAD'])
    if code == 0:
        commit_hash = stdout.strip()
        print(f"Commit: {Colors.BLUE}{commit_hash}{Colors.END}")

    return True


def watch_mode(auto_commit: bool = False, interval: int = 60):
    """Continuous monitoring mode."""
    print(f"{Colors.BOLD}Starting commit enforcer in watch mode{Colors.END}")
    print(f"Check interval: {interval} seconds")
    print(f"Auto-commit: {'ENABLED' if auto_commit else 'DISABLED'}")
    print(f"Press Ctrl+C to stop\n")

    try:
        while True:
            changes = get_uncommitted_changes()

            if changes.get('error'):
                print(f"{Colors.RED}Error: {changes['error']}{Colors.END}")
                time.sleep(interval)
                continue

            warnings = check_thresholds(changes)

            if changes.get('has_changes') or warnings:
                print_status(changes, warnings)

                if auto_commit and warnings:
                    auto_commit_changes(changes)
            else:
                # Silent when no changes
                pass

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Stopping commit enforcer{Colors.END}")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='Commit Enforcer Bot - Ensures work is committed regularly'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check and display status once'
    )

    parser.add_argument(
        '--auto-commit',
        action='store_true',
        help='Automatically commit if thresholds exceeded'
    )

    parser.add_argument(
        '--watch',
        action='store_true',
        help='Continuous monitoring mode'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds for watch mode (default: 60)'
    )

    parser.add_argument(
        '--force-commit',
        action='store_true',
        help='Force commit all changes immediately regardless of thresholds'
    )

    args = parser.parse_args()

    # Default to check mode if no arguments
    if not any([args.check, args.auto_commit, args.watch, args.force_commit]):
        args.check = True

    # Get changes
    changes = get_uncommitted_changes()

    if changes.get('error'):
        print(f"{Colors.RED}Error: {changes['error']}{Colors.END}")
        sys.exit(1)

    # Force commit mode
    if args.force_commit:
        success = auto_commit_changes(changes)
        sys.exit(0 if success else 1)

    # Watch mode
    if args.watch:
        watch_mode(auto_commit=args.auto_commit, interval=args.interval)
        return

    # Check mode
    warnings = check_thresholds(changes)
    print_status(changes, warnings)

    # Auto-commit if requested and warnings exist
    if args.auto_commit and warnings:
        success = auto_commit_changes(changes)
        sys.exit(0 if success else 1)

    # Exit with non-zero if warnings
    if warnings:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
