# Backend Tasks - Milestone 1: Basic Tmux Layout

## Overview
Milestone 1 creates the foundational tmux-based monitoring dashboard with a 2x2 layout. This milestone focuses on **session management**, **layout creation**, and **basic monitoring setup** rather than complex backend services.

## Task Breakdown

### Core Session Management Tasks

#### 1. Main Dashboard Launcher Script
**File**: `scripts/deployment/start_monitor.sh`
**Description**: Create the primary script that initializes the tmux monitoring dashboard
**Acceptance Criteria**:
- Creates named tmux session (e.g., "ensemble-monitor-{project_id}")
- Detects if session already exists and handles gracefully
- Sets up 2x2 pane layout with proper sizing
- Launches appropriate commands in each pane
- Provides command-line options for project-id, session-name, directories
- Returns success/failure exit codes
**Dependencies**: None
**Complexity**: Medium

#### 2. Clean Shutdown Script
**File**: `scripts/deployment/stop_monitor.sh`
**Description**: Create script for graceful dashboard termination
**Acceptance Criteria**:
- Accepts session name as parameter (with sensible default)
- Terminates all processes running in panes
- Kills tmux session cleanly
- Handles case where session doesn't exist
- Provides confirmation of shutdown
**Dependencies**: Task 1 (start_monitor.sh)
**Complexity**: Simple

#### 3. Tmux Layout Configuration
**File**: `scripts/deployment/config/tmux.conf`
**Description**: Custom tmux configuration for optimal dashboard experience
**Acceptance Criteria**:
- Configures 2x2 layout with equal pane sizing
- Sets appropriate key bindings for navigation
- Configures status bar for session identification
- Sets proper window/pane titles
- Optimizes for monitoring use case (no unnecessary features)
**Dependencies**: Task 1 (start_monitor.sh)
**Complexity**: Simple

### Pane Content Implementation Tasks

#### 4. Interactive Shell Setup (Pane 1)
**Description**: Configure top-left pane for interactive CLI usage
**Acceptance Criteria**:
- Starts with clean bash/zsh shell
- Sets working directory to project root
- Provides clear prompt indicating dashboard context
- Maintains shell history and environment variables
- Ready for Claude CLI integration (future milestone)
**Dependencies**: Task 1 (start_monitor.sh)
**Complexity**: Simple

#### 5. Log Stream Implementation (Pane 2)
**Description**: Set up real-time log streaming in top-right pane
**Acceptance Criteria**:
- Uses `tail -f` to stream backend.log file
- Handles missing log file gracefully (shows waiting message)
- Displays reasonable number of initial lines (50)
- Updates in real-time as new log entries appear
- Handles log rotation properly
**Dependencies**: Task 1 (start_monitor.sh)
**Complexity**: Simple

#### 6. File Browser Setup (Pane 3)
**Description**: Configure bottom-left pane with vim file browser
**Acceptance Criteria**:
- Opens vim in output directory (or project root if output doesn't exist)
- Uses vim's netrw file explorer mode
- Sets appropriate vim settings for file browsing
- Handles directory creation if output dir doesn't exist
- Provides clear navigation interface
**Dependencies**: Task 1 (start_monitor.sh)
**Complexity**: Simple

#### 7. Basic Project File Watcher (Pane 4)
**Description**: Implement simple file monitoring in bottom-right pane
**Acceptance Criteria**:
- Uses `watch` command to monitor project.json file
- Updates every 2 seconds by default
- Shows basic file content or "file not found" message
- Handles missing ensemble project directory gracefully
- Displays timestamp of last update
**Dependencies**: Task 1 (start_monitor.sh)
**Complexity**: Simple

### Directory Structure and Environment Tasks

#### 8. Directory Structure Creation
**Description**: Set up required directory structure for scripts and configuration
**Acceptance Criteria**:
- Creates scripts/deployment/ directory
- Creates scripts/deployment/config/ directory
- Creates scripts/monitoring/ directory (for future use)
- Sets proper file permissions (executable for .sh files)
- Includes .gitignore for temporary files
**Dependencies**: None
**Complexity**: Simple

#### 9. Environment Detection and Validation
**File**: `scripts/deployment/utils/env_check.sh` (helper script)
**Description**: Validate system requirements and environment setup
**Acceptance Criteria**:
- Checks tmux is installed and minimum version (3.0+)
- Verifies vim/nvim availability
- Validates ensemble project directory structure
- Checks file permissions for reading logs and project files
- Provides clear error messages for missing requirements
**Dependencies**: None
**Complexity**: Simple

#### 10. Project Auto-Detection Logic
**Description**: Implement logic to automatically detect current project context
**Acceptance Criteria**:
- Detects project ID from current working directory
- Scans for .ensemble directory structure
- Falls back to user-provided project-id parameter
- Validates project exists and is accessible
- Provides meaningful error if no project found
**Dependencies**: Task 9 (env_check.sh)
**Complexity**: Medium

### Error Handling and Logging Tasks

#### 11. Error Handling Framework
**Description**: Implement consistent error handling across all scripts
**Acceptance Criteria**:
- Standardized error message format
- Proper exit codes for different failure scenarios
- Graceful degradation when optional features fail
- Error logging to dedicated dashboard log file
- User-friendly error messages with suggested fixes
**Dependencies**: Tasks 1, 2 (main scripts)
**Complexity**: Simple

#### 12. Session Conflict Resolution
**Description**: Handle cases where monitoring session already exists
**Acceptance Criteria**:
- Detect existing sessions with same name
- Offer options: attach, kill and restart, or choose new name
- Prevent accidental session termination
- Clean up orphaned sessions automatically
- Provide clear feedback about session state
**Dependencies**: Task 1 (start_monitor.sh)
**Complexity**: Medium

## Task Dependencies

```
Task 8 (Directory Structure) → Task 9 (Environment Check)
                            ↓
Task 9 (Environment Check) → Task 10 (Project Detection)
                          ↓
Task 10 (Project Detection) → Task 1 (Main Launcher)
                            ↓
Task 1 (Main Launcher) → Tasks 2,3,4,5,6,7 (All dependent components)
                      ↓
Tasks 2,3,4,5,6,7 → Task 11 (Error Handling)
                 ↓
Task 11 (Error Handling) → Task 12 (Session Conflicts)
```

## Implementation Priority

### Phase 1: Foundation
1. Directory Structure Creation (Task 8)
2. Environment Detection (Task 9) 
3. Project Auto-Detection (Task 10)

### Phase 2: Core Functionality
4. Main Dashboard Launcher (Task 1)
5. Basic pane implementations (Tasks 4, 5, 6, 7)
6. Tmux Configuration (Task 3)

### Phase 3: Polish and Reliability
7. Clean Shutdown Script (Task 2)
8. Error Handling Framework (Task 11)
9. Session Conflict Resolution (Task 12)

## Testing Strategy

### Manual Testing
- Test on clean system without existing sessions
- Test with missing project directories
- Test with missing log files
- Test session restart scenarios
- Test across different terminal sizes

### Automated Testing
- Shell script linting with shellcheck
- Basic integration tests for session creation
- Environment validation testing
- Mock project file testing

## Success Criteria for Milestone 1

✅ Single command creates working 2x2 tmux dashboard
✅ All four panes display appropriate content
✅ Log streaming works in real-time
✅ File browser navigates project output
✅ Session persists through disconnections
✅ Clean shutdown works reliably
✅ Basic error handling for common failure cases

## Notes

- **No Complex Backend**: This milestone intentionally avoids complex backend services
- **Shell-First Approach**: Leverages proven Unix tools rather than custom daemons
- **Incremental Value**: Each task delivers standalone value
- **Future-Ready**: Architecture supports enhancement in later milestones
- **Cross-Platform**: Designed for macOS/Linux with tmux 3.0+