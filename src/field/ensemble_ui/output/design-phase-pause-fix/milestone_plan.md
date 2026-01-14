# Milestone Plan: Design Phase Pause Fix

## Project Overview
Fix the agent pipeline so that when agents return `status: "needs_user_input"`, the pipeline properly pauses and waits for user response instead of terminating.

## Milestone 1: Backend Status Detection and State Preservation
**Objective**: Modify backend to correctly detect `needs_user_input` status and preserve agent state for resumption.

### Deliverables
1. Update `_execute_agent_background` method to detect `needs_user_input` status
2. Set agent status to `awaiting_user_input` instead of `completed`
3. Store continuation context (original input, question, agent config)
4. Add proper logging for state transitions

### Acceptance Criteria
- [ ] When agent returns `{status: "needs_user_input"}`, backend sets status to `awaiting_user_input`
- [ ] Agent is NOT marked as `completed` when waiting for input
- [ ] Continuation context is properly stored in `active_agents` dict
- [ ] Logs show "Waiting for user input" instead of "Completed successfully"

### Dependencies
- None (first milestone)

### Estimated Effort
- Backend changes: ~2-3 hours

---

## Milestone 2: Answer-Triggered Agent Continuation
**Objective**: Implement mechanism to resume/respawn agent execution when user provides an answer.

### Deliverables
1. New `continue_agent_with_answer` method in `AgentOrchestrator`
2. Update `answer_question` endpoint to trigger continuation
3. Build continuation input with original context + user answer
4. Spawn new agent instance with continuation context

### Acceptance Criteria
- [ ] `answerQuestion` API call triggers agent continuation
- [ ] User's answer is incorporated into new agent's context
- [ ] Agent receives: original task, previous question, user answer, continuation instruction
- [ ] New agent execution starts successfully with proper context

### Dependencies
- Milestone 1 (needs status detection and context storage)

### Estimated Effort
- Backend changes: ~3-4 hours

---

## Milestone 3: Activity Tracking and UI Integration
**Objective**: Ensure proper activity tracking and UI correctly reflects agent states.

### Deliverables
1. Record state transitions in activity tracker (running → awaiting_user_input → running)
2. Verify UI correctly displays `awaiting_user_input` status
3. Ensure parent-child relationships maintained for continued agents
4. Add tests for new functionality

### Acceptance Criteria
- [ ] Activity tracker records `awaiting_user_input` state transitions
- [ ] UI status badges accurately reflect waiting state
- [ ] Request IDs and agent hierarchy maintained across continuation
- [ ] Tests verify the full flow works correctly

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
