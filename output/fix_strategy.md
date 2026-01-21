# Timeline Page Data Refresh Strategy

## Problem
The timeline page automatically refreshes and changes user's current view every two seconds, causing user frustration and loss of focus.

## Fix Strategy
1. Modify data refresh mechanism to maintain current scroll position
2. Implement scroll preservation during data updates
3. Prevent automatic view reset

### Specific Implementation Steps
1. Add `useRef` for scroll container
2. Store scroll position before data refresh
3. Restore scroll position after data update
4. Add option to pause/disable auto-refresh

### Key Code Modifications in `HorizontalTimelineView.jsx`
- Modify `fetchRequests()` to preserve scroll state
- Add scroll preservation logic in data fetch methods
- Implement scroll state management in `useEffect` hooks

## Performance Considerations
- Minimal performance overhead
- Non-intrusive to existing component structure
- Preserves real-time data update functionality