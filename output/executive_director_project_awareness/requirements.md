# Executive Director Project Awareness Enhancement

## Vision
Add project awareness capabilities to Executive Directors, enabling them to maintain context about their active project through a descriptive name, maintain notes (proto-history), and track task progress (completed vs remaining).

## Objectives
1. **Project Identity**: Executive Directors should know their project by a descriptive name
2. **Proto-History**: Maintain notes recording key decisions, observations, and context
3. **Task Tracking**: Record completed tasks and maintain awareness of remaining work
4. **Persistence**: Project context should survive across agent iterations and be visible to users

## Scope

### In Scope
- New `ProjectContext` class to encapsulate project awareness state
- Integration with existing `StateManager` for persistence
- Updates to Executive Director agent definition to utilize project context
- Methods to add/retrieve notes (proto-history entries)
- Methods to track task completion status
- JSON serialization for persistence and UI visibility

### Out of Scope
- Full project management features (estimates, deadlines, resources)
- Multi-project awareness (one project per Executive Director instance)
- Historical project archives (only current project)
- User authentication/permissions

## Technical Requirements

### ProjectContext Class (`src/runtime/agents/project_context.py`)
```python
class ProjectContext:
    project_name: str          # Descriptive project name
    project_description: str   # Brief description of what's being built
    created_at: datetime       # When project started
    
    # Proto-history: timestamped notes
    notes: List[ProjectNote]   # Chronological notes/observations
    
    # Task tracking
    completed_tasks: List[Task]   # Tasks that have been completed
    remaining_tasks: List[Task]   # Tasks still to be done
    
    # Methods
    add_note(content: str, category: str = "general") -> None
    mark_task_complete(task_id: str, outcome: str = None) -> None
    add_task(description: str, priority: str = "medium") -> Task
    to_dict() -> Dict  # For serialization
    from_dict(data: Dict) -> ProjectContext  # For deserialization
```

### ProjectNote Structure
```python
class ProjectNote:
    timestamp: datetime
    content: str
    category: str  # "decision", "observation", "milestone", "blocker", "general"
    related_task_id: Optional[str]
```

### Task Structure
```python
class Task:
    task_id: str  # UUID
    description: str
    priority: str  # "high", "medium", "low"
    status: str  # "pending", "in_progress", "completed", "blocked"
    created_at: datetime
    completed_at: Optional[datetime]
    outcome: Optional[str]  # Notes about how task was completed
```

### StateManager Integration
- Add `project_context` field to state schema
- Auto-save project context on checkpoint
- Auto-load project context on resume

### Executive Director Definition Updates
- Update input format to accept optional `project_context` for resumption
- Update output format to include current `project_context` state
- Add instructions for maintaining project awareness
- Add examples of when to add notes and update tasks

## Success Criteria
1. Executive Director can be initialized with a project name
2. Notes can be added and retrieved chronologically
3. Tasks can be tracked as completed or remaining
4. Project context persists across agent iterations
5. Context is serializable to JSON for UI visibility
6. Existing Executive Director functionality remains intact (backward compatible)

## Assumptions
- Project name is derived from user_vision or explicitly provided
- Notes are append-only (no editing/deletion for simplicity)
- Task IDs are auto-generated UUIDs
- All timestamps are ISO 8601 format
- Persistence uses existing state file mechanism

## Constraints
- Must integrate with existing StateManager without breaking changes
- Must not increase agent startup time significantly
- JSON serialization must be human-readable
- Compatible with Python 3.9+
