# Milestone Plan: Willow UI Updates - Tabbed Activity Feed

## Project Overview
Implement two frontend UI changes to the Ensemble UI:
1. Replace dropdown filter in Activity Feed with horizontal tabbed interface
2. Change application title from "Ensemble AI" to "Willow says Hi"

## Milestone 1: Tabbed Activity Feed & Title Update (Single Milestone)

### Objective
Modernize the Activity Feed filter UI and update application branding in a single cohesive implementation.

### Deliverables
1. Updated `App.jsx` with:
   - Title changed to "🎭 Willow says Hi"
   - Dropdown filter removed from Activity Feed Card.Header
   - `activityFilter` state removed
   - Pass all activities (unfiltered) to ActivityFeed component

2. Updated `ActivityFeed.jsx` with:
   - TAB_FILTERS constant with proper type groupings
   - `activeTab` state management
   - Internal filtering logic
   - Horizontal tab UI with count badges
   - Dark theme styling consistent with existing UI

### Acceptance Criteria
- [ ] Title displays "🎭 Willow says Hi" in header
- [ ] Horizontal tabbed interface visible in Activity Feed
- [ ] Tabs: All, Running, Completed, Spawned, Failed, Other
- [ ] Each tab shows count badge
- [ ] Active tab is visually distinct
- [ ] Clicking tab filters activities correctly
- [ ] Dark theme styling consistent (#1a1d29, #242836, #3a3f52)
- [ ] No console errors
- [ ] All existing activity display functionality preserved

### Dependencies
- Existing React Bootstrap components
- Existing dark theme CSS

### Estimated Effort
Low-Medium complexity - straightforward UI changes to existing components

## Implementation Notes

### Files to Modify
1. `/src/field/ensemble_ui/frontend/src/App.jsx`
2. `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`

### TAB_FILTERS Specification
```javascript
const TAB_FILTERS = {
  all: { label: 'All', types: null },
  running: { label: 'Running', types: ['agent_started', 'iteration_started', 'tool_use_started'] },
  completed: { label: 'Completed', types: ['agent_completed', 'iteration_completed', 'tool_use_completed'] },
  spawned: { label: 'Spawned', types: ['agent_spawned'] },
  failed: { label: 'Failed', types: ['agent_failed', 'tool_use_failed'] },
  other: { label: 'Other', types: ['message', 'question', 'answer', 'task_update', 'status_change', 'file_generated', 'git_commit', 'thinking', 'output_created'] }
};
```

### Design Decision
Move filtering INTO ActivityFeed.jsx component for better encapsulation:
- ActivityFeed receives ALL activities from App.jsx
- Tab filtering logic lives entirely within ActivityFeed.jsx
- Cleaner separation of concerns
