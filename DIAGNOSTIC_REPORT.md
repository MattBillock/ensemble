# Ensemble AI System Diagnostic Report
**Date:** January 11, 2026
**Generated:** Automated analysis of system behavior and logs

---

## Executive Summary

**Primary Issue:** Agents are executing successfully and generating files, but the UI does not properly reflect their work. Additionally, generated files are not being committed to version control.

**Impact:** Users cannot see the results of agent work in the UI, creating the perception that the system is not functioning despite successful executions.

**Root Causes Identified:**
1. **Activity Tracker Integration Gap** - File generation events not recorded in activity feed
2. **Dual Tracking Systems** - Old WebSocket system and new Activity Tracker are disconnected
3. **No Git Integration** - Agents lack tools to commit their changes
4. **UI Display Mismatch** - Frontend polls new activity API which doesn't include file generation data

---

## Detailed Findings

### 1. File Generation Status ✅ WORKING

**Evidence:**
```bash
# 27 new files created in output directory
src/field/ensemble_ui/output/CHANGE_INVENTORY.md
src/field/ensemble_ui/output/FEASIBILITY_ASSESSMENT.md
src/field/ensemble_ui/output/NAMING_AUDIT_REPORT.md
src/field/ensemble_ui/output/PROJECT_GENERATION_GUIDE.md
src/field/ensemble_ui/output/TERMINOLOGY_DICTIONARY.md
src/field/ensemble_ui/output/agent-naming-system/
src/field/ensemble_ui/output/decomposition_architecture.md
... and 20 more files
```

**Backend Log Evidence:**
```json
{"timestamp": "2026-01-11 03:28:08", "level": "INFO",
 "message": "[c54cc6d4][exec_dir_2] Found 34 new file(s) in output directory"}
```

**Conclusion:** Agents ARE successfully writing files. The write_file tool works correctly.

---

### 2. Activity Tracking Status ⚠️ PARTIALLY WORKING

**What's Working:**
- Activity tracker records agent starts, iterations, and tool use
- API endpoints return activity data correctly
- Agent states are tracked and updated

**What's NOT Working:**
- File generation events are NOT recorded in activity feed
- Generated files exist in old `active_agents` structure but not in new activity tracker
- No integration between file scanning and activity recording

**Evidence:**
```bash
# Activity API returns data
GET /api/activity/recent?limit=10
# Shows: agent_started, iteration_started, tool_use_started
# MISSING: file_generated, agent_output_created
```

**Code Gap:**
The `_scan_output_files()` method in `main.py` (line 115-159) finds generated files and stores them in `self.active_agents[agent_id]["generated_files"]`, but this data is never passed to the Activity Tracker.

---

### 3. Git Integration Status ❌ NOT IMPLEMENTED

**Evidence:**
```bash
# Git status shows 27 untracked files
?? src/field/ensemble_ui/output/CHANGE_INVENTORY.md
?? src/field/ensemble_ui/output/FEASIBILITY_ASSESSMENT.md
... 25 more untracked files

# Modified files (2570 insertions, 436 deletions) not committed
M coordinators/backend_coordinator.md
M coordinators/frontend_coordinator.md
... 10 agent definitions modified
```

**Current State:**
- Agents have `run_command` tool but don't use it for git operations
- No dedicated `git_commit` tool exists
- Agent definitions don't include git commit instructions
- No automatic commit workflow

**Impact:** All agent work exists only locally, not persisted to version control.

---

### 4. UI Display Status ⚠️ PARTIALLY WORKING

**What Users See:**
- ✅ Agent hierarchy (agents and their spawned sub-agents)
- ✅ Agent states (running/completed/failed)
- ✅ Current task descriptions
- ✅ Iteration progress
- ✅ Activity feed (agent starts, tool use)
- ❌ **Generated files** (NOT VISIBLE)
- ❌ File content previews
- ❌ Output summaries

**Why Generated Files Don't Show:**
1. UI polls `/api/activity/recent` for activity feed
2. Activity tracker doesn't record file generation
3. Old system stores files in `active_agents[id]["generated_files"]`
4. New activity API doesn't expose `active_agents` data
5. UI components expect activity feed format, not legacy format

**Code Evidence:**
```javascript
// App.jsx line 40-45
const [activitiesRes, hierarchyRes, statesRes, questionsRes, statusRes] =
  await Promise.all([
    getRecentActivities({ limit: 200 }),  // ← Activity feed
    getAgentHierarchy(),                   // ← Works
    getAllAgentStates(),                   // ← Works
    getPendingQuestions(),                 // ← Works
    getApplicationStatus()                 // ← Works
  ]);
```

No API call to get generated files from `active_agents`.

---

### 5. Agent Execution Status ✅ MOSTLY WORKING

**Agent Performance (from logs):**
```
Development Manager (exec 1): 8 iterations, completed in ~173 seconds
System Architect (exec 1): 2 iterations, completed in ~69 seconds
Development Manager (exec 2): 22 iterations, completed in ~1822 seconds (30 min)
System Architect (exec 2): 2 iterations, completed in ~57 seconds
Backend Coordinator: 2 iterations, completed in ~76 seconds
Test Coordinator: 2 iterations, completed in ~70 seconds
TDD Coordinator: 12 iterations, completed in ~440 seconds (7 min)
Unit Test Lead: 10 iterations, completed in ~140 seconds
```

**Issues Observed:**
- Development Manager sometimes takes excessive iterations (22, 51)
- Agents complete but return conversational text instead of JSON
- "ROGUE AGENT DETECTED" - Executive Director tried to write code directly (correctly blocked)

**Log Evidence:**
```json
{"level": "ERROR", "message": "Could not extract JSON from response:
 Since the TDD Coordinator completed but didn't create the files..."}
```

Agents are responding conversationally rather than with structured JSON output.

---

## System Architecture Analysis

### Current Dual-Tracking System

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Execution                          │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
               ▼                          ▼
    ┌──────────────────┐      ┌──────────────────────┐
    │  Activity Tracker │      │   active_agents      │
    │  (New System)     │      │   (Old System)       │
    ├──────────────────┤      ├──────────────────────┤
    │ • Iterations     │      │ • Agent status       │
    │ • Tool use       │      │ • Generated files ✓  │
    │ • Agent starts   │      │ • Results            │
    │ • Completions    │      │ • Logs               │
    │                  │      │ • Duration           │
    │ NO FILES ✗       │      │                      │
    └────────┬─────────┘      └──────────┬───────────┘
             │                           │
             ▼                           ▼
    ┌──────────────────┐      ┌──────────────────────┐
    │  Activity API     │      │  WebSocket (unused)  │
    │  /api/activity/*  │      │  /ws/agent-status    │
    └────────┬─────────┘      └──────────────────────┘
             │
             ▼
    ┌──────────────────┐
    │   UI Polling      │
    │   (Can't see      │
    │    files)         │
    └──────────────────┘
```

**Problem:** Two disconnected systems tracking different aspects of agent execution.

---

## Specific Code Issues

### Issue 1: Activity Tracker Doesn't Record File Generation

**Location:** `src/field/ensemble_ui/backend/main.py:193`

```python
# Scan for new files
generated_files = self._scan_output_files(output_dir, before_files, request_id, agent_id)

# Update with result
self.active_agents[agent_id]["status"] = "completed"
self.active_agents[agent_id]["result"] = result
self.active_agents[agent_id]["generated_files"] = generated_files  # ← Stored here

# MISSING: No call to activity tracker to record file generation!
# Should be:
# activity_tracker = AgentRuntime.get_activity_tracker()
# for file in generated_files:
#     activity_tracker.record_file_generated(agent_id, agent_name, request_id, file)
```

### Issue 2: No Activity Type for File Generation

**Location:** `src/runtime/agents/activity_tracker.py:10-24`

Current ActivityType enum:
```python
class ActivityType(str, Enum):
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    ITERATION_STARTED = "iteration_started"
    TOOL_USE_STARTED = "tool_use_started"
    TOOL_USE_COMPLETED = "tool_use_completed"
    # ... etc

    # MISSING:
    # FILE_GENERATED = "file_generated"
    # OUTPUT_CREATED = "output_created"
```

### Issue 3: No Git Integration

**Location:** Multiple agent definitions lack git commit instructions

Agents have instructions for spawning other agents, writing files, running tests, but NO instructions for:
- Committing changes with `git add` and `git commit`
- Writing proper commit messages
- Coordinating commits across file changes

**Example from `leadership/executive_director.md`:**
```markdown
## Available Tools
- **spawn_agent**: Spawn Development Manager
- **read_file**: Read files
- **run_command**: Execute commands

# MISSING: Git workflow instructions
```

### Issue 4: UI Doesn't Request File Data

**Location:** `src/field/ensemble_ui/frontend/src/App.jsx:40-46`

```javascript
const [activitiesRes, hierarchyRes, statesRes, questionsRes, statusRes] =
  await Promise.all([
    getRecentActivities({ limit: 200 }),
    getAgentHierarchy(),
    getAllAgentStates(),
    getPendingQuestions(),
    getApplicationStatus()
  ]);

// MISSING: Call to get generated files
// Should add: getGeneratedFiles(requestId)
```

---

## Performance Observations

### Agent Iteration Counts

| Agent Type | Min | Max | Avg | Status |
|-----------|-----|-----|-----|--------|
| Executive Director | 9 | 18 | 13.5 | ⚠️ High |
| Development Manager | 8 | 51 | 27 | ❌ Very High |
| System Architect | 2 | 2 | 2 | ✅ Good |
| Backend Coordinator | 2 | 2 | 2 | ✅ Good |
| Test Coordinator | 2 | 2 | 2 | ✅ Good |
| TDD Coordinator | 12 | 12 | 12 | ⚠️ Moderate |
| Unit Test Lead | 10 | 10 | 10 | ⚠️ Moderate |

**Analysis:**
- System Architect is highly efficient (always 2 iterations)
- Coordinators are efficient (always 2 iterations)
- Development Manager is problematic (up to 51 iterations!)
- Executive Director uses more iterations than expected

### Execution Times

| Agent | Duration | Iterations | Avg Time/Iteration |
|-------|----------|------------|-------------------|
| Dev Manager (exec 1) | 173s | 8 | 21.6s |
| System Architect | 69s | 2 | 34.5s |
| Dev Manager (exec 2) | 1822s | 22 | 82.8s |
| TDD Coordinator | 440s | 12 | 36.7s |
| Unit Test Lead | 140s | 10 | 14.0s |

**Analysis:**
- Dev Manager iteration time increases significantly in later executions (82.8s vs 21.6s)
- Unit Test Lead is most efficient per iteration (14s)
- System Architect takes longer per iteration but completes in fewer iterations

---

## Recommendations Summary

### Critical (Fix Immediately)

1. **Integrate File Generation into Activity Tracker**
   - Add `FILE_GENERATED` activity type
   - Record file generation in `_execute_agent_background()`
   - Expose via `/api/activity/recent`

2. **Add Generated Files API Endpoint**
   - Create `/api/agents/{agent_id}/files` to return generated files
   - Update UI to poll this endpoint
   - Display files in activity feed or separate panel

3. **Implement Git Integration**
   - Create `GitCommitTool` for agents
   - Add git workflow to agent instructions
   - Auto-commit after successful task completion

### High Priority

4. **Fix Agent JSON Output**
   - Agents are returning conversational text instead of JSON
   - Add output format validation
   - Improve agent prompts to enforce JSON structure

5. **Reduce Development Manager Iterations**
   - Investigate why Development Manager needs 22-51 iterations
   - Add better task decomposition
   - Improve termination conditions

### Medium Priority

6. **Unify Tracking Systems**
   - Migrate all data from `active_agents` to Activity Tracker
   - Deprecate old WebSocket system
   - Single source of truth for agent state

7. **Add UI File Viewer**
   - Display generated files in UI
   - Markdown preview for .md files
   - Code syntax highlighting for code files

---

## Testing Evidence

### Successful Operations ✅

- ✅ Agents spawn correctly
- ✅ Files are written to output directory
- ✅ Activity tracker records agent execution
- ✅ API endpoints respond correctly
- ✅ UI polls successfully at configurable intervals
- ✅ Agent hierarchy displays correctly
- ✅ Agent states update in real-time

### Failed Operations ❌

- ❌ Generated files don't appear in UI
- ❌ No git commits happen automatically
- ❌ File generation events not in activity feed
- ❌ Agent output sometimes non-JSON
- ❌ Development Manager takes excessive iterations

---

## Conclusion

**The system is fundamentally working** - agents execute, spawn sub-agents, write files, and complete tasks. However, **visibility is broken** due to the Activity Tracker not integrating with file generation, and **persistence is missing** due to lack of git integration.

**Immediate Action Required:**
1. Connect file generation to activity tracker
2. Add API endpoint for generated files
3. Update UI to display generated files
4. Implement git commit functionality

These fixes will restore user visibility into agent work and ensure results are persisted.
