# Tmux Monitoring Dashboard - Architecture Document

## Overview

This document describes the technical architecture for the Tmux Monitoring Dashboard, a 2x2 grid terminal interface for monitoring the ensemble agent swarm.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TMUX SESSION (ensemble-monitor)                   │
├─────────────────────────────────┬───────────────────────────────────────┤
│         PANE 1 (top-left)       │         PANE 2 (top-right)            │
│         Claude CLI Shell        │         Log Streamer                  │
│                                 │         (tail -f backend.log)         │
│         Interactive shell       │                                       │
│         for running ensemble    │         Real-time log output          │
│         commands                │         with ANSI color support       │
├─────────────────────────────────┼───────────────────────────────────────┤
│         PANE 3 (bottom-left)    │         PANE 4 (bottom-right)         │
│         Vim File Browser        │         Task Watcher                  │
│                                 │         (task_watcher.py)             │
│         netrw file navigation   │                                       │
│         in output directory     │         Reads ~/.ensemble/projects/   │
│                                 │         Displays task status          │
└─────────────────────────────────┴───────────────────────────────────────┘
```

## Component Design

### 1. Session Management Scripts

#### start_monitor.sh
**Purpose:** Launch and configure the tmux dashboard

**Location:** `scripts/monitoring/start_monitor.sh`

**Design:**
```
┌─────────────────────────────────────┐
│         start_monitor.sh            │
├─────────────────────────────────────┤
│ Inputs:                             │
│ - SESSION_NAME (default: ensemble-  │
│   monitor)                          │
│ - OUTPUT_DIR (default: pwd/output)  │
│ - LOG_FILE (default: backend.log)   │
│ - PROJECT_ID (optional)             │
├─────────────────────────────────────┤
│ Flow:                               │
│ 1. Check if session exists          │
│ 2. If exists, attach                │
│ 3. If not, create new session       │
│ 4. Split into 2x2 grid              │
│ 5. Launch commands in each pane     │
│ 6. Select Pane 1 (CLI)              │
│ 7. Attach to session                │
└─────────────────────────────────────┘
```

**Interface:**
```bash
./start_monitor.sh [OPTIONS]
  -n, --name        Session name (default: ensemble-monitor)
  -o, --output-dir  Output directory for vim (default: current dir)
  -l, --log-file    Log file to tail (default: backend.log)
  -p, --project-id  Project ID for task tracking
  -h, --help        Show help
```

#### stop_monitor.sh
**Purpose:** Cleanly terminate the monitoring session

**Location:** `scripts/monitoring/stop_monitor.sh`

**Design:**
```
┌─────────────────────────────────────┐
│         stop_monitor.sh             │
├─────────────────────────────────────┤
│ Inputs:                             │
│ - SESSION_NAME (default: ensemble-  │
│   monitor)                          │
├─────────────────────────────────────┤
│ Flow:                               │
│ 1. Check if session exists          │
│ 2. Kill session if exists           │
│ 3. Report status                    │
└─────────────────────────────────────┘
```

### 2. Task Watcher Script

#### task_watcher.py
**Purpose:** Monitor and display task status from project tracking

**Location:** `scripts/monitoring/task_watcher.py`

**Design:**
```
┌─────────────────────────────────────────────────────────┐
│                    task_watcher.py                       │
├─────────────────────────────────────────────────────────┤
│ Classes:                                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ TaskWatcher                                         │ │
│ │ - project_id: str                                   │ │
│ │ - refresh_interval: float                           │ │
│ │ - projects_dir: Path                                │ │
│ │ + load_project() -> dict                            │ │
│ │ + get_tasks() -> List[Task]                         │ │
│ │ + format_output() -> str                            │ │
│ │ + run() -> None                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Task (dataclass)                                    │ │
│ │ - id: str                                           │ │
│ │ - title: str                                        │ │
│ │ - status: TaskStatus                                │ │
│ │ - assigned_to: Optional[str]                        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ TaskStatus (Enum)                                   │ │
│ │ - TODO = "todo"                                     │ │
│ │ - IN_PROGRESS = "in_progress"                       │ │
│ │ - COMPLETED = "completed"                           │ │
│ │ - BLOCKED = "blocked"                               │ │
│ │ - CANCELLED = "cancelled"                           │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Flow:                                                    │
│ 1. Parse command line args                               │
│ 2. Initialize TaskWatcher                                │
│ 3. Enter main loop:                                      │
│    a. Clear screen                                       │
│    b. Load project.json                                  │
│    c. Parse tasks                                        │
│    d. Format and print output                            │
│    e. Sleep for refresh_interval                         │
│    f. Repeat                                             │
└─────────────────────────────────────────────────────────┘
```

**Output Format:**
```
═══ ENSEMBLE TASKS ═══
3 done | 2 active | 5 pending

✅ Create requirements doc
✅ Design architecture
✅ Break down milestones
🔄 Implement backend API
🔄 Write unit tests
⏳ Implement frontend
⏳ Integration tests
⏳ Documentation

Last updated: 12:34:56
```

**Interface:**
```bash
python3 task_watcher.py [OPTIONS]
  -p, --project-id   Project ID to monitor (required unless --all)
  -r, --refresh      Refresh interval in seconds (default: 2)
  -d, --projects-dir Projects directory (default: ~/.ensemble/projects)
  --all              Show latest project if no ID specified
  -h, --help         Show help
```

## Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Agent Swarm    │────▶│ project.json    │────▶│ task_watcher.py │
│ (updates tasks) │     │ (data store)    │     │ (reads & shows) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                    ~/.ensemble/projects/
                    └── {project_id}/
                        └── project.json
```

## File Structure

```
ensemble/
├── scripts/
│   └── monitoring/
│       ├── start_monitor.sh      # Launch dashboard
│       ├── stop_monitor.sh       # Stop dashboard
│       └── task_watcher.py       # Task status display
└── docs/
    └── monitoring-dashboard.md   # User documentation
```

## Integration Points

### 1. Project Tracking System
- **Location:** `~/.ensemble/projects/{project_id}/project.json`
- **Format:** JSON with tasks array containing status, title, description
- **Access:** Read-only by task_watcher.py

### 2. Backend Logs
- **Location:** `logs/backend.log` or `./backend.log`
- **Access:** Read via `tail -f`
- **Format:** Text with ANSI color codes

### 3. Output Directory
- **Location:** Configurable, default is project output directory
- **Access:** Read via vim/netrw

## Configuration

### Environment Variables (Optional)
```bash
ENSEMBLE_MONITOR_SESSION   # Default session name
ENSEMBLE_PROJECTS_DIR      # Path to projects directory
ENSEMBLE_LOG_FILE          # Path to log file
```

### Tmux Layout Configuration
```
┌────────────────────┬────────────────────┐
│       50%          │        50%         │
│                    │                    │
│    Pane 0 (CLI)    │  Pane 1 (Logs)     │
│       50%          │        50%         │
├────────────────────┼────────────────────┤
│       50%          │        50%         │
│                    │                    │
│  Pane 2 (Vim)      │  Pane 3 (Tasks)    │
│       50%          │        50%         │
└────────────────────┴────────────────────┘
```

## Error Handling

### start_monitor.sh
1. **tmux not installed:** Print error, exit with instructions
2. **Session exists:** Attach instead of creating new
3. **Invalid directory:** Print warning, use current directory
4. **Log file missing:** Create empty file or print warning

### task_watcher.py
1. **Project not found:** Display "No project selected" message
2. **Invalid JSON:** Display parse error, continue polling
3. **File permissions:** Display permission error message
4. **KeyboardInterrupt:** Clean exit

## Security Considerations

1. **Read-only access:** task_watcher.py only reads project files
2. **No network access:** All operations are local filesystem
3. **User permissions:** Scripts run with user's permissions

## Testing Strategy

### Unit Tests (task_watcher.py)
- Test JSON parsing with various inputs
- Test task status formatting
- Test error handling for missing files

### Integration Tests
- Test start_monitor.sh creates correct layout
- Test stop_monitor.sh cleanly kills session
- Test end-to-end with mock project file

### Manual Testing Checklist
- [ ] Launch dashboard on macOS
- [ ] Launch dashboard on Linux
- [ ] Test with bash shell
- [ ] Test with zsh shell
- [ ] Verify all panes function
- [ ] Test task updates display correctly

## Future Enhancements (Out of Scope)

1. **Parsed activity logs:** Transform raw logs to structured events
2. **Multi-project support:** Monitor multiple projects simultaneously
3. **Task filtering:** Filter by status, assignee, etc.
4. **Notifications:** Alert on task completion or errors
5. **Custom themes:** Configurable colors and layout
