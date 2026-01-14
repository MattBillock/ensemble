# Requirements Document: Whimsical Agent Names Integration

## Project Overview
**Project Name:** Whimsical Agent Names Integration  
**Project ID:** ebd1ab92  
**Created:** 2026-01-13  
**Priority:** HIGH (User has requested this "a bunch of times")

## Vision
Replace the current boring timestamp-based agent IDs (e.g., `executive_director_1768358954019`) with whimsical, memorable names from the existing agent naming system. This makes agent identification more human-friendly, easier to track in logs and UI, and adds personality to the system.

## Problem Statement
Currently, agents are assigned IDs based on their agent type plus a timestamp:
```python
self.agent_id = agent_id or f"{definition.name}_{datetime.now().timestamp()}"
```

This results in identifiers like:
- `executive_director_1768358954019`
- `tdd_coordinator_1768358954019_541afa8d`

These are:
- Hard to remember
- Not visually distinct
- Impersonal and robotic
- Difficult to reference in conversation

**The user has specifically requested whimsical names multiple times** - this is a high-priority user experience improvement.

## Existing Infrastructure
A whimsical naming system has already been created at:
- **Location:** `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/output/agent-naming-system/`
- **Module:** `name_data.py`
- **Contains:** 1000 whimsical names based on 60 unique base names
- **Examples:** "Lumawick", "Bramblejay", "Poppymere", "Fizzlewhisk", "Glimmerstone"

However, **this naming system is NOT currently integrated** into the agent runtime. It exists in the output directory but is not imported or used anywhere in the runtime code.

## Core Objectives
1. **Move naming module to runtime** - Relocate `name_data.py` from output directory to runtime package
2. **Create name generator** - Build a name generator that selects random names from the whimsical list
3. **Integrate into AgentRuntime** - Replace timestamp-based ID generation with whimsical names
4. **Ensure uniqueness** - Add suffix/numbering when names collide
5. **Maintain traceability** - Keep ability to identify agent type and hierarchy

## Scope

### In Scope
- Move `name_data.py` to `src/runtime/agents/` directory
- Create `AgentNameGenerator` class to handle name selection
- Modify `AgentRuntime.__init__` to use whimsical names
- Ensure name uniqueness across concurrent agents
- Update agent hierarchy display to show whimsical names
- Preserve agent type information in metadata

### Out of Scope
- Changing existing agent IDs (only affects new agents)
- Custom name selection by users
- Name categories or themes
- Name persistence across system restarts
- Agent renaming after creation

## Technical Requirements

### Functional Requirements

#### FR1: Name Generator
Create `AgentNameGenerator` class with:
- Random selection from `WHIMSICAL_NAMES` list
- Collision detection (track used names)
- Suffix addition for duplicates (e.g., "Lumawick-2")
- Thread-safe name generation for concurrent agents

#### FR2: Runtime Integration
Modify `AgentRuntime.__init__` to:
- Generate whimsical name instead of timestamp
- Store agent type separately in metadata
- Maintain backward compatibility with explicit `agent_id` parameter

#### FR3: Name Format
Generated agent IDs should follow pattern:
- **Primary:** `{whimsical_name}` (e.g., "Lumawick")
- **Collision:** `{whimsical_name}-{number}` (e.g., "Lumawick-2")
- **Preserve type:** Store agent type in `agent_hierarchy` metadata

### Non-Functional Requirements

#### NFR1: Performance
- Name generation should take < 1ms
- No performance degradation in agent spawning

#### NFR2: Reliability
- Thread-safe for concurrent agent creation
- No name collisions within same execution

#### NFR3: Usability
- Names must be memorable and pronounceable
- Names should be visually distinct in UI

## Technical Design

### File Structure
```
src/runtime/agents/
├── name_data.py           # Move from output/agent-naming-system/
├── name_generator.py      # New file
├── runtime.py            # Modified
└── activity_tracker.py   # Already tracks agent names
```

### Implementation Details

#### 1. Move name_data.py
**Action:** Move file from output directory to runtime
```bash
mv src/field/ensemble_ui/output/agent-naming-system/name_data.py \
   src/runtime/agents/name_data.py
```

#### 2. Create AgentNameGenerator
**File:** `src/runtime/agents/name_generator.py`
```python
"""Whimsical name generator for agents."""
import random
from typing import Set
from threading import Lock
from .name_data import WHIMSICAL_NAMES


class AgentNameGenerator:
    """Generates unique whimsical names for agents."""
    
    def __init__(self):
        self.used_names: Set[str] = set()
        self.lock = Lock()
        self.name_pool = list(WHIMSICAL_NAMES)
        random.shuffle(self.name_pool)
        self.pool_index = 0
    
    def generate_name(self, agent_type: str = None) -> str:
        """Generate a unique whimsical name for an agent.
        
        Args:
            agent_type: Optional agent type for metadata (not used in name)
            
        Returns:
            Unique whimsical name
        """
        with self.lock:
            # Try to get next name from shuffled pool
            base_name = self._get_next_base_name()
            
            # If already used, add suffix
            if base_name in self.used_names:
                counter = 2
                while f"{base_name}-{counter}" in self.used_names:
                    counter += 1
                final_name = f"{base_name}-{counter}"
            else:
                final_name = base_name
            
            self.used_names.add(final_name)
            return final_name
    
    def _get_next_base_name(self) -> str:
        """Get next name from shuffled pool, wrapping around."""
        name = self.name_pool[self.pool_index]
        self.pool_index = (self.pool_index + 1) % len(self.name_pool)
        return name
    
    def release_name(self, name: str):
        """Release a name back to the pool (when agent completes)."""
        with self.lock:
            self.used_names.discard(name)


# Global singleton instance
_generator = None

def get_name_generator() -> AgentNameGenerator:
    """Get or create the global name generator instance."""
    global _generator
    if _generator is None:
        _generator = AgentNameGenerator()
    return _generator
```

#### 3. Modify AgentRuntime
**File:** `src/runtime/agents/runtime.py`

**Current code (line 95):**
```python
self.agent_id = agent_id or f"{definition.name}_{datetime.now().timestamp()}"
```

**New code:**
```python
# Import at top of file
from .name_generator import get_name_generator

# In __init__ method
if agent_id is None:
    # Generate whimsical name
    name_gen = get_name_generator()
    self.agent_id = name_gen.generate_name(agent_type=definition.name)
else:
    self.agent_id = agent_id
```

#### 4. Update Activity Tracker
**File:** `src/runtime/agents/activity_tracker.py`

No changes needed - already stores both `agent_id` and `agent_name` (agent type) separately in hierarchy.

### Example Usage

**Before:**
```
Agent ID: executive_director_1768358954019
```

**After:**
```
Agent ID: Lumawick
Agent Type: executive_director
```

**With collision:**
```
Agent ID: Lumawick-2
Agent Type: tdd_coordinator
```

## Success Criteria

### Must Have
- ✅ `name_data.py` moved to `src/runtime/agents/`
- ✅ `AgentNameGenerator` class created and working
- ✅ AgentRuntime generates whimsical names by default
- ✅ No name collisions within single execution
- ✅ Thread-safe name generation
- ✅ Agent type still visible in UI and logs

### Should Have
- ✅ Names are memorable and easy to pronounce
- ✅ UI displays whimsical names instead of timestamps
- ✅ Activity tracker shows whimsical names in agent hierarchy
- ✅ Backward compatibility: explicit `agent_id` still works

### Nice to Have
- Name release when agent completes (optional optimization)
- Statistics on name usage
- Ability to regenerate name pool

## Testing Strategy

### Unit Tests
1. **Test name uniqueness:** Generate 100 names, verify all unique
2. **Test collision handling:** Force collisions, verify suffixes work
3. **Test thread safety:** Generate names from multiple threads
4. **Test pool exhaustion:** Generate > 1000 names, verify no errors

### Integration Tests
1. Spawn multiple agents, verify distinct names
2. Check activity tracker shows whimsical names
3. Verify agent hierarchy displays correctly
4. Test with explicit `agent_id` parameter (backward compat)

### Manual Tests
1. Run Ensemble UI, create project
2. Verify agent names in UI are whimsical
3. Check logs show readable names
4. Confirm question IDs use whimsical names

## Implementation Phases

### Phase 1: Foundation (30 minutes)
1. Move `name_data.py` to runtime
2. Create `AgentNameGenerator` class
3. Write unit tests for name generator

### Phase 2: Integration (30 minutes)
1. Modify `AgentRuntime.__init__` to use generator
2. Test with simple agent execution
3. Verify backward compatibility

### Phase 3: Validation (15 minutes)
1. Run full Ensemble UI workflow
2. Verify names appear correctly in UI
3. Check activity tracker integration
4. Commit changes

## Risks and Mitigations

### Risk: Name collisions in high-concurrency scenarios
**Mitigation:** Use thread lock in name generator; suffix handling for duplicates

### Risk: Names might not be unique enough with 60 base names
**Mitigation:** Pool contains 1000 names total; suffixes handle > 1000 agents

### Risk: Breaking existing code that expects timestamp format
**Mitigation:** Maintain `agent_name` field with agent type; only `agent_id` changes

### Risk: User might not like the generated names
**Mitigation:** Preserve explicit `agent_id` parameter for override if needed

## Dependencies
- Existing `name_data.py` module (already created)
- No external package dependencies
- Python threading library (standard library)

## Assumptions
1. The 60 whimsical base names are approved by user
2. Suffixes (-2, -3, etc.) are acceptable for collisions
3. Agent IDs don't need to persist across system restarts
4. Current agent type tracking in `agent_hierarchy` is sufficient

## Out of Scope (Explicit)
- Changing historical agent IDs in existing data
- User-facing name customization UI
- Name themes or categories (fantasy, sci-fi, etc.)
- Internationalization of names
- Agent naming conventions enforcement

## Questions for User
None - user has explicitly requested this feature multiple times, requirements are clear.

## Migration Notes
- **No breaking changes:** Explicit `agent_id` parameter still works
- **No data migration needed:** Only affects new agents
- **UI updates automatic:** Activity tracker already uses `agent_id` field
- **Logs unchanged:** Agent type still logged via `agent_name`

---

**Status:** Requirements Complete - Ready for Implementation  
**Next Phase:** Development (via Development Manager)  
**Estimated Time:** 1.5 hours total
