# Milestone 1: Core Data Models - Backend Tasks

## Overview
Create the fundamental data structures for project awareness in `src/runtime/agents/project_context.py`

## Tasks

### Task 1.1: Create ProjectNote Dataclass
**File**: `src/runtime/agents/project_context.py`

**Requirements**:
- Create `ProjectNote` dataclass with fields:
  - `timestamp: datetime` - When the note was created
  - `content: str` - The note content
  - `category: str` - One of: "decision", "observation", "milestone", "blocker", "general"
  - `related_task_id: Optional[str]` - Optional link to a task
- Add `to_dict()` method returning JSON-serializable dict
- Add `from_dict(data: Dict) -> ProjectNote` classmethod

**Acceptance Criteria**:
- All fields properly typed
- Default category is "general"
- Timestamp serializes to ISO 8601 string
- from_dict handles ISO 8601 string conversion back to datetime

---

### Task 1.2: Create Task Dataclass
**File**: `src/runtime/agents/project_context.py`

**Requirements**:
- Create `Task` dataclass with fields:
  - `task_id: str` - UUID string
  - `description: str` - Task description
  - `priority: str` - One of: "high", "medium", "low" (default "medium")
  - `status: str` - One of: "pending", "in_progress", "completed", "blocked" (default "pending")
  - `created_at: datetime` - When task was created
  - `completed_at: Optional[datetime]` - When task was completed (None if not completed)
  - `outcome: Optional[str]` - Notes about completion
- Add `to_dict()` method
- Add `from_dict(data: Dict) -> Task` classmethod
- Auto-generate task_id if not provided

**Acceptance Criteria**:
- UUID generated using `uuid.uuid4()` if not provided
- All timestamps use ISO 8601 format in serialization
- Proper handling of None values for optional fields

---

### Task 1.3: Create ProjectContext Class
**File**: `src/runtime/agents/project_context.py`

**Requirements**:
- Create `ProjectContext` class with:
  - `project_name: str` - Descriptive project name
  - `project_description: str` - Brief description (default empty string)
  - `created_at: datetime` - When project started (auto-set to now)
  - `notes: List[ProjectNote]` - Chronological notes
  - `completed_tasks: List[Task]` - Completed tasks
  - `remaining_tasks: List[Task]` - Pending/in-progress tasks
- Constructor should accept project_name as required, others optional

**Acceptance Criteria**:
- Constructor properly initializes all fields
- Lists default to empty lists
- created_at defaults to datetime.now()

---

### Task 1.4: Implement ProjectContext Methods
**File**: `src/runtime/agents/project_context.py`

**Requirements**:
- `add_note(content: str, category: str = "general", related_task_id: Optional[str] = None) -> ProjectNote`
  - Creates and appends a new note
  - Returns the created note
- `add_task(description: str, priority: str = "medium") -> Task`
  - Creates a new task with "pending" status
  - Adds to remaining_tasks
  - Returns the created task
- `mark_task_complete(task_id: str, outcome: Optional[str] = None) -> bool`
  - Finds task in remaining_tasks by ID
  - Sets status to "completed", completed_at to now, outcome if provided
  - Moves task from remaining_tasks to completed_tasks
  - Returns True if found and moved, False otherwise
- `get_task_by_id(task_id: str) -> Optional[Task]`
  - Searches both remaining_tasks and completed_tasks
  - Returns task or None

**Acceptance Criteria**:
- All methods work correctly
- mark_task_complete handles non-existent task_id gracefully
- Notes are added chronologically (newest at end)

---

### Task 1.5: Implement Serialization Methods
**File**: `src/runtime/agents/project_context.py`

**Requirements**:
- `to_dict() -> Dict[str, Any]`
  - Returns complete JSON-serializable dictionary
  - All datetimes as ISO 8601 strings
  - All nested objects (notes, tasks) as dicts
- `from_dict(data: Dict[str, Any]) -> ProjectContext` (classmethod)
  - Reconstructs ProjectContext from dict
  - Handles ISO 8601 string to datetime conversion
  - Reconstructs all nested ProjectNote and Task objects

**Acceptance Criteria**:
- Roundtrip: `ProjectContext.from_dict(context.to_dict())` equals original
- Human-readable JSON output
- Handles empty lists correctly

---

### Task 1.6: Add Module Exports
**File**: `src/runtime/agents/project_context.py`

**Requirements**:
- Add appropriate imports at top of file (datetime, uuid, dataclasses, typing)
- Add `__all__` export list with: ProjectNote, Task, ProjectContext
- Add module docstring

**Acceptance Criteria**:
- All three classes importable from module
- No circular import issues
- Compatible with Python 3.9+

---

## Dependencies
- Python standard library only (datetime, uuid, dataclasses, typing)
- No external packages required

## Output Location
`src/runtime/agents/project_context.py`
