# Prompt: Fix Frontend Null/Undefined Handling

## Context

Several frontend components access nested object properties without null checks, causing runtime errors when API returns unexpected data.

## Priority
HIGH - Causes component crashes on edge cases

## Files to Modify

1. `src/field/ensemble_ui/frontend/src/components/MetricsDashboard.jsx`
2. `src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`
3. `src/field/ensemble_ui/frontend/src/components/GeneratedFiles.jsx`
4. `src/field/ensemble_ui/frontend/src/components/CostTrackingDashboard.jsx`

## Requirements

### File 1: MetricsDashboard.jsx

**Location:** Lines 30-34 and throughout
**Current Pattern:**
```javascript
summary?.overall?.total_executions || 0
agentMetrics?.agents?.map(...)
summary?.most_active_agents.map(...)  // Missing ?. before map
```

**Fix:** Add optional chaining and null coalescing:
```javascript
// For scalar values
{summary?.overall?.total_executions ?? 0}
{summary?.overall?.success_rate?.toFixed(1) ?? '0.0'}%
{(summary?.overall?.avg_duration_ms ?? 0) / 1000}

// For arrays (use optional chaining AND default array)
{(agentMetrics?.agents ?? []).map(agent => ...)}
{(summary?.most_active_agents ?? []).map(agent => ...)}
```

**Also check:**
- Line 110: `summary.overall.avg_duration_ms` needs null check
- Line 134: `.map()` on potentially undefined array

### File 2: ActivityFeed.jsx

**Location:** Lines 145, 155, 160
**Current Pattern:**
```javascript
{data.result.summary}
{data.result.deliverables?.files}
```

**Fix:**
```javascript
{data?.result?.summary ?? 'No summary available'}
{(data?.result?.deliverables?.files ?? []).map(...)}
```

**Check all occurrences of:**
- `data.result`
- `data.result.summary`
- `data.result.deliverables`

### File 3: GeneratedFiles.jsx

**Location:** Line 160
**Current Pattern:**
```javascript
{file.preview.length >= 500 && ...}
```

**Fix:**
```javascript
{file.preview?.length >= 500 && ...}
// Or more defensive:
{(file.preview?.length ?? 0) >= 500 && ...}
```

**Also check:**
- All accesses to `file.preview`
- All accesses to `file.content`
- Any other nested file properties

### File 4: CostTrackingDashboard.jsx

**Location:** Line 227 and throughout
**Issues:**
```javascript
const efficiency = ((model.success_rate || 0) / relativeCost * 10).toFixed(1);
```

**Fix:** While this is safe from division issues, add null checks:
```javascript
const efficiency = (((model?.success_rate ?? 0) / relativeCost) * 10).toFixed(1);
```

**Check all:**
- `modelMetrics?.models?.map()`
- `costByAgent?.agents?.map()`
- Any nested property access

## General Patterns to Apply

### Pattern 1: Scalar Values
```javascript
// Before
{data.count}
{data.nested.value}

// After
{data?.count ?? 0}
{data?.nested?.value ?? 'default'}
```

### Pattern 2: Arrays to Map
```javascript
// Before
{data.items.map(item => ...)}

// After
{(data?.items ?? []).map(item => ...)}
```

### Pattern 3: Conditional Rendering
```javascript
// Before
{data.exists && <Component />}

// After
{data?.exists && <Component />}
```

### Pattern 4: Object Destructuring
```javascript
// Before
const { name, value } = data.item;

// After
const { name = '', value = 0 } = data?.item ?? {};
```

## Acceptance Criteria

1. No "cannot read property of undefined" errors in console
2. Components render gracefully with empty/missing data
3. Default values shown instead of blank/broken UI
4. No crashes when API returns partial data
5. All `.map()` calls are protected against undefined arrays

## Test Plan

1. Start frontend and backend
2. Open browser console and navigate through all views
3. Check for any undefined/null errors
4. Temporarily modify API to return partial data:
   ```python
   # In backend, return empty objects
   return {"data": {}}
   ```
5. Verify UI shows defaults instead of crashing

## Notes

- Use `??` (nullish coalescing) over `||` for numbers (0 is valid)
- Use `|| []` for arrays where empty is acceptable
- Use `?? {}` for objects to enable safe destructuring
- Add helpful default text like "No data available" where appropriate
