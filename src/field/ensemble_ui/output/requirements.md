# Executive Director Project Awareness - Milestone 1 Backend Requirements

## Project Vision
Implement the backend data models for the executive director project awareness system as specified in the milestone1_backend_tasks.md document. This is a well-defined implementation task with detailed specifications.

## Objectives
1. Create ProjectNote dataclass with timestamp, content, category, and optional task linking
2. Create Task dataclass with ID, description, priority, status, and completion tracking
3. Create ProjectContext class to manage notes and tasks with proper lifecycle methods
4. Implement complete serialization/deserialization for all data structures
5. Follow TDD methodology with comprehensive test coverage

## Core Features

### ProjectNote Dataclass
- Fields: timestamp, content, category, related_task_id (optional)
- Categories: "decision", "observation", "milestone", "blocker", "general"
- JSON serialization with ISO 8601 timestamp format
- Factory method for deserialization

### Task Dataclass  
- Fields: task_id (UUID), description, priority, status, created_at, completed_at, outcome
- Auto-generate UUID if not provided
- Priority levels: "high", "medium", "low"
- Status values: "pending", "in_progress", "completed", "blocked"
- Complete serialization support

### ProjectContext Class
- Project metadata: name, description, created_at
- Task management: remaining_tasks and completed_tasks lists
- Note tracking: chronological notes list
- Methods for adding notes, creating tasks, marking completion, task lookup
- Full serialization for persistence

## Technical Constraints
- Python 3.9+ compatibility
- Standard library only (no external dependencies)
- File location: src/runtime/agents/project_context.py
- Use dataclasses for data structures
- ISO 8601 format for all timestamp serialization
- UUID4 for task ID generation

## Success Criteria
- All dataclasses properly typed with default values
- Roundtrip serialization works correctly (to_dict/from_dict)
- Task lifecycle management functions properly
- Comprehensive test coverage following TDD methodology
- Code follows Python best practices and is well-documented

## Out of Scope
- Database persistence (focusing on in-memory data structures)
- API endpoints or web interfaces
- Authentication or authorization
- Performance optimization beyond basic efficiency

## Assumptions Made
- Single-threaded execution (no concurrency concerns)
- Memory-based storage is sufficient for this milestone
- Standard Python datetime handling is acceptable
- Simple string-based categorization is sufficient for notes and tasks