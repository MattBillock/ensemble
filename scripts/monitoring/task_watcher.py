#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Watcher - Real-time task status display for TMUX monitoring dashboard.

Displays agent tasks grouped by status with visual indicators:
- ✅ Completed
- 🔄 In Progress / Running
- ⏳ Pending
- ❌ Failed
- 🔁 Recovered

Usage:
    python task_watcher.py [--refresh SECONDS] [--project PROJECT_ID]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import urllib.request
import urllib.error


# Status icons
ICONS = {
    "completed": "✅",
    "running": "🔄",
    "in_progress": "🔄",
    "pending": "⏳",
    "failed": "❌",
    "stalled": "⚠️",
    "recovered": "🔁",
    "unknown": "❓"
}

# ANSI colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def fetch_api_data(endpoint: str, timeout: float = 2.0) -> Optional[Dict]:
    """Fetch data from the backend API."""
    try:
        url = f"http://localhost:8001/api/{endpoint}"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None
    except Exception:
        return None


def load_project_tracking(project_id: str) -> Optional[Dict]:
    """Load project tracking data from file."""
    projects_dir = Path.home() / ".ensemble" / "projects"
    project_file = projects_dir / project_id / "project.json"

    if project_file.exists():
        try:
            with open(project_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def get_all_projects() -> List[Dict]:
    """Get all project tracking files."""
    projects_dir = Path.home() / ".ensemble" / "projects"
    projects = []

    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                project_file = project_dir / "project.json"
                if project_file.exists():
                    try:
                        with open(project_file) as f:
                            data = json.load(f)
                            data['_project_id'] = project_dir.name
                            projects.append(data)
                    except (json.JSONDecodeError, IOError):
                        continue

    return projects


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_cost(cost: float) -> str:
    """Format cost as currency."""
    if cost < 0.01:
        return f"${cost:.4f}"
    return f"${cost:.2f}"


def truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def render_status_bar(stats: Dict[str, int]) -> str:
    """Render a status summary bar."""
    parts = []

    if stats.get('completed', 0) > 0:
        parts.append(f"{Colors.GREEN}{ICONS['completed']} {stats['completed']}{Colors.RESET}")
    if stats.get('running', 0) > 0:
        parts.append(f"{Colors.CYAN}{ICONS['running']} {stats['running']}{Colors.RESET}")
    if stats.get('pending', 0) > 0:
        parts.append(f"{Colors.YELLOW}{ICONS['pending']} {stats['pending']}{Colors.RESET}")
    if stats.get('failed', 0) > 0:
        parts.append(f"{Colors.RED}{ICONS['failed']} {stats['failed']}{Colors.RESET}")
    if stats.get('stalled', 0) > 0:
        parts.append(f"{Colors.MAGENTA}{ICONS['stalled']} {stats['stalled']}{Colors.RESET}")
    if stats.get('recovered', 0) > 0:
        parts.append(f"{Colors.BLUE}{ICONS['recovered']} {stats['recovered']}{Colors.RESET}")

    return " | ".join(parts) if parts else "No tasks"


def render_agent_line(agent: Dict, indent: int = 0) -> str:
    """Render a single agent line."""
    status = agent.get('status', 'unknown')
    icon = ICONS.get(status, ICONS['unknown'])
    name = agent.get('agent_name', agent.get('agent_id', 'Unknown'))
    agent_type = agent.get('agent_type', '')
    iteration = agent.get('iteration', 0)
    max_iter = agent.get('max_iterations', 0)
    family = agent.get('family_name', '')

    # Color based on status
    if status in ('completed',):
        color = Colors.GREEN
    elif status in ('running', 'in_progress'):
        color = Colors.CYAN
    elif status in ('failed',):
        color = Colors.RED
    elif status in ('stalled', 'recovered'):
        color = Colors.YELLOW
    else:
        color = Colors.DIM

    # Build display line
    prefix = "  " * indent
    name_display = truncate(name, 25)

    # Add family name if available
    if family:
        name_display = f"{name_display} [{family}]"

    iter_info = f"[{iteration}/{max_iter}]" if max_iter > 0 else ""

    return f"{prefix}{icon} {color}{name_display}{Colors.RESET} {Colors.DIM}{agent_type} {iter_info}{Colors.RESET}"


def render_session(session: Dict, agents: List[Dict]) -> List[str]:
    """Render a session with its agents."""
    lines = []

    session_id = session.get('session_id', 'Unknown')[:8]
    status = session.get('status', 'unknown')
    prompt = truncate(session.get('user_prompt', ''), 50)

    # Session header
    icon = ICONS.get(status, ICONS['unknown'])
    if status == 'running':
        color = Colors.CYAN
    elif status == 'completed':
        color = Colors.GREEN
    elif status == 'failed':
        color = Colors.RED
    else:
        color = Colors.DIM

    lines.append(f"{icon} {color}{Colors.BOLD}Session {session_id}{Colors.RESET}")
    lines.append(f"  {Colors.DIM}{prompt}{Colors.RESET}")

    # Group agents by status
    by_status = {}
    for agent in agents:
        s = agent.get('status', 'unknown')
        by_status.setdefault(s, []).append(agent)

    # Render agents by status (running first, then pending, then others)
    status_order = ['running', 'in_progress', 'pending', 'completed', 'failed', 'stalled', 'recovered']
    for s in status_order:
        if s in by_status:
            for agent in by_status[s]:
                lines.append(render_agent_line(agent, indent=1))

    return lines


def main():
    parser = argparse.ArgumentParser(description="Watch agent tasks in real-time")
    parser.add_argument('--refresh', '-r', type=float, default=2.0,
                       help="Refresh interval in seconds (default: 2)")
    parser.add_argument('--project', '-p', type=str,
                       help="Filter to specific project ID")
    parser.add_argument('--once', action='store_true',
                       help="Display once and exit (no refresh)")
    args = parser.parse_args()

    try:
        while True:
            clear_screen()

            # Header
            now = datetime.now().strftime("%H:%M:%S")
            print(f"{Colors.BOLD}═══════════════════════════════════════════════════{Colors.RESET}")
            print(f"{Colors.BOLD}  🎭 Ensemble Agent Task Watcher  {Colors.DIM}[{now}]{Colors.RESET}")
            print(f"{Colors.BOLD}═══════════════════════════════════════════════════{Colors.RESET}")
            print()

            # Try API first
            swarm_stats = fetch_api_data("swarm/stats")
            sessions_data = fetch_api_data("swarm/sessions")
            agents_data = fetch_api_data("swarm/agents")

            if swarm_stats:
                # API is available - use real-time data
                sessions = swarm_stats.get('sessions', {})
                agents = swarm_stats.get('agents', {})

                print(f"{Colors.BOLD}Sessions:{Colors.RESET} {sessions.get('running', 0)} running / {sessions.get('total', 0)} total")
                print(f"{Colors.BOLD}Agents:{Colors.RESET}   {render_status_bar(agents)}")

                if swarm_stats.get('recovery_pending', 0) > 0:
                    print(f"{Colors.YELLOW}⚠️  Recovery pending: {swarm_stats['recovery_pending']}{Colors.RESET}")

                print()
                print(f"{Colors.BOLD}─────────────────────────────────────────────────{Colors.RESET}")
                print()

                # Show running sessions with agents
                if sessions_data and agents_data:
                    sessions_list = sessions_data.get('sessions', [])
                    agents_list = agents_data.get('agents', [])

                    # Filter to running sessions
                    running_sessions = [s for s in sessions_list if s.get('status') == 'running'][:5]

                    for session in running_sessions:
                        session_id = session.get('session_id', '')
                        session_agents = [a for a in agents_list if a.get('session_id') == session_id]

                        for line in render_session(session, session_agents):
                            print(line)
                        print()

            else:
                # API not available - fall back to project files
                print(f"{Colors.YELLOW}⚠️  Backend not available - showing project files{Colors.RESET}")
                print()

                projects = get_all_projects()
                if args.project:
                    projects = [p for p in projects if p.get('_project_id', '').startswith(args.project)]

                if projects:
                    # Sort by creation date (newest first)
                    projects.sort(key=lambda p: p.get('created_at', ''), reverse=True)

                    for project in projects[:5]:
                        pid = project.get('_project_id', 'unknown')[:8]
                        status = project.get('status', 'unknown')
                        title = truncate(project.get('title', project.get('prompt', 'Untitled')), 40)

                        icon = ICONS.get(status, ICONS['unknown'])
                        print(f"{icon} {Colors.BOLD}Project {pid}{Colors.RESET}")
                        print(f"  {Colors.DIM}{title}{Colors.RESET}")

                        # Show tasks if available
                        tasks = project.get('tasks', [])
                        if tasks:
                            stats = {}
                            for task in tasks:
                                s = task.get('status', 'pending')
                                stats[s] = stats.get(s, 0) + 1
                            print(f"  Tasks: {render_status_bar(stats)}")
                        print()
                else:
                    print(f"{Colors.DIM}No projects found{Colors.RESET}")

            # Footer
            print()
            print(f"{Colors.BOLD}─────────────────────────────────────────────────{Colors.RESET}")
            print(f"{Colors.DIM}Press Ctrl+C to exit | Refresh: {args.refresh}s{Colors.RESET}")

            if args.once:
                break

            time.sleep(args.refresh)

    except KeyboardInterrupt:
        print(f"\n{Colors.DIM}Exiting...{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
