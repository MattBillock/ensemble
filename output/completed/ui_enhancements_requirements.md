# Ensemble UI Enhancement - Requirements

## Vision
Enhance the existing Ensemble UI with several user experience improvements to better track agent hierarchies, manage completed items, and provide better visibility into system metrics and code changes.

## Project Name
ensemble-ui-enhancements

## Objectives
1. Add question linking from agent hierarchy to original spawning question
2. Implement completed items section with collapsible/hideable functionality
3. Add two-word subject summaries to differentiate agent hierarchies at a glance
4. Improve layout: enlarge problem description section, make activity feed narrower
5. Make current agent tasks and activity feed collapsible
6. Add new metrics pane showing current models in use and code deltas

## Scope

### In Scope
**Feature 1: Agent Hierarchy Question Links**
- Add links in the AgentHierarchyTree component to the question that spawned each hierarchy
- Ensure links scroll or navigate to the relevant question in the UI
- Visual indication that hierarchy is linked to a question

**Feature 2: Completed Items Management**
- Create a "Completed" section for finished tasks/agents
- Make the completed section collapsible or hideable (either approach acceptable)
- Move completed items from active view to completed section automatically
- Maintain ability to view completed item details when needed

**Feature 3: Agent Hierarchy Differentiation**
- Generate two-word subject summaries for each agent hierarchy
- Display summary prominently in hierarchy view
- Summaries should be derived from task/problem description
- Make hierarchies easily distinguishable at a glance

**Feature 4: Layout Improvements**
- Enlarge problem description textarea (more height and width)
- Reduce width of activity feed column
- Redistribute space: more to problem input, less to activity feed
- Maintain responsive design principles

**Feature 5: Collapsible Sections**
- Make "Current Agent Tasks" pane collapsible
- Make "Activity Feed" pane collapsible
- Preserve collapse state during updates
- Add clear visual indicators for collapsed/expanded state

**Feature 6: Metrics Pane**
- New pane showing current models in use (Haiku, Sonnet, Opus counts)
- Display code delta metrics (lines added/removed, files changed)
- Real-time updates matching existing polling mechanism
- Clean, readable presentation of metrics

### Out of Scope
- Backend API changes (unless absolutely necessary for metrics)
- Authentication or user management
- Historical metrics or charting
- Export functionality for metrics
- Custom theme or color scheme changes beyond necessary UI adjustments

## Technical Constraints
- Must maintain existing React + Bootstrap UI framework
- Must work with existing API endpoints in `/services/api.js`
- Must maintain current polling mechanism (configurable intervals)
- No breaking changes to existing functionality
- Responsive design must be preserved

## Current Architecture Context
- **Frontend**: React with React-Bootstrap components
- **State Management**: Local React state with hooks
- **API Communication**: REST API via services/api.js
- **Polling**: 500ms-2s configurable intervals
- **Layout**: 3-column Bootstrap grid (currently 3-5-4 split)

## Detailed Requirements

### 1. Agent Hierarchy Question Links
- Add `question_id` or reference tracking to hierarchy data
- Implement clickable links in AgentHierarchyTree component
- Link should scroll to or highlight associated question
- Visual connection (icon, color coding) between hierarchy and question

### 2. Completed Items Section
- Filter agents/tasks by status === 'completed'
- Create separate collapsible section below active items
- Add "Show/Hide Completed" toggle button or collapse icon
- Maintain count badge showing number of completed items
- Default state: collapsed/hidden to reduce clutter

### 3. Two-Word Subject Summaries
- Generate from problem description or task name
- Algorithm: extract key nouns/verbs, create 2-word summary
- Examples: "UI Enhancement", "API Integration", "Bug Fix"
- Display next to hierarchy title or as subtitle
- Make it prominent for quick scanning

### 4. Layout Adjustments
**Current**: Col md={3} | md={5} | md={4}
**Proposed**: Col md={4} | md={4} | md={4} (or 4-3-5)
- Problem description textarea: increase rows from 4 to 6-8
- Make problem description card wider within its column
- Activity feed column should be narrower
- Ensure all content remains accessible and readable

### 5. Collapsible Sections Implementation
- Use Bootstrap Collapse component or custom implementation
- Add chevron icons to indicate expand/collapse state
- Store collapse state in component state (preserve during re-renders)
- Smooth transitions when collapsing/expanding
- Sections affected:
  - Current Agent Tasks card
  - Activity Feed card

### 6. Metrics Pane
**New section showing:**
- **Models in Use**:
  - Count of agents using Haiku
  - Count of agents using Sonnet
  - Count of agents using Opus
- **Code Delta Metrics**:
  - Total lines added (if available from API)
  - Total lines removed (if available from API)
  - Files changed count
  - Last updated timestamp
  
**Implementation**:
- Add new API endpoint or extend existing status endpoint
- Poll at same interval as other data
- Display in card format (similar to existing cards)
- Consider placement: below current tasks or as separate column section

## Success Criteria
1. **Question Links**: Click on hierarchy item navigates/scrolls to associated question
2. **Completed Section**: Completed items move to separate collapsible section automatically
3. **Summaries**: Each hierarchy displays clear 2-word summary
4. **Layout**: Problem description is noticeably larger, activity feed narrower but still functional
5. **Collapsible**: Both Current Tasks and Activity Feed can be collapsed/expanded smoothly
6. **Metrics**: New pane displays real-time model usage and code metrics
7. **No Regressions**: All existing functionality continues to work
8. **Performance**: UI remains responsive with no noticeable lag
9. **Tests**: New components have unit tests, existing tests still pass

## Implementation Assumptions
- **Backend Support**: Assume backend can provide necessary data (question IDs, metrics)
  - If metrics not available from backend, display mock/placeholder with note
- **Summary Generation**: Frontend-based text processing acceptable for subject summaries
- **Persistence**: Collapse states don't need to persist across page reloads
- **Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge - latest versions)

## API Endpoint Assumptions
Assume these are available or can be added:
- Existing endpoints already provide sufficient data for features 1-5
- May need new endpoint for metrics: `GET /api/metrics` returning:
  ```json
  {
    "models": {
      "haiku": 5,
      "sonnet": 3,
      "opus": 1
    },
    "code_delta": {
      "lines_added": 245,
      "lines_removed": 89,
      "files_changed": 12
    },
    "last_updated": "2024-01-11T02:56:00Z"
  }
  ```

## Deliverables
1. Updated React components:
   - AgentHierarchyTree.jsx (with question links)
   - App.jsx (layout changes, collapsible sections)
   - New MetricsPane.jsx component
   - Updated/new components for completed items management
2. Updated CSS/styling for layout changes
3. Unit tests for new components and modified functionality
4. Updated API service layer if new endpoints needed
5. README updates documenting new features

## Future Considerations (Not in Current Scope)
- Persistent collapse state in localStorage
- Historical metrics charting
- Customizable column layouts
- Export metrics to CSV/JSON
- Advanced filtering for completed items
- Search functionality in hierarchies
