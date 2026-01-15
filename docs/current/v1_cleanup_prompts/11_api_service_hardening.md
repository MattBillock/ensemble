# Prompt: Harden API Service Layer

## Context

The api.js service file has comprehensive coverage but could be improved with better error handling and response validation.

## Priority
MEDIUM - Improves reliability

## Files to Modify

1. `src/field/ensemble_ui/frontend/src/services/api.js`

## Requirements

### Part 1: Create Error Handling Utility

Add a helper function for consistent error handling:

```javascript
// At top of api.js
const API_BASE = 'http://localhost:8001';

class APIError extends Error {
  constructor(message, status, endpoint) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.endpoint = endpoint;
  }
}

async function fetchWithValidation(url, options = {}) {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const errorBody = await response.text();
      throw new APIError(
        `HTTP ${response.status}: ${errorBody || response.statusText}`,
        response.status,
        url
      );
    }

    // Handle empty responses
    const text = await response.text();
    if (!text) {
      return null;
    }

    return JSON.parse(text);
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Network error or JSON parse error
    throw new APIError(
      `Request failed: ${error.message}`,
      0,
      url
    );
  }
}
```

### Part 2: Update All Fetch Functions

Replace direct fetch calls with the utility:

**Before:**
```javascript
export async function fetchActivities(agentId = null, requestId = null, limit = 100) {
  try {
    const params = new URLSearchParams();
    if (agentId) params.append('agent_id', agentId);
    if (requestId) params.append('request_id', requestId);
    params.append('limit', limit);

    const response = await fetch(`${API_BASE}/api/activity/recent?${params}`);
    return await response.json();
  } catch (error) {
    console.error('Error fetching activities:', error);
    return [];
  }
}
```

**After:**
```javascript
export async function fetchActivities(agentId = null, requestId = null, limit = 100) {
  try {
    const params = new URLSearchParams();
    if (agentId) params.append('agent_id', agentId);
    if (requestId) params.append('request_id', requestId);
    params.append('limit', limit);

    const data = await fetchWithValidation(`${API_BASE}/api/activity/recent?${params}`);
    return data ?? [];
  } catch (error) {
    console.error('Error fetching activities:', error);
    return [];
  }
}
```

### Part 3: Return Appropriate Defaults

Ensure functions return safe defaults on error:

| Return Type | Default |
|-------------|---------|
| Array | `[]` |
| Object | `{}` |
| Number | `0` |
| Boolean | `false` |
| String | `''` |

**Examples:**
```javascript
// For list endpoints
export async function fetchAgentHierarchy() {
  try {
    return await fetchWithValidation(`${API_BASE}/api/activity/hierarchy`) ?? {};
  } catch (error) {
    console.error('Error:', error);
    return {};  // Not null!
  }
}

// For single item endpoints
export async function fetchMetricsSummary(days = 30) {
  try {
    return await fetchWithValidation(`${API_BASE}/api/metrics/summary?days=${days}`) ?? {
      overall: { total_executions: 0, success_rate: 0 }
    };
  } catch (error) {
    console.error('Error:', error);
    return { overall: { total_executions: 0, success_rate: 0 } };
  }
}
```

### Part 4: Add Request Timeout

Add timeout handling to prevent hanging requests:

```javascript
async function fetchWithValidation(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      // ... error handling
    }

    return JSON.parse(await response.text());
  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      throw new APIError('Request timed out', 408, url);
    }

    throw error;
  }
}
```

### Part 5: Add Response Type Validation (Optional)

For critical endpoints, add basic shape validation:

```javascript
function validateMetricsSummary(data) {
  if (!data || typeof data !== 'object') return false;
  if (!data.overall || typeof data.overall !== 'object') return false;
  return true;
}

export async function fetchMetricsSummary(days = 30) {
  try {
    const data = await fetchWithValidation(`${API_BASE}/api/metrics/summary?days=${days}`);

    if (!validateMetricsSummary(data)) {
      console.warn('Invalid metrics summary response shape');
      return { overall: { total_executions: 0, success_rate: 0 } };
    }

    return data;
  } catch (error) {
    console.error('Error:', error);
    return { overall: { total_executions: 0, success_rate: 0 } };
  }
}
```

## Acceptance Criteria

1. All fetch functions use fetchWithValidation utility
2. HTTP errors throw meaningful APIError
3. All functions return safe defaults (not null)
4. Request timeout is implemented
5. Network errors are caught and logged
6. No breaking changes to function signatures

## Test Plan

1. Test normal operation:
   ```bash
   npm run dev
   # Navigate through all views, verify data loads
   ```

2. Test error handling:
   - Stop backend, verify frontend shows errors gracefully
   - Restart backend, verify recovery

3. Test timeout:
   - Add artificial delay to backend endpoint
   - Verify timeout error is shown

4. Check console:
   - No uncaught promise rejections
   - Errors are logged with context

## Notes

- Don't change function signatures (would break callers)
- Focus on robustness, not new features
- Consider adding retry logic for transient failures (optional)
- Keep error messages user-friendly
