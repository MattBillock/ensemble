# Architecture: Recovery Agent System

## Architecture Overview

This architecture introduces a **Recovery Agent** into the agent hierarchy to govern job recovery. The key innovation is replacing direct retry mechanisms with agent-spawned recovery, ensuring recovered jobs appear in the main agent hierarchy alongside regular jobs.

**Architecture Pattern**: Agent-based Recovery Orchestration
**Rationale**: By treating recovery as a first-class agent-spawned operation, recovered jobs automatically integrate with existing swarm state tracking, hierarchy visualization, and monitoring infrastructure.

## System Components

### 1. Recovery Agent (`leadership/recovery_agent.md`)
**Role**: Specialized leadership agent that governs recovery operations
**Responsibilities**:
- Accept recovery task information from RecoveryOrchestrator
- Spawn Executive Directors to handle recovered tasks
- Track recovery attempts and maintain metadata
- Report recovery status back to orchestrator

**Can Spawn**: Executive Director only
**Cannot Spawn**: Direct code writers, coordinators, or other agents

### 2. Modified RecoveryOrchestrator (`swarm_recovery.py`)
**Role**: Orchestrates recovery queue processing
**Changes Required**:
- Instead of calling `_retry_agent()` directly, spawn Recovery Agent via `spawn_agent` tool
- Pass recovery context (original input, failure reason, strategy) to Recovery Agent
- Monitor spawned Recovery Agent for completion

### 3. Swarm State Integration
**Role**: Existing infrastructure, minimal changes needed
**Requirement**: Recovery Agent and its spawned Executive Directors must register properly
**Behavior**: Once agents register in swarm_state, they automatically appear in hierarchy API

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CURRENT FLOW (TO BE REPLACED)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  RecoveryOrchestrator                                                    │
│         │                                                                │
│         ▼                                                                │
│  _retry_agent() ──────► Direct Agent Spawn                               │
│         │                    (No swarm_state registration)               │
│         ▼                                                                │
│  Recovery Dashboard Only                                                 │
│  (Jobs NOT visible in hierarchy)                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        NEW FLOW (TO BE IMPLEMENTED)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  RecoveryOrchestrator                                                    │
│         │                                                                │
│         │ spawn_agent("leadership/recovery_agent", recovery_task)        │
│         ▼                                                                │
│  ┌─────────────────┐                                                     │
│  │ Recovery Agent  │ ◄──── Registers in swarm_state                      │
│  │ (leadership/)   │                                                     │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           │ spawn_agent("leadership/executive_director", original_task)  │
│           ▼                                                              │
│  ┌───────────────────────┐                                               │
│  │  Executive Director   │ ◄──── Registers in swarm_state                │
│  │  (recovered task)     │       Parent: Recovery Agent                  │
│  └────────┬──────────────┘                                               │
│           │                                                              │
│           ▼ (normal ED workflow)                                         │
│  ┌───────────────────────┐                                               │
│  │  Dev Manager, etc.    │ ◄──── All children visible in hierarchy       │
│  └───────────────────────┘                                               │
│                                                                          │
│  Result: All agents visible in Agent Hierarchy Tree                      │
│          + Recovery Dashboard still shows recovery-specific info         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## File/Directory Structure

### New Files to Create
```
src/
└── ensemble/
    └── docs/
        └── agents/
            └── leadership/
                └── recovery_agent.md    # New agent definition
```

### Files to Modify
```
src/
└── ensemble/
    └── runtime/
        └── swarm_recovery.py    # Use spawn_agent instead of direct retry
```

### No Changes Required
```
src/
└── field/
    └── ensemble_ui/
        └── backend/
            └── routes/
                └── activity.py   # Hierarchy endpoint already works
        └── frontend/
            └── src/
                └── components/
                    └── AgentHierarchyTree.jsx  # Already displays swarm_state
```

## Recovery Agent Definition

### Input Format
```json
{
  "recovery_task": {
    "original_agent_id": "string - ID of the failed agent",
    "original_session_id": "string - Session that contained the failed agent",
    "agent_type": "string - Type of agent that failed",
    "agent_name": "string - Name of agent that failed",
    "input_data": "object - Original input to the failed agent",
    "failure_reason": "string - Why the agent failed/stalled",
    "recovery_strategy": "string - Strategy to apply (retry, enhance_prompt, etc.)",
    "recovery_attempt": "integer - Which recovery attempt this is"
  },
  "output_directory": "string - Where to write artifacts"
}
```

### Output Format
```json
{
  "status": "success|failed|needs_user_input",
  "recovery_id": "string - ID of this recovery attempt",
  "spawned_executive_id": "string - ID of the Executive Director spawned",
  "original_agent_id": "string - Reference to original failed agent",
  "message": "string - Status message",
  "self_analysis": "string - Performance analysis"
}
```

### Agent Definition Structure
```markdown
# Recovery Agent

## Purpose
Governs job recovery by spawning Executive Directors for recovered tasks.

## Instructions
1. Receive recovery task from RecoveryOrchestrator
2. Extract original input_data and task context
3. Spawn Executive Director with original task + recovery metadata
4. Monitor Executive Director completion
5. Report recovery status

## Permissions
- can_spawn: ["leadership/executive_director"]
- can_write_code: false

## Input Format
(as above)

## Output Format
(as above)
```

## API Changes

### No New Endpoints Required
The existing `/api/activity/hierarchy` endpoint will automatically include recovered jobs once they register in swarm_state.

### Metadata Enhancement
Recovery-spawned agents should include metadata:
```json
{
  "agent_id": "recovery-exec-abc123",
  "agent_type": "leadership/executive_director",
  "metadata": {
    "is_recovery": true,
    "original_failed_agent_id": "original-abc123",
    "recovery_attempt": 1,
    "recovery_strategy": "retry",
    "failure_reason": "timeout"
  }
}
```

## Integration Points

### RecoveryOrchestrator Changes
```python
# BEFORE (swarm_recovery.py)
async def _process_recovery_task(self, task):
    await self._retry_agent(task)  # Direct retry, no hierarchy integration

# AFTER
async def _process_recovery_task(self, task):
    recovery_input = {
        "recovery_task": {
            "original_agent_id": task.agent_id,
            "original_session_id": task.session_id,
            "agent_type": task.agent_type,
            "agent_name": task.agent_name,
            "input_data": task.input_data,
            "failure_reason": task.failure_reason,
            "recovery_strategy": task.recovery_strategy,
            "recovery_attempt": task.attempt_count
        },
        "output_directory": self.output_directory
    }
    
    # Spawn Recovery Agent (which spawns ED, which registers in swarm_state)
    result = await self.spawn_agent(
        "leadership/recovery_agent",
        recovery_input
    )
```

## Testing Strategy

### Unit Tests
1. Recovery Agent definition parsing
2. Input/output format validation
3. Permission enforcement (can only spawn ED)

### Integration Tests
1. RecoveryOrchestrator → Recovery Agent spawning
2. Recovery Agent → Executive Director spawning
3. Swarm state registration verification

### End-to-End Tests
1. Trigger a recoverable failure
2. Verify job enters recovery queue
3. Verify Recovery Agent spawns
4. Verify Executive Director appears in hierarchy
5. Verify recovery metadata preserved

## Backward Compatibility

### Preserved Functionality
- Recovery queue continues to work
- Recovery dashboard continues to show recovery status
- Recovery history is still populated
- Existing UI components unchanged

### New Behavior
- Recovered jobs NOW also appear in Agent Hierarchy
- Recovery metadata available in hierarchy view

## Risks and Mitigations

### Risk 1: spawn_agent Availability
**Issue**: RecoveryOrchestrator may not have access to spawn_agent tool
**Mitigation**: Ensure RecoveryOrchestrator runs in a context with tool access, or create a spawning utility

### Risk 2: Session Management
**Issue**: Recovered jobs may create orphaned sessions
**Mitigation**: Recovery Agent should reuse existing session or create with proper parent reference

### Risk 3: Infinite Recovery Loops
**Issue**: Recovery Agent could fail, triggering more recovery
**Mitigation**: Mark Recovery Agent as non-recoverable or add loop detection

## Success Criteria

1. ✅ When a job is recovered, it appears in the main Agent Hierarchy tree
2. ✅ Users can track recovery progress the same way as regular jobs
3. ✅ Recovery metadata (attempt count, original failure) is preserved
4. ✅ No regression in existing recovery functionality
5. ✅ All tests pass

## Open Questions (None - Decisions Made)

1. **Session handling**: Recovery Agent creates new session linked to recovery queue entry
2. **Recovery Agent failures**: Mark Recovery Agent as non-recoverable to prevent loops
3. **UI changes**: None required - existing UI auto-displays registered agents
