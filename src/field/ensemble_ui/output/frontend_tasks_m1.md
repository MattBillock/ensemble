# Frontend Tasks - Milestone 1: Activity Feed Tabbed Interface

## Overview
Replace the dropdown filter in ActivityFeed.jsx with a horizontal tabbed interface that groups related activity types with count badges and dark theme styling.

## Tasks

### Task 1: Remove Dropdown Filter
**Description**: Remove the existing dropdown filter component from ActivityFeed.jsx
**Complexity**: Low
**Acceptance Criteria**:
- Dropdown filter completely removed
- No broken references or unused imports
**File**: `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`

### Task 2: Add Tab Filter Constants
**Description**: Define tab filter configuration with activity type groupings
**Complexity**: Low
**Acceptance Criteria**:
- TAB_FILTERS constant defined with proper structure
- All activity types from ActivityType enum covered
- Correct groupings: All, Running, Completed, Spawned, Failed, Other
**File**: `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`

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

### Task 3: Implement Tab State Management
**Description**: Add useState for active tab and filtering logic
**Complexity**: Medium
**Acceptance Criteria**:
- activeTab state initialized to 'all'
- filteredActivities computed based on activeTab
- Filter logic correctly matches activity types
**File**: `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`

### Task 4: Create Tab Component UI
**Description**: Implement horizontal tab button group with styling
**Complexity**: Medium
**Acceptance Criteria**:
- Horizontal button group below Activity Feed header
- Each tab shows label and count badge
- Active tab visually highlighted
- Dark theme styling (#1a1d29, #242836, #3a3f52)
- Tabs are clickable and update state
**File**: `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`

### Task 5: Add Count Badge Calculation
**Description**: Calculate and display activity counts per tab
**Complexity**: Medium
**Acceptance Criteria**:
- Count calculated for each tab based on activity types
- Counts update when activities change
- Badge displayed next to tab label
**File**: `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`

### Task 6: Apply Tab Styling
**Description**: Add CSS styles for tab components matching dark theme
**Complexity**: Low
**Acceptance Criteria**:
- Tabs styled with dark theme colors
- Hover states for tabs
- Active tab has distinct background
- Responsive layout
**File**: `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx` (inline styles or CSS module)

## Dependencies
- React Bootstrap (existing)
- Existing ActivityFeed component structure
- Existing dark theme CSS variables

## Implementation Order
1. Task 2 (constants) → Task 1 (remove dropdown) → Task 3 (state) → Task 4 (UI) → Task 5 (counts) → Task 6 (styling)

## Testing Notes
- Unit test tab filtering logic separately
- Verify all activity types are covered by tab filters
- Test count calculation accuracy
