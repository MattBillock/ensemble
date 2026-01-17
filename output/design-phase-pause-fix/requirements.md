# Requirements: Design Phase Pause Fix Implementation

## Project Overview
**Project Name**: Design Phase Pause Fix Implementation
**Purpose**: Fix the agent pipeline termination issue when agents return `needs_user_input` status during the design phase
**Priority**: High - critical bug fix
**TDD Required**: Yes - write tests first, then implementation

## Problem Statement
Currently, when an Executive Director agent returns `status: "needs_user_input"` during the design phase, the backend incorrectly marks the agent as "completed" instead of pausing execution to wait for user input. This causes the pipeline to terminate prematurely, preventing proper user interaction and continuation.

## Core Requirements

### 1. Agent Status Handling (CRITICAL)
- **REQ-001**: `_execute_agent_background` method MUST detect `needs_user_input` status from agent results
- **REQ-002**: Agents with `needs_user_input` status MUST be marked as `"awaiting_user_input"` (NOT "completed")
- **REQ-003**: Agent context MUST be preserved for later continuation including:
  - Original input data
  - Question asked to user
  - Agent type information
- **REQ-004**: Agent logs MUST reflect waiting state with appropriate message

### 2. Question-Answer Flow (CRITICAL)
- **REQ-005**: `answer_question` endpoint MUST trigger agent continuation after recording answer
- **REQ-006**: System MUST match answers to waiting agents using question_id
- **REQ-007**: Answer processing MUST happen asynchronously to avoid blocking response

### 3. Agent Continuation (CRITICAL) 
- **REQ-008**: New `continue_agent_with_answer` method MUST spawn fresh agent with continuation context
- **REQ-009**: Continuation context MUST include:
  - Original task input
  - Previous question
  - User's answer
  - Clear instruction to continue implementation
- **REQ-010**: Agent continuation MUST use Executive Director agent type for consistency

### 4. Data Structure Requirements
- **REQ-011**: `active_agents[agent_id]` MUST support new fields:
  - `awaiting_question_id`: Links agent to pending question
  - `continuation_context`: Stores resumption data
- **REQ-012**: Status field MUST support `"awaiting_user_input"` state
- **REQ-013**: State transitions MUST follow: `running → awaiting_user_input → [answer] → running → completed`

## Implementation Scope

### Files to Modify
- **Primary**: `backend/main.py` - All core changes
- **Secondary**: Test files for validation

### Components to Change
1. **`_execute_agent_background` method** (modify existing)
2. **`answer_question` endpoint** (modify existing) 
3. **`continue_agent_with_answer` method** (add new)

## Testing Requirements (TDD)

### Unit Tests (MUST IMPLEMENT)
- **TEST-001**: Verify `_execute_agent_background` correctly detects `needs_user_input`
- **TEST-002**: Verify continuation context is properly stored and structured
- **TEST-003**: Verify `continue_agent_with_answer` builds correct input data
- **TEST-004**: Verify state transitions work correctly
- **TEST-005**: Verify question_id matching logic works

### Integration Tests (MUST IMPLEMENT)
- **TEST-006**: Mock agent returns `needs_user_input` → verify status becomes `awaiting_user_input`
- **TEST-007**: Submit answer → verify new agent spawned with correct context
- **TEST-008**: End-to-end flow from question through continuation to completion

## Success Criteria
- ✅ Agent pipeline NO LONGER terminates when `needs_user_input` is returned
- ✅ User sees appropriate "waiting" status in UI
- ✅ User can provide answer and agent continues with full context
- ✅ All tests pass (unit + integration)
- ✅ No regression in normal (non-question) agent execution flow

## Out of Scope
- Persistent storage for paused agents (agents lost on server restart)
- Multiple question support (one question per agent session)
- Question timeout handling
- Hot reload of agent definitions during continuation
- UI changes (backend focus only)

## Technical Constraints
- **Language**: Python (FastAPI backend)
- **Testing Framework**: pytest
- **Async**: Must use async/await patterns for continuations
- **Backwards Compatibility**: Must not break existing agent execution
- **Error Handling**: Must gracefully handle missing agents or invalid question_ids

## Assumptions
- Question tracking system already exists and works correctly
- Executive Director agent can handle continuation context appropriately
- UI will properly display `awaiting_user_input` status
- Single concurrent answer per question_id (no race conditions expected)

## Dependencies
- Existing `AgentOrchestrator` class
- Existing question tracking system
- FastAPI BackgroundTasks for async processing
- Current agent spawning infrastructure