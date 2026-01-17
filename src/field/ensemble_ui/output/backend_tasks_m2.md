# Backend Tasks - Question-Answer Flow Implementation

## Milestone Overview
Fix the agent pipeline termination issue when agents return `needs_user_input` status during the design phase. The system must pause execution, wait for user input, and continue with proper context preservation.

## Task Breakdown

### Foundation Tasks

#### Task 1: Agent Status Detection Enhancement
**Description**: Modify `_execute_agent_background` method to properly detect and handle `needs_user_input` status from agent results.

**Acceptance Criteria**:
- Method detects `status: "needs_user_input"` in agent response
- Agent marked as `"awaiting_user_input"` instead of "completed"
- Agent execution stops without terminating pipeline
- Logs indicate waiting state with clear message

**Dependencies**: None
**Complexity**: Simple
**Test Requirements**: Unit test for status detection logic

#### Task 2: Agent Context Preservation System
**Description**: Implement context storage system to preserve agent state for continuation after user input.

**Acceptance Criteria**:
- `active_agents[agent_id]` stores `awaiting_question_id` field
- `continuation_context` field stores resumption data
- Context includes: original input, question asked, agent type info
- Data structure supports state transitions

**Dependencies**: Task 1
**Complexity**: Medium
**Test Requirements**: Unit tests for context storage and retrieval

#### Task 3: Continue Agent Method Implementation
**Description**: Create new `continue_agent_with_answer` method to spawn fresh agent with continuation context after receiving user answer.

**Acceptance Criteria**:
- Method accepts question_id and user answer
- Builds proper continuation context with original task + answer
- Spawns Executive Director agent with continuation instructions
- Returns agent_id for new execution thread

**Dependencies**: Task 2
**Complexity**: Medium
**Test Requirements**: Unit tests for context building and agent spawning

### Integration Tasks

#### Task 4: Answer Question Endpoint Enhancement
**Description**: Modify existing `answer_question` endpoint to trigger agent continuation using BackgroundTasks for async processing.

**Acceptance Criteria**:
- Endpoint records answer using existing question system
- Finds agent waiting for specific question_id
- Calls `continue_agent_with_answer` asynchronously
- Returns immediate response without blocking
- Handles missing agents/invalid question_ids gracefully

**Dependencies**: Task 3
**Complexity**: Medium
**Test Requirements**: Integration test for endpoint flow

#### Task 5: State Transition Management
**Description**: Implement proper state transitions for agents going through question-answer flow.

**Acceptance Criteria**:
- State flow: `running → awaiting_user_input → [answer] → running → completed`
- State changes reflected in agent status tracking
- UI receives appropriate status updates
- No race conditions in state transitions

**Dependencies**: Tasks 1, 2, 3
**Complexity**: Simple
**Test Requirements**: Integration tests for state transitions

### Testing Tasks

#### Task 6: Unit Test Suite Implementation
**Description**: Implement comprehensive unit tests for all new functionality following TDD approach.

**Test Coverage**:
- `_execute_agent_background` status detection
- Context preservation and structure validation  
- `continue_agent_with_answer` input building
- State transition logic
- Question_id matching functionality

**Dependencies**: Tasks 1-5
**Complexity**: Medium
**Test Requirements**: Full pytest suite with >95% coverage

#### Task 7: Integration Test Suite Implementation  
**Description**: Implement end-to-end integration tests for question-answer flow.

**Test Scenarios**:
- Mock agent returns `needs_user_input` → verify awaiting status
- Submit answer → verify new agent spawned with context
- Complete flow from question through continuation to completion
- Error handling for invalid question_ids/missing agents

**Dependencies**: Task 6
**Complexity**: Complex
**Test Requirements**: Full integration test suite with mock agents

### Error Handling & Edge Cases

#### Task 8: Error Handling Implementation
**Description**: Implement robust error handling for edge cases in question-answer flow.

**Acceptance Criteria**:
- Graceful handling of missing agents for question_id
- Invalid question_id error responses
- Agent continuation failures don't crash pipeline
- Proper logging for all error conditions
- Fallback mechanisms for corrupted context

**Dependencies**: Tasks 1-5
**Complexity**: Medium
**Test Requirements**: Error condition unit tests

#### Task 9: Backwards Compatibility Validation
**Description**: Ensure all changes maintain backwards compatibility with existing agent execution flows.

**Acceptance Criteria**:
- Normal (non-question) agents execute unchanged
- Existing API endpoints maintain same behavior
- No performance regression in standard flows
- All existing tests continue passing

**Dependencies**: All previous tasks
**Complexity**: Simple
**Test Requirements**: Regression test suite

### Documentation & Final Tasks

#### Task 10: Code Documentation
**Description**: Add comprehensive documentation for all new methods and data structures.

**Acceptance Criteria**:
- All new methods have docstrings with examples
- Data structure changes documented
- State transition diagram included
- API endpoint documentation updated

**Dependencies**: Tasks 1-9
**Complexity**: Simple
**Test Requirements**: Documentation review

## Task Dependencies Map
```
Foundation Layer:
Task 1 (Status Detection) → Task 2 (Context Preservation) → Task 3 (Continue Method)

Integration Layer:  
Task 4 (Answer Endpoint) ← Task 3
Task 5 (State Transitions) ← Tasks 1,2,3

Testing Layer:
Task 6 (Unit Tests) ← Tasks 1-5
Task 7 (Integration Tests) ← Task 6

Quality Layer:
Task 8 (Error Handling) ← Tasks 1-5
Task 9 (Backwards Compatibility) ← All Previous
Task 10 (Documentation) ← Tasks 1-9
```

## Critical Path
Task 1 → Task 2 → Task 3 → Task 4 → Task 6 → Task 7

## Implementation Priority
1. **Phase 1** (Core): Tasks 1-3 (Foundation functionality)
2. **Phase 2** (Integration): Tasks 4-5 (Endpoint integration) 
3. **Phase 3** (Validation): Tasks 6-7 (Testing)
4. **Phase 4** (Quality): Tasks 8-10 (Error handling & docs)

## Technical Notes
- **Framework**: FastAPI backend with async/await patterns
- **Testing**: pytest with comprehensive unit and integration coverage
- **Error Strategy**: Fail gracefully without crashing pipeline
- **Context Format**: JSON-serializable data structures
- **Async Pattern**: BackgroundTasks for non-blocking continuation

## Success Metrics
- ✅ No pipeline termination on `needs_user_input` status
- ✅ User sees "waiting" status in UI 
- ✅ Agent continues with full context after answer
- ✅ All tests pass (unit + integration)
- ✅ Zero regression in normal agent flows