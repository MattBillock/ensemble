# Project View Dashboard - Architecture Document

## Overview
This document describes the architecture for adding a Project View to the Ensemble UI that displays project status, SDLC position, milestones, next steps, and provides a "Continue to Next Step" action button.

## Architecture Goals
1. **Integration**: Seamlessly integrate with existing UI patterns and backend infrastructure
2. **Reusability**: Leverage existing project_tracker.py module for data
3. **Consistency**: Follow established patterns in App.jsx and existing components
4. **Performance**: Meet performance targets (<500ms list, <1s details)

## System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ensemble UI                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     React Frontend                         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────────┐ │  │
│  │  │Activity │ │Timeline │ │ Metrics │ │  ProjectView     │ │  │
│  │  │  View   │ │  View   │ │   View  │ │    (NEW)         │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────────────┘ │  │
│  └────────────────────────────┬──────────────────────────────┘  │
│                               │ HTTP/REST                        │
│  ┌────────────────────────────┴──────────────────────────────┐  │
│  │                    FastAPI Backend                         │  │
│  │  ┌────────────────┐  ┌─────────────────┐                  │  │
│  │  │ Existing APIs  │  │ New Project APIs │                 │  │
│  │  │ /api/projects/ │  │ /api/projects/   │                 │  │
│  │  │    summary     │  │ {id}/details     │                 │  │
│  │  └────────────────┘  │ {id}/continue    │                 │  │
│  │                      └─────────────────┘                  │  │
│  └────────────────────────────┬──────────────────────────────┘  │
│                               │                                  │
│  ┌────────────────────────────┴──────────────────────────────┐  │
│  │               Data Layer                                   │  │
│  │  ┌──────────────────┐  ┌───────────────────────┐          │  │
│  │  │  project_tracker │  │  swarm_state (SQLite) │          │  │
│  │  │  (~/.ensemble/   │  │                       │          │  │
│  │  │    projects/)    │  │                       │          │  │
│  │  └──────────────────┘  └───────────────────────┘          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Backend Architecture

### New API Endpoints

#### GET `/api/projects/{project_id}/details`
Returns comprehensive project details for the view.

**Response Schema**:
```json
{
  "project_id": "string",
  "project_name": "string",
  "description": "string",
  "status": "active|paused|completed|failed",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime",
  "sdlc_phase": "requirements|architecture|planning|implementation|testing|complete|unknown",
  "milestones": {
    "total": 0,
    "completed": 0,
    "in_progress": 0,
    "items": [
      {
        "id": "string",
        "name": "string",
        "status": "todo|in_progress|completed",
        "tasks_total": 0,
        "tasks_completed": 0
      }
    ]
  },
  "tasks": {
    "total": 0,
    "todo": 0,
    "in_progress": 0,
    "completed": 0,
    "blocked": 0
  },
  "next_steps": [
    {
      "task_id": "string",
      "description": "string",
      "assigned_to": "string|null"
    }
  ],
  "recent_notes": [
    {
      "timestamp": "ISO datetime",
      "author": "string",
      "note": "string",
      "category": "string"
    }
  ],
  "request_id": "string|null"
}
```

#### POST `/api/projects/{project_id}/continue`
Triggers continuation of project execution.

**Request Body**:
```json
{
  "instruction": "string (optional - specific instruction for next step)"
}
```

**Response Schema**:
```json
{
  "success": true,
  "request_id": "string",
  "message": "string"
}
```

**Implementation Notes**:
- Creates a new Executive Director agent
- Passes project_id and context
- Sets auto_continue=true for seamless progression

### SDLC Phase Detection Logic

The SDLC phase will be determined by analyzing project notes in this priority order:

1. **Explicit Phase Notes**: Look for notes with category "milestone" containing phase keywords
2. **Task Analysis**: Analyze task descriptions for phase-related keywords
3. **Default**: Return "unknown" if phase cannot be determined

**Phase Keywords**:
- `requirements`: "requirements", "user story", "user vision"
- `architecture`: "architecture", "system design", "technical design"
- `planning`: "planning", "task breakdown", "milestone"
- `implementation`: "implementation", "coding", "development", "TDD"
- `testing`: "testing", "test", "QA", "validation"
- `complete`: "complete", "done", "delivered"

### Data Integration

**ProjectTracker Integration**:
```python
from src.runtime.agents.project_tracker import ProjectTracker

tracker = ProjectTracker()  # Uses ~/.ensemble/projects/

# Get project details
project = tracker.get_project(project_id)
summary = tracker.get_project_summary(project_id)
next_tasks = tracker.get_next_tasks(project_id)
```

## Frontend Architecture

### Component Hierarchy

```
App.jsx
└── ProjectView.jsx (new main component)
    ├── ProjectList (left panel)
    │   └── ProjectListItem (for each project)
    ├── ProjectDetails (right panel)
    │   ├── ProjectStatusCard.jsx
    │   │   └── Status badge, name, timestamps
    │   ├── SDLCIndicator.jsx
    │   │   └── Visual phase progress bar
    │   ├── MilestoneProgress.jsx
    │   │   └── Progress bar, milestone list
    │   ├── TaskSummary (inline)
    │   │   └── Task counts by status
    │   ├── NextStepsPanel.jsx
    │   │   └── Actionable next tasks
    │   └── ContinueButton
    │       └── "Continue to Next Step" action
```

### State Management

Following existing App.jsx patterns, use React useState hooks:

```javascript
// ProjectView.jsx state
const [projects, setProjects] = useState([]);           // List of projects
const [selectedProject, setSelectedProject] = useState(null);  // Currently selected
const [projectDetails, setProjectDetails] = useState(null);    // Detailed view data
const [isLoading, setIsLoading] = useState(false);
const [isContinuing, setIsContinuing] = useState(false);       // Continue button state
const [error, setError] = useState(null);
```

### API Service Functions

Add to `api.js`:

```javascript
// Get list of tracked projects
export const getTrackedProjects = async () => {
  const response = await fetch(`${API_BASE}/projects/tracked`);
  return response.json();
};

// Get detailed project view
export const getProjectDetails = async (projectId) => {
  const response = await fetch(`${API_BASE}/projects/${projectId}/details`);
  return response.json();
};

// Trigger project continuation
export const continueProject = async (projectId, instruction = null) => {
  const response = await fetch(`${API_BASE}/projects/${projectId}/continue`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instruction })
  });
  return response.json();
};
```

### UI Styling

Following existing dark theme patterns:
```javascript
const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#1a1d29'
  },
  card: {
    backgroundColor: '#242836',
    border: '1px solid #3a3f52',
    borderRadius: '4px'
  },
  text: {
    color: '#e4e6eb'
  },
  muted: {
    color: '#9ca3af'
  }
};
```

## Component Specifications

### ProjectView.jsx
**Purpose**: Main container component managing project list and details display
**Props**: None (top-level view component)
**State**: projects, selectedProject, projectDetails, isLoading, error
**Polling**: Optional auto-refresh every 5 seconds when project is selected

### ProjectStatusCard.jsx
**Purpose**: Display project header information
**Props**: 
- `project`: { name, status, created_at, updated_at, request_id }
**Renders**: Name, status badge, timestamps

### SDLCIndicator.jsx
**Purpose**: Visual SDLC phase progress indicator
**Props**:
- `currentPhase`: string (one of the SDLC phases)
**Renders**: Horizontal progress indicator with phase labels

### MilestoneProgress.jsx
**Purpose**: Display milestone tracking information
**Props**:
- `milestones`: { total, completed, in_progress, items }
**Renders**: Progress bar, numerical stats, optional milestone list

### NextStepsPanel.jsx
**Purpose**: Show actionable next steps
**Props**:
- `nextSteps`: Array of { task_id, description, assigned_to }
- `onContinue`: Function to trigger continue action
- `isContinuing`: Boolean loading state
**Renders**: List of next steps, Continue button

## Data Flow

```
1. User navigates to "Projects" tab
2. ProjectView fetches project list via getTrackedProjects()
3. User selects a project from list
4. ProjectView fetches details via getProjectDetails(projectId)
5. Components render with project data
6. User clicks "Continue to Next Step"
7. ProjectView calls continueProject(projectId)
8. Backend spawns Executive Director
9. UI shows success/error feedback
```

## Error Handling

### Backend
- Return 404 for unknown project_id
- Return 500 with error details for internal failures
- Handle missing project_tracker gracefully

### Frontend
- Show loading spinners during API calls
- Display error alerts for failed requests
- Handle empty/null states gracefully
- Confirmation dialog before continue action

## Security Considerations
- No authentication required (matches existing endpoints)
- Input validation on project_id (UUID format)
- Rate limiting on continue endpoint (prevent spam)

## Testing Strategy

### Backend Tests
- Unit tests for SDLC phase detection logic
- Integration tests for new endpoints
- Mock project_tracker for isolated testing

### Frontend Tests
- Component rendering tests with mock data
- User interaction tests (selection, continue button)
- Error state rendering tests

## File Locations

### Backend Files
- `/src/field/ensemble_ui/backend/main.py` - Add new endpoints

### Frontend Files
- `/src/field/ensemble_ui/frontend/src/App.jsx` - Add Projects tab
- `/src/field/ensemble_ui/frontend/src/components/ProjectView.jsx` - New
- `/src/field/ensemble_ui/frontend/src/components/ProjectStatusCard.jsx` - New
- `/src/field/ensemble_ui/frontend/src/components/SDLCIndicator.jsx` - New
- `/src/field/ensemble_ui/frontend/src/components/MilestoneProgress.jsx` - New
- `/src/field/ensemble_ui/frontend/src/components/NextStepsPanel.jsx` - New
- `/src/field/ensemble_ui/frontend/src/services/api.js` - Add functions

### Test Files
- `/src/field/ensemble_ui/backend/tests/test_project_endpoints.py` - New
- `/src/field/ensemble_ui/frontend/src/components/__tests__/ProjectView.test.jsx` - New
