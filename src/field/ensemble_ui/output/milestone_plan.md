# Ensemble V1 Cleanup - Milestone Plan

## Project: Ensemble V1 Cleanup
## Project ID: 430c992f
## Created: 2025-01-15

---

## Overview

This cleanup project addresses 12+ discrete technical debt items organized into 4 priority phases. Each task has detailed specifications in `/docs/current/v1_cleanup_prompts/`.

---

## Milestone 1: Critical Bug Fixes (Phase 1)

### Objective
Fix all critical bugs that can crash the UI or cause silent failures.

### Tasks (Can run in parallel - touch different files)
| Task ID | Prompt File | Description | Files |
|---------|-------------|-------------|-------|
| 1.1 | 01_frontend_division_by_zero.md | Fix divide by zero in progress bars | HorizontalTimelineView.jsx, App.jsx, AchievementsDashboard.jsx |
| 1.2 | 02_frontend_http_validation.md | Add HTTP response validation | api.js, dashboard components |
| 1.3 | 03_backend_error_handling.md | Fix error responses and bare excepts | backend/main.py |
| 1.4 | 04_runtime_activity_tracker.md | Fix request filtering and cleanup | activity_tracker.py |

### Deliverables
- [ ] No NaN values in progress bars
- [ ] HTTP errors handled gracefully in frontend
- [ ] No bare `except:` clauses in backend
- [ ] Request filtering and cleanup working in activity tracker

### Acceptance Criteria
- No division by zero errors in any scenario
- HTTP errors return meaningful messages
- All exceptions properly typed and logged
- Memory doesn't grow indefinitely for completed requests

### Dependencies
None - this is the first milestone

---

## Milestone 2: High Priority Cleanup (Phase 2)

### Objective
Remove dead code, add defensive null checks, update documentation.

### Tasks
| Task ID | Prompt File | Description | Files |
|---------|-------------|-------------|-------|
| 2.1 | 05_frontend_null_handling.md | Add null checks across components | Various React components |
| 2.2 | 06_frontend_redux_removal.md | Remove unused Redux infrastructure | store/, main.jsx |
| 2.3 | 07_agent_registry_update.md | Update AGENT_REGISTRY.md | docs/current/AGENT_REGISTRY.md |
| 2.4 | 08_backend_runtime_cleanup.md | Fix system polish and metrics | Backend/runtime files |

### Deliverables
- [ ] No null reference errors in frontend
- [ ] Redux infrastructure removed (dead code eliminated)
- [ ] Agent registry documents all 19+ agents
- [ ] Backend runtime cleanup complete

### Acceptance Criteria
- Frontend renders without null errors
- Store directory removed, main.jsx simplified
- AGENT_REGISTRY.md complete and accurate
- Backend metrics and cleanup working

### Dependencies
- Requires Milestone 1 completion

---

## Milestone 3: Medium Priority Polish (Phase 3)

### Objective
Clean up terminology, unused components, and improve API hardening.

### Tasks
| Task ID | Prompt File | Description | Files |
|---------|-------------|-------------|-------|
| 3.1 | 09_agent_definitions_cleanup.md | Fix terminology in agent definitions | Agent markdown files |
| 3.2 | 10_frontend_component_cleanup.md | Remove/integrate unused components | Various React components |
| 3.3 | 11_api_service_hardening.md | Improve API error handling | Frontend API service |

### Deliverables
- [ ] Consistent terminology in agent definitions
- [ ] Unused components removed or integrated
- [ ] API service has retry logic and better error handling

### Acceptance Criteria
- No drum corps terminology in agent definitions
- No orphaned components
- API calls handle failures gracefully

### Dependencies
- Requires Milestone 2 completion

---

## Milestone 4: Low Priority Improvements (Phase 4)

### Objective
Add documentation and make hardcoded values configurable.

### Tasks
| Task ID | Prompt File | Description | Files |
|---------|-------------|-------------|-------|
| 4.1 | 13_documentation.md | Add missing documentation | backend/main.py, CLAUDE.md |
| 4.2 | 14_configuration.md | Make hardcoded values configurable | Various files |

### Deliverables
- [ ] All API endpoints have docstrings
- [ ] Hardcoded values in configuration
- [ ] CLAUDE.md updated

### Acceptance Criteria
- FastAPI /docs shows endpoint documentation
- Configuration via environment variables
- Updated developer documentation

### Dependencies
- Requires Milestone 3 completion

---

## Execution Strategy

### Phase 1 Parallelization
Tasks 1.1-1.4 touch different files and can run in parallel:
- Frontend tasks (1.1, 1.2): Different components, can parallel
- Backend task (1.3): Independent file
- Runtime task (1.4): Independent file

### Git Strategy
- Commit after each task completion
- Descriptive commit messages per task
- Branch: main (cleanup tasks)

### Verification
Each task has its own test plan in the prompt file. Must verify:
1. Run test plan from prompt
2. Ensure no regression
3. Manual UI verification where applicable

---

## Risk Assessment

### High Risk
- Task 1.4 (Activity Tracker): Complex state management changes
- Task 2.2 (Redux Removal): Must verify no usage before removal

### Medium Risk
- Task 1.2 (HTTP Validation): Many files to update
- Task 2.4 (Backend Runtime): Complex system

### Low Risk
- Task 1.1 (Division by Zero): Simple fixes
- Documentation tasks: No code impact

---

## Timeline Estimate

| Milestone | Estimated Duration | Notes |
|-----------|-------------------|-------|
| Milestone 1 | 2-4 hours | Critical path, parallel execution |
| Milestone 2 | 3-5 hours | More complex, verification needed |
| Milestone 3 | 2-3 hours | Polish work |
| Milestone 4 | 1-2 hours | Documentation focus |

**Total Estimated: 8-14 hours**
