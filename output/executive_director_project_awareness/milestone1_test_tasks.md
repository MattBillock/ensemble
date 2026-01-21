# Milestone 1: Core Data Models - Test Tasks

## Overview
Create comprehensive unit tests for ProjectNote, Task, and ProjectContext classes.

## Test File Location
`tests/runtime/agents/test_project_context.py`

## Test Tasks

### Test Suite 1: ProjectNote Tests

**Test 1.1.1**: test_project_note_creation
- Create ProjectNote with all fields
- Assert all fields are set correctly

**Test 1.1.2**: test_project_note_default_category
- Create ProjectNote without category
- Assert category defaults to "general"

**Test 1.1.3**: test_project_note_to_dict
- Create ProjectNote
- Call to_dict()
- Assert returns dict with all fields
- Assert timestamp is ISO 8601 string

**Test 1.1.4**: test_project_note_from_dict
- Create dict with note data (timestamp as ISO string)
- Call ProjectNote.from_dict()
- Assert creates valid ProjectNote
- Assert timestamp is datetime object

**Test 1.1.5**: test_project_note_roundtrip
- Create ProjectNote
- Convert to dict and back
- Assert equality of all fields

---

### Test Suite 2: Task Tests

**Test 1.2.1**: test_task_creation_with_all_fields
- Create Task with all fields specified
- Assert all fields set correctly

**Test 1.2.2**: test_task_auto_generates_id
- Create Task without task_id
- Assert task_id is generated (non-empty string)

**Test 1.2.3**: test_task_default_priority
- Create Task without priority
- Assert priority is "medium"

**Test 1.2.4**: test_task_default_status
- Create Task without status
- Assert status is "pending"

**Test 1.2.5**: test_task_to_dict
- Create Task
- Call to_dict()
- Assert returns dict with all fields
- Assert datetimes are ISO 8601 strings
- Assert None values handled correctly

**Test 1.2.6**: test_task_from_dict
- Create dict with task data
- Call Task.from_dict()
- Assert creates valid Task with correct types

**Test 1.2.7**: test_task_roundtrip
- Create Task with various states
- Convert to dict and back
- Assert equality

---

### Test Suite 3: ProjectContext Tests

**Test 1.3.1**: test_project_context_creation
- Create ProjectContext with project_name
- Assert project_name set
- Assert created_at is set (datetime)
- Assert lists are empty

**Test 1.3.2**: test_project_context_with_description
- Create ProjectContext with name and description
- Assert both are set correctly

**Test 1.3.3**: test_add_note
- Create ProjectContext
- Call add_note()
- Assert note added to notes list
- Assert returned note matches

**Test 1.3.4**: test_add_note_with_category
- Add note with specific category
- Assert category is set

**Test 1.3.5**: test_add_note_with_related_task
- Add note with related_task_id
- Assert link is preserved

**Test 1.3.6**: test_add_task
- Create ProjectContext
- Call add_task()
- Assert task in remaining_tasks
- Assert task has generated ID
- Assert status is "pending"

**Test 1.3.7**: test_add_task_with_priority
- Add task with high priority
- Assert priority is "high"

**Test 1.3.8**: test_mark_task_complete_success
- Add task
- Call mark_task_complete()
- Assert returns True
- Assert task moved to completed_tasks
- Assert task removed from remaining_tasks
- Assert status is "completed"
- Assert completed_at is set

**Test 1.3.9**: test_mark_task_complete_with_outcome
- Add and complete task with outcome
- Assert outcome is set

**Test 1.3.10**: test_mark_task_complete_not_found
- Call mark_task_complete with non-existent ID
- Assert returns False
- Assert no exceptions raised

**Test 1.3.11**: test_get_task_by_id_from_remaining
- Add task
- Call get_task_by_id()
- Assert returns the task

**Test 1.3.12**: test_get_task_by_id_from_completed
- Add and complete task
- Call get_task_by_id()
- Assert returns the task

**Test 1.3.13**: test_get_task_by_id_not_found
- Call get_task_by_id with non-existent ID
- Assert returns None

---

### Test Suite 4: ProjectContext Serialization Tests

**Test 1.4.1**: test_project_context_to_dict_empty
- Create ProjectContext with no notes/tasks
- Call to_dict()
- Assert returns valid dict
- Assert lists are empty

**Test 1.4.2**: test_project_context_to_dict_with_notes
- Create context, add notes
- Call to_dict()
- Assert notes serialized correctly

**Test 1.4.3**: test_project_context_to_dict_with_tasks
- Create context, add tasks (some completed)
- Call to_dict()
- Assert both task lists serialized

**Test 1.4.4**: test_project_context_from_dict
- Create dict representation
- Call ProjectContext.from_dict()
- Assert creates valid context

**Test 1.4.5**: test_project_context_roundtrip_empty
- Create empty context
- Roundtrip through dict
- Assert equality

**Test 1.4.6**: test_project_context_roundtrip_full
- Create context with notes and tasks
- Roundtrip through dict
- Assert all data preserved

**Test 1.4.7**: test_project_context_json_serializable
- Create full context
- Convert to dict
- Assert json.dumps() works without error

---

## Test Utilities Needed

```python
import pytest
from datetime import datetime
import json
from src.runtime.agents.project_context import ProjectNote, Task, ProjectContext
```

## Acceptance Criteria
- All tests pass
- Tests cover happy path and edge cases
- Tests are isolated (no shared state)
- Tests use pytest fixtures where appropriate
