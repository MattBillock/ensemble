# Executive Director Project Awareness - Milestone Plan

## Project Overview
Add project awareness capabilities to Executive Directors, enabling context maintenance about active projects through descriptive names, notes (proto-history), and task tracking.

## Implementation Status: PARTIAL
**Last Updated**: 2026-01-15
**Implemented by**: Claude Opus 4.5 (manual implementation)

Milestone 1 (Core Data Models) complete. Milestones 2-3 pending.

## Milestone 1: Core Data Models - ✅ COMPLETE
**Objective**: Create the fundamental data structures for project awareness

**Deliverables**:
- `ProjectNote` dataclass with timestamp, content, category, and related_task_id
- `Task` dataclass with id, description, priority, status, timestamps, and outcome
- `ProjectContext` class with project metadata, notes list, and task lists
- Serialization methods (to_dict, from_dict) for JSON persistence
- Unit tests for all data structures

**Acceptance Criteria**:
- [x] All classes are properly typed with type hints
- [x] Serialization/deserialization roundtrips without data loss
- [ ] All tests pass (tests deferred)
- [x] Compatible with Python 3.9+

**Dependencies**: None

---

## Milestone 2: StateManager Integration - ⏳ PENDING
**Objective**: Integrate ProjectContext with existing StateManager for persistence

**Deliverables**:
- Updated StateManager to include `project_context` field in state schema
- Auto-save project context on checkpoint
- Auto-load project context on resume
- Methods to access and update project context
- Integration tests for persistence

**Acceptance Criteria**:
- Project context survives agent iterations
- Backward compatible with existing state files (no project_context = None)
- Checkpoint includes project context
- Resume restores project context

**Dependencies**: Milestone 1

---

## Milestone 3: Executive Director Definition Updates - ⏳ PENDING
**Objective**: Update Executive Director agent to utilize project context

**Deliverables**:
- Updated input format to accept optional `project_context`
- Updated output format to include current `project_context` state
- Instructions for maintaining project awareness
- Examples for when to add notes and update tasks

**Acceptance Criteria**:
- Executive Director can initialize with project name
- Output includes serialized project context
- Instructions are clear and actionable
- Backward compatible (existing invocations still work)

**Dependencies**: Milestone 1, Milestone 2

---

## Technical Decisions Made
1. **File Location**: `src/runtime/agents/project_context.py` (as specified in requirements)
2. **UUID Library**: Use standard library `uuid.uuid4()` for task IDs
3. **Datetime Format**: ISO 8601 as specified in requirements
4. **Note Categories**: "decision", "observation", "milestone", "blocker", "general"
5. **Task Priorities**: "high", "medium", "low"
6. **Task Statuses**: "pending", "in_progress", "completed", "blocked"

## Timeline
Each milestone should be completed sequentially. Milestone 1 is the foundation, Milestone 2 enables persistence, and Milestone 3 integrates with the agent system.
