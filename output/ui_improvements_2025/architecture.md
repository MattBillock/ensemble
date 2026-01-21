# UI Improvements 2025 - Architecture Design

## Context
This is an **ENHANCEMENT** to the existing Ensemble UI at `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/`. The existing application is a React + FastAPI web application with:
- Frontend: React 18 at `frontend/src/`
- Backend: FastAPI at `backend/`
- Current polling-based updates (1-2 second intervals)
- Existing components: AgentHierarchyTree, activity feed, etc.

## Enhancement Overview
Two focused improvements:
1. **Project-based agent grouping** in hierarchy view
2. **Status summary bar** with stage indicators

## A) Architecture Pattern
**Enhancement Pattern**: Incremental feature addition with minimal disruption
- Extend existing data models (backward compatible)
- Add new UI components alongside existing ones
- Leverage existing polling mechanism
- No breaking changes to API contracts

## B) Technology Stack (Existing + Enhancements)

### Frontend (No Changes to Stack)
- **Framework**: React 18 (existing)
- **UI Library**: React Bootstrap (existing)
- **State Management**: React hooks (useState, useEffect)
- **Real-time Updates**: Polling (existing 1-2 second intervals)

### Backend (No Changes to Stack)
- **Framework**: FastAPI (existing)
- **Language**: Python 3.11+ (existing)
- **Response Format**: JSON (existing)

### New Dependencies (Minimal)
- Frontend: None required (use existing React Bootstrap icons/badges)
- Backend: None required (extend existing models)

## C) System Components

### Backend Enhancements

#### 1. Enhanced Activity Tracker (`backend/activity_tracker.py` or similar)
**Purpose**: Track project_id and current_stage for each agent execution

**Changes**:
- Add `project_id` field to activity records
  - Format: UUID or timestamp-based identifier
  - Generated at submission time
- Add `current_stage` field to activity records
  - Values: "requirements", "architecture", "planning", "implementation", "testing", "complete"
  - Updated by agents as they progress

**Data Model Extension**:
```python
# Existing model + new fields
{
  "agent_id": "string",
  "agent_type": "string", 
  "status": "string",
  "parent_id": "string",
  # NEW FIELDS:
  "project_id": "string",  # Group identifier
  "current_stage": "string",  # Process stage
  "project_name": "string"  # Optional display name
}
```

#### 2. Enhanced API Endpoints

**Existing Endpoint Enhancement**: `GET /api/activity`
- **Backward Compatible**: Add new fields to existing response
- **Response Enhancement**:
```json
{
  "agents": [
    {
      "agent_id": "...",
      "agent_type": "...",
      "status": "...",
      "project_id": "abc123",  // NEW
      "current_stage": "implementation",  // NEW
      "project_name": "UI Improvements"  // NEW (optional)
    }
  ]
}
```

**Optional New Endpoint**: `GET /api/projects/summary`
- Returns aggregated project statistics
- Response:
```json
{
  "projects": [
    {
      "project_id": "abc123",
      "project_name": "UI Improvements",
      "agent_count": 5,
      "active_agents": 2,
      "current_stage": "implementation",
      "status": "running"
    }
  ]
}
```

### Frontend Enhancements

#### 1. Modified Component: `AgentHierarchyTree`
**Location**: `frontend/src/components/AgentHierarchyTree.jsx` (or similar)

**Changes**:
- Add project grouping logic
- Group agents by `project_id` before rendering hierarchy
- Add project-level header components
- Add expand/collapse state per project
- Maintain existing hierarchy structure within each project

**Component Structure**:
```
AgentHierarchyTree
├─ ProjectGroup (NEW wrapper)
│  ├─ ProjectHeader (NEW)
│  │  ├─ Project name/ID
│  │  ├─ Summary badges (agent count, status)
│  │  └─ Expand/collapse toggle
│  └─ AgentNode (EXISTING - nested under project)
│     └─ Child AgentNodes...
```

**Logic**:
```javascript
// Pseudo-code
function groupAgentsByProject(agents) {
  return agents.reduce((groups, agent) => {
    const projectId = agent.project_id || 'default';
    if (!groups[projectId]) {
      groups[projectId] = [];
    }
    groups[projectId].push(agent);
    return groups;
  }, {});
}
```

#### 2. New Component: `StatusSummaryBar`
**Location**: `frontend/src/components/StatusSummaryBar.jsx` (new file)

**Purpose**: Display system-wide status summary at top of UI

**Features**:
- Show active project count
- Show current stages being worked on
- Show agent counts by status (running, completed, failed)
- Color-coded health indicators
- Real-time updates via polling

**Data Structure**:
```javascript
{
  activeProjects: 3,
  stages: {
    requirements: 0,
    architecture: 1,
    planning: 0,
    implementation: 2,
    testing: 1,
    complete: 0
  },
  agents: {
    running: 8,
    completed: 15,
    failed: 1
  }
}
```

**Visual Layout**:
```
+----------------------------------------------------------------+
| 🎯 3 Active Projects | 🏗️ Architecture (1) | 💻 Implementation (2) | 🧪 Testing (1) |
| ✅ 15 Complete | ⏳ 8 Running | ❌ 1 Failed |
+----------------------------------------------------------------+
```

#### 3. Enhanced Component: Badge System
**Location**: Throughout existing components

**Changes**:
- Add stage-specific badges with icons
- Stage icon mapping:
  - 📋 Requirements
  - 🏗️ Architecture
  - 📝 Planning
  - 💻 Implementation
  - 🧪 Testing
  - ✅ Complete
- Color variants for each stage
- Consistent styling across all components

**Implementation**:
```javascript
// Stage badge component
function StageBadge({ stage }) {
  const stageConfig = {
    requirements: { icon: '📋', variant: 'primary' },
    architecture: { icon: '🏗️', variant: 'info' },
    planning: { icon: '📝', variant: 'secondary' },
    implementation: { icon: '💻', variant: 'warning' },
    testing: { icon: '🧪', variant: 'success' },
    complete: { icon: '✅', variant: 'success' }
  };
  
  const config = stageConfig[stage] || { icon: '❓', variant: 'light' };
  return <Badge variant={config.variant}>{config.icon} {stage}</Badge>;
}
```

## D) File/Directory Structure

### New/Modified Files

```
ensemble_ui/
├── backend/
│   ├── activity_tracker.py (MODIFIED - add project_id, stage tracking)
│   ├── api_routes.py (MODIFIED - enhance endpoints)
│   └── models.py (MODIFIED - add new fields to schemas)
│
├── frontend/src/
│   ├── components/
│   │   ├── AgentHierarchyTree.jsx (MODIFIED - add project grouping)
│   │   ├── StatusSummaryBar.jsx (NEW - summary bar component)
│   │   ├── ProjectGroup.jsx (NEW - project wrapper component)
│   │   ├── ProjectHeader.jsx (NEW - project header with stats)
│   │   └── StageBadge.jsx (NEW - stage indicator badge)
│   │
│   ├── hooks/
│   │   └── useProjectGrouping.js (NEW - project grouping logic)
│   │
│   └── utils/
│       └── stageHelpers.js (NEW - stage utilities and mappings)
│
└── output/ui_improvements_2025/
    ├── requirements.md (existing)
    ├── milestones.md (existing)
    └── architecture.md (this file)
```

## E) Data Flow

### Submission Flow (Enhanced)
```
1. User submits problem via form
2. Backend generates project_id (UUID)
3. Executive Director agent spawned with project_id
4. All child agents inherit project_id
5. Agents update current_stage as they progress
6. Activity tracker maintains project_id and stage
```

### Display Flow (Enhanced)
```
1. Frontend polls /api/activity (existing mechanism)
2. Response includes project_id and current_stage (NEW)
3. Frontend groups agents by project_id
4. StatusSummaryBar aggregates stats across projects
5. AgentHierarchyTree renders project groups
6. Badges display current_stage for each agent
7. Repeat polling every 1-2 seconds (existing)
```

## F) API Contract (Backward Compatible)

### Enhanced GET /api/activity
**Request**: No changes
**Response**: Extended fields (backward compatible)
```json
{
  "agents": [
    {
      // Existing fields
      "agent_id": "ed-001",
      "agent_type": "executive_director",
      "status": "running",
      "parent_id": null,
      "children": ["dev-001"],
      
      // NEW fields (optional for backward compatibility)
      "project_id": "proj-abc123",
      "current_stage": "implementation",
      "project_name": "UI Improvements"
    }
  ]
}
```

### Optional GET /api/projects/summary
**Request**: None
**Response**: 
```json
{
  "projects": [
    {
      "project_id": "proj-abc123",
      "project_name": "UI Improvements",
      "total_agents": 10,
      "active_agents": 3,
      "completed_agents": 6,
      "failed_agents": 1,
      "current_stage": "implementation",
      "status": "running",
      "started_at": "2025-01-11T10:00:00Z"
    }
  ],
  "summary": {
    "total_projects": 1,
    "active_projects": 1,
    "total_agents": 10
  }
}
```

## G) State Management

### Frontend State
**Existing State** (no changes):
- Agent list from polling
- Hierarchy expand/collapse state

**New State**:
- Project expand/collapse state (per project)
- Project grouping cache (computed from agent list)
- Status summary cache (computed from agent list)

**Implementation**:
```javascript
// Project grouping state
const [projectGroups, setProjectGroups] = useState({});
const [expandedProjects, setExpandedProjects] = useState(new Set());

// Compute project groups from agents
useEffect(() => {
  const groups = groupAgentsByProject(agents);
  setProjectGroups(groups);
}, [agents]);
```

### Backend State
**Existing State** (no changes):
- Agent execution tracking
- Activity history

**New State**:
- Project ID generation and tracking
- Stage progression tracking per agent

## H) Testing Strategy

### Backend Tests
1. **Unit Tests**: 
   - project_id generation
   - Stage tracking updates
   - API response format validation
   
2. **Integration Tests**:
   - Multiple projects running concurrently
   - Stage progression through workflow
   - Backward compatibility with old clients

### Frontend Tests
1. **Unit Tests**:
   - Project grouping logic
   - Status summary calculations
   - Stage badge rendering
   
2. **Integration Tests**:
   - Project expand/collapse
   - Real-time updates with multiple projects
   - Activity feed filtering by project

3. **Visual Tests**:
   - StatusSummaryBar rendering
   - Project headers with various states
   - Stage badges across all stages

### Performance Tests
- UI responsiveness with 10+ concurrent projects
- Memory usage during long-running sessions
- Polling performance with large agent counts

## I) Migration Strategy

### Phase 1: Backend Enhancement
1. Add project_id and current_stage fields to models
2. Update activity tracker to generate/track project_id
3. Enhance API responses (backward compatible)
4. Deploy backend changes
5. **Verification**: Old frontend still works

### Phase 2: Frontend Enhancement
1. Add StatusSummaryBar component
2. Modify AgentHierarchyTree for project grouping
3. Add stage badges throughout UI
4. Deploy frontend changes
5. **Verification**: New features work with enhanced backend

### Phase 3: Testing & Polish
1. Comprehensive testing with multiple projects
2. Performance optimization if needed
3. Documentation updates
4. User acceptance testing

## J) Risks and Mitigations

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Backward compatible API changes
- Extensive regression testing
- Feature flags for gradual rollout

### Risk 2: Performance Degradation
**Mitigation**:
- Efficient grouping algorithms (O(n) complexity)
- Memoization of computed values
- Performance testing with 10+ projects

### Risk 3: State Management Complexity
**Mitigation**:
- Keep state changes minimal
- Leverage existing patterns
- Clear separation of concerns

### Risk 4: UI Clutter with Many Projects
**Mitigation**:
- Collapsible project groups
- Clear visual hierarchy
- Optional project filtering/search (future)

## K) Open Questions (None - Decisions Made)

All technical decisions made based on:
- Existing architecture patterns
- Requirement constraints (polling, React Bootstrap)
- Best practices for React state management
- Minimal disruption approach

## L) Success Criteria

### Technical Success
- ✅ All existing tests pass
- ✅ New features covered by tests
- ✅ API backward compatible
- ✅ No performance regression
- ✅ Clean code following existing patterns

### Functional Success
- ✅ Agents grouped by project in hierarchy
- ✅ Project-level statistics visible
- ✅ Status summary bar shows current stages
- ✅ Stage badges throughout UI
- ✅ Real-time updates continue to work
- ✅ Multi-project workflows clearly separated

## M) Next Steps
1. Review architecture with Development Manager
2. Break down into tasks by Backend/Frontend/Test Coordinators
3. Implement Milestone 1 (Backend) via TDD Coordinator
4. Iterate through remaining milestones
5. Deploy and validate
