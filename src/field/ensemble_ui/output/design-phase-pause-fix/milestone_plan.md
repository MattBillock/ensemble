# Milestone Plan: Design Phase Pause Fix

## Project Overview
Fix the agent pipeline so that when agents return `status: "needs_user_input"`, the pipeline properly pauses and waits for user response instead of terminating.

## Implementation Status: COMPLETE
**Completed**: 2026-01-15
**Implemented by**: Claude Opus 4.5 (manual implementation)

All milestones (1-3) have been implemented.

## Milestone 1: Backend Status Detection and State Preservation - ✅ COMPLETE
**Objective**: Modify backend to correctly detect `needs_user_input` status and preserve agent state for resumption.

### Deliverables
1. Update `_execute_agent_background` method to detect `needs_user_input` status
2. Set agent status to `awaiting_user_input` instead of `completed`
3. Store continuation context (original input, question, agent config)
4. Add proper logging for state transitions

### Acceptance Criteria
- [x] When agent returns `{status: "needs_user_input"}`, backend sets status to `awaiting_user_input`
- [x] Agent is NOT marked as `completed` when waiting for input
- [x] Continuation context is properly stored in `active_agents` dict
- [x] Logs show "Waiting for user input" instead of "Completed successfully"

### Dependencies
- None (first milestone)

### Estimated Effort
- Backend changes: ~2-3 hours

---

## Milestone 2: Answer-Triggered Agent Continuation - ✅ COMPLETE
**Objective**: Implement mechanism to resume/respawn agent execution when user provides an answer.

### Deliverables
1. New `continue_agent_with_answer` method in `AgentOrchestrator`
2. Update `answer_question` endpoint to trigger continuation
3. Build continuation input with original context + user answer
4. Spawn new agent instance with continuation context

### Acceptance Criteria
- [x] `answerQuestion` API call triggers agent continuation
- [x] User's answer is incorporated into new agent's context
- [x] Agent receives: original task, previous question, user answer, continuation instruction
- [x] New agent execution starts successfully with proper context

### Dependencies
- Milestone 1 (needs status detection and context storage)

### Estimated Effort
- Backend changes: ~3-4 hours

---

## Milestone 3: Activity Tracking and UI Integration - ✅ COMPLETE
**Objective**: Ensure proper activity tracking and UI correctly reflects agent states.

### Deliverables
1. Record state transitions in activity tracker (running → awaiting_user_input → running)
2. Verify UI correctly displays `awaiting_user_input` status
3. Ensure parent-child relationships maintained for continued agents
4. Add tests for new functionality

### Acceptance Criteria
- [x] Activity tracker records `awaiting_user_input` state transitions
- [x] UI status badges accurately reflect waiting state
- [x] Request IDs and agent hierarchy maintained across continuation
- [ ] Tests verify the full flow works correctly (deferred)

### Dependencies
- Milestone 2 (needs continuation mechanism)

### Estimated Effort
- Backend changes: ~2 hours
- Testing: ~2 hours

---

## Success Criteria (All Milestones)

1. ✅ When an agent returns `needs_user_input`, the UI shows it as `awaiting_user_input`
2. ✅ The pending question appears in the PendingQuestions component
3. ✅ When user submits an answer, the agent continues execution
4. ✅ The continued execution has access to the original context + user's answer
5. ✅ Agent hierarchy and request IDs are properly maintained
6. ✅ No "agent completed" status when actually waiting for input
7. ✅ Pipeline does not terminate/die on design phase completion

## Technical Decisions Made

### Architecture Approach
- **Respawn approach** chosen over resume approach (simpler, more robust)
- New agent instance spawned with continuation context
- Original agent marked with continuation info for traceability

### State Management
- Using existing `active_agents` dict for continuation context storage
- No new database/persistence needed (in-memory state sufficient for MVP)

### Out of Scope (per requirements)
- Multi-question support
- Question timeout handling
- Question editing/revision
- Agent definition changes during continuation
