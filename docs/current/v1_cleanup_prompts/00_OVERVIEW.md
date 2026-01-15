# V1 Cleanup Prompts Overview

This directory contains agent swarm prompts to fix all identified issues in the Ensemble V1 cleanup.

## Execution Order

Execute these prompts in order. Each phase should be completed before moving to the next.

### Phase 1: Critical Bug Fixes
1. `01_frontend_division_by_zero.md` - Fix divide by zero in progress bars
2. `02_frontend_http_validation.md` - Add HTTP response validation
3. `03_backend_error_handling.md` - Fix error responses and bare excepts
4. `04_runtime_activity_tracker.md` - Fix request filtering and cleanup

### Phase 2: High Priority Cleanup
5. `05_frontend_null_handling.md` - Add null checks across components
6. `06_frontend_redux_removal.md` - Remove unused Redux infrastructure
7. `07_agent_registry_update.md` - Document all agents properly
8. `08_backend_runtime_cleanup.md` - Fix system polish and metrics

### Phase 3: Medium Priority Polish
9. `09_agent_definitions_cleanup.md` - Fix terminology and models
10. `10_frontend_component_cleanup.md` - Remove/integrate unused components
11. `11_api_service_hardening.md` - Improve API error handling

### Phase 4: Low Priority Improvements
13. `13_documentation.md` - Add missing documentation
14. `14_configuration.md` - Make hardcoded values configurable

## Usage

Each prompt file contains:
1. **Context** - What the agent needs to understand
2. **Files to Modify** - Specific files that need changes
3. **Requirements** - Detailed specification of changes
4. **Acceptance Criteria** - How to verify the fix is complete
5. **Test Plan** - How to test the changes

## Agent Assignment

| Prompt | Recommended Agent |
|--------|-------------------|
| 01-02 | Frontend Developer |
| 03 | Backend Developer |
| 04, 08 | Backend Developer |
| 05-06 | Frontend Developer |
| 07, 09 | Executive Director (documentation) |
| 10-11 | Frontend Developer |
| 12 | Backend Developer |
| 13-14 | Development Manager |
