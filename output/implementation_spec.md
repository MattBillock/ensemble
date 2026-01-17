# Implementation Specification: Timeline Scroll Preservation

## Objective
Modify HorizontalTimelineView component to maintain user's scroll position during periodic data refreshes.

## Required Changes in `/src/field/ensemble_ui/frontend/src/components/HorizontalTimelineView.jsx`

### 1. Import Updates
```javascript
import React, { useState, useEffect, useRef, useCallback } from 'react';
```

### 2. State and Ref Management
- Add new refs to track scroll position:
```javascript
const containerRef = useRef(null);
const scrollPositionRef = useRef({ x: 0, y: 0 });
```

### 3. Scroll Preservation Methods
Implement two new methods:
```javascript
const preserveScrollPosition = useCallback(() => {
  if (containerRef.current) {
    scrollPositionRef.current = {
      x: containerRef.current.scrollLeft,
      y: containerRef.current.scrollTop
    };
  }
}, []);

const restoreScrollPosition = useCallback(() => {
  if (containerRef.current) {
    containerRef.current.scrollLeft = scrollPositionRef.current.x;
    containerRef.current.scrollTop = scrollPositionRef.current.y;
  }
}, []);
```

### 4. Modify `useEffect` for Request Fetching
Update to preserve scroll state:
```javascript
useEffect(() => {
  const fetchRequests = async () => {
    try {
      preserveScrollPosition();
      const response = await fetch('http://localhost:8001/api/requests?limit=20');
      // Existing fetch logic
      
      setTimeout(restoreScrollPosition, 0);
    } catch (error) {
      // Existing error handling
    }
  };

  fetchRequests();
  const interval = setInterval(fetchRequests, 2000);
  return () => clearInterval(interval);
}, [preserveScrollPosition, restoreScrollPosition, selectedRequest]);
```

### 5. Container Ref Update
Modify container div to use new ref:
```javascript
<div
  ref={containerRef}
  style={{
    flex: 1,
    overflowX: 'auto',
    overflowY: 'auto',
    padding: '20px'
  }}
>
  {/* Existing content */}
</div>
```

## Testing Requirements
1. Verify scroll position remains stable during periodic refreshes
2. Test with long timeline and varied scroll positions
3. Ensure no performance degradation
4. Validate across different browsers

## Performance Considerations
- Use `useCallback` to memoize scroll methods
- Minimal overhead with `setTimeout` for scroll restoration
- Preserve existing component logic

## Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- React 17+ recommended
- ES6+ environment required