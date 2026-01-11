# Ensemble UI Enhancements - Milestones Plan

## Project Overview
**Project**: ensemble_ui_enhancements
**Requirements**: ui_enhancement_requirements.md
**Duration**: 6 milestones
**Priority**: Completed items management is highest priority

## Milestone 1: Completed Items Management (PRIORITY)
**Objective**: Implement hide/show and bottom positioning for completed items in Activity Feed and Agent States panes

**Deliverables**:
- Toggle controls in Activity Feed header (show/hide completed, position at bottom)
- Toggle controls in Agent States header (show/hide completed)
- Filtering logic to hide completed items based on status
- Sorting logic to move completed items to bottom of lists
- Visual separator between active and completed sections
- Collapsible "Completed" section when showing at bottom
- Count badges showing hidden/completed item counts
- LocalStorage persistence for user preferences
- Updated App.jsx with new state management

**Acceptance Criteria**:
- User can toggle completed items visibility in both panes
- User can choose to show completed items at bottom
- Preferences persist across browser sessions
- Visual separator clearly distinguishes active from completed
- Count badges accurately reflect item counts
- No breaking changes to existing UI functionality

**Dependencies**: None (first milestone)

**Estimated Effort**: 2-3 days

---

## Milestone 2: Enhanced Filtering - Activity Feed
**Objective**: Implement advanced filtering capabilities for the Activity Feed pane

**Deliverables**:
- Filter UI components (search input, dropdowns for agent ID and type)
- Time range filter (last hour, today, all)
- Filter state management in React
- Combined filter logic (agent ID + type + text search + time range)
- Active filter badges showing current applied filters
- Remove button on each filter badge
- "Clear all filters" button
- Backend API parameter support for filtering (optional optimization)

**Acceptance Criteria**:
- User can filter by agent ID via dropdown/autocomplete
- User can filter by activity type (started, completed, failed, output, log)
- User can search text across activity messages
- User can filter by time range
- Multiple filters can be combined
- Active filters are clearly displayed as badges
- User can remove individual filters or clear all
- Filters work correctly with completed items toggle

**Dependencies**: Milestone 1 (completed items management)

**Estimated Effort**: 3-4 days

---

## Milestone 3: Enhanced Filtering - Agent States
**Objective**: Implement advanced filtering and sorting for Agent States pane

**Deliverables**:
- Filter UI components (status dropdown, tier dropdown, search input)
- Filter by status (running, completed, failed, awaiting_user_input)
- Filter by agent tier (leadership, coordinators, developers, testers)
- Search by agent name/ID
- Sort options dropdown (by status, by start time, by name)
- Sort implementation for all options
- Filter state management

**Acceptance Criteria**:
- User can filter agents by status
- User can filter agents by tier
- User can search by agent name or ID
- User can sort agents by status, start time, or name
- Filters and sorting work together correctly
- Performance is acceptable with many agents

**Dependencies**: Milestone 1, Milestone 2 (for UI consistency)

**Estimated Effort**: 2-3 days

---

## Milestone 4: Improved Badging
**Objective**: Enhance badges across all panes with more information and interactivity

**Deliverables**:
- Agent tier badges with color coding (leadership=purple, coordinators=blue, developers=green, testers=orange)
- Relative timestamp badges ("2m ago", "1h ago")
- Progress percentage badges for agents
- Badge styling consistent with dark theme
- Click-to-filter functionality on badges
- Hover tooltips for additional context
- Pulsing animation for actively running agents
- Badge utility functions and components

**Acceptance Criteria**:
- All activity items show agent tier badges
- Timestamps display in relative format
- Progress percentages shown when available
- Badges use consistent color scheme
- Clicking a badge filters by that criterion
- Tooltips provide additional context on hover
- Running agents have pulsing visual indicator
- Badges are visually appealing and readable

**Dependencies**: Milestone 2, Milestone 3 (to enable click-to-filter)

**Estimated Effort**: 2-3 days

---

## Milestone 5: Session Persistence & Resumption
**Objective**: Enable task resumption after interruption (e.g., API credit exhaustion)

**Deliverables**:
**Backend**:
- State persistence layer (SQLite or JSON file)
- Execution checkpoint tracking at agent boundaries
- `POST /api/resume-task` endpoint
- `GET /api/task-context/{request_id}` endpoint
- `GET /api/execution-checkpoints/{request_id}` endpoint
- Checkpoint save logic in agent orchestration

**Frontend**:
- Detect interrupted task on page load (check localStorage)
- "Resume Task" banner/button component
- Resume workflow (call resume API, handle response)
- Update localStorage with task context
- Show resumption status to user

**Acceptance Criteria**:
- Backend persists agent execution state to disk
- Checkpoints are saved at agent boundaries
- Frontend detects interrupted tasks on page load
- User can click "Resume Task" button
- System resumes from last checkpoint successfully
- User receives feedback on resumption status
- Error handling for non-resumable tasks
- Backward compatible with existing functionality

**Dependencies**: All previous milestones (full UI must be functional)

**Estimated Effort**: 4-5 days

---

## Milestone 6: Integration & Polish
**Objective**: Final integration, performance optimization, and user acceptance

**Deliverables**:
- Full integration of all features into App.jsx
- Consistent styling and dark theme across new components
- Loading states for all async operations
- Error handling and user feedback for all operations
- Performance optimization for large datasets
- Unit tests for new components
- Integration tests for workflows
- Updated documentation
- User guide for new features

**Acceptance Criteria**:
- All features work together seamlessly
- UI is responsive and performs well with 100+ activities/agents
- No console errors or warnings
- Consistent styling with existing UI
- All async operations have loading indicators
- Errors display helpful messages
- Documentation is complete and accurate
- User guide is clear and helpful

**Dependencies**: All previous milestones

**Estimated Effort**: 2-3 days

---

## Implementation Order & Rationale

1. **Milestone 1** (Completed Items) - Highest user priority, immediate UX win
2. **Milestone 2** (Activity Feed Filtering) - Builds on M1, addresses core filtering needs
3. **Milestone 4** (Improved Badging) - Quick UX wins, enhances information density
4. **Milestone 3** (Agent States Filtering) - Similar to M2, completes filtering suite
5. **Milestone 5** (Session Resumption) - Most complex, addresses API credit issue
6. **Milestone 6** (Integration & Polish) - Final quality pass

## Risk Mitigation

**LocalStorage Limits**: 
- Limit stored task context to essential data only
- Implement cleanup of old task contexts

**State Serialization Complexity**:
- Checkpoint only at agent boundaries (clear state)
- Use JSON serialization for simplicity

**Filter Performance**:
- Implement client-side pagination if needed
- Consider backend filtering for large datasets

**UI Clutter**:
- Use collapsible filter sections
- Progressive disclosure of advanced options

## Success Metrics

- Users can manage completed items (hide/show/bottom positioning)
- Users can filter activities and agents by multiple criteria
- Enhanced badges provide more context at a glance
- Users can resume interrupted tasks after API reload
- UI remains responsive with large datasets
- Zero regressions in existing functionality
