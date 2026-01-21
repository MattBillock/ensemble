# Frontend Tasks - Update Interval Selector Options

## Tasks Breakdown

### 1. Locate Interval Selector Component
- **Complexity:** Simple
- **Description:** Find the existing interval selector component in the project
- **Acceptance Criteria:**
  - Identify the exact file and location of the interval selector
  - Confirm it's a dropdown or similar selection mechanism
- **Dependencies:** None

### 2. Update Interval Options Array/Object
- **Complexity:** Simple
- **Description:** Modify the interval options from current [500ms, 1s, 2s] to [1s, 1m, 5m]
- **Acceptance Criteria:**
  - Options display shows: "1s", "1m", "5m"
  - Corresponding millisecond values correct
    - 1s = 1000ms
    - 1m = 60000ms
    - 5m = 300000ms
- **Dependencies:** Task 1 (Component Location)

### 3. Implement Interval Conversion Logic
- **Complexity:** Medium
- **Description:** Create utility function to convert interval labels to milliseconds
- **Acceptance Criteria:**
  - Function accepts interval label (e.g., "1s", "1m", "5m")
  - Returns correct millisecond value
  - Handles default case (fallback to 1m)
- **Dependencies:** Task 2 (Interval Options)

### 4. Update Default Interval Selection
- **Complexity:** Simple
- **Description:** Set default interval to "1m" (1 minute)
- **Acceptance Criteria:**
  - Component loads with "1m" pre-selected
  - Millisecond value defaults to 60000
- **Dependencies:** Task 2 (Interval Options)

### 5. Handle Legacy Interval Values
- **Complexity:** Medium
- **Description:** Add migration logic for any saved preferences with old values
- **Acceptance Criteria:**
  - Legacy values (500ms, 2s) mapped to new defaults
  - No errors when loading previously saved configurations
- **Dependencies:** Task 3 (Conversion Logic)

### 6. Update UI Labels and Tooltips
- **Complexity:** Simple
- **Description:** Refresh any text related to interval selection
- **Acceptance Criteria:**
  - Clear labels showing seconds (s) and minutes (m)
  - Optional tooltips explaining interval meanings
- **Dependencies:** Task 2 (Interval Options)

### 7. Write Unit Tests for Interval Component
- **Complexity:** Medium
- **Description:** Create comprehensive tests for interval selector
- **Acceptance Criteria:**
  - Test rendering of new options
  - Test conversion logic
  - Test default selection
  - Verify no regressions in existing functionality
- **Dependencies:** Tasks 1-6 (All previous tasks)

### 8. Manual UI Testing
- **Complexity:** Simple
- **Description:** Verify UI changes in browser
- **Acceptance Criteria:**
  - Dropdown shows correct options
  - Selecting each interval triggers correct update frequency
  - No console errors
  - UI remains responsive
- **Dependencies:** Task 7 (Unit Tests)

## Task Dependencies
1. Locate Interval Selector Component
2. Update Interval Options Array/Object ➜ depends on Task 1
3. Implement Interval Conversion Logic ➜ depends on Task 2
4. Update Default Interval Selection ➜ depends on Task 2
5. Handle Legacy Interval Values ➜ depends on Task 3
6. Update UI Labels and Tooltips ➜ depends on Task 2
7. Write Unit Tests ➜ depends on Tasks 1-6
8. Manual UI Testing ➜ depends on Task 7

## Recommended Execution Order
Follow the numbered task sequence for best results.