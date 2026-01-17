# Test Strategy - Core Bug Fixes

## Overview
This document defines the testing strategy for fixing activity tracking bugs in the Ensemble UI. The fixes address three interconnected issues: WriteFileTool tracking, auto-increment calls, and global file tracking visibility.

## Test Strategy Summary

### Coverage Goals
- **Unit Test Coverage**: 85% for new tracking logic
- **Integration Coverage**: 100% of tracking workflows
- **Regression Coverage**: All existing functionality

### Test Types

#### 1. Unit Tests
Focus on individual component behavior with mocked dependencies.

#### 2. Integration Tests  
Test component interactions and data flow through tracking system.

#### 3. Regression Tests
Ensure backward compatibility and existing functionality.

---

## Test Task Breakdown

### Task 1: WriteFileTool Unit Tests
**Type**: Unit Test  
**Priority**: High  
**Estimated Effort**: 4 hours

**Test Scenarios**:
1. **Test WriteFileTool with tracking context**
   - Initialize WriteFileTool with agent_id, agent_name, request_id
   - Execute file write operation
   - Verify ActivityTracker.record_file_generated() called with correct parameters
   - Verify original file writing functionality preserved

2. **Test WriteFileTool without tracking context**
   - Initialize WriteFileTool with no tracking parameters
   - Execute file write operation
   - Verify ActivityTracker.record_file_generated() NOT called
   - Verify file still written successfully (backward compatibility)

3. **Test WriteFileTool partial context**
   - Initialize with only some tracking parameters (e.g., agent_id but no request_id)
   - Verify graceful handling of partial context
   - Verify tracking still occurs when agent_id present

**Mocks Required**:
- Mock `write_file()` function
- Mock `ActivityTracker.record_file_generated()`

**Assertions**:
- File writing behavior unchanged
- Tracking calls made only when context provided
- Correct parameters passed to tracking methods

---

### Task 2: ActivityTracker Enhancement Unit Tests
**Type**: Unit Test  
**Priority**: High  
**Estimated Effort**: 3 hours

**Test Scenarios**:
1. **Test record_file_generated() auto-increment**
   - Call record_file_generated() with valid parameters
   - Verify increment_request_counts() called with files=1
   - Verify file event logging occurs

2. **Test record_agent_started() auto-increment**
   - Call record_agent_started() 
   - Verify increment_request_counts() called with agents=1
   - Verify agent start event logging

3. **Test record_git_commit() auto-increment**
   - Call record_git_commit()
   - Verify increment_request_counts() called with commits=1
   - Verify git commit event logging

**Mocks Required**:
- Mock `increment_request_counts()`
- Mock logging functions

**Assertions**:
- Auto-increment calls made with correct parameters
- Event logging occurs for each activity type
- Error handling for invalid parameters

---

### Task 3: ToolRegistry Integration Tests
**Type**: Integration Test  
**Priority**: Medium  
**Estimated Effort**: 3 hours

**Test Scenarios**:
1. **Test ToolRegistry.default() with tracking context**
   - Call ToolRegistry.default() with agent context
   - Verify WriteFileTool initialized with tracking parameters
   - Test end-to-end file writing with tracking

2. **Test ToolRegistry.default() without tracking context**
   - Call ToolRegistry.default() with no agent context
   - Verify WriteFileTool works without tracking
   - Ensure backward compatibility

**Mocks Required**:
- Minimal mocking - test near real conditions
- Mock file system for safety

**Assertions**:
- Tools properly initialized with context
- Tracking flows through tool registry
- No errors with missing context

---

### Task 4: Activity Tracking End-to-End Tests
**Type**: Integration Test  
**Priority**: High  
**Estimated Effort**: 5 hours

**Test Scenarios**:
1. **Test complete file generation tracking flow**
   - Initialize agent with tracking context
   - Execute multiple file write operations
   - Verify files appear in `/api/activity/files` endpoint
   - Verify request counts increment correctly

2. **Test mixed tracking scenarios**
   - Execute file operations with and without tracking
   - Verify only tracked operations appear in activity data
   - Verify counts reflect only tracked operations

3. **Test activity timeline integration**
   - Perform various tracked activities (files, commits, agent starts)
   - Query activity timeline endpoint
   - Verify accurate counts in timeline data

**Test Environment**:
- Real ActivityTracker instance
- Mock API endpoints for verification
- Temporary file system for file operations

**Assertions**:
- Activity data accurately reflects operations
- Timeline shows correct counts
- File list contains expected entries

---

### Task 5: Backward Compatibility Regression Tests
**Type**: Regression Test  
**Priority**: High  
**Estimated Effort**: 4 hours

**Test Scenarios**:
1. **Test existing WriteFileTool usage patterns**
   - Run existing test suite against modified WriteFileTool
   - Verify all existing tests pass
   - Test legacy initialization patterns

2. **Test existing agent workflows**
   - Execute typical agent file generation workflows
   - Verify no breaking changes in agent behavior
   - Test error handling unchanged

3. **Test API endpoint compatibility**
   - Verify activity endpoints return expected format
   - Test with both tracked and untracked data
   - Ensure no API contract changes

**Test Data**:
- Use existing test fixtures
- Create scenarios matching current production usage

**Assertions**:
- All existing functionality preserved
- No performance regression
- API contracts unchanged

---

### Task 6: Performance and Error Handling Tests
**Type**: Unit/Integration Test  
**Priority**: Medium  
**Estimated Effort**: 3 hours

**Test Scenarios**:
1. **Test performance impact**
   - Benchmark file operations with/without tracking
   - Verify tracking overhead < 5ms per operation
   - Test with large file operations

2. **Test error handling**
   - Test tracking with invalid parameters
   - Test ActivityTracker failures
   - Verify graceful degradation when tracking fails

3. **Test concurrent operations**
   - Multiple agents writing files simultaneously
   - Verify tracking accuracy under load
   - Test thread safety of tracking operations

**Performance Targets**:
- Tracking overhead: < 5ms per operation
- Memory overhead: < 1MB for tracking data structures
- No blocking behavior in file operations

**Assertions**:
- Performance within acceptable limits
- Graceful error handling
- No data corruption under concurrent load

---

## Test Execution Strategy

### Phase 1: Unit Tests (Tasks 1-2)
- Run in isolation with full mocking
- Fast feedback on individual components
- Target: 90%+ code coverage

### Phase 2: Integration Tests (Tasks 3-4) 
- Test component interactions
- Verify data flow correctness
- Target: 100% workflow coverage

### Phase 3: Regression Tests (Task 5)
- Validate backward compatibility
- Run existing test suite
- Target: Zero breaking changes

### Phase 4: Performance Tests (Task 6)
- Validate performance requirements
- Test under load
- Target: < 5ms overhead

## Test Environment Requirements

### Dependencies
- pytest framework
- Mock library for unit tests
- Temporary file system access
- Test database/activity tracker instance

### Test Data
- Sample agent contexts (agent_id, agent_name, request_id)
- Various file content scenarios
- Activity tracker state fixtures

### Continuous Integration
- All tests must pass before merge
- Coverage reports generated
- Performance benchmarks recorded

## Success Criteria

### Functional
- All tracking workflows working correctly
- File generation properly recorded
- Request counts accurately updated

### Quality
- 85%+ unit test coverage
- 100% integration test coverage
- Zero regression test failures

### Performance  
- Tracking overhead < 5ms
- No memory leaks
- Graceful error handling

## Risk Mitigation

### Circular Import Risk
- Test import order in multiple scenarios
- Verify local import patterns work

### Performance Risk
- Benchmark tracking operations
- Test with large file scenarios
- Monitor memory usage

### Compatibility Risk
- Extensive regression testing
- Test various initialization patterns
- Validate API contract preservation

---

## Test Tasks Summary

| Task | Type | Priority | Effort | Focus |
|------|------|----------|--------|-------|
| 1 | Unit | High | 4h | WriteFileTool tracking |
| 2 | Unit | High | 3h | ActivityTracker enhancements |
| 3 | Integration | Medium | 3h | ToolRegistry integration |
| 4 | Integration | High | 5h | End-to-end tracking flow |
| 5 | Regression | High | 4h | Backward compatibility |
| 6 | Performance | Medium | 3h | Performance & error handling |

**Total Estimated Effort**: 22 hours  
**Critical Path**: Tasks 1 → 2 → 4 → 5