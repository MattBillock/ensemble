# Requirements: Fix Agent Pipeline Design Phase Termination

## Problem Statement
When agents complete the design phase and return `status: "needs_user_input"`, the development pipeline terminates/dies instead of generating a pending task for the user and waiting for their response. This causes the entire agent pipeline to stop prematurely.

## Root Cause Analysis

### Current Behavior (Broken)
1. Agent (e.g., Executive Director) returns `{"status": "needs_user_input", "user_question": "..."}`
2. Runtime correctly:
   - Records the question in activity tracker
   - Adds `question_id` and `awaiting_user_input` to response
   - Returns the response to backend
3. Backend (`_execute_agent_background`) incorrectly:
   - Sets agent status to `"completed"` regardless of `needs_user_input`
   - Logs "Completed successfully"
   - No continuation mechanism is triggered
4. UI shows:
   - Agent marked as "completed" (wrong - should be "awaiting_user_input")
   - Question appears in PendingQuestions component
   - User can submit an answer via `answerQuestion` API
5. Answer handling (`record_answer`):
   - Updates question record with answer
   - Updates agent state to "running" (optimistic)
   - BUT does not actually resume the agent execution

### Desired Behavior (Fixed)
1. Agent returns `{"status": "needs_user_input", "user_question": "..."}`
2. Runtime correctly records question (already works)
3. Backend should:
   - Detect `needs_user_input` status in result
   - Set agent status to `"awaiting_user_input"` (NOT "completed")
   - Store the execution state for resumption
4. UI should:
   - Show agent as "awaiting_user_input" with prominent question badge
   - Display question in PendingQuestions component (already works)
5. When user answers:
   - Resume agent execution with user's answer as input
   - Agent continues from where it left off

## Requirements

### Functional Requirements

#### FR1: Backend Status Detection
- When agent result contains `status: "needs_user_input"`, backend MUST set agent status to `"awaiting_user_input"`
- Agent should NOT be marked as "completed" when waiting for user input
- Affected file: `src/field/ensemble_ui/backend/main.py`
- Location: `_execute_agent_background` method

#### FR2: Agent State Preservation
- When agent returns `needs_user_input`, preserve execution context for resumption:
  - Agent definition and configuration
  - Original input data
  - Question ID and question text
  - Request ID for tracing
- Store this in `active_agents` dict for the waiting agent

#### FR3: Answer-Triggered Continuation
- When `answerQuestion` API is called, it must trigger agent continuation
- Two approaches (choose one):
  1. **Respawn approach**: Start a new agent instance with original context + user answer
  2. **Resume approach**: Use runtime's `set_user_answer` and resume execution (more complex)
- Recommended: Respawn approach (simpler, more robust)

#### FR4: Answer Integration in New Execution
- User's answer must be incorporated into the new agent's context
- The agent should receive:
  - Original task/requirements
  - Previous agent's question
  - User's answer
  - Instruction to continue based on clarification

#### FR5: Activity Tracker Updates
- Record state transitions: running → awaiting_user_input → running → completed
- Record answer received event
- Maintain proper hierarchy for resumed/respawned agents

### Non-Functional Requirements

#### NFR1: No Pipeline Death
- Agent pipeline must never terminate when user input is needed
- System must remain responsive and ready to accept answers

#### NFR2: UI Visibility
- Users must clearly see which agents need input
- Status badges should accurately reflect "awaiting_user_input" state

#### NFR3: Traceability
- Request IDs and parent-child relationships must be maintained across continuation

## Technical Design

### Changes Required

#### 1. `backend/main.py` - `_execute_agent_background` method
```python
# After getting result, check for needs_user_input
if result and result.get("status") == "needs_user_input":
    self.active_agents[agent_id]["status"] = "awaiting_user_input"
    self.active_agents[agent_id]["awaiting_question_id"] = result.get("question_id")
    self.active_agents[agent_id]["continuation_context"] = {
        "original_input": input_data,
        "question": result.get("user_question"),
        "agent_def_path": exec_dir_path  # or however agent is loaded
    }
    self.active_agents[agent_id]["logs"].append(f"❓ Waiting for user input: {result.get('user_question', 'No question provided')}")
    return  # Don't mark as completed
```

#### 2. `backend/main.py` - Answer handling endpoint
Currently, `record_answer` just updates the activity tracker. Need to add:
```python
@app.post("/api/activity/questions/{question_id}/answer")
async def answer_question(question_id: str, answer: dict, background_tasks: BackgroundTasks):
    # ... existing code ...
    
    # Find the agent waiting for this answer
    for agent_id, agent_info in orchestrator.active_agents.items():
        if agent_info.get("awaiting_question_id") == question_id:
            # Trigger continuation with answer
            background_tasks.add_task(
                orchestrator.continue_agent_with_answer,
                agent_id,
                answer["answer"]
            )
            break
```

#### 3. `backend/main.py` - New continuation method
```python
def continue_agent_with_answer(self, agent_id: str, answer: str):
    """Continue an agent execution after receiving user answer."""
    agent_info = self.active_agents.get(agent_id)
    if not agent_info:
        return
    
    context = agent_info.get("continuation_context", {})
    original_input = context.get("original_input", {})
    question = context.get("question", "")
    
    # Build continuation input with answer context
    continuation_input = {
        **original_input,
        "continuation_context": {
            "previous_question": question,
            "user_answer": answer,
            "instruction": "The user has answered your question. Please continue with implementation based on their clarification."
        }
    }
    
    # Spawn new executive director with continuation context
    # ... similar to spawn_executive_director but with continuation_input
```

#### 4. Activity Tracker - New event type (optional but recommended)
Add `AWAITING_USER_INPUT` state transition for better tracking.

## Success Criteria

1. ✅ When an agent returns `needs_user_input`, the UI shows it as "awaiting_user_input"
2. ✅ The pending question appears in the PendingQuestions component
3. ✅ When user submits an answer, the agent continues execution
4. ✅ The continued execution has access to the original context + user's answer
5. ✅ Agent hierarchy and request IDs are properly maintained
6. ✅ No "agent completed" status when actually waiting for input
7. ✅ Pipeline does not terminate/die on design phase completion

## Out of Scope
- Multi-question support (handle one question at a time for now)
- Question timeout handling
- Question editing/revision
- Agent definition changes (use existing agent structure)

## Assumptions
- Only one question per agent at a time
- User will provide an answer (no timeout handling needed initially)
- Continuation uses the same budget tier as original execution
- Agent definitions are stable (no hot-reload during continuation)

## Dependencies
- Existing activity tracker infrastructure (works correctly)
- Existing PendingQuestions UI component (works correctly)
- Existing answerQuestion API endpoint (needs enhancement)
