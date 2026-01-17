# Backend Tasks - Milestone 2: Enhanced Task Monitoring

## Overview
This milestone focuses on creating an intelligent task watcher with formatted display and real-time updates. The core deliverable is `task_watcher.py` that parses project.json, displays formatted task lists with status icons, provides auto-refresh, and shows summary counts.

## Task Breakdown

### Core Backend Tasks

#### Task 1: Project State File Parser
**Description**: Create a robust JSON parser for project state files that can handle different project structures and task formats.

**Acceptance Criteria**:
- Parse ~/.ensemble/projects/{project_id}/project.json
- Handle missing or malformed JSON gracefully
- Extract task data (id, description, status, assigned_to)
- Support multiple project schemas
- Return structured task data for display formatting

**Dependencies**: None
**Complexity**: Simple
**Estimated Time**: 2-3 hours

#### Task 2: Task Status Classification Engine
**Description**: Implement business logic to categorize tasks by status and determine appropriate display formatting.

**Acceptance Criteria**:
- Map task statuses to display categories (completed, in_progress, todo, blocked, cancelled)
- Assign status icons (✅ ❌ 🔄 ⏳ 🚫)
- Handle edge cases (null status, unknown status values)
- Sort tasks within each category by creation/update time
- Calculate status counts for summary display

**Dependencies**: Task 1
**Complexity**: Simple
**Estimated Time**: 2-3 hours

#### Task 3: File System Watcher Service
**Description**: Create a file watching service that monitors project state changes and triggers display updates.

**Acceptance Criteria**:
- Watch ~/.ensemble/projects/{project_id}/project.json for changes
- Use efficient file watching (inotify on Linux, fswatch on macOS)
- Fallback to polling if file watching unavailable
- Handle file deletion, creation, and modification events
- Debounce rapid changes to prevent excessive updates
- Graceful error handling for permission issues

**Dependencies**: None
**Complexity**: Medium
**Estimated Time**: 4-5 hours

#### Task 4: Display Formatter Service
**Description**: Create a service that formats task data into a visually appealing terminal display with proper spacing and alignment.

**Acceptance Criteria**:
- Generate formatted task list with status icons
- Implement proper text truncation for long task names
- Create status summary header (e.g., "3 done | 2 active | 5 pending")
- Support configurable display width
- Handle empty task lists gracefully
- Use Unicode characters safely across terminals
- Implement color coding if terminal supports it

**Dependencies**: Task 1, Task 2
**Complexity**: Medium
**Estimated Time**: 3-4 hours

#### Task 5: Configuration Management System
**Description**: Implement configuration system for task watcher settings and project selection.

**Acceptance Criteria**:
- Support environment variables (ENSEMBLE_PROJECT_ID, TASK_REFRESH_INTERVAL)
- Provide command-line argument parsing
- Default configuration values for common scenarios
- Configuration validation and error messages
- Support for multiple output formats (tmux, console)

**Dependencies**: None
**Complexity**: Simple
**Estimated Time**: 2-3 hours

#### Task 6: Tmux Integration Layer
**Description**: Create tmux-specific output formatting and pane management functionality.

**Acceptance Criteria**:
- Format output for tmux pane display
- Handle tmux buffer management
- Support tmux session detection
- Implement tmux-specific refresh commands
- Handle tmux pane resizing gracefully
- Clear previous content before updates

**Dependencies**: Task 4
**Complexity**: Medium
**Estimated Time**: 3-4 hours

### Supporting Backend Tasks

#### Task 7: Error Handling and Logging Framework
**Description**: Implement comprehensive error handling and logging for debugging and monitoring.

**Acceptance Criteria**:
- Structured logging with appropriate levels (DEBUG, INFO, WARN, ERROR)
- Error recovery for common failures (file not found, permission denied)
- Log rotation for long-running processes
- Performance monitoring (parse time, update frequency)
- User-friendly error messages in display

**Dependencies**: All core tasks
**Complexity**: Simple
**Estimated Time**: 2-3 hours

#### Task 8: Performance Optimization Service
**Description**: Optimize parsing and display performance for large project files and frequent updates.

**Acceptance Criteria**:
- Implement incremental parsing (only process changed data)
- Cache parsed results to reduce computation
- Optimize memory usage for long-running process
- Benchmark and profile performance bottlenecks
- Support for projects with 100+ tasks

**Dependencies**: Task 1, Task 2, Task 3
**Complexity**: Medium
**Estimated Time**: 3-4 hours

#### Task 9: Multi-Project Support Backend
**Description**: Extend backend to support monitoring multiple projects simultaneously.

**Acceptance Criteria**:
- Project discovery in ~/.ensemble/projects/
- Project switching interface
- Concurrent file watching for multiple projects
- Project-specific configuration
- Resource management for multiple watchers

**Dependencies**: Task 1, Task 3, Task 5
**Complexity**: Complex
**Estimated Time**: 5-6 hours

### Integration and Testing Tasks

#### Task 10: Unit Test Suite
**Description**: Create comprehensive unit tests for all backend components.

**Acceptance Criteria**:
- Test coverage ≥ 90% for all modules
- Mock file system interactions
- Test error conditions and edge cases
- Parameterized tests for different project schemas
- Performance tests for large datasets
- Tests for configuration variations

**Dependencies**: All implementation tasks
**Complexity**: Medium
**Estimated Time**: 4-5 hours

#### Task 11: Integration Testing Framework
**Description**: Create integration tests that verify end-to-end functionality with real project files.

**Acceptance Criteria**:
- Test with real project.json files
- Verify file watching triggers correctly
- Test tmux integration in controlled environment
- Cross-platform compatibility tests (Linux/macOS)
- Memory and resource leak detection
- Performance regression testing

**Dependencies**: All implementation tasks
**Complexity**: Medium
**Estimated Time**: 3-4 hours

#### Task 12: Main Application Controller
**Description**: Create the main task_watcher.py script that orchestrates all components.

**Acceptance Criteria**:
- Command-line interface with help documentation
- Graceful startup and shutdown
- Signal handling (SIGINT, SIGTERM)
- Main event loop with proper error handling
- Integration with all backend services
- Exit codes for different scenarios

**Dependencies**: All core tasks
**Complexity**: Simple
**Estimated Time**: 2-3 hours

## Task Dependencies

```
Task 1 (Parser) → Task 2 (Classification) → Task 4 (Formatter) → Task 6 (Tmux)
                                                               → Task 12 (Main)
Task 3 (Watcher) → Task 12 (Main)
Task 5 (Config) → Task 12 (Main)
Task 7 (Logging) → Task 12 (Main)
Task 8 (Performance) → Task 12 (Main)
Task 9 (Multi-Project) → Task 12 (Main)

Task 10 (Unit Tests) ← All Implementation Tasks
Task 11 (Integration) ← All Implementation Tasks
```

## Priority Order

### Phase 1: Core Functionality (Critical Path)
1. Task 1: Project State File Parser
2. Task 2: Task Status Classification Engine
3. Task 4: Display Formatter Service
4. Task 12: Main Application Controller

### Phase 2: Real-time Updates
5. Task 3: File System Watcher Service
6. Task 6: Tmux Integration Layer

### Phase 3: Production Readiness
7. Task 5: Configuration Management System
8. Task 7: Error Handling and Logging Framework
9. Task 10: Unit Test Suite
10. Task 11: Integration Testing Framework

### Phase 4: Optimization and Enhancement
11. Task 8: Performance Optimization Service
12. Task 9: Multi-Project Support Backend

## Technical Notes

### Key Backend Technologies
- **Language**: Python 3.8+
- **File Watching**: `watchdog` library with inotify/fswatch fallback
- **JSON Parsing**: Built-in `json` module with error handling
- **CLI**: `argparse` for command-line interface
- **Logging**: Built-in `logging` module
- **Testing**: `pytest` with `pytest-cov` for coverage

### Data Models
```python
@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class ProjectState:
    project_id: str
    tasks: List[Task]
    last_updated: datetime
```

### Configuration Schema
```python
@dataclass
class WatcherConfig:
    project_id: str
    refresh_interval: float = 1.0
    max_task_length: int = 60
    output_format: str = "tmux"
    log_level: str = "INFO"
```

This task breakdown provides a comprehensive backend implementation plan for Milestone 2 with clear dependencies, acceptance criteria, and priority ordering.