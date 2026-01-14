# Requirements: Willow UI Updates - Tabbed Activity Feed

## Overview
Implement approved changes from `frontend_tasks_m1.md` to enhance the Ensemble UI activity feed interface and update the application title.

## User Approval
User has explicitly approved the content of `frontend_tasks_m1.md` for implementation.

## Change Requests

### 1. Title Change
**File**: `/src/field/ensemble_ui/frontend/src/App.jsx`
**Change**: Update the application title from `🎭 Ensemble AI` to `🎭 Willow says Hi`
**Location**: Header section, line ~134 (the h4 element)

### 2. Activity Feed Tabbed Interface
**File**: `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`

#### 2.1 Remove Dropdown Filter
- The dropdown filter is actually in App.jsx (Form.Select with activityFilter state)
- Remove the dropdown from the Activity Feed Card.Header in App.jsx
- Remove the `activityFilter` state variable and related filtering logic from App.jsx

#### 2.2 Add Tab Filter Constants to ActivityFeed.jsx
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

#### 2.3 Tab State Management
- Add `activeTab` state initialized to 'all'
- Filter activities based on activeTab selection
- Pass all activities to ActivityFeed (not pre-filtered)

#### 2.4 Tab Component UI
- Horizontal button group below Activity Feed header
- Each tab shows label and count badge
- Active tab visually highlighted
- Dark theme styling (#1a1d29, #242836, #3a3f52)

#### 2.5 Count Badge Calculation
- Calculate count for each tab based on activity types
- Counts update when activities change
- Badge displayed next to tab label

#### 2.6 Tab Styling
- Dark theme colors matching existing UI
- Hover states for tabs
- Active tab has distinct background
- Responsive layout

## Technical Notes

### Current State Analysis
- ActivityFeed.jsx is a pure component that receives `activities` prop
- The dropdown filter currently exists in App.jsx (lines ~280-297)
- App.jsx handles the `activityFilter` state and `filteredActivities` computation
- ActivityFeed.jsx does not currently have any filtering logic

### Implementation Approach
**Option A (Recommended)**: Move filtering INTO ActivityFeed.jsx
- ActivityFeed receives ALL activities from App.jsx
- Tab filtering logic lives entirely within ActivityFeed.jsx
- Cleaner separation of concerns

**Option B**: Keep filtering in App.jsx, just change UI
- Replace dropdown with tabs in App.jsx
- ActivityFeed stays unchanged

**Decision**: Use Option A - Move filtering into ActivityFeed.jsx component for better encapsulation.

## Files to Modify
1. `/src/field/ensemble_ui/frontend/src/App.jsx`
   - Change title from "Ensemble AI" to "Willow says Hi"
   - Remove dropdown filter from Activity Feed Card.Header
   - Remove `activityFilter` state variable
   - Pass unfiltered `activities` to ActivityFeed (instead of `filteredActivities`)

2. `/src/field/ensemble_ui/frontend/src/components/ActivityFeed.jsx`
   - Add TAB_FILTERS constant
   - Add activeTab state
   - Add filtering logic based on activeTab
   - Add tab UI component with badges showing counts
   - Style tabs to match dark theme

## Acceptance Criteria
- [ ] Title displays "🎭 Willow says Hi" in header
- [ ] Horizontal tabbed interface visible in Activity Feed
- [ ] Tabs: All, Running, Completed, Spawned, Failed, Other
- [ ] Each tab shows count badge
- [ ] Active tab is visually distinct
- [ ] Clicking tab filters activities correctly
- [ ] Dark theme styling consistent with existing UI
- [ ] No console errors
- [ ] All existing activity display functionality preserved

## Dependencies
- React Bootstrap (existing)
- Existing ActivityFeed component structure
- Existing dark theme CSS variables
