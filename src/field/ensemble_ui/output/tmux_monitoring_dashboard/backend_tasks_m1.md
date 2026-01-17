# Backend Tasks - Milestone 1: Basic Tmux Layout (MVP)

## Overview
This milestone creates the foundational tmux monitoring dashboard with a 2x2 layout providing real-time monitoring capabilities. The focus is on establishing the basic infrastructure using shell scripts and native Unix tools.

## Task Breakdown

### Task 1: Core Session Management Script
**ID**: BT-M1-001  
**Description**: Create main launcher script that establishes tmux session with 2x2 layout  
**Acceptance Criteria**:
- Creates named tmux session (ensemble-monitor-{project_id})
- Establishes exact 2x2 pane layout using tmux commands
- Handles existing session detection and cleanup
- Supports command-line options for project-id, session-name
- Returns success/failure exit codes

**Dependencies**: None  
**Complexity**: Medium  
**File**: `scripts/deployment/start_monitor.sh`

### Task 2: Session Cleanup Script  
**ID**: BT-M1-002  
**Description**: Create clean shutdown script for tmux session management  
**Acceptance Criteria**:
- Safely terminates tmux session by name
- Kills any child processes spawned by monitoring
- Handles missing session gracefully (no error)
- Supports optional session name parameter
- Provides confirmation message

**Dependencies**: Task 1 (session naming convention)  
**Complexity**: Simple  
**File**: `scripts/deployment/stop_monitor.sh`

### Task 3: Interactive CLI Pane Setup
**ID**: BT-M1-003  
**Description**: Configure top-left pane for interactive shell usage  
**Acceptance Criteria**:
- Opens in project root directory
- Provides standard bash/zsh shell
- Sets appropriate environment variables (PROJECT_ID, etc.)
- Ready for manual command execution
- Maintains session on terminal disconnect

**Dependencies**: Task 1 (session management)  
**Complexity**: Simple  
**Implementation**: Shell script commands in start_monitor.sh

### Task 4: Log Streaming Pane
**ID**: BT-M1-004  
**Description**: Implement real-time log streaming in top-right pane  
**Acceptance Criteria**:
- Uses tail -f to stream backend.log in real-time
- Starts with last 50 lines of existing log
- Handles missing log file gracefully (shows waiting message)
- Auto-resumes when log file appears
- Displays timestamps and maintains scroll position

**Dependencies**: Task 1 (session management)  
**Complexity**: Simple  
**Implementation**: tail -f command with error handling

### Task 5: File Browser Pane
**ID**: BT-M1-005  
**Description**: Set up vim-based file browser in bottom-left pane  
**Acceptance Criteria**:
- Opens vim in netrw (directory browser) mode
- Starts in project output directory
- Allows navigation and file editing
- Falls back to 'less' if vim unavailable
- Maintains directory context between files

**Dependencies**: Task 1 (session management)  
**Complexity**: Simple  
**Implementation**: vim/netrw configuration in tmux

### Task 6: Basic Project Monitoring Pane
**ID**: BT-M1-006  
**Description**: Implement basic project file monitoring in bottom-right pane  
**Acceptance Criteria**:
- Uses watch command to monitor project.json changes
- Shows raw project file content or "No project found"
- Updates every 2 seconds
- Handles missing project file gracefully
- Displays current timestamp for last update

**Dependencies**: Task 1 (session management)  
**Complexity**: Simple  
**Implementation**: watch command with JSON file monitoring

### Task 7: Project Detection Logic
**ID**: BT-M1-007  
**Description**: Implement project ID detection and validation  
**Acceptance Criteria**:
- Auto-detects project ID from current working directory
- Validates project exists in ~/.ensemble/projects/
- Supports explicit --project-id parameter override
- Provides clear error messages for missing projects
- Sets environment variables for other panes

**Dependencies**: None  
**Complexity**: Medium  
**Implementation**: Shell script logic in start_monitor.sh

### Task 8: Tmux Configuration
**ID**: BT-M1-008  
**Description**: Create optimal tmux configuration for monitoring dashboard  
**Acceptance Criteria**:
- Sets appropriate pane borders and titles
- Configures mouse support for pane navigation
- Sets status line to show session info
- Optimizes key bindings for monitoring workflow
- Ensures compatibility with tmux 3.0+

**Dependencies**: Task 1 (session management)  
**Complexity**: Simple  
**File**: `scripts/deployment/config/tmux.conf`

### Task 9: Error Handling and Validation
**ID**: BT-M1-009  
**Description**: Implement comprehensive error handling across all scripts  
**Acceptance Criteria**:
- Validates tmux availability and version
- Checks file system permissions
- Handles missing directories/files gracefully
- Provides helpful error messages with suggestions
- Implements proper exit codes for automation

**Dependencies**: Tasks 1-6 (all core functionality)  
**Complexity**: Medium  
**Implementation**: Error checking across all shell scripts

### Task 10: Basic Documentation
**ID**: BT-M1-010  
**Description**: Create essential documentation for Milestone 1  
**Acceptance Criteria**:
- README with installation and usage instructions
- Command reference for start/stop scripts
- Troubleshooting guide for common issues
- Requirements and compatibility information
- Example usage scenarios

**Dependencies**: Tasks 1-9 (complete functionality)  
**Complexity**: Simple  
**Files**: `docs/README.md`, `docs/troubleshooting.md`

## Task Dependencies
```
Task 1 (Session Management) 
    ↓
Tasks 2,3,4,5,6,8 (Pane Setup & Cleanup)
    ↓  
Task 7 (Project Detection)
    ↓
Task 9 (Error Handling)
    ↓
Task 10 (Documentation)
```

## Priority Order
1. **Task 1**: Core session management (foundation)
2. **Task 7**: Project detection (required for other panes)
3. **Tasks 3,4,5,6**: Pane setup (can be developed in parallel)
4. **Task 2**: Session cleanup
5. **Task 8**: Tmux configuration
6. **Task 9**: Error handling
7. **Task 10**: Documentation

## Implementation Notes

### Technology Choices
- **Shell scripting (Bash)**: Primary implementation language
- **Tmux commands**: Direct tmux control for layout management
- **Native Unix tools**: tail, watch, vim for pane content
- **Environment variables**: Cross-pane communication
- **JSON**: Project tracking data format

### File Structure
```
scripts/
├── deployment/
│   ├── start_monitor.sh       # Tasks 1, 3-7, 9
│   ├── stop_monitor.sh        # Task 2
│   └── config/
│       └── tmux.conf          # Task 8
docs/
├── README.md                  # Task 10
└── troubleshooting.md         # Task 10
```

### Critical Paths
- Session management must work before any pane setup
- Project detection must work before monitoring can function
- Error handling should be implemented throughout development

### Testing Strategy
- Manual testing on macOS and Linux
- Test various tmux versions (3.0+)
- Test missing file scenarios
- Test permission issues
- Validate session cleanup

## Success Criteria
- Single command launches complete dashboard
- All 4 panes display correctly in 2x2 grid
- Log streaming works in real-time
- File browser navigates output directory
- Session persists if terminal disconnects
- Clean shutdown script works
- Basic project monitoring shows file changes

## Handoff to TDD Coordinator
This task breakdown provides specific, testable components for TDD implementation. Each task has clear acceptance criteria suitable for test-driven development. The TDD Coordinator should implement tasks in the specified priority order, ensuring each component works independently before integration.