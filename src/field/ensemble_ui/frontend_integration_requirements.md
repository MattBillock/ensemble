# Frontend-Backend Integration Requirements

## Objective
Connect the existing React frontend to the FastAPI backend to enable full-stack Ensemble agent functionality.

## Current State
- ✅ React frontend with ProblemInputForm (Milestone 1)
- ✅ FastAPI backend with /api/generate-solution and /ws/agent-status (Milestone 2)
- ❌ No connection between frontend and backend
- ❌ No real-time status display
- ❌ No solution display component

## Requirements

### 1. Backend API Integration
Create `src/services/api.js` module:
- Function to POST problem description to `/api/generate-solution`
- Returns agent_id for tracking
- Error handling for network failures
- Base URL configuration (http://localhost:8000)

### 2. WebSocket Connection Manager
Create `src/services/websocket.js` module:
- Connect to `ws://localhost:8000/ws/agent-status`
- Handle connection lifecycle (open, close, error)
- Parse incoming JSON status messages
- Callback system for status updates
- Auto-reconnect on disconnect (with backoff)

### 3. Agent Status Display Component
Create `src/components/AgentStatus.jsx`:
- Display list of active agents
- Show current agent phase/status
- Real-time progress updates
- Loading animations
- Error state display

### 4. Solution Display Component
Create `src/components/SolutionDisplay.jsx`:
- Show generated code/solution when complete
- Syntax highlighting (use Prism.js or similar)
- Copy-to-clipboard button
- Formatted output for readability

### 5. Update App.jsx
- Integrate WebSocket connection on mount
- Call API when problem submitted
- Pass status updates to AgentStatus component
- Display SolutionDisplay when agent completes
- Handle cleanup on unmount

## Technical Constraints
- Must use React hooks (useState, useEffect, useCallback)
- Must handle WebSocket reconnection gracefully
- Must work with existing Tailwind CSS styling
- Must maintain existing test coverage

## Success Criteria
- [ ] User can submit problem description via form
- [ ] Frontend calls POST /api/generate-solution successfully
- [ ] WebSocket connection established and maintained
- [ ] Real-time agent status updates display correctly
- [ ] Solution displays when agent completes
- [ ] All new components have tests
- [ ] Existing tests still pass

## Out of Scope
- Actual agent execution (backend placeholder is OK for now)
- Authentication
- Multiple concurrent problems
- Problem history/persistence
