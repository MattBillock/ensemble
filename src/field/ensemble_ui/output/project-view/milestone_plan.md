# Project View Dashboard - Milestone Plan

## Project Overview
**Project Name**: Project View Dashboard
**Description**: Add a dedicated Project View to the Ensemble UI that displays project status, SDLC position, milestone progress, next steps, and includes a "Continue to Next Step" button to advance implementation.

## Milestones

### Milestone 1: Backend API Enhancement
**Objective**: Create and enhance backend endpoints to support project view functionality

**Deliverables**:
1. Enhanced `/api/projects/{project_id}/details` endpoint for detailed project view
2. New `/api/projects/{project_id}/continue` endpoint to trigger project continuation
3. SDLC phase determination logic from project notes/status
4. Integration with existing project_tracker.py module

**Acceptance Criteria**:
- GET `/api/projects/{project_id}/details` returns complete project state including SDLC phase, milestones, tasks
- POST `/api/projects/{project_id}/continue` triggers a new Executive Director with appropriate context
- API handles missing/incomplete project data gracefully
- Endpoints respond within specified performance thresholds (<500ms for list, <1s for details)

**Dependencies**: None (uses existing project_tracker.py)

---

### Milestone 2: Frontend Project View Components
**Objective**: Build React components for the Project View dashboard

**Deliverables**:
1. ProjectView.jsx - Main container component with project list and details pane
2. ProjectStatusCard.jsx - Project header showing name, status, timestamps
3. SDLCIndicator.jsx - Visual SDLC phase progress indicator
4. MilestoneProgress.jsx - Milestone tracking with progress bar
5. NextStepsPanel.jsx - Actionable next steps display
6. Integration with App.jsx navigation (new "Projects" tab)
7. API service integration (api.js updates)

**Acceptance Criteria**:
- Project list displays all projects with status badges
- Selected project shows detailed view with all required information
- SDLC indicator clearly shows current phase
- Milestone progress displays numerical counts and visual progress bar
- "Continue to Next Step" button triggers backend continuation endpoint
- UI follows existing dark theme and Bootstrap patterns
- Loading and error states handled appropriately

**Dependencies**: Milestone 1 (backend endpoints must be available)

---

### Milestone 3: Testing and Polish
**Objective**: Comprehensive testing and UI refinement

**Deliverables**:
1. Backend unit tests for new endpoints
2. Frontend component tests (Jest/React Testing Library)
3. Integration testing for continue functionality
4. Error handling refinement
5. Loading state animations
6. Documentation

**Acceptance Criteria**:
- All new backend endpoints have unit test coverage
- Frontend components render correctly in tests
- Continue functionality works end-to-end
- Error states display user-friendly messages
- Documentation updated for new endpoints

**Dependencies**: Milestones 1 and 2

---

## Technical Decisions Made

### Architecture Decisions
1. **SDLC Phase Tracking**: Will infer SDLC phase from project notes by scanning for phase-related keywords (requirements, architecture, planning, implementation, testing). This is pragmatic given current data.

2. **Milestone Data Source**: Will use project tracker tasks and notes to infer milestones. Tasks tagged as milestones or notes with category "milestone" will be used.

3. **Continue Functionality**: Will spawn a new Executive Director agent with the project context, instructing it to continue to the next phase/milestone.

4. **Component Structure**: Single ProjectView.jsx as main container with sub-components for modularity, following existing patterns like SelfImprovementDashboard.

### Technical Stack (Following Existing Patterns)
- Backend: FastAPI (Python) with existing project_tracker integration
- Frontend: React with Bootstrap components
- State: Local React state (following App.jsx pattern)
- Styling: Inline styles with existing dark theme colors

## Risk Mitigation
1. **SDLC Phase Detection**: If project notes don't contain phase information, default to "unknown" with graceful UI handling
2. **Milestone Data**: If no milestone data exists, show "No milestones defined" rather than empty state
3. **Continue Action**: Include confirmation dialog and proper error handling for failed continuation attempts

## Estimated Scope
- **Milestone 1**: ~200-300 lines backend code
- **Milestone 2**: ~500-700 lines frontend code (5 components + api changes)
- **Milestone 3**: ~200-300 lines test code + documentation
