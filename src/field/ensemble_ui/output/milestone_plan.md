# Fix Metrics Pane Agent Display - Milestone Plan

## Project Overview
Fix UI panes to properly display all agent types and activity states with dynamic filtering based on actual system data rather than hardcoded values.

## Milestone 1: Dynamic Activity Feed Enhancement (Priority: HIGH)

### Objective
Replace hardcoded activity filter dropdown with dynamic generation based on actual activity data, including semantic groupings for better user experience.

### Deliverables
1. Dynamic filter generation logic that scans activities for unique types
2. Semantic grouping implementation (Agent Lifecycle, Tool Usage, Errors, etc.)
3. Enhanced filter logic supporting category-based filtering
4. Activity count display per filter option
5. Real-time filter updates as new activities arrive

### Acceptance Criteria
- Activity feed shows ALL activity types present in the system
- Filter options generated dynamically from actual data
- Semantic categories work correctly (e.g., "Agent Lifecycle" shows spawned, completed, failed)
- Activity counts displayed next to each filter option
- Filters update when new activity types appear
- Performance maintained with 200+ activities

### Dependencies
- Current activity data structure analysis
- Frontend React component modifications

### Estimated Duration: 3-5 days

---

## Milestone 2: Agent Type Visibility & Error State Enhancement (Priority: MEDIUM)

### Objective
Ensure all agent types are visible across UI panes and improve error/failed state visibility for better debugging.

### Deliverables
1. Enhanced agent type filtering in relevant panes
2. Better error state highlighting and visibility
3. Agent type categorization display
4. "Problem agents" quick filter
5. Error details display enhancement

### Acceptance Criteria
- All spawned agent types visible in UI panes (Executive Director, Development Manager, System Architect, TDD Coordinator, etc.)
- Failed agents prominently displayed with clear visual distinction
- Error activities easy to filter and find
- Agent type categories shown in displays
- Quick access to problematic agents

### Dependencies
- Milestone 1 completion
- Agent state data structure analysis

### Estimated Duration: 2-3 days

---

## Milestone 3: Metrics Pane Verification & Polish (Priority: MEDIUM)

### Objective
Verify metrics pane includes all agent types and add any missing coverage, plus final polish of the enhanced filtering system.

### Deliverables
1. Backend metrics aggregation verification
2. Frontend metrics display enhancements
3. Agent type distribution in summary views
4. Final UI polish and testing
5. Documentation updates

### Acceptance Criteria
- Metrics pane shows performance data for ALL agent types
- Agent type distribution visible in summary
- All new filtering features work reliably
- UI remains performant and responsive
- User experience improvements validated

### Dependencies
- Milestone 2 completion
- Backend API analysis

### Estimated Duration: 1-2 days

---

## Total Project Timeline: 6-10 days

## Risk Mitigation
- **Performance Risk**: Implement efficient filtering algorithms, test with large datasets
- **Data Structure Changes**: Analyze existing activity format first to ensure compatibility
- **Real-time Update Issues**: Leverage existing polling logic, avoid breaking changes

## Success Metrics
1. User can see all spawned agent types in UI
2. Activity feed shows all actual activity types (no missing types)
3. Failed/error states are clearly visible and filterable
4. Filter dropdown is dynamic and reflects real system state
5. Performance remains acceptable with large activity datasets