# Tmux Monitoring Dashboard - Architecture Proposal

## Architecture Overview

The Tmux Monitoring Dashboard is a **terminal-based monitoring system** that provides real-time visibility into ensemble agent swarm operations through a 2x2 tmux layout. The architecture follows a **modular shell-script design** with Python components for data processing.

### Architecture Pattern
- **Composition-based approach**: Combines standard Unix tools (tmux, vim, tail) with custom monitoring scripts
- **Event-driven display**: Real-time updates through file watching and periodic polling
- **Session-based persistence**: Tmux session management for reliable operation

### Design Rationale
This architecture prioritizes **developer experience** and **operational simplicity** over complex frameworks. By leveraging mature Unix tools and lightweight scripts, we achieve:
- Zero deployment complexity (runs anywhere tmux exists)
- Immediate visual feedback for development workflows
- Low resource overhead
- High reliability through proven tools

## Tech Stack

### Core Technologies
- **Shell Scripting (Bash)**: Session management, layout creation, process orchestration
  - *Why*: Universal availability, excellent for process management, tmux integration
  - *Alternatives considered*: Go/Rust binaries (overkill for this scope), Python (poor tmux integration)

- **Python 3.8+**: Data processing, JSON parsing, formatted display
  - *Why*: Excellent JSON handling, cross-platform, already used in ensemble system
  - *Alternatives considered*: jq + awk (limited formatting), Node.js (additional dependency)

- **Tmux 3.0+**: Terminal multiplexing, session management, layout control
  - *Why*: Industry standard for terminal sessions, excellent layout control, session persistence
  - *Alternatives considered*: GNU Screen (less flexible), custom terminal UI (complex)

### Supporting Tools
- **Vim/Neovim**: File browsing and editing in dedicated pane
- **Unix utilities**: tail, watch, ps for system monitoring
- **Standard JSON**: Data exchange format for task tracking

### Dependencies
**Minimal by design**:
- tmux (required)
- Python 3.8+ (required) 
- vim (optional, fallback to less)
- Standard Unix tools (tail, watch, ps)

## System Components

### 1. Session Management Layer
**File**: `scripts/deployment/start_monitor.sh`
**Responsibility**: 
- Create and configure tmux session
- Set up 2x2 pane layout
- Launch monitoring components in each pane
- Handle session naming and cleanup

**File**: `scripts/deployment/stop_monitor.sh`
**Responsibility**:
- Clean session shutdown
- Process cleanup
- Resource deallocation

### 2. Task Monitoring Engine
**File**: `scripts/monitoring/task_watcher.py`
**Responsibility**:
- Parse project.json from ensemble tracking system
- Format task status with visual indicators
- Provide real-time updates (1-2 second intervals)
- Handle error states gracefully

**Data Flow**:
```
~/.ensemble/projects/{project_id}/project.json 
→ task_watcher.py (parse/format) 
→ Bottom-right pane (display)
```

### 3. Log Streaming Component
**Implementation**: Native `tail -f` command
**Responsibility**:
- Stream backend.log in real-time
- Display in top-right pane
- No custom processing (raw log visibility)

### 4. File Browser Component
**Implementation**: Vim opened to project output directory
**Responsibility**:
- Navigate project output files
- Allow editing/viewing of generated content
- Provide familiar interface for file operations

## File/Directory Structure

```
tmux_monitoring_dashboard/
├── architecture.md                    # This document
├── milestone_plan.md                  # Development roadmap
├── scripts/
│   ├── deployment/
│   │   ├── start_monitor.sh           # Main launcher script
│   │   ├── stop_monitor.sh            # Clean shutdown script
│   │   └── config/
│   │       └── tmux.conf              # Custom tmux configuration
│   └── monitoring/
│       ├── task_watcher.py            # Python task status monitor
│       └── log_formatter.sh           # Optional log processing
├── docs/
│   ├── README.md                      # User documentation
│   ├── troubleshooting.md            # Common issues and solutions
│   └── customization.md              # Configuration options
└── tests/
    ├── test_task_watcher.py          # Unit tests for Python components
    └── integration_tests.sh          # End-to-end testing
```

## Data Model

### Project Tracking Integration
The system leverages the existing ensemble project tracking structure:

```json
// ~/.ensemble/projects/{project_id}/project.json
{
  "id": "project_id",
  "name": "Project Name",
  "tasks": [
    {
      "id": "task_1",
      "status": "completed|in_progress|todo|blocked|cancelled",
      "description": "Task description",
      "assigned_to": "agent_type"
    }
  ],
  "notes": [...]
}
```

### Display State Model
```python
# task_watcher.py internal state
{
  "project_name": str,
  "task_counts": {
    "completed": int,
    "in_progress": int, 
    "todo": int,
    "blocked": int
  },
  "formatted_tasks": [
    {
      "icon": "✅|⚡|⏳|🚫",
      "status": str,
      "description": str,
      "agent": str
    }
  ],
  "last_updated": timestamp
}
```

## Pane Layout Design

```
┌─────────────────┬─────────────────┐
│ Pane 1          │ Pane 2          │
│ Interactive CLI │ Log Stream      │
│ (Claude CLI)    │ (tail -f)       │
├─────────────────┼─────────────────┤
│ Pane 3          │ Pane 4          │
│ File Browser    │ Task Monitor    │
│ (vim)           │ (task_watcher)  │
└─────────────────┴─────────────────┘
```

**Pane Responsibilities**:
- **Pane 1 (top-left)**: Interactive shell for Claude CLI and manual commands
- **Pane 2 (top-right)**: Real-time log streaming from backend.log
- **Pane 3 (bottom-left)**: File navigation and editing for project outputs
- **Pane 4 (bottom-right)**: Formatted task status display with live updates

## API Design

### Command Line Interface
```bash
# Start monitoring dashboard
./scripts/deployment/start_monitor.sh [options]

Options:
  --project-id ID      Specific project to monitor (default: detect from cwd)
  --session-name NAME  Custom tmux session name (default: ensemble-monitor)
  --log-file PATH      Log file to monitor (default: backend.log)
  --output-dir PATH    Output directory for file browser (default: ./output)

# Stop dashboard
./scripts/deployment/stop_monitor.sh [session-name]
```

### Python Script Interface
```bash
# Task watcher (run internally by tmux)
python scripts/monitoring/task_watcher.py --project-id ID [--refresh-rate SECONDS]
```

## Deployment Strategy

### Local Development
1. **Direct execution**: Scripts run directly from project directory
2. **No installation required**: Uses system tools and Python
3. **Configuration**: Environment variables and command-line options

### Environment Requirements
- **macOS/Linux**: Primary targets with tmux support
- **Terminal**: Any terminal that supports tmux (iTerm2, Terminal.app, xterm)
- **Permissions**: Read access to ensemble project directory, write access to tmux socket

### Session Management
```bash
# Sessions are named and managed
tmux new-session -d -s ensemble-monitor-{project_id}

# Multiple projects can have separate sessions
ensemble-monitor-project1
ensemble-monitor-project2
```

### Configuration Options
Environment variables for customization:
- `TMUX_MONITOR_SESSION`: Session name prefix
- `TMUX_MONITOR_REFRESH`: Update interval (default: 2s)
- `TMUX_MONITOR_LOG_LINES`: Initial log lines to display (default: 50)

## Testing Strategy

### Unit Testing
- **Python components**: pytest for task_watcher.py logic
- **Mock project.json files**: Test various task states and edge cases
- **Error handling**: Missing files, malformed JSON, permission issues

### Integration Testing
- **Full session creation**: Verify all panes start correctly
- **Cross-platform**: Test on macOS and Linux
- **Tmux versions**: Validate compatibility with tmux 3.0+
- **Resource cleanup**: Ensure clean shutdown doesn't leave processes

### Manual Testing
- **User workflows**: Start/stop/restart scenarios
- **Performance**: Monitor resource usage with multiple projects
- **Visual verification**: Layout correctness across terminal sizes

### Testing Commands
```bash
# Run unit tests
python -m pytest tests/test_task_watcher.py

# Run integration tests
./tests/integration_tests.sh

# Performance test
./tests/performance_test.sh --duration 300 --projects 5
```

## Alternatives Considered

### 1. Web-Based Dashboard
**Rejected because**:
- Adds complexity (HTTP server, frontend framework)
- Breaks developer terminal workflow
- Requires network setup and port management
- Overkill for development monitoring

### 2. Native GUI Application
**Rejected because**:
- Platform-specific development required
- Much higher complexity for minimal benefit
- Doesn't integrate with terminal-based development
- Additional dependencies and deployment complexity

### 3. Rich Terminal UI (Python)
**Rejected because**:
- Single-process limitation (can't run Claude CLI simultaneously)
- Complex keyboard handling and layout management
- Less familiar interface than standard tmux
- Harder to customize and extend

### 4. Docker-Based Solution
**Rejected because**:
- Unnecessary containerization for local development tool
- Complicates file system access and integration
- Adds startup overhead and complexity
- Doesn't align with lightweight philosophy

## Risks and Mitigations

### Risk 1: Tmux Version Compatibility
**Impact**: Layout breaks or features don't work on older tmux versions
**Mitigation**: 
- Test on tmux 3.0+ (widely available)
- Graceful fallback for unsupported features
- Clear version requirements in documentation

### Risk 2: File System Permissions
**Impact**: Cannot read project files or logs
**Mitigation**:
- Check permissions at startup
- Provide clear error messages
- Fallback to read-only mode when possible

### Risk 3: Performance with Large Projects
**Impact**: Slow updates with hundreds of tasks
**Mitigation**:
- Efficient JSON parsing with streaming
- Configurable refresh rates
- Task display pagination if needed

### Risk 4: Terminal Size Limitations
**Impact**: Poor layout on small terminal windows
**Mitigation**:
- Minimum size requirements (80x24)
- Responsive layout adjustments
- Clear documentation of requirements

### Risk 5: Session Conflicts
**Impact**: Multiple monitoring sessions interfere
**Mitigation**:
- Project-specific session naming
- Session detection before creation
- Clean shutdown of existing sessions

## Open Questions

### 1. Log Filtering Preferences
**Question**: Should we implement log filtering/highlighting, or keep raw output?
**Options**: 
- Raw logs (simple, shows everything)
- Basic filtering (ERROR/INFO levels)
- Full parsing with color coding
**Recommendation**: Start with raw logs, add filtering in Milestone 3 based on user feedback

### 2. Task Display Detail Level
**Question**: How much task detail should be visible in limited pane space?
**Options**:
- Status + count only
- Status + brief description
- Full task details with scrolling
**Recommendation**: Status + brief description, with vim integration for full details

### 3. Multi-Project Support
**Question**: Should one dashboard monitor multiple projects simultaneously?
**Options**:
- Single project per session (current design)
- Tabbed interface for multiple projects
- Split display for comparing projects
**Recommendation**: Start with single project, evaluate multi-project need based on usage

## Key Decisions Summary

1. **Shell-script architecture** over frameworks for simplicity and reliability
2. **2x2 tmux layout** provides optimal information density
3. **Python for data processing** leverages existing ecosystem integration
4. **Real-time file watching** instead of polling for responsiveness
5. **Minimal dependencies** for maximum compatibility
6. **Project-specific sessions** for clean separation and management

This architecture balances simplicity, functionality, and developer experience while maintaining the flexibility to evolve based on user needs.