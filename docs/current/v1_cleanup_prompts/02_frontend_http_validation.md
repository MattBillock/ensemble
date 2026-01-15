# Prompt: Add HTTP Response Validation to Frontend

## Context

All frontend API calls use fetch but don't check `response.ok` before parsing JSON. This means HTTP errors (400, 404, 500) are silently swallowed and undefined data gets set in component state, causing cascading errors.

## Priority
CRITICAL - Causes silent failures and broken UI states

## Files to Modify

1. `src/field/ensemble_ui/frontend/src/services/api.js` (primary)
2. All dashboard components that make direct fetch calls:
   - `MetricsDashboard.jsx`
   - `CostTrackingDashboard.jsx`
   - `RecoveryDashboard.jsx`
   - `AchievementsDashboard.jsx`
   - `SelfImprovementDashboard.jsx`
   - `App.jsx`

## Requirements

### Part 1: Fix api.js (Central Fix)

For every function in `api.js` that uses fetch, add response validation:

**Current Pattern:**
```javascript
export async function fetchSomething() {
  try {
    const response = await fetch(`${API_BASE}/endpoint`);
    return await response.json();
  } catch (error) {
    console.error('Error:', error);
    return null;
  }
}
```

**Fixed Pattern:**
```javascript
export async function fetchSomething() {
  try {
    const response = await fetch(`${API_BASE}/endpoint`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching something:', error);
    return null;
  }
}
```

Apply this fix to ALL fetch functions in api.js (there are approximately 50+ functions).

### Part 2: Fix Dashboard Components

Dashboard components that make direct fetch calls should also validate:

**MetricsDashboard.jsx** - Around lines 22-34:
```javascript
// Current
setSummary(await summaryRes.json());

// Fixed
if (!summaryRes.ok) throw new Error(`HTTP ${summaryRes.status}`);
setSummary(await summaryRes.json());
```

Apply to all direct fetch calls in dashboards.

### Part 3: Handle Error State in UI

After adding HTTP validation, ensure error states are handled in the UI:

```javascript
// In useEffect catch blocks, set meaningful error state
catch (error) {
  console.error('Error loading data:', error);
  setError(error.message);  // If error state exists
  // Or set data to safe defaults
  setData([]);
}
```

## Acceptance Criteria

1. All fetch calls in api.js check `response.ok`
2. All direct dashboard fetch calls check `response.ok`
3. HTTP errors (400, 404, 500) throw meaningful errors
4. Error messages include HTTP status code
5. Catch blocks log the error clearly
6. Components don't crash when API returns error

## Test Plan

1. Start frontend and backend
2. Temporarily modify backend to return 500 for an endpoint
3. Verify frontend shows error message instead of crashing
4. Check browser console for meaningful error logs
5. Verify no "undefined" errors in console

## Notes

- Return empty arrays `[]` for list endpoints on error
- Return empty objects `{}` for single-item endpoints on error
- Don't return `null` if the component expects an array (causes `.map()` errors)
- Consider adding a global error handler utility function
