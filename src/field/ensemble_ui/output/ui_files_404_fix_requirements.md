# UI Files Endpoint 404 Error - Bug Fix Requirements

## Problem Statement

Users are seeing 404 "Not Found" errors in the UI when the frontend attempts to fetch generated files from the backend API. The error message appears as:

```
{"detail":"Not Found"}
```

Preceded by a BOM character (`\ufeff`), indicating potential encoding or response format issues.

## Context

- **User Report**: "Seeing a bunch of these errors in the ui when pinging files UI"
- **Affected Endpoint**: `/api/activity/files`
- **Frontend Location**: `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/frontend/`
- **Backend Location**: `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/backend/`
- **Output Directory**: `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/output/`

## Technical Investigation Required

### 1. Backend Status
- Verify backend server is running on expected port (8001)
- Check if endpoint registration is correct
- Validate endpoint handler function exists and is accessible

### 2. Frontend API Calls
- Review `getGeneratedFiles()` function in `frontend/src/services/api.js`
- Verify correct URL construction and parameters
- Check polling interval and frequency (currently set to 1000ms in App.jsx)

### 3. Potential Root Causes
- Backend server not running or crashed
- Endpoint URL mismatch between frontend and backend
- CORS configuration issues
- Activity tracker database connectivity problems
- Missing dependencies or import errors in backend

## Files to Examine

### Backend Files
1. `backend/main.py` - Main FastAPI application
   - Line 717: `@app.get("/api/activity/files")` endpoint definition
   - Activity tracker integration
   - Error handling

2. Backend runtime dependencies:
   - `src/runtime/agents/activity_tracker.py` - Activity tracking system
   - `src/runtime/agents/runtime.py` - AgentRuntime class

### Frontend Files
1. `frontend/src/services/api.js` - API service layer
   - `getGeneratedFiles()` function
   - API_BASE_URL configuration

2. `frontend/src/App.jsx` - Main application component
   - Polling logic for file updates
   - Error handling display

3. `frontend/src/components/GeneratedFiles.jsx` - Files display component

## Expected Behavior

1. Frontend polls `/api/activity/files` endpoint at configured interval
2. Backend returns JSON response with generated files:
   ```json
   {
     "files": [...],
     "count": 0
   }
   ```
3. UI displays files in the "Generated Files" section without errors

## Success Criteria

1. **No 404 errors** when frontend polls files endpoint
2. **Correct response format** - JSON without BOM characters
3. **Files displayed** in UI when agents generate outputs
4. **Error handling** - Graceful degradation if backend temporarily unavailable
5. **Logging** - Clear error messages in both frontend console and backend logs

## Constraints

- **No breaking changes** to existing API contract
- **Maintain backwards compatibility** with current frontend implementation
- **Minimal code changes** - focus on fixing the specific 404 issue
- **Preserve existing functionality** - don't break other endpoints

## Out of Scope

- Adding new features to file display
- Redesigning the UI layout
- Changing polling architecture to WebSockets
- Performance optimization beyond fixing the bug

## Assumptions

- Backend is intended to run on port 8001
- Frontend is configured to connect to localhost:8001
- Activity tracker database exists and is accessible at `~/.ensemble/metrics.db`
- All required Python dependencies are installed

## Acceptance Tests

1. **Backend health check**: `curl http://localhost:8001/api/status` returns 200 OK
2. **Files endpoint test**: `curl http://localhost:8001/api/activity/files` returns JSON (not 404)
3. **Frontend test**: Open UI in browser, verify no 404 errors in console for `/api/activity/files`
4. **Integration test**: Generate a file via agent execution, verify it appears in UI without errors

## Deliverables

1. **Root cause analysis** - Document why 404 was occurring
2. **Code fixes** - Implement solution in backend/frontend as needed
3. **Verification** - Test all affected endpoints work correctly
4. **Documentation** - Update any relevant docs about endpoint usage
