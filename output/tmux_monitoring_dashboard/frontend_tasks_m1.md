# Frontend Tasks - Milestone 1: Basic Tmux Layout (MVP)

## Overview
This milestone creates a functional 2x2 tmux layout with basic monitoring capabilities. The focus is on establishing the foundational architecture using shell scripts and standard Unix tools for session management, layout creation, and basic monitoring.

## User Flow Summary
1. Developer runs `./scripts/deployment/start_monitor.sh` 
2. Tmux session launches with 2x2 layout automatically configured
3. Four panes display: CLI shell, log stream, file browser, and basic task watch
4. Developer can interact with all panes while monitoring real-time activity
5. Developer runs `./scripts/deployment/stop_monitor.sh` for clean shutdown

## Task Breakdown

### 1. Session Management Foundation
**Task**: `session-launcher`
**Description**: Create main startup script that handles tmux session creation and configuration
**Acceptance Criteria**:
- Single command `./scripts/deployment/start_monitor.sh` launches complete dashboard
- Creates named tmux session (ensemble-monitor-{project_id})
- Handles existing session detection and cleanup
- Sets up project-specific environment variables
- Provides clear feedback on startup success/failure

**Dependencies**: None
**Complexity**: Medium
**Files Created**: `scripts/deployment/start_monitor.sh`

### 2. Tmux Layout Configuration
**Task**: `tmux-layout-setup`  
**Description**: Configure 2x2 pane layout with proper sizing and navigation
**Acceptance Criteria**:
- Creates exactly 4 panes in 2x2 grid layout
- Each pane has appropriate size allocation (50/50 split)
- Panes are numbered and accessible (0-3)
- Layout persists and doesn't break on terminal resize
- Supports minimum terminal size of 80x24

**Dependencies**: session-launcher
**Complexity**: Simple
**Files Created**: Layout configuration within start_monitor.sh

### 3. Interactive Shell Pane (Pane 1)
**Task**: `shell-pane-setup`
**Description**: Configure top-left pane as interactive shell environment
**Acceptance Criteria**:
- Pane 1 opens to project root directory 
- Shell prompt is ready for user input
- Environment variables are properly set (PROJECT_ID, OUTPUT_DIR)
- User can run commands immediately after dashboard start
- Shell history is preserved within session

**Dependencies**: tmux-layout-setup
**Complexity**: Simple
**Files Created**: Configuration within start_monitor.sh

### 4. Log Streaming Pane (Pane 2)
**Task**: `log-stream-pane`
**Description**: Set up real-time log streaming in top-right pane
**Acceptance Criteria**:
- Automatically starts `tail -f backend.log` in pane 2
- Shows last 50 lines of log on startup
- Updates in real-time as new log entries appear
- Handles missing log file gracefully with informative message
- Log file path is configurable via command line option

**Dependencies**: tmux-layout-setup  
**Complexity**: Simple
**Files Created**: Log streaming configuration within start_monitor.sh

### 5. File Browser Pane (Pane 3)
**Task**: `file-browser-pane`
**Description**: Configure bottom-left pane with vim for file navigation
**Acceptance Criteria**:
- Opens vim in project output directory
- Shows directory listing on startup (netrw explorer)
- User can navigate and edit files immediately
- Falls back to `less` if vim is not available
- Directory path is configurable via command line option

**Dependencies**: tmux-layout-setup
**Complexity**: Simple
**Files Created**: File browser configuration within start_monitor.sh

### 6. Basic Task Monitoring Pane (Pane 4)
**Task**: `basic-task-watch`
**Description**: Set up simple task monitoring using watch command
**Acceptance Criteria**:
- Uses `watch` command to display project.json contents every 2 seconds
- Shows raw JSON in readable format (pretty-printed if possible)
- Handles missing project.json file with clear message
- Updates automatically as tasks change
- Provides visual indication of last update time

**Dependencies**: tmux-layout-setup
**Complexity**: Simple  
**Files Created**: Task watch configuration within start_monitor.sh

### 7. Clean Shutdown Script
**Task**: `shutdown-script`
**Description**: Create script for graceful dashboard shutdown
**Acceptance Criteria**:
- Command `./scripts/deployment/stop_monitor.sh` cleanly stops dashboard
- Terminates tmux session without leaving orphan processes
- Accepts optional session name parameter
- Provides confirmation message on successful shutdown
- Handles case where session doesn't exist gracefully

**Dependencies**: session-launcher
**Complexity**: Simple
**Files Created**: `scripts/deployment/stop_monitor.sh`

### 8. Directory Structure Setup
**Task**: `directory-structure`
**Description**: Create required directory structure and empty placeholder files
**Acceptance Criteria**:
- Creates all necessary directories as per architecture
- Includes README.md placeholder in docs/
- Creates empty config/ directory for future tmux configuration
- All scripts have proper executable permissions
- Directory structure matches architecture document exactly

**Dependencies**: None
**Complexity**: Simple
**Files Created**: Directory structure, placeholder files

### 9. Command Line Argument Parsing
**Task**: `cli-argument-parsing`
**Description**: Add command line option support to start_monitor.sh
**Acceptance Criteria**:
- Supports --project-id option with validation
- Supports --session-name option for custom session naming
- Supports --log-file option for custom log file path
- Supports --output-dir option for custom output directory
- Provides --help option with usage information
- Validates all input parameters and shows clear error messages

**Dependencies**: session-launcher
**Complexity**: Medium
**Files Created**: Enhanced start_monitor.sh with argument parsing

### 10. Session Persistence and Recovery
**Task**: `session-persistence`
**Description**: Handle session persistence and reconnection scenarios
**Acceptance Criteria**:
- Detects existing session before creating new one
- Offers to attach to existing session or create new one
- Preserves session state if terminal disconnects
- Handles multiple concurrent projects with separate sessions
- Session cleanup on unexpected termination

**Dependencies**: session-launcher, shutdown-script
**Complexity**: Medium
**Files Created**: Session management logic within scripts

### 11. Basic Error Handling
**Task**: `error-handling`
**Description**: Implement comprehensive error handling for all components
**Acceptance Criteria**:
- Checks for tmux availability before proceeding
- Validates project directory exists and is accessible
- Handles missing log files gracefully
- Provides clear error messages for common failure scenarios
- Exits cleanly on any critical error with proper cleanup

**Dependencies**: All previous tasks
**Complexity**: Medium  
**Files Created**: Error handling throughout all scripts

### 12. Basic Documentation
**Task**: `basic-documentation`
**Description**: Create minimal documentation for Milestone 1 usage
**Acceptance Criteria**:
- README.md with basic usage instructions
- Documents all command line options
- Includes troubleshooting section for common issues
- Provides examples for typical usage scenarios
- Clear system requirements and dependencies

**Dependencies**: All functional tasks complete
**Complexity**: Simple
**Files Created**: `docs/README.md`, updated architecture documentation

## Implementation Order

### Phase 1: Foundation (Tasks 1, 8)
1. directory-structure
2. session-launcher

### Phase 2: Layout Setup (Tasks 2-6)  
3. tmux-layout-setup
4. shell-pane-setup
5. log-stream-pane
6. file-browser-pane
7. basic-task-watch

### Phase 3: Management (Tasks 7, 10, 11)
8. shutdown-script
9. session-persistence
10. error-handling

### Phase 4: Polish (Tasks 9, 12)
11. cli-argument-parsing
12. basic-documentation

## Dependencies Summary
- **No dependencies**: directory-structure, session-launcher
- **Requires tmux session**: All pane setup tasks (3-6)
- **Requires core functionality**: shutdown-script, error-handling, documentation
- **Enhancement tasks**: cli-argument-parsing, session-persistence

## Technical Notes

### Shell Script Structure
```bash
#!/bin/bash
# scripts/deployment/start_monitor.sh
# - Argument parsing and validation
# - Environment setup
# - Tmux session creation
# - Pane configuration and command execution
# - Error handling and cleanup
```

### Tmux Commands Used
- `tmux new-session -d -s session_name`
- `tmux split-window -h -t session_name`
- `tmux split-window -v -t session_name:0`
- `tmux send-keys -t session_name:pane 'command' C-m`
- `tmux attach-session -t session_name`

### File Permissions
All shell scripts need executable permissions: `chmod +x scripts/deployment/*.sh`

## Success Criteria
- Complete 2x2 tmux dashboard launches with single command
- All 4 panes function as specified
- Real-time log monitoring works
- File browser allows navigation and editing
- Clean shutdown preserves system state
- Ready for Milestone 2 task monitoring enhancements

## Testing Strategy
- Manual testing on macOS and Linux
- Terminal size compatibility testing
- Session creation/destruction cycles
- Error condition testing (missing files, permission issues)
- Multiple project support validation