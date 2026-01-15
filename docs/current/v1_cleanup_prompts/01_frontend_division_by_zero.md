# Prompt: Fix Frontend Division by Zero Issues

## Context

The Ensemble UI has several locations where progress bars calculate width percentages by dividing current value by max value. When max value is 0, this causes NaN to be rendered, breaking the UI.

## Priority
CRITICAL - Can crash UI rendering

## Files to Modify

1. `src/field/ensemble_ui/frontend/src/components/HorizontalTimelineView.jsx`
2. `src/field/ensemble_ui/frontend/src/App.jsx`
3. `src/field/ensemble_ui/frontend/src/components/AchievementsDashboard.jsx`

## Requirements

### File 1: HorizontalTimelineView.jsx

**Location:** Around line 508
**Current Code:**
```javascript
width={`${(selectedAgent.current_iteration / selectedAgent.max_iterations) * 100}%`}
```

**Fix:** Add fallback to prevent division by zero:
```javascript
width={`${(selectedAgent.current_iteration / (selectedAgent.max_iterations || 1)) * 100}%`}
```

Search for ALL similar patterns in this file and fix them all. Look for any division involving:
- `current_iteration / max_iterations`
- Any percentage calculations with potential zero denominators

### File 2: App.jsx

**Location:** Around line 494
**Current Code:**
```javascript
width={`${(state.current_iteration / state.max_iterations) * 100}%`}
```

**Fix:** Same pattern - add `|| 1` fallback:
```javascript
width={`${(state.current_iteration / (state.max_iterations || 1)) * 100}%`}
```

Search entire file for similar patterns.

### File 3: AchievementsDashboard.jsx

**Location:** Around line 118
**Current Code:**
```javascript
now={(unlockedCount / achievements.length) * 100}
```

**Fix:** Guard against empty achievements array:
```javascript
now={achievements.length > 0 ? (unlockedCount / achievements.length) * 100 : 0}
```

## Acceptance Criteria

1. No division by zero errors when:
   - An agent has `max_iterations: 0`
   - The achievements array is empty
   - Any iteration counter is zero
2. Progress bars show 0% instead of NaN
3. UI renders without errors in these edge cases

## Test Plan

1. Start the frontend: `cd src/field/ensemble_ui/frontend && npm run dev`
2. Check browser console for any NaN warnings
3. If possible, create a test scenario with:
   - Empty achievements list
   - Agent with max_iterations = 0
4. Verify progress bars render as 0% width, not broken

## Notes

- Use `|| 1` pattern for simple divisions where 0% is acceptable fallback
- Use conditional rendering `? : 0` for cases where we want explicit 0
- Do NOT use `Math.max(1, denominator)` - the `|| 1` pattern is cleaner
- Check for similar patterns in other components while you're in the codebase
