# Ensemble V1 Cleanup - Requirements Document

## Project Overview

### Vision
Execute a comprehensive cleanup of the Ensemble V1 codebase to fix all identified issues across 4 phases: Critical Bug Fixes, High Priority Cleanup, Medium Priority Polish, and Low Priority Improvements. This cleanup will improve system stability, code quality, maintainability, and documentation.

### Core Problem
The Ensemble V1 codebase has accumulated technical debt including:
- Critical bugs (division by zero in progress bars, HTTP validation issues, bare except clauses)
- Dead code (unused Redux infrastructure)
- Incomplete implementations (request filtering, memory cleanup)
- Missing/outdated documentation (agent registry, API docs)
- Inconsistent error handling and hardcoded values

### Solution
Systematic execution of 12 discrete cleanup tasks organized into 4 priority phases, each with clear acceptance criteria and test plans already defined in the cleanup prompts.

## Execution Strategy

### Source of Truth
All detailed specifications are in `/docs/current/v1_cleanup_prompts/`:
- Each prompt contains Context, Files to Modify, Requirements, Acceptance Criteria, and Test Plan
- Agents should read their assigned prompt file for complete specifications

### Agent Assignments

| Phase | Prompt File | Agent Type | Description |
|-------|-------------|------------|-------------|
| 1 | 01_frontend_division_by_zero.md | Frontend Developer | Fix divide by zero in progress bars |
| 1 | 02_frontend_http_validation.md | Frontend Developer | Add HTTP response validation |
| 1 | 03_backend_error_handling.md | Backend Developer | Fix error responses and bare excepts |
| 1 | 04_runtime_activity_tracker.md | Backend Developer | Fix request filtering and cleanup |
| 2 | 05_frontend_null_handling.md | Frontend Developer | Add null checks across components |
| 2 | 06_frontend_redux_removal.md | Frontend Developer | Remove unused Redux infrastructure |
| 2 | 07_agent_registry_update.md | Documentation | Update AGENT_REGISTRY.md |
| 2 | 08_backend_runtime_cleanup.md | Backend Developer | Fix system polish and metrics |
| 3 | 09_agent_definitions_cleanup.md | Documentation | Fix terminology and models |
| 3 | 10_frontend_component_cleanup.md | Frontend Developer | Remove/integrate unused components |
| 3 | 11_api_service_hardening.md | Frontend Developer | Improve API error handling |
| 4 | 13_documentation.md | Documentation | Add missing documentation |
| 4 | 14_configuration.md | Backend Developer | Make hardcoded values configurable |

## Phase 1: Critical Bug Fixes (MUST COMPLETE FIRST)

### Task 1.1: Frontend Division by Zero
- **Files**: HorizontalTimelineView.jsx, App.jsx, AchievementsDashboard.jsx
- **Issue**: Progress bars calculate `current/max` without checking for zero denominator
- **Fix**: Add `|| 1` fallback or conditional rendering for zero cases
- **Priority**: CRITICAL - Can crash UI rendering

### Task 1.2: Frontend HTTP Validation
- **Files**: frontend/src/services/api.js (or similar)
- **Issue**: HTTP responses not validated before use
- **Fix**: Add response status checks, handle non-JSON responses gracefully
- **Priority**: CRITICAL - Causes runtime errors

### Task 1.3: Backend Error Handling
- **File**: backend/main.py
- **Issues**: 
  - Tuple returns instead of HTTPException (line 865)
  - Bare `except:` clauses swallowing all exceptions (lines 643, 784)
  - Missing input validation on query parameters
- **Fix**: Use HTTPException, specific exception handling with logging, add Query validation
- **Priority**: CRITICAL - Silent failures, inconsistent API behavior

### Task 1.4: Runtime Activity Tracker
- **File**: src/runtime/agents/activity_tracker.py
- **Issues**:
  - `get_agent_hierarchy()` returns unfiltered data when request_id provided
  - `clear_request()` doesn't actually clear hierarchy/states
  - Answer activity missing request_id
- **Fix**: Implement proper filtering and cleanup, pass request_id through all methods
- **Priority**: CRITICAL - Memory leaks, incorrect data isolation

## Phase 2: High Priority Cleanup

### Task 2.1: Frontend Null Handling
- **Files**: Various React components
- **Issue**: Missing null/undefined checks causing runtime errors
- **Fix**: Add defensive null checks, optional chaining, default values
- **Priority**: HIGH - Prevents crashes

### Task 2.2: Redux Removal
- **Files**: store/store.js, store/agentSlice.js, main.jsx
- **Issue**: Redux is configured but completely unused (dead code)
- **Fix**: Remove store directory, update main.jsx to remove Provider
- **Priority**: HIGH - Dead code maintenance burden
- **Prerequisite**: Verify NO components actually use Redux before removal

### Task 2.3: Agent Registry Update (Documentation)
- **File**: docs/current/AGENT_REGISTRY.md
- **Issue**: Lists 16 agents but 19+ exist; missing status, spawn paths
- **Fix**: Document all agents, add status column, document spawn hierarchy
- **Priority**: HIGH - Documentation doesn't match reality

### Task 2.4: Backend Runtime Cleanup
- **Files**: Various backend/runtime files
- **Issue**: System polish and metrics incomplete
- **Fix**: Per prompt specifications
- **Priority**: HIGH

## Phase 3: Medium Priority Polish

### Task 3.1: Agent Definitions Cleanup (Documentation)
- **Files**: Agent definition markdown files
- **Issue**: Old drum corps terminology still present, model preferences inconsistent
- **Fix**: Standardize terminology, update model recommendations
- **Priority**: MEDIUM

### Task 3.2: Frontend Component Cleanup
- **Files**: Various unused React components
- **Issue**: Components exist but aren't integrated
- **Fix**: Remove or properly integrate unused components
- **Priority**: MEDIUM

### Task 3.3: API Service Hardening
- **Files**: Frontend API service layer
- **Issue**: Error handling could be more robust
- **Fix**: Add retry logic, better error messages, timeout handling
- **Priority**: MEDIUM

## Phase 4: Low Priority Improvements

### Task 4.1: Documentation
- **Files**: Backend main.py, runtime modules, CLAUDE.md
- **Issue**: Missing docstrings, outdated docs
- **Fix**: Add FastAPI docstrings, document complex functions
- **Priority**: LOW - Improves maintainability

### Task 4.2: Configuration
- **Files**: Various files with hardcoded values
- **Issue**: Values should be configurable
- **Fix**: Extract to configuration, add env var support
- **Priority**: LOW - Improves flexibility

## Technical Constraints

### Must Preserve
- All existing functionality
- API contracts (no breaking changes to API responses)
- Test compatibility

### Technology Stack
- Frontend: React + Vite
- Backend: Python + FastAPI
- Runtime: Python with SQLite metrics

### Testing Requirements
- All changes must not break existing tests
- Each task includes its own test plan in the prompt file
- Manual verification required for UI changes

## Success Criteria

### Phase 1 Complete When:
- [ ] No NaN values appear in any progress bars
- [ ] HTTP errors are handled gracefully
- [ ] No bare `except:` clauses in backend
- [ ] Request filtering works correctly in activity tracker
- [ ] Memory doesn't grow indefinitely for completed requests

### Phase 2 Complete When:
- [ ] No null reference errors in frontend
- [ ] Redux infrastructure removed (or documented as intentionally kept)
- [ ] Agent registry documents all 19+ agents with status
- [ ] Backend runtime cleanup complete per prompt specs

### Phase 3 Complete When:
- [ ] No drum corps terminology in agent definitions
- [ ] Unused components removed or integrated
- [ ] API service has improved error handling

### Phase 4 Complete When:
- [ ] All API endpoints have docstrings visible in /docs
- [ ] Hardcoded values moved to configuration
- [ ] CLAUDE.md updated with any new patterns

## Implementation Notes

### Parallel vs Sequential Execution
- Phase 1 tasks can be executed in parallel (different files)
- Phase 2 tasks mostly parallel except Redux removal (verify first)
- Each phase should complete before next phase starts

### Rollback Strategy
- Git commits after each task
- Easy to revert individual changes if needed

### Communication
- Read the specific prompt file before starting work
- Follow acceptance criteria exactly
- Run test plan for verification

## Out of Scope
- New feature development
- Major architectural changes
- Performance optimization beyond fixing memory leaks
- Migration to different technologies

## Assumptions Made
- All prompt files exist and contain accurate specifications
- The codebase is buildable and runnable in current state
- Test environment is available for verification
- No breaking changes to external APIs needed
