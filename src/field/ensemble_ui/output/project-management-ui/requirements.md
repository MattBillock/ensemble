# Project Management UI Requirements

## Vision
Add a project management page to the Ensemble UI that provides a unified view of all in-progress and completed projects, allowing users to review requirements, view execution history (task request pipeline), and initiate or resume project execution.

## Problem Statement
Currently, the Ensemble UI focuses on real-time activity monitoring but lacks:
1. A way to view and manage **projects** (stored in `~/.ensemble/projects/`)
2. The ability to **review requirements** before or after execution
3. A **project-level history view** showing the complete task request pipeline from start to finish
4. Tools to **initiate/resume execution** on projects that need user input

## Objectives
1. **Project List View**: Display all projects with status, progress, and key metadata
2. **Project Detail View**: Show comprehensive project information including requirements, tasks, notes, and execution history
3. **Requirements Review**: Allow viewing and potentially editing requirements documents
4. **Task Pipeline Visualization**: Show the hierarchy and flow of agent executions for a project
5. **Execution Control**: Enable starting new tasks or resuming paused projects

## Scope

### In Scope
- New "Projects" view accessible from the main navigation
- Project list with filtering (active, completed, paused, all)
- Project detail modal/page with:
  - Project metadata (name, description, status, dates)
  - Requirements document viewer (from output directory)
  - Task list with status tracking
  - Notes/history timeline
  - Agent execution pipeline (linked to activity tracker)
- Ability to resume projects waiting for user input
- Link between projects and their generated files

### Out of Scope
- Creating new projects (already handled by Executive Director spawning)
- Modifying project state directly (should go through agents)
- Deleting or archiving projects (future enhancement)
- Project templates

## Technical Requirements

### Backend (FastAPI)
New API endpoints needed:

1. `GET /api/projects` - List all projects
   - Query params: `status` (filter), `limit`, `offset`
   - Returns: List of project summaries

2. `GET /api/projects/{project_id}` - Get project details
   - Returns: Full project state including tasks and notes

3. `GET /api/projects/{project_id}/requirements` - Get requirements document
   - Returns: Content of requirements.md from project output directory

4. `GET /api/projects/{project_id}/pipeline` - Get execution pipeline
   - Returns: Agent hierarchy and activities linked to this project's request_id

5. `POST /api/projects/{project_id}/resume` - Resume project execution
   - Body: `{ "user_input": "string" }` (if resuming from user question)

### Frontend (React)
New components needed:

1. **ProjectsView** - Main container component (like MetricsDashboard)
   - Project list sidebar
   - Project detail panel

2. **ProjectList** - List of projects with filters
   - Status badges (active, completed, paused)
   - Progress indicators
   - Search/filter controls

3. **ProjectDetail** - Detailed project view
   - Tabs: Overview, Requirements, Tasks, History, Pipeline

4. **RequirementsViewer** - Display requirements.md with markdown rendering

5. **TaskPipeline** - Visualization of agent execution flow
   - Link to existing AgentHierarchyTree component
   - Show agent status, results, and timing

6. **ProjectHistory** - Timeline of notes and milestones

### Data Flow
1. Projects are stored in `~/.ensemble/projects/{project_id}.json`
2. Each project has:
   - `project_id`, `project_name`, `description`, `status`
   - `tasks`: Dict of task_id → task state
   - `notes`: List of timestamped notes
   - `request_id`: Links to activity tracker for execution data
   - `output_directory`: Path to generated files

3. Integration points:
   - Activity Tracker: Filter by `request_id` to get execution data
   - Generated Files: Link via `output_directory` path
   - Pending Questions: Match by project's `request_id`

## User Stories

1. **As a user**, I want to see all my projects in one place so I can track what's in progress
2. **As a user**, I want to view project requirements before starting execution to verify the AI understood my intent
3. **As a user**, I want to see the full execution pipeline showing which agents ran and what they produced
4. **As a user**, I want to resume a project that's waiting for my input
5. **As a user**, I want to see the history of decisions and milestones for a project

## UI/UX Requirements

### Navigation
- Add "Projects" button to main header navigation (alongside Activity and Metrics)
- Use same dark theme as existing UI (`#1a1d29` background, `#242836` cards)

### Project List
- Card-based layout showing:
  - Project name and status badge
  - Progress bar (tasks completed / total)
  - Created/Updated timestamps
  - Quick actions (view, resume if paused)

### Project Detail
- Full-width panel or modal
- Tabbed interface for different sections
- Collapsible sections for large content
- Syntax highlighting for requirements markdown

## Success Criteria
1. Users can view all projects and their statuses
2. Users can drill down into any project to see full details
3. Users can see the complete agent execution pipeline for a project
4. Users can resume projects that are waiting for input
5. Requirements documents are viewable with proper formatting
6. Performance: List loads in < 500ms, detail view in < 1s

## Assumptions
- Projects directory (`~/.ensemble/projects/`) is accessible to the backend
- Requirements documents follow naming convention `requirements.md`
- Activity tracker maintains data for the lifetime of recent projects
- Frontend will use polling (existing pattern) rather than WebSocket for project updates

## Dependencies
- Existing ProjectTracker (`src/runtime/agents/project_tracker.py`)
- Existing Activity Tracker API endpoints
- React Bootstrap UI components (already in use)
- Existing dark theme styling

## Implementation Notes
- Reuse existing components where possible (AgentHierarchyTree, ActivityFeed)
- Follow existing patterns for API calls (see `services/api.js`)
- Consider pagination for projects list if count grows large
- Cache project list in frontend state to reduce API calls
