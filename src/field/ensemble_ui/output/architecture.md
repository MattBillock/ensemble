# Executive Director Project Awareness - Architecture Design

## Overview
Add project awareness capabilities to Executive Director agents, enabling persistent understanding of projects through descriptive naming and historical note-keeping. This involves creating a ProjectContextManager class, a new tool for agents, and integration with the existing Executive Director agent definition.

## Architecture Style
**Layered Architecture** - Clear separation between data layer (context manager), tool layer (agent tools), and presentation layer (agent integration).

## Project Structure
```
src/ensemble_runtime/
├── project_context/
│   ├── __init__.py               # Package exports
│   ├── project_context_manager.py # Core manager class
│   ├── models.py                  # Data classes (ProjectContext, TaskEntry, NoteEntry)
│   └── exceptions.py              # Custom exceptions
├── tools/
│   └── tools.py                   # Add manage_project_context tool (extend existing)
└── agents/
    └── leadership/
        └── executive_director.md  # Update agent definition

tests/
├── unit/
│   ├── test_project_context_manager.py
│   └── test_models.py
├── integration/
│   └── test_project_context_tool.py
└── e2e/
    └── test_executive_director_context.py

output/
└── project_context.json           # Persisted project context file
```

## Core Components

### 1. models.py
**Purpose**: Type-safe data structures for project context

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class NoteCategory(Enum):
    DECISION = "decision"
    OBSERVATION = "observation"
    BLOCKER = "blocker"
    PROGRESS = "progress"
    OTHER = "other"

class ProjectStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

@dataclass
class TaskEntry:
    task_id: str
    description: str
    priority: str = "medium"
    estimated_by: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    outcome: Optional[str] = None

@dataclass
class NoteEntry:
    timestamp: datetime
    author: str
    category: NoteCategory
    content: str

@dataclass
class ProjectContext:
    project_name: str
    project_description: str
    created_at: datetime
    current_phase: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    completed_tasks: List[TaskEntry] = field(default_factory=list)
    pending_tasks: List[TaskEntry] = field(default_factory=list)
    notes: List[NoteEntry] = field(default_factory=list)
```

---

### 2. project_context_manager.py
**Purpose**: Core manager for project context operations

**Public API**:
```python
class ProjectContextManager:
    def __init__(self, context_path: Optional[str] = None):
        """Initialize manager with optional path to existing context file."""
        
    def initialize_project(self, name: str, description: str) -> ProjectContext:
        """Create new project context with given name and description."""
        
    def load_context(self, path: str) -> ProjectContext:
        """Load existing context from JSON file."""
        
    def save_context(self, path: Optional[str] = None) -> str:
        """Save current context to JSON file. Returns file path."""
        
    def add_completed_task(self, task: TaskEntry) -> None:
        """Record a completed task."""
        
    def add_pending_task(self, task: TaskEntry) -> None:
        """Add a pending task."""
        
    def remove_pending_task(self, task_id: str) -> TaskEntry:
        """Remove and return a pending task by ID."""
        
    def complete_task(self, task_id: str, outcome: str, completed_by: Optional[str] = None) -> TaskEntry:
        """Move task from pending to completed with outcome details."""
        
    def add_note(self, note: NoteEntry) -> None:
        """Add a note to the project history."""
        
    def get_summary(self) -> str:
        """Return human-readable summary of project status."""
        
    def to_dict(self) -> dict:
        """Serialize context to dictionary."""
        
    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectContextManager':
        """Create manager from serialized dictionary."""
```

**Serialization Format (project_context.json)**:
```json
{
  "project_name": "Executive Director Project Awareness",
  "project_description": "Add project awareness capabilities to ED agents",
  "created_at": "2024-01-15T10:30:00Z",
  "current_phase": "implementation",
  "status": "active",
  "completed_tasks": [
    {
      "task_id": "task-001",
      "description": "Create ProjectContextManager class",
      "completed_at": "2024-01-15T14:30:00Z",
      "completed_by": "TDD Coordinator",
      "outcome": "All tests passing"
    }
  ],
  "pending_tasks": [
    {
      "task_id": "task-002",
      "description": "Integrate with Executive Director",
      "priority": "high",
      "dependencies": ["task-001"]
    }
  ],
  "notes": [
    {
      "timestamp": "2024-01-15T10:35:00Z",
      "author": "Executive Director",
      "category": "decision",
      "content": "Chose Option B for file-based persistence"
    }
  ]
}
```

---

### 3. tools.py Extension
**Purpose**: Add manage_project_context tool to existing tool registry

**Tool Definition**:
```python
# Add to existing tools.py

def manage_project_context(action: str, **kwargs) -> dict:
    """
    Manage project context for Executive Director.
    
    Actions:
        - init: Initialize new project context
            kwargs: name (str), description (str), output_dir (str)
        - add_task: Add a pending task
            kwargs: task_id (str), description (str), priority (str, optional)
        - complete_task: Mark task as completed
            kwargs: task_id (str), outcome (str), completed_by (str, optional)
        - add_note: Add a note to project history
            kwargs: category (str), content (str), author (str)
        - get_status: Get current project status summary
            kwargs: output_dir (str)
    
    Returns:
        dict with 'success' (bool) and 'result' or 'error' keys
    """

# Register in ToolRegistry
TOOLS = {
    # ... existing tools
    "manage_project_context": {
        "function": manage_project_context,
        "description": "Manage project context for tracking progress, tasks, and notes",
        "parameters": {
            "action": "string - One of: init, add_task, complete_task, add_note, get_status",
            "name": "string - Project name (for init)",
            "description": "string - Project description (for init)",
            "task_id": "string - Task identifier (for add_task, complete_task)",
            "priority": "string - Task priority: low, medium, high (optional)",
            "outcome": "string - Task completion outcome (for complete_task)",
            "category": "string - Note category: decision, observation, blocker, progress, other",
            "content": "string - Note content (for add_note)",
            "author": "string - Note author (for add_note)",
            "output_dir": "string - Directory containing project_context.json"
        }
    }
}
```

---

### 4. Executive Director Updates
**Purpose**: Enable Executive Director to use project context

**Updates to executive_director.md**:

1. **Add to Available Tools**:
```markdown
## Available Tools
- spawn_agent: Spawn specialist agents
- manage_project_context: Track project identity, tasks, and notes
  - init: Initialize project with name and description at start
  - add_task/complete_task: Track task progress
  - add_note: Record decisions and observations
  - get_status: Get summary for status reports
```

2. **Update Instructions**:
```markdown
## Project Context Workflow
1. At START of project: Call manage_project_context with action='init' to name the project
2. After each major decision: Add a note with category='decision'
3. When assigning tasks: Add pending tasks
4. When tasks complete: Mark tasks complete with outcomes
5. In status reports: Include project name and summary
```

3. **Update Output Format**:
```markdown
## Output Format
{
  "status": "...",
  "project_context": {
    "project_name": "descriptive name from context",
    "current_phase": "current phase",
    "completed_count": 5,
    "pending_count": 3
  },
  ...
}
```

---

### 5. Activity Tracker Integration
**Purpose**: Log project context changes in activity tracker

**New Activity Type**:
```python
class ActivityType(Enum):
    # ... existing types
    PROJECT_CONTEXT_UPDATE = "project_context_update"
```

**Activity Entry Structure**:
```python
{
    "type": "project_context_update",
    "timestamp": "2024-01-15T10:30:00Z",
    "action": "init|add_task|complete_task|add_note",
    "details": {
        "project_name": "...",
        "affected_entity": "task-001 or note content preview"
    }
}
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Executive Director Agent                     │
│                                                                 │
│  1. Receives project request                                    │
│  2. Calls manage_project_context(action='init', name=..., ...)  │
│  3. Throughout execution, adds tasks/notes                      │
│  4. On completion, updates final status                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   manage_project_context Tool                    │
│                                                                 │
│  - Routes actions to ProjectContextManager                      │
│  - Handles file path resolution                                 │
│  - Returns structured responses                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ProjectContextManager                         │
│                                                                 │
│  - Manages ProjectContext data structure                        │
│  - Handles JSON serialization/deserialization                   │
│  - Provides human-readable summaries                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    project_context.json                          │
│                                                                 │
│  - Persistent storage                                           │
│  - Human-readable                                               │
│  - One per output directory                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Specifications

### Language & Standards
- **Python Version**: 3.9+ (for modern type hints)
- **Code Style**: PEP 8 compliant, black formatter
- **Type Hints**: Full type hints on all functions
- **Docstrings**: Google-style docstrings

### Dependencies
- Standard library only for core functionality
- pytest for testing
- dataclasses (stdlib)
- json (stdlib)
- datetime (stdlib)
- typing (stdlib)

### Error Handling
```python
class ProjectContextError(Exception):
    """Base exception for project context operations."""

class ContextNotInitializedError(ProjectContextError):
    """Raised when operations attempted on uninitialized context."""

class ContextFileError(ProjectContextError):
    """Raised when file operations fail."""

class TaskNotFoundError(ProjectContextError):
    """Raised when task_id not found."""
```

---

## Testing Strategy

### Unit Tests
1. **Models**: Test serialization/deserialization of all data classes
2. **ProjectContextManager**: Test all CRUD operations
3. **Edge cases**: Empty lists, missing fields, invalid data

### Integration Tests
1. **Tool Integration**: Test manage_project_context tool with various actions
2. **File Persistence**: Test save/load cycle
3. **Activity Tracker**: Test logging of context updates

### End-to-End Tests
1. **Full Workflow**: Executive Director creates and manages context
2. **Resumption**: Load existing context and continue work
3. **Error Recovery**: Handle missing/corrupt context files

---

## Implementation Priority

1. **Milestone 1**: Core models and ProjectContextManager (foundation)
2. **Milestone 2**: Tool integration (enable agent use)
3. **Milestone 3**: Executive Director updates (full integration)
4. **Milestone 4**: Testing and documentation (quality)

---

## Security Considerations
- Context file written with user permissions only
- No sensitive data stored in context (no credentials)
- Input validation on all tool parameters

---

## Future Extensions (Out of Scope)
- Multi-project support
- UI visualization
- Context merging
- Cross-agent context sharing

---

## Success Criteria
- ✅ Executive Director can name projects at start
- ✅ Completed tasks recorded with timestamps
- ✅ Notes can be added throughout execution
- ✅ Remaining work tracked
- ✅ Context persists to readable JSON file
- ✅ Context loadable on subsequent executions
- ✅ Activity tracker shows updates
