# Executive Director Project Awareness - Architecture

## Overview
This document describes the architecture for adding project awareness capabilities to Executive Directors in the Ensemble agent system.

## System Context

### Existing Components
- **StateManager** (`src/runtime/agents/state.py`): Manages agent execution state, checkpointing, and resume functionality
- **AgentDefinition** (`src/runtime/agents/definition.py`): Parses agent definitions from markdown files
- **AgentRuntime** (`src/runtime/agents/runtime.py`): Executes agents with conversation management

### New Components
- **ProjectContext** (`src/runtime/agents/project_context.py`): New module encapsulating project awareness state

## Component Architecture

### ProjectContext Module Structure

```
src/runtime/agents/project_context.py
├── ProjectNote (dataclass)
│   ├── timestamp: datetime
│   ├── content: str
│   ├── category: str
│   └── related_task_id: Optional[str]
├── Task (dataclass)
│   ├── task_id: str
│   ├── description: str
│   ├── priority: str
│   ├── status: str
│   ├── created_at: datetime
│   ├── completed_at: Optional[datetime]
│   └── outcome: Optional[str]
└── ProjectContext (class)
    ├── project_name: str
    ├── project_description: str
    ├── created_at: datetime
    ├── notes: List[ProjectNote]
    ├── completed_tasks: List[Task]
    ├── remaining_tasks: List[Task]
    ├── add_note()
    ├── add_task()
    ├── mark_task_complete()
    ├── get_task_by_id()
    ├── to_dict()
    └── from_dict()
```

## Data Flow

### Initialization Flow
```
User/Agent Request
       │
       ▼
┌─────────────────────┐
│  Executive Director │
│     Definition      │
└──────────┬──────────┘
           │ input_data includes project_name
           ▼
┌─────────────────────┐
│   ProjectContext    │
│   (new instance)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    StateManager     │
│  (stores context)   │
└─────────────────────┘
```

### Persistence Flow
```
Agent Iteration
       │
       ▼
┌─────────────────────┐
│ ProjectContext      │
│ updates (notes,     │
│ task changes)       │
└──────────┬──────────┘
           │ to_dict()
           ▼
┌─────────────────────┐
│   StateManager      │
│   checkpoint()      │
└──────────┬──────────┘
           │
           ▼
    state.json file
```

### Resume Flow
```
state.json file
       │
       ▼
┌─────────────────────┐
│   StateManager      │
│      load()         │
└──────────┬──────────┘
           │ project_context dict
           ▼
┌─────────────────────┐
│ ProjectContext      │
│   from_dict()       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Executive Director │
│   (resumed with     │
│    context)         │
└─────────────────────┘
```

## Integration Points

### StateManager Integration
Add to `StateManager.__init__()` state schema:
```python
self.state: Dict[str, Any] = {
    # ... existing fields ...
    "project_context": None,  # NEW: ProjectContext serialized dict
}
```

Add methods:
- `set_project_context(context: ProjectContext)`: Set and serialize project context
- `get_project_context() -> Optional[ProjectContext]`: Get deserialized project context

### Executive Director Definition Updates
Input format additions:
```json
{
  "project_name": "string - descriptive project name (optional)",
  "project_context": "object - existing ProjectContext for resumption (optional)"
}
```

Output format additions:
```json
{
  "project_context": "object - current ProjectContext state"
}
```

## Design Decisions

### 1. Immutable Notes
Notes are append-only to maintain audit trail and simplify implementation. No edit/delete operations.

### 2. UUID for Task IDs
Using `uuid.uuid4()` for task identifiers ensures uniqueness without coordination.

### 3. ISO 8601 Timestamps
All timestamps use ISO 8601 format for human readability and JSON serialization.

### 4. Optional Project Context
Project context is optional for backward compatibility. Existing agents without project awareness continue to work.

### 5. Category Enum Values
Note categories are string literals rather than enums for JSON serialization simplicity:
- "decision", "observation", "milestone", "blocker", "general"

### 6. Task Status Transitions
```
pending → in_progress → completed
    ↓         ↓
  blocked   blocked
```

## File Locations
- **New File**: `src/runtime/agents/project_context.py`
- **Modified**: `src/runtime/agents/state.py`
- **Modified**: `agents/leadership/executive_director.md` (definition)
- **New Tests**: `tests/runtime/agents/test_project_context.py`

## Testing Strategy
1. **Unit Tests**: ProjectNote, Task, ProjectContext classes
2. **Integration Tests**: StateManager persistence roundtrip
3. **End-to-End Tests**: Executive Director with project context

## Backward Compatibility
- StateManager handles missing `project_context` field gracefully (defaults to None)
- Executive Director works without project_name input (uses default or None)
- Existing state files remain valid
