# Test Strategy: Milestone 1 & 2 - Backend Enhancement and Frontend Project Hierarchy

## Test Objectives
1. Validate backend project_id and stage tracking
2. Verify frontend AgentHierarchyTree project grouping
3. Ensure expand/collapse functionality works
4. Confirm backend and frontend integration

## Backend Test Tasks

### Unit Tests: Activity Tracking
1. Test project_id generation 
   - Validates unique ID creation
   - Ensures deterministic format
2. Test current_stage state transitions
   - Verify valid stage progression
   - Check stage update mechanics
3. Validate project tracking model extensions
   - Confirm data model accepts new fields
   - Check serialization/deserialization

### Integration Tests: API Endpoints
1. Test `/api/activity` response with project metadata
   - Validate new fields present
   - Ensure backward compatibility
2. Test optional `/api/projects/summary` endpoint
   - Validate aggregated project stats
   - Check multi-project scenarios

## Frontend Test Tasks

### Unit Tests: Project Grouping
1. Test `groupAgentsByProject()` utility function
   - Correctly group agents by project_id
   - Handle agents without project_id
   - Performance with 10+ agents
2. Test state management hooks
   - `useProjectGrouping()` computation
   - Expand/collapse state tracking

### Component Tests: AgentHierarchyTree
1. Verify project group rendering
   - Correct project header display
   - Agent nesting under projects
2. Test expand/collapse interactions
   - Project level expand/collapse
   - Nested agent visibility
3. Badge and status rendering
   - Correct stage badge rendering
   - Project summary badge accuracy

### Integration Tests
1. Full polling cycle test
   - Project tracking through polling
   - Real-time updates
2. Multiple project workflow
   - Simultaneous project rendering
   - Performance under load

## E2E Test Scenarios

### Happy Path Scenarios
1. Single project workflow
   - Submit problem
   - Track agent hierarchy
   - Verify stage progression
2. Multi-project workflow
   - Create 3+ concurrent projects
   - Navigate between projects
   - Check expand/collapse

### Error/Edge Case Scenarios
1. Project with no agents
2. Long-running projects
3. Rapid project submissions
4. Incomplete stage information

## Performance & Scalability Tests
1. 10+ concurrent project rendering
2. Memory usage tracking
3. Polling performance
4. Stage badge computation speed

## Recommended Test Coverage
- Backend Unit Tests: 90%
- Backend Integration Tests: 100%
- Frontend Unit Tests: 85%
- Frontend Component Tests: 80%
- E2E Happy Path: 100%
- E2E Error Scenarios: 75%

## Testing Approach
- Framework: pytest (backend), Jest (frontend)
- Mocking: Extensive use of mock dependencies
- Snapshot testing for UI components
- Performance profiling

## Risks & Mitigations
1. Performance degradation
   - Use memoization
   - Efficient grouping algorithms
2. State management complexity
   - Minimal state changes
   - Clear separation of concerns
3. UI clutter with multiple projects
   - Comprehensive expand/collapse
   - Clear visual hierarchy

## Out of Scope
- Advanced project management features
- Authentication scenarios
- Historical project archives