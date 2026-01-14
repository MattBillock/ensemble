# Test Tasks - Milestone 1: Activity Feed Tabbed Interface

## Overview
Test tab filtering logic, activity type grouping, count badge accuracy, and dark theme styling for the new tabbed interface in ActivityFeed.jsx.

## Unit Test Tasks

### Test 1: Tab Filter Constants Validation
**Description**: Verify TAB_FILTERS configuration is correct
**Test Cases**:
- All tabs have required structure (label, types)
- 'all' tab has types: null
- 'running' tab contains correct activity types
- 'completed' tab contains correct activity types
- 'spawned' tab contains correct activity types
- 'failed' tab contains correct activity types
- 'other' tab contains all remaining activity types
- No activity type is missing from all tabs combined

### Test 2: Filter Logic Tests
**Description**: Test filtering function with different tab selections
**Test Cases**:
- Filter with 'all' returns all activities
- Filter with 'running' returns only running activities
- Filter with empty activities array returns empty
- Filter handles unknown activity types gracefully

### Test 3: Count Calculation Tests
**Description**: Test count badge calculations
**Test Cases**:
- Count is accurate for each tab
- Count updates when activities array changes
- Count is 0 for tabs with no matching activities

## Integration Test Tasks

### Test 4: Tab Switching Behavior
**Description**: Test tab click changes filtered activities
**Test Cases**:
- Clicking tab updates activeTab state
- Filtered activities list updates immediately
- Active tab styling changes on click

### Test 5: Real-time Update Tests
**Description**: Test counts and filtering with live data updates
**Test Cases**:
- New activities update counts
- Filter results update when new matching activity arrives
- Tab retains selection after data refresh

## Visual/Manual Test Tasks

### Test 6: Dark Theme Styling Verification
**Description**: Verify styling matches requirements
**Checklist**:
- Tab group background: #242836
- Inactive tab text: #9ca3af
- Active tab background: #3a3f52
- Active tab text: #ffffff
- Badge styling consistent
- Hover states work

### Test 7: Responsive Layout Tests
**Description**: Verify tabs work on different screen sizes
**Checklist**:
- Tabs fit on mobile screens
- Tabs don't wrap unexpectedly
- Touch targets are adequate size

## Coverage Requirements
- All TAB_FILTERS combinations tested
- Filter logic 100% coverage
- Count calculation 100% coverage
- Tab click handlers tested

## Test Files to Create
- `/src/field/ensemble_ui/frontend/src/components/__tests__/ActivityFeed.test.jsx`
