# Ensemble UI Bug Fixes - Milestone Plan

## Project Overview
Fix three identified bugs in the Ensemble UI:
1. Approve All button not spawning agents
2. Blank agent names in Metrics Dashboard
3. Verify YOLO mode is working (confirmed working - no fix needed)

## Milestone 1: Backend Bug Fixes

### Objective
Fix the "Approve All" button to correctly spawn executive agents for pending reviews.

### Root Cause
The `approve_all_pending_reviews` function calls `swarm.update_pending_review_status()` but the `SwarmStateManager` class only defines `update_pending_review()`. This method name mismatch causes an AttributeError.

### Deliverables
1. Fix method call at line ~2309: `update_pending_review_status` → `update_pending_review`
2. Fix method call at lines ~2336-2339: Same correction with proper keyword arguments
3. Unit tests verifying the fix

### File Changes
- `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/backend/main.py`

### Acceptance Criteria
- [ ] Approve All button spawns agents for all pending reviews
- [ ] Approved count shows correct number (> 0 when reviews exist)
- [ ] Status changes to "in_progress" for approved items

---

## Milestone 2: Frontend Bug Fixes

### Objective
Fix blank agent names in the Metrics Dashboard by adding fallback text.

### Root Cause
The MetricsDashboard component renders `{agent.agent_name}` directly without null checks.

### Deliverables
1. Add fallback `|| '(unknown agent)'` for agent names in:
   - Most Active Agents table (line ~137)
   - Best Performing Agents table (line ~169)
   - Agent Performance table (line ~212)
   - Error Analysis table (line ~373)

### File Changes
- `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/frontend/src/components/MetricsDashboard.jsx`

### Acceptance Criteria
- [ ] No blank entries in agent name columns
- [ ] Shows "(unknown agent)" for null/empty values
- [ ] Existing valid agent names still display correctly

---

## Milestone 3: Verification

### Objective
Verify all fixes work correctly and YOLO mode is functioning as designed.

### Deliverables
1. Manual verification checklist completed
2. Integration test results

### Acceptance Criteria
- [ ] Bug #1: Approve All creates agents with approved count > 0
- [ ] Bug #2: No blank agent names in Metrics Dashboard
- [ ] Bug #3: YOLO mode bypasses review phases (confirmed working)

---

## Timeline
- Milestone 1: Backend Fix - Immediate
- Milestone 2: Frontend Fix - Immediate (parallel)
- Milestone 3: Verification - After M1 and M2 complete

## Dependencies
- Milestone 3 depends on Milestone 1 and 2 completion
