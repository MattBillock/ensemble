# Fix Agent Coordination Issue

## Problem
Executive Director fails to spawn Development Manager due to missing required input field `project_name`.

## Root Cause
Executive Director's instructions (line 63-66 in `leadership/executive_director.md`) show spawning Development Manager with only:
```
spawn_agent("leadership/development_manager", {
  "requirements_file": "path/to/requirements.md",
  "output_directory": "path/from/input"
})
```

But Development Manager requires (per `leadership/development_manager.md` line 16-20):
```json
{
  "requirements_file": "string - path to requirements document",
  "output_directory": "string - where to create artifacts",
  "project_name": "string - project name"
}
```

## Required Fix

### File: `leadership/executive_director.md`

**Location**: Lines 63-66 (in Phase 2: Orchestrate Development)

**Current**:
```
spawn_agent("leadership/development_manager", {
  "requirements_file": "path/to/requirements.md",
  "output_directory": "path/from/input"
})
```

**Required**:
```
spawn_agent("leadership/development_manager", {
  "requirements_file": "path/to/requirements.md",
  "output_directory": "path/from/input",
  "project_name": "name from user_vision or context"
})
```

**Additional instruction needed**: Add guidance that Executive Director should derive project_name from user_vision or use the directory name or context.

## Acceptance Criteria
1. Executive Director instructions updated with project_name parameter
2. Instructions explain how to derive project_name
3. Example shows all three required fields
4. Change is minimal (only adds missing parameter)

## Test
After fix, run: `python complete_ui_pipeline.py`
Expected: Executive Director successfully spawns Development Manager without missing field errors.

## Priority
CRITICAL - blocks all agent pipeline execution
