#!/usr/bin/env python3
"""
Push Enforcer Bot - Ensures committed work is pushed to remote regularly

This bot:
1. Monitors for unpushed commits on local branches
2. Warns when unpushed commits exceed thresholds
3. Can automatically push to remote (optional, requires confirmation)
4. Logs push enforcement actions

Usage:
    python push_enforcer.py --check           # Check and warn only
    python push_enforcer.py --auto-push       # Auto-push if threshold exceeded
    python push_enforcer.py --watch           # Continuous monitoring mode
    python push_enforcer.py --force-push      # Force push immediately
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
MAX_UNPUSHED_COMMITS = 5
MAX_TIME_SINCE_PUSH_MINUTES = 60

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


def get_current_branch() -> Optional[str]:
    """Get current git branch name."""
    code, stdout, stderr = run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])

    if code != 0:
        return None

    return stdout.strip()


def get_remote_branch(branch: str) -> Optional[str]:
    """Get the remote tracking branch for the given branch."""
    code, stdout, stderr = run_git_command(['rev-parse', '--abbrev-ref', f'{branch}@{{upstream}}'])

    if code != 0:
        return None

    return stdout.strip()


def get_unpushed_commits() -> Dict[str, any]:
    """Get information about unpushed commits."""
    branch = get_current_branch()

    if not branch:
        return {
            'error': 'Could not determine current branch',
            'has_unpushed': False
        }

    remote_branch = get_remote_branch(branch)

    if not remote_branch:
        return {
            'error': f'Branch {branch} has no remote tracking branch',
            'branch': branch,
            'has_unpushed': False,
            'has_remote': False
        }

    # Get list of unpushed commits
    code, stdout, stderr = run_git_command(['log', f'{remote_branch}..{branch}', '--oneline'])

    if code != 0:
        return {
            'error': f'Failed to get unpushed commits: {stderr}',
            'branch': branch,
            'has_unpushed': False
        }

    commit_lines = [line for line in stdout.strip().split('\n') if line.strip()]
    commit_count = len(commit_lines)

    # Parse commits
    commits = []
    for line in commit_lines:
        parts = line.split(' ', 1)
        if len(parts) == 2:
            commit_hash, message = parts
            commits.append({
                'hash': commit_hash,
                'message': message
            })

    # Get last push time (approximate from remote branch HEAD)
    code, stdout, stderr = run_git_command(['log', '-1', '--format=%ct', remote_branch])
    last_push_time = None

    if code == 0 and stdout.strip():
        try:
            last_push_timestamp = int(stdout.strip())
            current_timestamp = int(time.time())
            last_push_time = (current_timestamp - last_push_timestamp) // 60
        except ValueError:
            pass

    return {
        'has_unpushed': commit_count > 0,
        'has_remote': True,
        'branch': branch,
        'remote_branch': remote_branch,
        'commit_count': commit_count,
        'commits': commits,
        'last_push_minutes': last_push_time
    }


def check_thresholds(status: Dict) -> List[str]:
    """Check if any thresholds are exceeded and return warnings."""
    warnings = []

    if not status.get('has_unpushed'):
        return warnings

    commit_count = status.get('commit_count', 0)
    last_push = status.get('last_push_minutes')

    if commit_count > MAX_UNPUSHED_COMMITS:
        warnings.append(
            f"Too many unpushed commits: {commit_count} (threshold: {MAX_UNPUSHED_COMMITS})"
        )

    if last_push and last_push > MAX_TIME_SINCE_PUSH_MINUTES:
        warnings.append(
            f"Too long since last push: {last_push} minutes (threshold: {MAX_TIME_SINCE_PUSH_MINUTES})"
        )

    return warnings


def print_status(status: Dict, warnings: List[str]):
    """Print current status with colors."""
    print(f"\n{Colors.BOLD}=== Push Enforcer Status ==={Colors.END}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if status.get('error'):
        print(f"{Colors.RED}Error: {status['error']}{Colors.END}")
        return

    branch = status.get('branch', 'unknown')
    remote_branch = status.get('remote_branch', 'none')

    print(f"Branch: {Colors.BLUE}{branch}{Colors.END}")

    if not status.get('has_remote'):
        print(f"{Colors.YELLOW}⚠ No remote tracking branch configured{Colors.END}")
        return

    print(f"Remote: {Colors.BLUE}{remote_branch}{Colors.END}")
    print()

    if not status.get('has_unpushed'):
        print(f"{Colors.GREEN}✓ All commits pushed to remote{Colors.END}")
        return

    commit_count = status.get('commit_count', 0)
    commits = status.get('commits', [])
    last_push = status.get('last_push_minutes')

    print(f"{Colors.BOLD}Unpushed Commits: {commit_count}{Colors.END}")

    if last_push is not None:
        print(f"Last push: {last_push} minutes ago")

    print()

    # Show commits (max 10)
    print(f"{Colors.BOLD}Recent unpushed commits:{Colors.END}")
    for commit in commits[:10]:
        print(f"  {Colors.YELLOW}{commit['hash']}{Colors.END} {commit['message']}")

    if len(commits) > 10:
        print(f"  ... and {len(commits) - 10} more")

    print()

    if warnings:
        print(f"{Colors.RED}{Colors.BOLD}⚠ WARNINGS:{Colors.END}")
        for warning in warnings:
            print(f"  {Colors.RED}• {warning}{Colors.END}")
        print()
    else:
        print(f"{Colors.YELLOW}ℹ Unpushed commits within thresholds{Colors.END}")
        print()


def auto_push_commits(status: Dict, force: bool = False) -> bool:
    """Automatically push commits to remote."""
    if not status.get('has_unpushed'):
        print(f"{Colors.GREEN}No commits to push{Colors.END}")
        return True

    if not status.get('has_remote'):
        print(f"{Colors.RED}No remote tracking branch configured{Colors.END}")
        return False

    branch = status.get('branch')
    commit_count = status.get('commit_count', 0)

    print(f"{Colors.YELLOW}Pushing {commit_count} commit(s) to remote...{Colors.END}")
    print(f"Branch: {branch}")

    # Push to remote
    code, stdout, stderr = run_git_command(['push'])

    if code != 0:
        print(f"{Colors.RED}Failed to push: {stderr}{Colors.END}")

        # Check if it's a force-push situation
        if 'rejected' in stderr and 'non-fast-forward' in stderr:
            print(f"{Colors.RED}Remote has diverged - manual intervention required{Colors.END}")

        return False

    print(f"{Colors.GREEN}✓ Successfully pushed {commit_count} commit(s){Colors.END}")
    return True


def watch_mode(auto_push: bool = False, interval: int = 300):
    """Continuous monitoring mode (default 5 minutes)."""
    print(f"{Colors.BOLD}Starting push enforcer in watch mode{Colors.END}")
    print(f"Check interval: {interval} seconds")
    print(f"Auto-push: {'ENABLED' if auto_push else 'DISABLED'}")
    print(f"Press Ctrl+C to stop\n")

    try:
        while True:
            status = get_unpushed_commits()

            if status.get('error') and not status.get('has_remote'):
                # Silent for branches without remotes
                time.sleep(interval)
                continue

            warnings = check_thresholds(status)

            if status.get('has_unpushed') or warnings:
                print_status(status, warnings)

                if auto_push and warnings:
                    auto_push_commits(status)

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Stopping push enforcer{Colors.END}")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='Push Enforcer Bot - Ensures commits are pushed regularly'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check and display status once'
    )

    parser.add_argument(
        '--auto-push',
        action='store_true',
        help='Automatically push if thresholds exceeded'
    )

    parser.add_argument(
        '--watch',
        action='store_true',
        help='Continuous monitoring mode'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds for watch mode (default: 300 = 5 minutes)'
    )

    parser.add_argument(
        '--force-push',
        action='store_true',
        help='Force push all commits immediately regardless of thresholds'
    )

    args = parser.parse_args()

    # Default to check mode if no arguments
    if not any([args.check, args.auto_push, args.watch, args.force_push]):
        args.check = True

    # Get status
    status = get_unpushed_commits()

    if status.get('error') and status.get('has_remote') is False:
        print(f"{Colors.YELLOW}Branch has no remote tracking branch - skipping{Colors.END}")
        sys.exit(0)

    # Force push mode
    if args.force_push:
        success = auto_push_commits(status, force=True)
        sys.exit(0 if success else 1)

    # Watch mode
    if args.watch:
        watch_mode(auto_push=args.auto_push, interval=args.interval)
        return

    # Check mode
    warnings = check_thresholds(status)
    print_status(status, warnings)

    # Auto-push if requested and warnings exist
    if args.auto_push and warnings:
        success = auto_push_commits(status)
        sys.exit(0 if success else 1)

    # Exit with non-zero if warnings
    if warnings:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
