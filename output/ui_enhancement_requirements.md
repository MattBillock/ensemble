# Requirements: UI Enhancement - Completed Items Filtering, Improved Filtering & Badging

## Vision
The user needs improved UI capabilities to:
1. **Resume After Failure**: Ability to retry operations after API credit exhaustion and reload
2. **Completed Items Management**: Hide or show completed items at the bottom of the list to reduce clutter
3. **Enhanced Filtering**: Better filtering capabilities across panes to find specific agents/activities
4. **Improved Badging**: More informative badges across all UI panes for better status visibility

## Objectives
1. Implement session/state persistence to support resumption after interruption
2. Add completed items filtering with show/hide toggle and "show at bottom" option
3. Enhance filtering capabilities across all panes (Activity Feed, Agent States, Hierarchy)
4. Improve badge visibility and information density throughout the UI
5. Prioritize completed items management as the highest priority feature

## Scope

### In Scope

#### Priority 1: Completed Items Management (HIGHEST PRIORITY)
1. **Activity Feed Completed Items Control**
   - Toggle to hide/show completed activities
   - Option to show completed items at the bottom of the list
   - Persist user preference across sessions
   - Visual separator between active and completed items
   - Count badge showing hidden completed items

2. **Agent States Completed Items Control**
   - Toggle to hide/show completed agents in "Current Agent Tasks" pane
   - Option to move completed agents to bottom of list
   - Collapsible "Completed" section when showing at bottom
   - Count badge showing completed agents

#### Priority 2: Enhanced Filtering
3. **Activity Feed Advanced Filtering**
   - Filter by agent ID (dropdown or autocomplete)
   - Filter by activity type (started, completed, failed, output, log)
   - Text search across activity messages
   - Filter by timestamp range (last hour, today, all)
   - Combine multiple filters
   - "Clear filters" button
   - Active filter badges showing current filters

4. **Agent States Filtering**
   - Filter by status (running, completed, failed, awaiting_user_input)
   - Filter by agent tier (leadership, coordinators, developers, testers)
   - Search by agent name/ID
   - Sort options (by status, by start time, by name)

5. **Hierarchy Filtering**
   - Search/filter agent hierarchy tree
   - Highlight matching agents
   - Collapse/expand all functionality

#### Priority 3: Improved Badging
6. **Enhanced Badge Information**
   - Activity Feed: Add agent tier badges (color-coded)
   - Activity Feed: Add timestamp badges (relative time: "2m ago")
   - Agent States: Add progress percentage badges when available
   - Agent States: Add agent tier identification badges
   - Header: Add total tasks badge, failure rate percentage
   - Consistent color scheme across all badges

7. **Badge Interactivity**
   - Click badges to filter by that criterion
   - Hover tooltips for additional context
   - Badge animations for status changes (pulsing for running)

#### Priority 4: Session Persistence & Resumption
8. **State Persistence**
   - Save UI preferences to localStorage (filter states, collapsed sections, poll interval)
   - Save current task/request context
   - Backend: Persist agent execution state to allow resumption
   - Backend: Track execution checkpoints

9. **Retry/Resume Capability**
   - "Resume Last Task" button when interruption detected
   - Backend: Resume from last checkpoint after failure
   - Show resumption status in UI
   - Warn user if state cannot be resumed

### Out of Scope
- Multi-user session management
- Cloud-based state persistence (only localStorage)
- Automatic retry on API failure (manual resume only)
- Historical session replay
- Export/import of filter configurations

## User Stories

### Completed Items Management
1. As a user, I want to hide completed activities so I can focus on active work
2. As a user, I want to show completed items at the bottom so I can reference them without clutter
3. As a user, I want to see a count of hidden completed items
4. As a user, I want my completed items preference saved across sessions
5. As a user, I want to collapse/expand the completed section when viewing at bottom

### Enhanced Filtering
1. As a user, I want to filter activities by agent ID so I can trace a specific agent's work
2. As a user, I want to search activity messages so I can find specific events
3. As a user, I want to filter agents by status so I can focus on failures or running agents
4. As a user, I want to combine multiple filters to narrow down results
5. As a user, I want to clear all filters with one click

### Improved Badging
1. As a user, I want to see agent tiers in badges so I know which level is working
2. As a user, I want relative timestamps so I know how recent an activity is
3. As a user, I want to click badges to filter by that criterion
4. As a user, I want badges to show progress percentages when available
5. As a user, I want visual indicators (pulsing) for actively running agents

### Resumption
1. As a user, I want to resume after an API credit failure so I don't lose work
2. As a user, I want to see if my last task was interrupted
3. As a user, I want to manually trigger a resume of the last task
4. As a user, I want confirmation if state cannot be resumed

## Technical Constraints

### Existing System Integration
- Must integrate with existing React/Bootstrap UI framework (App.jsx)
- Must use existing FastAPI backend on port 8001
- Must not break existing WebSocket/polling infrastructure
- Current polling interval: 500ms-2000ms (configurable)

### Frontend Requirements
- Use existing dark theme (#1a1d29 background, #242836 cards)
- Use Bootstrap components (Badge, Button, Dropdown, Form, etc.)
- Use localStorage for preference persistence
- Maintain existing 3-column layout
- Support mobile/responsive design

### Backend Requirements
- Add persistence layer for agent execution state (SQLite or JSON file)
- Track execution checkpoints for resumability
- Add API endpoints for state persistence and resumption
- Maintain backward compatibility with existing endpoints

## Success Criteria
1. Users can hide/show completed items with a toggle in both Activity Feed and Agent States panes
2. Users can show completed items at bottom of lists with clear visual separation
3. Completed items preference persists across browser sessions
4. Users can filter activities by agent ID, type, and text search with combined filters
5. Users can filter agent states by status and tier
6. All panes show enhanced badges with tier, timestamp, and progress information
7. Badges are clickable to apply filters
8. Users can resume interrupted tasks after API credit reload
9. Backend persists sufficient state to resume from last checkpoint
10. UI shows clear indication of resumable tasks

## Assumptions Made
- Using localStorage for client-side state (no backend user preferences)
- Agent execution state can be serialized and persisted (JSON format)
- Checkpoints are at agent boundaries (before spawning new agent)
- Completed items are identified by status === 'completed'
- User has modern browser with localStorage support
- Resume capability is manual (user-triggered), not automatic
- Filter preferences persist but filter selections reset on page load
- Badge color scheme: leadership=purple, coordinators=blue, developers=green, testers=orange

## Technical Notes

### Existing State Management
- Uses React useState hooks (no Redux/Zustand currently)
- Polling mechanism in App.jsx with useEffect
- Agent states tracked in `agentStates` object
- Activities tracked in `activities` array

### Required New State
- `completedVisible` - boolean for completed items visibility
- `completedAtBottom` - boolean for completed items positioning
- `activityFilters` - object with agentId, type, searchText, timeRange
- `agentStateFilters` - object with status, tier, searchText
- `lastTaskContext` - object for resumption data

### Required New API Endpoints
- `POST /api/resume-task` - Resume last interrupted task
- `GET /api/task-context/{request_id}` - Get task context for resumption
- `GET /api/execution-checkpoints/{request_id}` - Get available checkpoints
- `POST /api/save-checkpoint` - Save execution checkpoint (backend internal)

### Existing API Endpoints to Leverage
- `GET /api/activities` - Current activities (add filter params)
- `GET /api/agent-states` - Current agent states (add filter params)
- `GET /api/status` - Application status

### LocalStorage Schema
```javascript
{
  "ensemble_ui_preferences": {
    "completedVisible": true,
    "completedAtBottom": true,
    "pollInterval": 1000,
    "collapsedSections": {
      "completedActivities": false,
      "completedAgents": true
    }
  },
  "ensemble_ui_last_task": {
    "requestId": "uuid",
    "timestamp": "ISO8601",
    "status": "interrupted",
    "canResume": true
  }
}
```

## UI Layout Changes

### Activity Feed Header
```
┌─────────────────────────────────────────────────────────────┐
│ Activity Feed [200 activities] [🔍 Search...] [Filters ▼]   │
│ ✓ Show Completed  ✓ Completed at Bottom                    │
│ Active Filters: [Agent: dev-001 ✕] [Type: completed ✕]     │
└─────────────────────────────────────────────────────────────┘
```

### Agent States Header
```
┌─────────────────────────────────────────────────────────────┐
│ Current Agent Tasks [5 active] [Filters ▼]                  │
│ ✓ Show Completed  Sort: [Status ▼]                         │
└─────────────────────────────────────────────────────────────┘
```

### New Header Section for Resumption
```
┌─────────────────────────────────────────────────────────────┐
│ 🟡 Last task interrupted. [📋 Resume Task]                   │
└─────────────────────────────────────────────────────────────┘
```

### Enhanced Badge Examples
- Agent activity: `[👤 Backend Dev] [🕐 2m ago] [✅ Completed]`
- Running agent: `[💼 Coordinator] [🔄 Running] [75%] ⚡`
- Failed agent: `[🔬 Tester] [❌ Failed] [Retry ↻]`

## Milestones

### Milestone 1: Completed Items Management (PRIORITY)
**Goal**: Implement hide/show and bottom positioning for completed items
- Add toggle controls to Activity Feed and Agent States headers
- Implement filtering logic to hide completed items
- Implement sorting logic to move completed items to bottom
- Add visual separator and collapsible section for bottom items
- Add count badges for hidden/completed items
- Implement localStorage persistence for preferences
- Testing: Verify toggle behavior, sorting, and persistence

### Milestone 2: Enhanced Filtering - Activity Feed
**Goal**: Advanced filtering for activity feed
- Add filter UI components (search, dropdowns, checkboxes)
- Implement filter state management
- Add filter logic for agent ID, type, text search, time range
- Add active filter badges with remove buttons
- Add "Clear all filters" button
- Testing: Verify filter combinations work correctly

### Milestone 3: Enhanced Filtering - Agent States
**Goal**: Advanced filtering for agent states pane
- Add filter UI components
- Implement filter by status and tier
- Add agent name/ID search
- Add sort options (status, time, name)
- Testing: Verify filtering and sorting

### Milestone 4: Improved Badging
**Goal**: Enhanced badges across all panes
- Add agent tier badges with color coding
- Add relative timestamp badges
- Add progress percentage badges
- Implement badge click-to-filter functionality
- Add hover tooltips for badges
- Add pulsing animation for running agents
- Testing: Verify badge appearance and interactivity

### Milestone 5: Session Persistence & Resumption
**Goal**: Enable task resumption after interruption
- Backend: Implement execution state persistence (SQLite/JSON)
- Backend: Implement checkpoint tracking at agent boundaries
- Backend: Create `/api/resume-task` endpoint
- Backend: Create `/api/task-context` and `/api/execution-checkpoints` endpoints
- Frontend: Detect interrupted task on page load
- Frontend: Add "Resume Task" UI component
- Frontend: Handle resume workflow
- Testing: Test interruption scenarios and resumption

### Milestone 6: Integration & Polish
**Goal**: Final integration and user testing
- Integrate all features into App.jsx
- Ensure consistent styling and dark theme
- Add loading states and error handling
- Performance testing with large datasets
- User acceptance testing
- Documentation updates

## Implementation Priority Order
1. **Completed Items Management** (M1) - Highest user priority
2. **Enhanced Filtering - Activity Feed** (M2)
3. **Improved Badging** (M4) - Quick wins for UX
4. **Enhanced Filtering - Agent States** (M3)
5. **Session Persistence & Resumption** (M5) - Most complex, addresses API credit issue
6. **Integration & Polish** (M6)

## Risk Assessment
- **Medium Risk**: LocalStorage size limits for large task contexts (mitigate: limit stored data)
- **Medium Risk**: Backend state serialization complexity (mitigate: checkpoint at clear boundaries)
- **Low Risk**: Filter performance with large datasets (mitigate: client-side pagination)
- **Low Risk**: UI clutter from too many filter options (mitigate: collapsible filter sections)
