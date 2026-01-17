# Architecture: Design Phase Pause Fix

## Overview
This document outlines the architectural changes needed to fix the agent pipeline design phase termination issue. The fix is focused on the backend `main.py` file with minimal architectural impact.

## Current Architecture (Broken Flow)

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Agent     │      │   Runtime   │      │   Backend   │      │     UI      │
│  (ED)       │─────▶│  Execute    │─────▶│ Background  │─────▶│  Display    │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
       │                    │                    │                    │
       │ returns            │ records            │ sets status        │ shows
       │ needs_user_input   │ question           │ to "completed"     │ "completed"
       │                    │ correctly          │ (WRONG!)           │ (WRONG!)
       └────────────────────┴────────────────────┴────────────────────┘
                                   ✗ PIPELINE ENDS
```

## Target Architecture (Fixed Flow)

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Agent     │      │   Runtime   │      │   Backend   │      │     UI      │
│  (ED)       │─────▶│  Execute    │─────▶│ Background  │─────▶│  Display    │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
       │                    │                    │                    │
       │ returns            │ records            │ sets status to     │ shows
       │ needs_user_input   │ question           │ "awaiting_user_    │ "waiting"
       │                    │ correctly          │ input" + stores    │ badge
       │                    │                    │ context            │
       │                    │                    │                    │
       ▼                    │                    ▼                    ▼
┌─────────────┐             │            ┌─────────────┐      ┌─────────────┐
│ User        │             │            │ Backend     │      │ UI shows    │
│ sees        │─────────────┴───────────▶│ receives    │─────▶│ agent       │
│ question    │                          │ answer      │      │ running     │
└─────────────┘                          └─────────────┘      └─────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │ Spawn new   │
                                         │ agent with  │
                                         │ context +   │
                                         │ answer      │
                                         └─────────────┘
                                                │
                                                ▼
                                         ✓ PIPELINE CONTINUES
```

## Component Changes

### 1. `_execute_agent_background` Method (MODIFY)

**Location**: `backend/main.py`, line ~165

**Current Behavior**:
```python
# After agent execution
self.active_agents[agent_id]["status"] = "completed"
self.active_agents[agent_id]["logs"].append("✅ Completed successfully")
```

**New Behavior**:
```python
# Check for needs_user_input BEFORE marking completed
if result and result.get("status") == "needs_user_input":
    self.active_agents[agent_id]["status"] = "awaiting_user_input"
    self.active_agents[agent_id]["awaiting_question_id"] = result.get("question_id")
    self.active_agents[agent_id]["continuation_context"] = {
        "original_input": input_data,
        "question": result.get("user_question"),
        "agent_type": self.active_agents[agent_id].get("type")
    }
    self.active_agents[agent_id]["logs"].append(f"❓ Waiting for user input...")
    return  # DO NOT mark as completed
else:
    # Normal completion
    self.active_agents[agent_id]["status"] = "completed"
    self.active_agents[agent_id]["logs"].append("✅ Completed successfully")
```

### 2. `answer_question` Endpoint (MODIFY)

**Location**: `backend/main.py`, line ~605

**Current Behavior**:
```python
@app.post("/api/activity/questions/{question_id}/answer")
async def answer_question(question_id: str, answer: dict):
    tracker.record_answer(question_id, answer["answer"])
    return {"success": True}
```

**New Behavior**:
```python
@app.post("/api/activity/questions/{question_id}/answer")
async def answer_question(question_id: str, answer: dict, background_tasks: BackgroundTasks):
    tracker.record_answer(question_id, answer["answer"])
    
    # Find agent waiting for this answer and trigger continuation
    for agent_id, agent_info in orchestrator.active_agents.items():
        if agent_info.get("awaiting_question_id") == question_id:
            background_tasks.add_task(
                orchestrator.continue_agent_with_answer,
                agent_id,
                answer["answer"]
            )
            break
    
    return {"success": True}
```

### 3. New `continue_agent_with_answer` Method (ADD)

**Location**: `backend/main.py`, add to `AgentOrchestrator` class

```python
def continue_agent_with_answer(self, agent_id: str, answer: str):
    """Continue agent execution after receiving user answer."""
    agent_info = self.active_agents.get(agent_id)
    if not agent_info:
        return
    
    context = agent_info.get("continuation_context", {})
    original_input = context.get("original_input", {})
    question = context.get("question", "")
    
    # Build continuation input
    continuation_input = {
        **original_input,
        "continuation_context": {
            "previous_question": question,
            "user_answer": answer,
            "instruction": "Continue with implementation based on user's clarification."
        }
    }
    
    # Spawn new executive director with continuation context
    # (reuse existing spawn_executive_director logic)
```

## Data Flow

### New Fields in `active_agents[agent_id]`

| Field | Type | Purpose |
|-------|------|---------|
| `status` | string | Now includes `"awaiting_user_input"` state |
| `awaiting_question_id` | string | Links agent to pending question |
| `continuation_context` | object | Stores context for resumption |
| `continuation_context.original_input` | object | Original task input |
| `continuation_context.question` | string | The question asked |
| `continuation_context.agent_type` | string | Type of agent to respawn |

### State Transitions

```
initializing → running → awaiting_user_input → [answer received] → running → completed
                                      └── OR → error
```

## Testing Strategy

### Unit Tests
1. Test `_execute_agent_background` correctly detects `needs_user_input`
2. Test continuation context is properly stored
3. Test `continue_agent_with_answer` builds correct input

### Integration Tests
1. Mock agent returns `needs_user_input` → verify status is `awaiting_user_input`
2. Submit answer → verify new agent spawned with correct context
3. End-to-end flow from question to continuation

## Files to Modify

| File | Changes |
|------|---------|
| `backend/main.py` | Main implementation - all 3 components |

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Agent state lost on restart | Out of scope - noted as limitation |
| Multiple concurrent answers | Use question_id to match correctly |
| Original agent context stale | Copy context at pause time |

## Out of Scope
- Persistent storage for paused agents
- Multi-question support
- Question timeout handling
- Hot reload of agent definitions during continuation
