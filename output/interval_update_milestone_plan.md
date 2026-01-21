# Milestone Plan: Update Ensemble UI Interval Options

## Project Overview
**Project ID:** 1e1283ed  
**Date:** 2026-01-13  
**Status:** In Progress

## Analysis Summary

### Current Implementation (in App.jsx)
The interval selector is located in the header section with these current options:
- 500ms (500 milliseconds)
- 1s (1 second / 1000ms)  
- 2s (2 seconds / 2000ms)

Default: 1000ms (1 second)

### Target Implementation
Update to:
- 1s (1 second / 1000ms)
- 1m (1 minute / 60000ms)
- 5m (5 minutes / 300000ms)

Default: 1000ms (1 second) - keeping same default

### Key Code Location
File: `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/frontend/src/App.jsx`

Lines to modify:
1. ButtonGroup with interval buttons (around lines 165-180)
2. Activity Feed header display showing current interval (around line 263)

---

## Milestone 1: Update Interval Options (Single Milestone Project)

### Objective
Update the interval dropdown options from "500ms, 1s, 2s" to "1s, 1m, 5m" in the Ensemble UI.

### Deliverables
1. Updated `App.jsx` with new interval options
2. Unit tests for the interval functionality
3. Documentation of changes

### Tasks
1. **Modify interval ButtonGroup** - Change button values and labels
   - Replace 500ms button with 1s (1000ms)
   - Replace 1s button with 1m (60000ms)
   - Replace 2s button with 5m (300000ms)

2. **Update interval display logic** - Fix status text in Activity Feed
   - Convert milliseconds to human-readable format (1s, 1m, 5m)

3. **Test the changes** - Verify intervals work correctly
   - Manual verification that polling works at each interval
   - Unit tests for interval values

4. **Update documentation** - Note the changes made

### Acceptance Criteria
- [ ] Dropdown shows "1s", "1m", "5m" options
- [ ] Selecting "1s" results in 1-second update interval (1000ms)
- [ ] Selecting "1m" results in 1-minute update interval (60000ms)  
- [ ] Selecting "5m" results in 5-minute update interval (300000ms)
- [ ] UI updates at the correct frequency for each selection
- [ ] No console errors or warnings
- [ ] Default interval remains at 1s (1000ms)

### Dependencies
None - this is a single file modification

### Estimated Effort
Low complexity - straightforward value and label updates

---

## Technical Decisions Made
1. **Keep default at 1000ms** - This is the most responsive reasonable default
2. **Use existing ButtonGroup pattern** - No architectural changes needed
3. **Add helper function for interval display** - Convert ms to human-readable format
