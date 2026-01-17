# Tmux Monitoring Dashboard for Ensemble Agent Swarm

## Vision
Create a tmux-based 2x2 monitoring dashboard that provides real-time visibility into the ensemble agent swarm's operation. This dashboard allows developers to observe agent activity, browse output files, and track task progress all in a single terminal view.

## Problem Statement
Currently, monitoring the ensemble agent swarm requires switching between multiple terminal windows/tabs to view:
- The CLI running Claude
- Activity logs
- Output files
- Task progress

This context switching reduces efficiency and makes it harder to correlate events across different aspects of the system.

## Solution
A tmux session with a 2x2 grid layout providing simultaneous views of:
1. **Pane 1 (top-left)**: CLI running Claude agent
2. **Pane 2 (top-right)**: Live-streaming activity logs
3. **Pane 3 (bottom-left)**: Vim opened to output directory for file browsing
4. **Pane 4 (bottom-right)**: Master task list showing completed, in-progress, and upcoming tasks

## Requirements

### Functional Requirements

#### FR-1: Tmux Session Management
- FR-1.1: Script to create a new tmux session named "ensemble-monitor" (or configurable name)
- FR-1.2: Script to attach to existing session if it already exists
- FR-1.3: Script to cleanly kill/destroy the monitoring session
- FR-1.4: Session should persist if terminal disconnects

#### FR-2: Pane 1 - Claude CLI
- FR-2.1: Run the ensemble CLI with Claude in interactive mode
- FR-2.2: Position in top-left quadrant
- FR-2.3: Allow user interaction with the CLI
- FR-2.4: Support different ensemble entry points (Executive Director, etc.)

#### FR-3: Pane 2 - Activity Logs
- FR-3.1: Stream logs/backend.log in real-time (tail -f or similar)
- FR-3.2: Position in top-right quadrant
- FR-3.3: Show colored output if logs support ANSI colors
- FR-3.4: Auto-scroll to latest entries
- FR-3.5: Consider alternative: parse activity tracker events for cleaner output

#### FR-4: Pane 3 - Vim File Browser
- FR-4.1: Open vim with netrw or NERDTree at the output directory
- FR-4.2: Position in bottom-left quadrant
- FR-4.3: Allow user to navigate and view generated files
- FR-4.4: Support configurable output directory path
- FR-4.5: Default to ensemble_ui/output directory

#### FR-5: Pane 4 - Master Task List
- FR-5.1: Display a continuously-updated list of all swarm tasks
- FR-5.2: Position in bottom-right quadrant
- FR-5.3: Tasks grouped by status:
  - ✅ Completed tasks
  - 🔄 In-progress tasks
  - ⏳ Upcoming/pending tasks
- FR-5.4: Each task shown as short topic (<10 words)
- FR-5.5: Auto-refresh as swarm updates task states
- FR-5.6: Source task data from:
  - ~/.ensemble/projects/{project_id}/project.json
  - Activity tracker events
  - Project tracking system

#### FR-6: Task List Update Mechanism
- FR-6.1: Create a task list watcher script that monitors project state
- FR-6.2: Update display every 1-2 seconds (configurable)
- FR-6.3: Tasks updated by swarm agents via project_tracking tool
- FR-6.4: Show task count summary at top (e.g., "3 done | 2 active | 5 pending")

### Non-Functional Requirements

#### NFR-1: Usability
- NFR-1.1: Single command to launch the entire dashboard
- NFR-1.2: Clear documentation on how to navigate between panes (Ctrl-b + arrow keys)
- NFR-1.3: Reasonable default pane sizes (equal 50/50 splits)

#### NFR-2: Compatibility
- NFR-2.1: Work with tmux 3.0+ (modern features like -Z for zoom)
- NFR-2.2: Work on macOS and Linux
- NFR-2.3: Support both bash and zsh shells

#### NFR-3: Configurability
- NFR-3.1: Allow customization of session name
- NFR-3.2: Allow customization of output directory
- NFR-3.3: Allow customization of log file path
- NFR-3.4: Allow customization of project ID for task tracking

## Technical Architecture

### Components

1. **start_monitor.sh** - Main script to launch tmux dashboard
   - Creates tmux session
   - Sets up 2x2 layout
   - Launches appropriate commands in each pane

2. **stop_monitor.sh** - Script to cleanly stop the dashboard
   - Kills tmux session
   - Cleans up any background processes

3. **task_watcher.py** (or .sh) - Script for Pane 4
   - Watches ~/.ensemble/projects/ for changes
   - Parses project.json for task status
   - Formats and displays task list
   - Refreshes on interval or file change (inotify/fswatch)

### Integration Points

1. **Project Tracking System** (existing)
   - Location: ~/.ensemble/projects/{project_id}/project.json
   - Contains: tasks with status (todo, in_progress, completed, blocked)
   - Updated by: agents via project_tracking tool

2. **Activity Tracker** (existing)
   - Location: src/runtime/agents/activity_tracker.py
   - Events: TASK_UPDATE, AGENT_STARTED, AGENT_COMPLETED
   - Could emit events to a log file for task_watcher to consume

3. **Backend Logs** (existing)
   - Location: logs/backend.log
   - Contains: Agent execution logs, errors, status updates

## User Interface Layout

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│                                     │                                     │
│     PANE 1: Claude CLI              │     PANE 2: Activity Logs           │
│                                     │                                     │
│     $ ensemble run --problem "..."  │     [12:34:56] Agent started: ED    │
│     > Thinking...                   │     [12:34:57] Tool: spawn_agent    │
│     > Created requirements.md       │     [12:35:01] Agent: DevManager    │
│                                     │     [12:35:02] Writing: arch.md     │
│                                     │                                     │
├─────────────────────────────────────┼─────────────────────────────────────┤
│                                     │                                     │
│     PANE 3: Vim File Browser        │     PANE 4: Task List               │
│                                     │                                     │
│     " Press ? for help              │     ═══ ENSEMBLE TASKS ═══          │
│     ..                              │     3 done | 2 active | 5 pending   │
│     requirements.md                 │                                     │
│     architecture.md                 │     ✅ Create requirements doc      │
│     milestones.md                   │     ✅ Design architecture          │
│     src/                            │     ✅ Break down milestones        │
│       main.py                       │     🔄 Implement backend API        │
│       tests/                        │     🔄 Write unit tests             │
│                                     │     ⏳ Implement frontend           │
│                                     │     ⏳ Integration tests            │
│                                     │     ⏳ Documentation                │
│                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

## Implementation Milestones

### Milestone 1: Basic Tmux Layout (MVP)
- Create start_monitor.sh with 2x2 layout
- Pane 1: Simple shell (placeholder for CLI)
- Pane 2: tail -f on backend.log
- Pane 3: vim opened to output directory
- Pane 4: Simple watch command on project file

**Deliverables:**
- scripts/deployment/start_monitor.sh
- scripts/deployment/stop_monitor.sh
- Documentation in README

### Milestone 2: Task Watcher Script
- Create task_watcher.py to parse project.json
- Formatted output with status icons
- Auto-refresh on interval
- Summary counts

**Deliverables:**
- scripts/monitoring/task_watcher.py
- Integration with tmux pane 4

### Milestone 3: Full Integration
- Connect Claude CLI to Pane 1
- Enhanced log formatting for Pane 2
- Polish and documentation

**Deliverables:**
- Updated start_monitor.sh with CLI integration
- User documentation
- Example usage in README

## Success Criteria

1. **One-command launch**: Run `./scripts/deployment/start_monitor.sh` and get full dashboard
2. **Task visibility**: See all tasks update in real-time as swarm operates
3. **File access**: Easily browse and view output files without leaving tmux
4. **Log streaming**: See activity logs scroll in real-time
5. **CLI access**: Interact with Claude CLI while monitoring

## Assumptions

1. User has tmux installed (v3.0+)
2. User has vim installed
3. Project uses ~/.ensemble/projects/ for project tracking
4. Activity logs are written to logs/backend.log
5. User is familiar with basic tmux navigation (Ctrl-b + arrows)

## Out of Scope

1. Custom tmux theme/styling (use user's existing tmux config)
2. Mouse support configuration (rely on user's tmux settings)
3. Multiple project monitoring (single project at a time)
4. Historical task analytics (just current state)
5. GUI-based monitoring (this is terminal-only)

## Dependencies

### External
- tmux >= 3.0
- vim (with netrw built-in)
- Python 3.8+ (for task_watcher.py)
- bash or zsh

### Internal
- Project tracking system (~/.ensemble/projects/)
- Activity tracker (src/runtime/agents/activity_tracker.py)
- Existing deployment scripts (scripts/deployment/)

## Open Questions

1. Should task_watcher use filesystem watching (fswatch/inotify) or polling?
   - **Decision**: Start with polling (simpler), optimize later if needed

2. Should Pane 2 show raw logs or parsed activity events?
   - **Decision**: Start with raw logs, consider parsed view as enhancement

3. How should the CLI pane be started - automatically run a command or wait for user?
   - **Decision**: Start with shell ready for user to run command, consider auto-start option
