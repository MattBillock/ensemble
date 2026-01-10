# Ensemble UI - Completion Requirements

## Overview
Complete the Ensemble UI web application to provide a functional interface for submitting problems and monitoring agent execution in real-time.

## Current State
- ✅ React frontend with ProblemInputForm component
- ✅ FastAPI backend skeleton with CORS
- ✅ WebSocket endpoint for real-time updates
- ✅ Basic styling with Tailwind CSS
- ⚠️ Backend NOT integrated with real Ensemble agent runtime
- ⚠️ Status display shows raw JSON (not user-friendly)
- ⚠️ No agent hierarchy visualization
- ⚠️ No detailed agent output display

## Requirements

### 1. Backend Integration with Agent Runtime
**File**: `src/field/ensemble_ui/backend/main.py`

**Requirements**:
- Import Ensemble agent runtime (AgentDefinition, AgentRuntime, ToolRegistry)
- Add project root to sys.path for imports
- Update `AgentOrchestrator.spawn_executive_director()` to:
  - Accept problem description parameter
  - Load Executive Director agent from `leadership/executive_director.md`
  - Set up tools (ToolRegistry + SpawnAgentTool)
  - Execute agent with input: `{"user_vision": problem, "output_directory": "...", "context": "..."}`
  - Store agent status in `active_agents` dict
  - Return agent_id and result
- Update `/api/generate-solution` endpoint to:
  - Accept POST with `{"problem": "string"}`
  - Call `spawn_executive_director()`
  - Return `{"agent_id": "...", "status": "completed", "result": {...}}`
- Handle errors gracefully with status updates

**Acceptance**:
- Backend starts without import errors
- Can spawn Executive Director agent
- Agent executes and returns results
- Status tracked in orchestrator

### 2. AgentStatusDisplay Component
**File**: `src/field/ensemble_ui/frontend/src/components/AgentStatusDisplay.jsx`

**Requirements**:
- Accept `agentStatus` prop (object with agent info)
- Display agent type, status, progress
- Show hierarchical agent spawning (parent/child relationships)
- Color-coded status badges:
  - Blue: initializing/running
  - Green: completed
  - Red: error
  - Gray: waiting
- Show iteration count if available
- Show current phase (requirements, architecture, implementation, etc.)
- Expandable sections for detailed info

**Acceptance**:
- Component renders without errors
- Shows clear, user-friendly agent status
- Updates in real-time as status changes
- Visual hierarchy is clear

### 3. AgentHierarchy Visualization
**File**: `src/field/ensemble_ui/frontend/src/components/AgentHierarchy.jsx`

**Requirements**:
- Visual tree/hierarchy of spawned agents
- Show:
  - Executive Director at top
  - Development Manager below
  - System Architect, Coordinators, TDD Coordinator branches
  - Leads and Developers as leaf nodes
- Each node shows:
  - Agent name/type
  - Status indicator (dot: green/blue/red/gray)
  - Click to expand details
- Use simple CSS tree structure or SVG

**Acceptance**:
- Clear visual hierarchy of agents
- Real-time updates as agents spawn
- Intuitive navigation
- Responsive design

### 4. Enhanced App.jsx Integration
**File**: `src/field/ensemble_ui/frontend/src/App.jsx`

**Requirements**:
- Use new AgentStatusDisplay component instead of raw JSON
- Use AgentHierarchy component to show spawning tree
- Show results in dedicated section with formatting:
  - Files created (with links)
  - Milestones completed
  - Any errors or warnings
- Better loading states with messages
- Error handling with retry button

**Acceptance**:
- Clean, professional UI
- All components integrated
- Smooth user experience
- No console errors

### 5. Test Backend Integration
**File**: `tests/test_backend_integration.py` (create)

**Requirements**:
- Test backend imports successfully
- Test AgentOrchestrator initialization
- Test `/api/generate-solution` endpoint (mock agent execution)
- Test WebSocket connection
- Test agent status retrieval

**Acceptance**:
- All tests pass
- No import errors
- API returns expected structure

## Technical Constraints
- Backend: Python 3.11+, FastAPI, python-dotenv
- Frontend: React 18, Tailwind CSS
- Use existing Ensemble agent runtime (no modifications)
- Follow TDD where practical
- Use async/await for agent execution
- Handle long-running agent tasks gracefully

## File Structure
```
src/field/ensemble_ui/
├── backend/
│   └── main.py                 # Integrate agent runtime
├── frontend/src/
│   ├── App.jsx                 # Update with new components
│   ├── components/
│   │   ├── ProblemInputForm.jsx      # ✅ Exists
│   │   ├── AgentStatusDisplay.jsx    # 🆕 Create
│   │   └── AgentHierarchy.jsx        # 🆕 Create
│   └── services/
│       └── api.js              # ✅ Already correct
├── output/                     # 🆕 Create (agent output)
└── tests/
    └── test_backend_integration.py   # 🆕 Create
```

## Success Criteria
1. User can submit problem description via UI
2. Backend spawns Executive Director agent
3. Agent execution visible in real-time
4. Agent hierarchy displays as agents spawn
5. Results shown clearly when complete
6. Errors handled gracefully
7. All tests pass
8. UI is responsive and professional

## Priority
1. Backend integration (CRITICAL - nothing works without this)
2. AgentStatusDisplay (IMPORTANT - user needs feedback)
3. Testing (IMPORTANT - verify integration works)
4. AgentHierarchy (NICE TO HAVE - improves UX)
5. Enhanced results display (NICE TO HAVE - improves UX)

## Notes
- Agent execution may take 30s-2min depending on problem
- Consider adding execution time estimates
- May need background task queue for production (FastAPI BackgroundTasks)
- WebSocket should push updates every N seconds during execution
