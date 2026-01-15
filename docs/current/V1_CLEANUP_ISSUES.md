# Ensemble V1 Cleanup Issues - Prioritized List

**Generated:** 2026-01-14
**Purpose:** Comprehensive list of issues, half-implemented features, and deficiencies requiring cleanup for V1 release

---

## Summary Statistics

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Agent Definitions | 1 | 2 | 3 | 2 | 8 |
| Runtime Code | 2 | 2 | 3 | 3 | 10 |
| Backend API | 2 | 3 | 4 | 3 | 12 |
| Frontend | 3 | 3 | 3 | 2 | 11 |
| **TOTAL** | **8** | **10** | **13** | **10** | **41** |

---

## Priority 1: CRITICAL Issues

### C1. Frontend - Division by Zero in Progress Bars
**Location:** `src/field/ensemble_ui/frontend/src/components/HorizontalTimelineView.jsx:508`
**Also:** `src/field/ensemble_ui/frontend/src/App.jsx:494`
**Issue:** Progress bar width calculations divide by `max_iterations` without checking for zero
```javascript
width={`${(selectedAgent.current_iteration / selectedAgent.max_iterations) * 100}%`}
```
**Impact:** JavaScript NaN rendered as style, breaks UI rendering
**Fix:** Add `|| 1` fallback: `(current / (max || 1)) * 100`

### C2. Frontend - Division by Zero in Achievements
**Location:** `src/field/ensemble_ui/frontend/src/components/AchievementsDashboard.jsx:118`
**Issue:** Achievement progress calculation divides by `achievements.length`
```javascript
now={(unlockedCount / achievements.length) * 100}
```
**Impact:** Crashes if achievements array is empty
**Fix:** Guard with `achievements.length || 1` or conditional rendering

### C3. Frontend - Missing HTTP Response Validation
**Location:** All dashboard components (20+ locations)
**Issue:** API calls don't check `response.ok` before parsing JSON
```javascript
const response = await fetch(url);
const data = await response.json();  // No error check!
```
**Impact:** Silent failures on API errors, undefined data in state
**Fix:** Add `if (!response.ok) throw new Error()` before `.json()`

### C4. Agent Definitions - Model Preference Mismatches
**Location:** `leadership/executive_director.md`, `leadership/development_manager.md`, `leadership/system_architect.md`, `leadership/tdd_coordinator.md`
**Issue:** Agent definition files use different models than AGENT_REGISTRY.md recommends:
| Agent | Registry Says | Definition Says |
|-------|---------------|-----------------|
| Executive Director | sonnet | sonnet (OK) |
| Development Manager | sonnet | haiku (WRONG) |
| System Architect | opus | haiku (WRONG) |
| TDD Coordinator | sonnet | haiku (WRONG) |

**Impact:** Strategic agents using suboptimal models for their complexity
**Fix:** Update definitions to match registry recommendations

### C5. Backend - Inconsistent Error Response Format
**Location:** `src/field/ensemble_ui/backend/main.py:865`
**Issue:** Returns tuple instead of proper HTTPException
```python
return ({"error": "Agent not found"}, 404)  # Wrong!
```
**Impact:** FastAPI can't properly handle status codes
**Fix:** Use `raise HTTPException(status_code=404, detail="...")`

### C6. Backend - Bare Except Clauses in WebSocket
**Location:** `src/field/ensemble_ui/backend/main.py:643, 784`
**Issue:** Bare `except:` swallows all exceptions including system errors
**Impact:** Masks bugs, can hide KeyboardInterrupt and SystemExit
**Fix:** Use `except Exception as e:` with proper logging

### C7. Runtime - Request Filtering Not Implemented
**Location:** `src/runtime/agents/activity_tracker.py:525`
**Issue:** `get_agent_hierarchy(request_id)` ignores the parameter
```python
# Filter by request_id
# This would require storing request_id in hierarchy
return self.agent_hierarchy  # RETURNS UNFILTERED!
```
**Impact:** Cannot isolate hierarchy view to specific request
**Fix:** Store request_id in hierarchy and filter properly

### C8. Runtime - Activity Cleanup Not Implemented
**Location:** `src/runtime/agents/activity_tracker.py:543-550`
**Issue:** `clear_request()` method is incomplete
```python
# For now, we'll keep the data
```
**Impact:** Memory accumulates indefinitely for completed requests
**Fix:** Implement proper cleanup with request_id tracking

---

## Priority 2: HIGH Issues

### H1. Frontend - Null/Undefined Handling Gaps
**Locations:**
- `MetricsDashboard.jsx:30-34` - Nested property access without null checks
- `ActivityFeed.jsx:145,155,160` - Assumes `data.result.*` exists
- `GeneratedFiles.jsx:160` - `file.preview.length` without null check

**Impact:** Runtime errors on unexpected API responses
**Fix:** Add optional chaining `?.` and null coalescing `??`

### H2. Frontend - Unused Redux Infrastructure
**Location:** `src/field/ensemble_ui/frontend/src/store/`
**Issue:** Redux store configured but never used - all state via useState
**Impact:** Dead code, confusing for maintenance
**Fix:** Either remove Redux or migrate state management to it

### H3. Frontend - Inconsistent Styling Approach
**Locations:**
- `AgentStatusPane.jsx` - Uses Tailwind exclusively
- `PipelineTreeView.jsx:81,86` - Uses dynamic Tailwind classes that won't work
- Most components use React Bootstrap

**Impact:** Visual inconsistency, broken Tailwind dynamic classes
**Fix:** Standardize on React Bootstrap OR migrate fully to Tailwind

### H4. Backend - Missing Input Validation
**Locations:**
- All `days` query parameters (could be negative)
- All `limit` parameters (no upper bounds)
- `threshold_minutes` in recovery endpoints

**Impact:** Could cause unexpected behavior or resource exhaustion
**Fix:** Add Pydantic validators or manual checks with sensible bounds

### H5. Backend - Hardcoded Cost Calculations
**Locations:**
- `main.py:1543-1544` - Hardcoded cost-per-token
- `main.py:1626-1633` - Model-specific pricing
- `main.py:1585-1586, 1675-1676` - More hardcoded costs

**Impact:** Cost estimates will be wrong when API pricing changes
**Fix:** Move to config file or shared cost_calculator.py

### H6. Agent Registry - Unregistered Agents
**Issue:** AGENT_REGISTRY.md lists 16 agents but 19+ exist:
- `api_lead.md` - Exists but not in registry
- `api_developer.md` - Exists but not in registry
- `api_test_writer.md` - Exists but not in registry
- `database_manager.md` - Exists but orphaned
- `code_quality_director.md` - Leadership but unlisted
- `system_polish_director.md` - Leadership but unlisted
- `question_marshal.md` - Leadership but unlisted

**Impact:** Confusion about which agents are active
**Fix:** Update registry to document all agents and their status

### H7. Agent Registry - API Test Writer Not in Spawn Tree
**Location:** `testers/api_test_writer.md`
**Issue:** No clear spawning path - API Lead doesn't spawn this agent
**Impact:** Agent exists but cannot be spawned through hierarchy
**Fix:** Add to spawn permissions or document alternative invocation

### H8. Runtime - Broad Exception Handling
**Locations:** 20+ instances throughout runtime code
**Issue:** Bare `except Exception as e:` catches everything
```python
except Exception as e:
    logger.warning(f"Failed to ...{e}")
```
**Impact:** Programming errors and API changes hidden
**Fix:** Catch specific exception types

### H9. Backend - System Polish Endpoints Not Functional
**Location:** `main.py:1800-1829`
**Issue:** Creates config but background job never runs
**Impact:** Feature appears available but does nothing
**Fix:** Implement background_tasks.add_task() or remove endpoints

### H10. Runtime - Metrics Insert Missing Columns
**Location:** `src/runtime/agents/metrics.py:161`
**Issue:** INSERT statement doesn't include token/cost columns
**Impact:** Token usage data not persisted to database
**Fix:** Add missing column bindings to INSERT

---

## Priority 3: MEDIUM Issues

### M1. Backend - Thread Safety Issues
**Locations:**
- `main.py:574` - Global `orchestrator` shared across requests
- `main.py:100` - `active_connections` list without locks
- `main.py:1754-1758` - `_streaming_config` modified unsafely

**Impact:** Race conditions under concurrent requests
**Fix:** Add threading.Lock or use async-safe patterns

### M2. Backend - Optional Parameters Defaulting to None
**Locations:** 10+ endpoints with `Optional[str] = None` parameters
**Issue:** Could return null values in response data unexpectedly
**Impact:** Frontend must handle nulls everywhere
**Fix:** Return empty arrays/objects instead of null where appropriate

### M3. Backend - File Truncation Without Warning
**Locations:**
- `main.py:166-167` - Files >50KB silently truncated
- `main.py:245` - Previews limited to 500 chars

**Impact:** Users see partial data without knowing it's truncated
**Fix:** Add truncation indicator in response

### M4. Agent Definitions - Old Drum Corps Terminology
**Locations:** Multiple agent .md files
**References to:** "Snare", "Trumpet", "Percussion Coordinator", "Brass Coordinator", "Visual Tech", "Dance Tech"
**CLAUDE.md says:** "Don't use deprecated drum corps naming"
**Impact:** Confusion about actual agent names
**Fix:** Replace all drum corps terms with standard role names

### M5. Agent Definitions - Inconsistent "Supervised By" Fields
**Locations:** Most developer and tester agent files
**Issue:** Reference non-existent coordinators like "Brass Coordinator"
**Impact:** Documentation is misleading
**Fix:** Update or remove Supervised By fields

### M6. Runtime - WebSocket Buffer Not Persistent
**Location:** `src/runtime/agents/websocket_manager.py`
**Issue:** Event buffer in memory, lost on restart
**Impact:** Reconnecting clients after restart get no history
**Fix:** Consider persistent buffer or document limitation

### M7. Frontend - Components Created But Not Used
**Files:**
- `AgentStatusPane.jsx` - Not imported in App.jsx
- `FileViewerPane.jsx` - Not imported in App.jsx
- `ProblemInputForm.jsx` - Used in old App, not current

**Impact:** Dead code, wasted effort
**Fix:** Either integrate or remove

### M8. Frontend - API Service Error Handling
**Location:** `src/field/ensemble_ui/frontend/src/services/api.js`
**Issue:** All functions have try-catch but error responses don't check status
**Impact:** Network errors handled, but HTTP errors (400, 500) not caught
**Fix:** Add response.ok validation in api.js functions

### M9. Agent Definitions - TDD Coordinator Spawns Non-Existent Agent
**Location:** `leadership/tdd_coordinator.md`
**Issue:** Can spawn "support/visual_tech" which doesn't exist
**Impact:** Spawn would fail at runtime
**Fix:** Remove from spawn permissions or create agent

### M10. Runtime - Unused Resilience Classes
**Location:** `src/runtime/agents/`
**Issue:** RateLimiter and TimeoutManager defined but never used
**Impact:** Dead code
**Fix:** Integrate or remove

### M11. Backend - CORS Overly Permissive
**Location:** `main.py:566-572`
**Issue:** Allows all origins, methods, headers
**Impact:** Security concern for production
**Fix:** Restrict to known frontend origins

### M12. Backend - Potential Null Returns Not Guarded
**Locations:**
- `main.py:1026` - `get_request_timeline()` could return None
- `main.py:1236` - `get_feedback_for_agent()` could return None
- Various recovery endpoints

**Impact:** Attribute errors on None objects
**Fix:** Add null checks before accessing properties

### M13. Runtime - Git Commit Agent Name Missing
**Location:** `src/runtime/agents/tools.py:720`
**Issue:** Records `agent_id` instead of `agent_name` in git commits
**Impact:** Less readable commit activity logs
**Fix:** Pass agent_name through tool context

---

## Priority 4: LOW Issues

### L1. Backend - No Endpoint Documentation
**Location:** `main.py`
**Issue:** Most endpoints lack docstrings beyond WebSocket events
**Impact:** Poor DX, harder to maintain
**Fix:** Add docstrings and response_model types

### L2. Frontend - PipelineTreeView Dynamic Tailwind
**Location:** `PipelineTreeView.jsx:81,86`
**Issue:** Uses `ml-${depth * 6}` which Tailwind can't process
**Impact:** Styling doesn't work correctly
**Fix:** Use inline styles or static class combinations

### L3. Agent Definitions - Database Manager Orphaned
**Location:** `developers/database_manager.md`
**Issue:** Not in hierarchy, not spawnable, "Supervised By: Synth Tech"
**Impact:** Unclear if agent is deprecated or special-case
**Fix:** Add to hierarchy or document as deprecated

### L4. Runtime - Activity Tracker Answer Missing Request ID
**Location:** `activity_tracker.py:321`
**Issue:** Answer activities have empty request_id field
**Impact:** Cannot filter answers by request
**Fix:** Pass request_id through answer recording

### L5. Runtime - CircuitBreaker Parameters Hardcoded
**Location:** `src/runtime/agents/runtime.py`
**Issue:** 5 failure threshold, 60s timeout are hardcoded
**Impact:** Cannot tune for different environments
**Fix:** Move to configuration

### L6. Backend - No Rate Limiting
**Location:** `main.py`
**Issue:** No rate limiting on any endpoints
**Impact:** API vulnerable to abuse
**Fix:** Add rate limiting middleware

### L7. Frontend - No Loading States in Some Dashboards
**Locations:** Various dashboard components
**Issue:** Some views don't show loading state during data fetch
**Impact:** Blank screens during load
**Fix:** Add consistent loading indicators

### L8. Agent Definitions - Circular Spawn Potential
**Location:** TDD Coordinator spawn permissions
**Issue:** Can spawn all Leads who can spawn Developers
**Impact:** Complex spawn trees, potential confusion
**Fix:** Document expected spawn patterns clearly

### L9. Runtime - No Graceful Shutdown
**Location:** `src/runtime/agents/`
**Issue:** No signal handling for clean shutdown
**Impact:** Could leave agents in bad state
**Fix:** Add signal handlers and cleanup

### L10. Backend - WebSocket Stats Not Real-Time
**Location:** `main.py:804`
**Issue:** Stats are snapshot, not live-updating
**Impact:** Stale connection counts
**Fix:** Document or make real-time

---

## Implementation Order Recommendation

### Phase 1: Critical Bug Fixes (Must Fix)
1. C1, C2 - Division by zero fixes (frontend)
2. C3 - HTTP response validation (frontend)
3. C5, C6 - Backend error handling
4. C7, C8 - Runtime activity tracker fixes

### Phase 2: High Priority Cleanup
5. H1 - Null/undefined handling (frontend)
6. H2 or H3 - Redux removal OR styling standardization
7. H6, H7 - Agent registry documentation
8. H9, H10 - Backend/runtime cleanup

### Phase 3: Medium Priority Polish
9. M4, M5 - Agent definition terminology cleanup
10. M7 - Remove unused frontend components
11. M8 - API service error handling
12. M11 - CORS configuration

### Phase 4: Low Priority Improvements
13. L1-L10 - Documentation, configuration, nice-to-haves

---

## Files Requiring Changes

### Frontend (12 files)
- `App.jsx` - Division by zero fix
- `HorizontalTimelineView.jsx` - Division by zero fix
- `AchievementsDashboard.jsx` - Division by zero fix
- `MetricsDashboard.jsx` - Null checks
- `ActivityFeed.jsx` - Null checks
- `GeneratedFiles.jsx` - Null checks
- `CostTrackingDashboard.jsx` - Error handling
- `RecoveryDashboard.jsx` - Error handling
- `api.js` - HTTP status checks
- `store/` - Remove or integrate
- `AgentStatusPane.jsx` - Style fix or remove
- `PipelineTreeView.jsx` - Style fix

### Backend (1 file)
- `main.py` - Error responses, validation, thread safety

### Runtime (4 files)
- `activity_tracker.py` - Request filtering, cleanup
- `metrics.py` - Insert column fix
- `tools.py` - Agent name in git commits
- `websocket_manager.py` - Consider persistence

### Agent Definitions (15+ files)
- `leadership/development_manager.md` - Model fix
- `leadership/system_architect.md` - Model fix
- `leadership/tdd_coordinator.md` - Model fix, spawn fix
- `developers/*.md` - Terminology cleanup
- `testers/*.md` - Terminology cleanup
- `AGENT_REGISTRY.md` - Document all agents

---

## Testing Requirements

After fixes, verify:
1. Progress bars render correctly with zero max_iterations
2. Empty achievements array doesn't crash
3. API errors show proper error messages
4. Agents spawn with correct models
5. Activity hierarchy filters by request_id
6. Git commits record agent names
7. Token usage persists to metrics DB
8. System polish endpoints work or are removed
