# Prompt: Remove Unused Redux Infrastructure

## Context

The frontend has a Redux store configured but it's completely unused. All state management is done with local useState hooks. This is dead code that should be removed to reduce confusion.

## Priority
HIGH - Dead code, maintenance burden

## Files to Modify

1. `src/field/ensemble_ui/frontend/src/store/store.js` - DELETE
2. `src/field/ensemble_ui/frontend/src/store/agentSlice.js` - DELETE
3. `src/field/ensemble_ui/frontend/src/store/` directory - DELETE
4. `src/field/ensemble_ui/frontend/src/main.jsx` - Remove Provider
5. `src/field/ensemble_ui/frontend/package.json` - Remove Redux dependencies (optional)

## Requirements

### Step 1: Check for Any Redux Usage

First, search the codebase for any Redux usage:
```bash
grep -r "useSelector\|useDispatch\|Provider\|configureStore" src/field/ensemble_ui/frontend/src/
```

If ANY components use Redux, do NOT proceed with removal. Instead, document which components use it.

### Step 2: Remove Redux Provider from main.jsx

**Current Code (main.jsx):**
```javascript
import { Provider } from 'react-redux';
import { store } from './store/store';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </StrictMode>,
)
```

**Fixed Code:**
```javascript
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './index.css';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### Step 3: Delete Store Directory

Delete the entire store directory:
- `src/field/ensemble_ui/frontend/src/store/store.js`
- `src/field/ensemble_ui/frontend/src/store/agentSlice.js`
- `src/field/ensemble_ui/frontend/src/store/` (directory)

### Step 4: Update package.json (Optional)

If you want to fully clean up, remove Redux dependencies from package.json:
```json
// Remove these from dependencies:
"@reduxjs/toolkit": "...",
"react-redux": "...",
```

Then run `npm install` to update package-lock.json.

**Note:** This step is optional - keeping the dependencies doesn't hurt and avoids potential issues.

## Alternative: Integrate Redux Instead

If the team prefers to USE Redux instead of removing it, here's what would need to happen:

1. Keep the store infrastructure
2. Migrate App.jsx state to Redux:
   - `activities` -> Redux slice
   - `hierarchy` -> Redux slice
   - `agentStates` -> Redux slice
   - etc.
3. Update components to use `useSelector` and `useDispatch`

This is a larger effort and should be a separate task if chosen.

## Acceptance Criteria

1. No Redux imports in the codebase
2. App still renders and functions correctly
3. No unused dependencies warning
4. Build succeeds without errors
5. All features still work (verify manually)

## Test Plan

1. Before changes, verify app works: `npm run dev`
2. Make the changes
3. Run: `npm run build` - should succeed
4. Run: `npm run dev` - app should work
5. Navigate through all views
6. Submit a test problem and verify agent tracking works
7. Check browser console for errors

## Notes

- This is a cleanup task - removing unused code
- If ANY Redux usage is found, abort and report findings
- The useState approach is working fine, no need to migrate to Redux
- Keeping dependencies in package.json is safer than removing them
