# Recovery Implementation Plan

**Generated**: 2026-01-13  
**Based on**: recovery_recommendations.md  
**Purpose**: System-level guidance for recovering 10 stalled projects

## Architectural Constraint

**IMPORTANT**: As stated in recovery_recommendations.md:
> "Executive Directors should not spawn other Executive Directors"
> "This is a system-level recovery operation, not something one Executive Director should orchestrate by spawning peer-level agents"

Each project already has its own Executive Director context. Recovery requires **resuming those contexts**, not creating new ones.

## Recovery Actions by Category

### Category 1: Stalled In-Progress Tasks (Resume Development Managers)

These projects have Development Managers that started but didn't complete. The owning Executive Director should re-spawn or resume the Development Manager.

| Project ID | Project Name | Task ID | Action Required |
|------------|--------------|---------|-----------------|
| bb528d28 | Local Weather Display Widget | 25a708e9 | Resume ED context, re-spawn Development Manager with implementation mandate |
| 0114ab16 | Ensemble UI Enhancements | 2c48f5cc | Resume ED context, clear architecture conflicts, restart Development Manager |
| 4af1c241 | Agent Hierarchy Organization | 551c5cdb | Resume ED context, check Development Manager status and continue |

### Category 2: Unstarted Todo Tasks (Spawn Appropriate Agents)

These projects have tasks defined but never started. The owning Executive Director should spawn the assigned agent.

| Project ID | Project Name | Task ID | Assigned Agent | Action Required |
|------------|--------------|---------|----------------|-----------------|
| 84dd6401 | Agent Tracking Metrics Feature | 4f156ea4 | leadership/development_manager | Resume ED, spawn Development Manager |
| 5f5892f3 | Agent Cost Tracking - Frontend | 8d4f054d | frontend_developer* | Resume ED, fix assignment to TDD Coordinator, spawn |
| 66af6b69 | Agent Cost Tracking - Backend | 0c2be00c, c2b44d9d, c72aedcd | tdd_coordinator | Resume ED, spawn TDD Coordinator for 3 tasks |
| d863e0cc | Agent Completion Visibility | a560e23e, e24d6a7a, 1f37d367 | coordinators | Resume ED, spawn Development Manager to orchestrate |
| ea916e81 | Ensemble UI Completion | 4eb9f45f, 0bbd4553 | leadership/tdd_coordinator | Resume ED, spawn TDD Coordinator |

*Note: Task 8d4f054d incorrectly assigned to "frontend_developer" - should be TDD Coordinator

### Category 3: Planning-Only Projects (Need Requirements)

These projects were created but never had tasks defined. The owning Executive Director should continue from requirements phase.

| Project ID | Project Name | Description | Action Required |
|------------|--------------|-------------|-----------------|
| e30078c1 | Verifier Agent Swarm | Deploy swarm for unit tests, linting, docs, GitHub | Resume ED, gather requirements, create tasks |
| 168565b8 | Ensemble UI Activity Pane Graph | Simple bar graph showing bot count per phase | Resume ED, gather requirements, create tasks |

## Implementation for System/UI Layer

The system that manages agent execution should:

1. **Identify Active Contexts**: Check which Executive Director processes are currently running
2. **Queue Recovery**: For each project needing recovery:
   - Load project tracking file from ~/.ensemble/projects/{project_id}.json
   - Reconstruct Executive Director context from notes and task history
   - Resume execution at the appropriate phase
3. **Prioritization**: Start with in-progress tasks (Category 1) as they're closest to completion
4. **Concurrency Control**: Limit concurrent Executive Directors per user's capacity settings

## Project Recovery Commands (For System Layer)

```python
# Pseudocode for recovery orchestration

def recover_project(project_id: str) -> None:
    """Resume Executive Director for a stalled project."""
    project_data = load_project(f"~/.ensemble/projects/{project_id}.json")
    
    # Determine phase from project state
    if not project_data['tasks']:
        phase = 'requirements'
    elif any(t['status'] == 'in_progress' for t in project_data['tasks'].values()):
        phase = 'implementation'  
    elif all(t['status'] == 'todo' for t in project_data['tasks'].values()):
        phase = 'planning'
    
    # Spawn Executive Director with context
    spawn_executive_director(
        project_id=project_id,
        resume_phase=phase,
        context=project_data
    )

# Priority order for recovery
recovery_queue = [
    # Category 1: In-progress (highest priority)
    'bb528d28',  # Weather Widget
    '0114ab16',  # UI Enhancements
    '4af1c241',  # Agent Hierarchy
    
    # Category 2: Todo tasks
    '84dd6401',  # Tracking Metrics
    '66af6b69',  # Cost Tracking Backend
    '5f5892f3',  # Cost Tracking Frontend
    'd863e0cc',  # Completion Visibility
    'ea916e81',  # UI Completion
    
    # Category 3: Planning only (lowest priority)
    'e30078c1',  # Verifier Swarm
    '168565b8',  # Activity Graph
]
```

## What This Executive Director Can Do

Since I cannot spawn peer-level Executive Directors to take over these projects, I can:

1. ✅ **Document this recovery plan** (done)
2. ✅ **Analyze project states** (done)
3. ❌ **Execute recovery** - Requires system-level intervention

## Recommended Next Steps for User

1. **Manual Recovery**: For each project, start a new Executive Director session with context like:
   ```
   "Continue project {project_id}: {project_name}. Resume from {phase}."
   ```

2. **System Enhancement**: Add recovery functionality to the UI that can:
   - List stalled projects
   - Resume Executive Director contexts
   - Track recovery progress

3. **Automation**: Create a recovery agent type that can orchestrate multiple ED resumptions with proper rate limiting

## Conclusion

This recovery requires system-level orchestration beyond a single Executive Director's scope. The recommendations document correctly identified this as a constraint. The proper path forward is implementing recovery at the system/UI layer, not within the agent hierarchy.
