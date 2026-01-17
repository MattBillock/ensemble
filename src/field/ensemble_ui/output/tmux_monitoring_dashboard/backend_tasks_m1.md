# Backend Tasks - Basic Tmux Layout (MVP)

## Overview
This milestone focuses on creating the foundational tmux-based monitoring dashboard with basic functionality. The goal is to establish the 2x2 layout and implement core components without complex dynamic features.

## Task Breakdown

### Task 1: Core Tmux Session Management
**Description**: Create the main script that initializes and manages the tmux monitoring session
**Priority**: Critical Path - Foundation
**Complexity**: Simple

**Acceptance Criteria**:
- Script creates tmux session named "ensemble-monitor" (configurable)
- Implements 2x2 grid layout (4 equal panes)
- Handles existing session detection and attachment
- Provides clean session termination
- Cross-platform compatibility (macOS/Linux)

**Implementation Requirements**:
- File: `scripts/deployment/start_monitor.sh`
- Bash script with proper error handling
- Environment variables for configuration
- Session persistence on disconnect
- Tmux version compatibility check (3.0+)

**Dependencies**: None

---

### Task 2: Session Termination Script
**Description**: Create companion script for clean dashboard shutdown
**Priority**: High - Operational
**Complexity**: Simple

**Acceptance Criteria**:
- Cleanly kills tmux session by name
- Handles case where session doesn't exist
- Provides confirmation message
- No orphaned processes

**Implementation Requirements**:
- File: `scripts/deployment/stop_monitor.sh`
- Bash script with session detection
- Graceful process termination
- User feedback on success/failure

**Dependencies**: Task 1 (session management patterns)

---

### Task 3: Log Streaming Component
**Description**: Implement real-time log streaming for Pane 2
**Priority**: High - Core Feature
**Complexity**: Simple

**Acceptance Criteria**:
- Streams `logs/backend.log` in real-time using `tail -f`
- Auto-scrolls to show latest entries
- Handles log file rotation gracefully
- Preserves ANSI color codes if present
- Configurable log file path

**Implementation Requirements**:
- Integrated into start_monitor.sh
- Fallback for missing log file
- Optional log colorization
- Buffer management for large files

**Dependencies**: Task 1 (tmux session structure)

---

### Task 4: File Browser Integration
**Description**: Configure vim-based file browser for Pane 3
**Priority**: Medium - User Experience
**Complexity**: Simple

**Acceptance Criteria**:
- Opens vim with netrw in output directory
- Navigable file tree interface
- Supports configurable output directory path
- Defaults to `ensemble_ui/output` directory
- Works with standard vim installation

**Implementation Requirements**:
- Vim launched with netrw directory browsing
- Environment variable for output path
- Error handling for missing directories
- Basic vim configuration for file browsing

**Dependencies**: Task 1 (pane configuration)

---

### Task 5: Basic Task Display
**Description**: Create simple task list viewer for Pane 4
**Priority**: High - Core Feature
**Complexity**: Medium

**Acceptance Criteria**:
- Displays project tasks from `~/.ensemble/projects/{project_id}/project.json`
- Shows task status with basic icons (✅ ⏳ 🔄)
- Groups tasks by status (completed, in-progress, pending)
- Updates every 2 seconds via watch command
- Handles missing project file gracefully

**Implementation Requirements**:
- Simple script using `watch` + `jq` or Python
- JSON parsing from project tracking system
- Basic text formatting for tmux pane
- Error handling for malformed JSON
- Configurable project ID

**Dependencies**: Task 1 (pane structure)

---

### Task 6: Configuration Management
**Description**: Implement configuration system for dashboard customization
**Priority**: Medium - Flexibility
**Complexity**: Simple

**Acceptance Criteria**:
- Environment variables for all configurable options
- Default values for all settings
- Configuration validation
- Documentation of all options

**Configuration Options**:
- `ENSEMBLE_SESSION_NAME`: Tmux session name (default: "ensemble-monitor")
- `ENSEMBLE_PROJECT_ID`: Project to monitor (required)
- `ENSEMBLE_OUTPUT_DIR`: Output directory path (default: "ensemble_ui/output")
- `ENSEMBLE_LOG_PATH`: Log file location (default: "logs/backend.log")

**Implementation Requirements**:
- Centralized configuration loading
- Input validation and sanitization
- Clear error messages for missing required config
- Documentation in script comments

**Dependencies**: All other tasks (configuration integration)

---

### Task 7: Basic Error Handling
**Description**: Implement comprehensive error handling across all scripts
**Priority**: Medium - Robustness
**Complexity**: Simple

**Acceptance Criteria**:
- Validates all dependencies (tmux, vim, required files)
- Provides helpful error messages
- Graceful degradation when possible
- Exit codes for script automation
- Logs errors appropriately

**Error Scenarios to Handle**:
- Missing tmux installation
- Insufficient tmux version
- Missing project files
- Permission issues
- Invalid configuration

**Implementation Requirements**:
- Dependency checking functions
- Standardized error reporting
- User-friendly error messages
- Proper exit codes

**Dependencies**: All implementation tasks (error handling integration)

---

### Task 8: Documentation and Usage Guide
**Description**: Create comprehensive documentation for the monitoring dashboard
**Priority**: Medium - User Experience
**Complexity**: Simple

**Acceptance Criteria**:
- Clear installation instructions
- Usage examples with screenshots/ASCII
- Configuration reference
- Troubleshooting guide
- Navigation help (tmux commands)

**Documentation Requirements**:
- README.md with getting started guide
- Configuration reference
- Tmux navigation quick reference
- Common issues and solutions
- Example workflows

**Dependencies**: All implementation tasks (complete system to document)

## Implementation Order

### Phase 1: Foundation (Tasks 1-2)
1. Task 1: Core Tmux Session Management
2. Task 2: Session Termination Script

### Phase 2: Core Features (Tasks 3-5)
3. Task 3: Log Streaming Component
4. Task 4: File Browser Integration  
5. Task 5: Basic Task Display

### Phase 3: Polish (Tasks 6-8)
6. Task 6: Configuration Management
7. Task 7: Basic Error Handling
8. Task 8: Documentation and Usage Guide

## Success Criteria for Milestone

✅ **Single Command Launch**: `./scripts/deployment/start_monitor.sh` creates full dashboard
✅ **2x2 Layout**: Four functional panes as specified
✅ **Live Log Streaming**: Real-time backend log display
✅ **File Browser**: Navigate output files with vim/netrw
✅ **Task List**: Basic display of project tasks with status
✅ **Clean Shutdown**: `./scripts/deployment/stop_monitor.sh` terminates cleanly
✅ **Cross-Platform**: Works on macOS and Linux
✅ **Documentation**: Clear usage instructions

## Technical Notes

### File Structure
```
scripts/
  deployment/
    start_monitor.sh    # Main launcher
    stop_monitor.sh     # Clean shutdown
  monitoring/
    (Future: task_watcher.py for enhanced features)
```

### Key Technologies
- **Shell Scripting**: Bash for tmux orchestration
- **Tmux**: Session and pane management
- **System Tools**: tail, watch, jq (for JSON parsing)
- **Text Editor**: vim with netrw
- **Configuration**: Environment variables

### Integration Points
- **Project Tracking**: `~/.ensemble/projects/{project_id}/project.json`
- **Backend Logs**: `logs/backend.log`
- **Output Directory**: `ensemble_ui/output/` (configurable)
- **Tmux Session**: Persistent, named session for monitoring

This task breakdown provides a solid foundation for the tmux monitoring dashboard while keeping the MVP scope focused and achievable.