# Tmux Monitoring Dashboard - Task Breakdown

## Overview
This document contains the detailed task breakdown for implementing the Tmux Monitoring Dashboard.

## Milestone 1: Basic Tmux Layout (MVP)

### Task 1.1: Create start_monitor.sh
**Type:** Shell Script
**Priority:** High
**Dependencies:** None

**Description:**
Create the main bash script that launches the tmux monitoring dashboard with a 2x2 grid layout.

**Requirements:**
- Parse command-line arguments for configuration
- Support flags: -n (session name), -o (output dir), -l (log file), -p (project id)
- Check if session already exists and attach if so
- Create new tmux session with proper name
- Split into 2x2 grid (horizontal split, then vertical splits)
- Launch appropriate commands in each pane:
  - Pane 0 (top-left): bash shell (for CLI)
  - Pane 1 (top-right): tail -f on log file
  - Pane 2 (bottom-left): vim with netrw in output directory
  - Pane 3 (bottom-right): task_watcher.py (or placeholder)
- Select Pane 0 for user interaction
- Attach to the session

**Acceptance Criteria:**
- [ ] Script is executable
- [ ] Creates 2x2 grid layout
- [ ] All panes show correct content
- [ ] Works on macOS and Linux
- [ ] Supports bash and zsh

### Task 1.2: Create stop_monitor.sh
**Type:** Shell Script
**Priority:** High
**Dependencies:** Task 1.1

**Description:**
Create a bash script to cleanly terminate the monitoring session.

**Requirements:**
- Parse session name argument (or use default)
- Check if session exists
- Kill session if exists
- Report status to user

**Acceptance Criteria:**
- [ ] Script is executable
- [ ] Cleanly kills tmux session
- [ ] Handles case when session doesn't exist
- [ ] Provides user feedback

## Milestone 2: Task Watcher Script

### Task 2.1: Create task_watcher.py
**Type:** Python Script
**Priority:** High
**Dependencies:** Milestone 1

**Description:**
Create a Python script that monitors and displays task status from the project tracking system.

**Requirements:**
- Parse command-line arguments for configuration
- Support flags: -p (project id), -r (refresh interval), -d (projects dir), --all
- Load and parse project.json from ~/.ensemble/projects/{project_id}/
- Extract tasks with their status
- Format output with:
  - Header with project info
  - Summary counts (completed, in-progress, pending)
  - Tasks grouped by status with icons (✅, 🔄, ⏳)
  - Timestamp of last update
- Clear screen and refresh on interval
- Handle errors gracefully (missing file, invalid JSON, etc.)
- Support Ctrl+C for clean exit

**Classes to implement:**
- TaskStatus (Enum): todo, in_progress, completed, blocked, cancelled
- Task (dataclass): id, title, status, assigned_to
- TaskWatcher: main class with load_project, get_tasks, format_output, run methods

**Acceptance Criteria:**
- [ ] Correctly parses project.json
- [ ] Displays tasks with proper formatting
- [ ] Refreshes automatically
- [ ] Handles errors gracefully
- [ ] Works with Python 3.8+

## Milestone 3: Full Integration & Polish

### Task 3.1: Update start_monitor.sh for Full Integration
**Type:** Shell Script Update
**Priority:** Medium
**Dependencies:** Tasks 1.1, 2.1

**Description:**
Update the start script to properly integrate all components.

**Requirements:**
- Launch task_watcher.py in Pane 3 with correct project ID
- Add dependency checks (tmux, vim, python3)
- Improve error messages
- Add --help output

**Acceptance Criteria:**
- [ ] All panes work together
- [ ] Helpful error messages for missing dependencies
- [ ] Comprehensive --help output

### Task 3.2: Create User Documentation
**Type:** Documentation
**Priority:** Medium
**Dependencies:** All implementation tasks

**Description:**
Create comprehensive user documentation for the monitoring dashboard.

**Requirements:**
- Installation requirements
- Quick start guide
- Configuration options
- Tmux navigation tips
- Troubleshooting section

**Acceptance Criteria:**
- [ ] Clear and concise documentation
- [ ] Covers all features
- [ ] Includes examples
