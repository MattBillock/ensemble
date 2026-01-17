# Frontend Tasks - Core Bug Fixes

## Overview
This milestone focuses on fixing activity tracking bugs in the backend Python components. While primarily backend-focused, there are minimal frontend implications for testing and verification.

## Component Analysis

### Backend Components (Primary Focus)
- `WriteFileTool` class in `src/runtime/agents/tools.py`
- `ActivityTracker` class in `src/runtime/agents/activity_tracker.py` 
- Tool registry and context propagation

### Frontend Components (Testing & Verification)
- Activity tracking endpoints (`/api/activity/files`, `/api/activity/timeline`)
- UI components that display agent activity metrics
- Testing utilities for verifying activity tracking

## Task Breakdown

### Task 1: Backend WriteFileTool Enhancement
**Type**: Backend Enhancement  
**Complexity**: Medium  
**Component**: `src/runtime/agents/tools.py`

**Description**: 
Modify WriteFileTool to accept optional tracking context parameters and record file generation to ActivityTracker when context is provided.

**Acceptance Criteria**:
- WriteFileTool.__init__() accepts agent_id, agent_name, request_id parameters
- WriteFileTool.execute() calls ActivityTracker.record_file_generated() when context provided
- Maintains backward compatibility (works without tracking context)
- ToolRegistry.default() passes tracking context to WriteFileTool

**Dependencies**: None

---

### Task 2: Backend ActivityTracker Auto-Increment
**Type**: Backend Enhancement  
**Complexity**: Simple  
**Component**: `src/runtime/agents/activity_tracker.py`

**Description**:
Add automatic increment calls to activity tracking methods to ensure request counts update correctly.

**Acceptance Criteria**:
- record_agent_started() calls increment_request_counts()
- record_file_generated() calls increment_request_counts(files=1)  
- record_git_commit() calls increment_request_counts(commits=1)
- Counters update automatically when activities occur

**Dependencies**: None

---

### Task 3: Backend Integration Tests
**Type**: Testing  
**Complexity**: Medium  
**Component**: Test files for activity tracking

**Description**:
Create comprehensive tests to verify WriteFileTool and ActivityTracker integration works correctly.

**Acceptance Criteria**:
- Test WriteFileTool with tracking context records to ActivityTracker
- Test WriteFileTool without context maintains compatibility
- Test increment_request_counts updates counters correctly
- Integration test: file generation flows through to activity APIs
- All existing tests continue to pass

**Dependencies**: Task 1, Task 2

---

### Task 4: Frontend Verification Testing
**Type**: Frontend Testing  
**Complexity**: Simple  
**Component**: Activity tracking UI verification

**Description**:
Verify that frontend activity tracking displays work correctly after backend fixes are implemented.

**Acceptance Criteria**:
- Activity endpoints return non-zero counts after agent activity
- UI components display accurate file generation metrics
- Timeline shows correct agent activity counts
- No frontend code changes required (verification only)

**Dependencies**: Task 1, Task 2, Task 3

---

## Implementation Order

1. **Task 1 & 2** (Parallel): Backend enhancements to WriteFileTool and ActivityTracker
2. **Task 3**: Integration testing of backend changes  
3. **Task 4**: Frontend verification testing

## Technical Notes

### No Frontend Code Changes Required
This milestone is primarily backend-focused. The frontend UI components that display activity tracking metrics should automatically show correct data once the backend tracking is fixed.

### Testing Strategy
- Unit tests for WriteFileTool tracking context
- Integration tests for activity tracking flow
- Frontend verification that existing UI works with fixed backend

### Risk Assessment
- **Low Risk**: Changes are localized to backend tracking components
- **Compatibility**: Backward compatibility maintained throughout
- **Performance**: Minimal impact from lightweight tracking calls

## Ready for TDD Coordinator

This task breakdown is ready for implementation via TDD Coordinator. The tasks are clearly defined with specific acceptance criteria and focus on fixing the core activity tracking bugs without requiring frontend code changes.