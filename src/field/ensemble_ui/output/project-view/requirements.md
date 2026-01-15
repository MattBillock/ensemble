# Project View Dashboard Requirements

## Overview
Add a dedicated Project View to the Ensemble UI that provides comprehensive visibility into a project's status, SDLC position, milestone progress, and next steps with actionable controls.

## User Vision
"Let's add a project view, so we can see a project view, its status, its position in the SDLC, the number of milestones determined, the number completed, and next steps along with a 'continue to next step' button to force the agent system to move to implementation."

## Objectives

### Primary Goals
1. **Project Status Visibility**: Display comprehensive project status at a glance
2. **SDLC Position Tracking**: Show where the project is in the Software Development Lifecycle
3. **Milestone Progress**: Display milestone counts (total, completed, remaining)
4. **Next Steps Visibility**: Show actionable next steps for the project
5. **Manual Control**: Provide "Continue to Next Step" button to force advancement

### Success Criteria
- Users can view project status without navigating multiple screens
- SDLC phase is clearly visible (requirements → architecture → planning → implementation → testing → complete)
- Milestone progress shows as numerical count and visual progress indicator
- Next steps are clearly listed with descriptions
- "Continue to Next Step" button triggers agent system to advance implementation

## Functional Requirements

### FR-1: Project Selection
- Display list of active projects (from `/api/projects/summary` or project tracker)
- Allow selection of a specific project to view details
- Show project name, created date, and current status in list

### FR-2: Project Status Display
- Show overall project status: active, paused, completed, failed
- Display project name and description
- Show creation timestamp and last update timestamp
- Display associated request_id for tracing

### FR-3: SDLC Position Indicator
- Visual indicator showing current phase:
  - Requirements
  - Architecture
  - Planning (task breakdown)
  - Implementation
  - Testing
  - Complete
- Phase should be determined from project tracking data or Executive Director output

### FR-4: Milestone Tracking
- Display total number of milestones determined
- Show number of milestones completed
- Show number of milestones remaining/in-progress
- Visual progress bar (completed/total)
- List individual milestones with their status

### FR-5: Task Summary
- Show task counts by status (todo, in_progress, completed, blocked)
- Completion percentage
- Link to detailed task view if available

### FR-6: Next Steps Display
- List next actionable steps for the project
- Show which tasks can be started (no blocking dependencies)
- Display agent assignments for pending tasks

### FR-7: Continue to Next Step Button
- Button to trigger continuation of project execution
- When clicked:
  - Spawn a new Executive Director with context to continue
  - Pass project_id and current state
  - Include instruction to proceed to next phase/milestone
- Visual feedback during execution (loading state)
- Error handling for failed continuations

### FR-8: Agent Activity for Project
- Show currently running agents for this project
- Display recent agent activity
- Link to agent hierarchy for the project

## Technical Requirements

### Backend Integration

#### Existing Endpoints to Leverage
- `GET /api/projects/summary` - List projects with summary stats
- `GET /api/activity/hierarchy` - Agent hierarchy for project
- `GET /api/requests/{request_id}/timeline` - Timeline data
- `POST /api/generate-solution` - For continuation functionality

#### New/Enhanced Endpoints Needed
- `GET /api/projects/{project_id}/details` - Detailed project view with milestones
- `POST /api/projects/{project_id}/continue` - Trigger project continuation

### Data Sources
- Project Tracker (`~/.ensemble/projects/`) - SDLC state, milestones, notes
- Swarm State (SQLite) - Active agents, session data
- Activity Tracker - Recent activities

### Frontend Components
- New view tab "Projects" in App.jsx navigation
- ProjectView.jsx - Main component
- ProjectStatusCard.jsx - Project header with status
- SDLCIndicator.jsx - Visual SDLC phase indicator
- MilestoneProgress.jsx - Milestone tracking display
- NextStepsPanel.jsx - Actionable next steps

## UI/UX Specifications

### Visual Design
- Follow existing dark theme (backgroundColor: '#1a1d29')
- Card-based layout consistent with other views
- Use existing Badge component for status indicators
- Progress bars for milestone completion

### Layout (Desktop)
```
+--------------------------------------------------+
| [Navigation: Activity | Timeline | ... | Projects] |
+--------------------------------------------------+
| Project List (Left)  |  Project Details (Right)   |
|                      |                            |
| [Project 1]         | Project Name                |
| [Project 2] <--     | Status: Active | Phase: X   |
| [Project 3]         |                            |
|                     | SDLC Progress              |
|                     | [=====>------] Architecture |
|                     |                            |
|                     | Milestones                 |
|                     | 3/7 Complete [=====>--]    |
|                     |                            |
|                     | Next Steps                 |
|                     | • Task A (assigned: Dev)   |
|                     | • Task B (unassigned)      |
|                     |                            |
|                     | [Continue to Next Step]    |
+--------------------------------------------------+
```

## Non-Functional Requirements

### Performance
- Project list should load in < 500ms
- Project details should load in < 1s
- Continue action should show immediate feedback

### Reliability
- Handle missing/incomplete project data gracefully
- Show meaningful error states
- Recover from backend failures

### Accessibility
- Keyboard navigation for project selection
- Screen reader compatible status indicators
- Clear visual contrast for all states

## Out of Scope
- Project deletion/archival (future feature)
- Milestone editing (manual intervention)
- Budget/cost per project (exists in Cost Tracking view)
- Multi-project comparison view

## Dependencies
- Existing project_tracker.py module
- Backend main.py endpoints
- React Bootstrap UI framework
- Existing API service layer

## Assumptions
1. Project data is available in ~/.ensemble/projects/ directory
2. Executive Director agents create and maintain project state
3. SDLC phase is tracked in project notes or result status
4. Backend has access to project tracker module

## Risks
- SDLC phase may not be consistently tracked in current implementation
- Milestone data may be sparse for older projects
- "Continue" action may require careful context preservation
