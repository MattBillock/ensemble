# Frontend Tasks - Project-Based Agent Hierarchy Enhancement

## Task 1: Extend Agent Hierarchy Data Processing
- **Description**: Modify data processing logic to group agents by project_id
- **Complexity**: Medium
- **Dependencies**: None
- **Acceptance Criteria**:
  - Implement `groupAgentsByProject` utility function
  - Function transforms flat agent list into project-grouped structure
  - Handles agents without explicit project_id
- **Implementation Notes**:
  - Create in `src/utils/projectHelpers.js`
  - Use `reduce` for efficient grouping
  - Default to 'default' project if no project_id

## Task 2: Project Group Component
- **Description**: Create new ProjectGroup component to wrap agents from same project
- **Complexity**: Medium
- **Dependencies**: Task 1
- **Acceptance Criteria**:
  - Renders project header with project name
  - Shows project-level statistics (agent counts, status)
  - Supports expand/collapse functionality
  - Maintains existing agent hierarchy rendering within project
- **Implementation Notes**:
  - Create in `src/components/ProjectGroup.jsx`
  - Use React Bootstrap for consistent styling
  - Implement state management for expand/collapse

## Task 3: Project Header Component
- **Description**: Develop component for project group headers
- **Complexity**: Simple
- **Dependencies**: Task 2
- **Acceptance Criteria**:
  - Displays project name/ID
  - Shows summary badges (agent count, status)
  - Includes expand/collapse toggle
  - Consistent styling with existing UI
- **Implementation Notes**:
  - Create in `src/components/ProjectHeader.jsx`
  - Use existing badge components
  - Implement toggle state management

## Task 4: Modify AgentHierarchyTree Component
- **Description**: Update existing AgentHierarchyTree to use project grouping
- **Complexity**: Complex
- **Dependencies**: Task 1, Task 2, Task 3
- **Acceptance Criteria**:
  - Render agents grouped by project
  - Preserve existing hierarchy structure within each project
  - Support project-level expand/collapse
  - Maintain all existing rendering and interaction behaviors
- **Implementation Notes**:
  - Modify `src/components/AgentHierarchyTree.jsx`
  - Use new ProjectGroup and ProjectHeader components
  - Ensure minimal changes to existing logic

## Task 5: Stage Badge Enhancement
- **Description**: Improve stage badge system for more informative display
- **Complexity**: Simple
- **Dependencies**: None
- **Acceptance Criteria**:
  - Create reusable StageBadge component
  - Support all defined stages (requirements, architecture, etc.)
  - Use consistent icons and color variants
  - Easily composable across different components
- **Implementation Notes**:
  - Create in `src/components/StageBadge.jsx`
  - Define stage configuration with icons and variants
  - Make component flexible and reusable

## Task 6: Project Expand/Collapse State Management
- **Description**: Implement state management for project group interactions
- **Complexity**: Medium
- **Dependencies**: Task 2, Task 4
- **Acceptance Criteria**:
  - Track expanded/collapsed state for each project
  - Persist state across re-renders
  - Support programmatic expand/collapse
  - Smooth transitions between states
- **Implementation Notes**:
  - Use React `useState` hook
  - Create custom hook `useProjectGrouping`
  - Store state in `src/hooks/useProjectGrouping.js`

## Task 7: Integration and Compatibility Testing
- **Description**: Ensure new project grouping works with existing system
- **Complexity**: Complex
- **Dependencies**: All previous tasks
- **Acceptance Criteria**:
  - All existing tests pass
  - New project grouping logic compatible with current API
  - Performance maintained with multiple projects
  - No regression in existing functionality
- **Implementation Notes**:
  - Write integration tests
  - Test with various agent list scenarios
  - Verify polling mechanism still works
  - Performance testing with 10+ projects