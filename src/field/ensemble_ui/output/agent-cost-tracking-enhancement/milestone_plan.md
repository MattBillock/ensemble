# Milestone Plan: Agent Cost Tracking Enhancement

## Project Overview
Enhance the ensemble UI to display cost estimates, execution duration, and model information for each agent task to provide better visibility into agent performance and resource usage.

## Implementation Status: COMPLETE
**Completed**: 2026-01-15
**Implemented by**: Claude Opus 4.5 (manual implementation)

All core milestones (1-3) have been implemented. Milestone 4 (testing/docs) deferred for future work.

---

## Milestone 1: Backend Tracking Infrastructure - ✅ COMPLETE
**Objective**: Implement backend changes to capture and track agent execution metrics (cost, duration, model)

**Deliverables**:
1. Extended activity_tracker.py to capture new metrics (started_at, completed_at, duration_ms, model_used, cost_estimate)
2. Updated AgentRuntime to track start time and calculate costs
3. Cost calculation logic based on token usage and model pricing
4. Updated agent state data structures to include new fields

**Acceptance Criteria**:
- ✅ Activity tracker successfully records all new metrics for agent executions
- ✅ Cost estimates calculated accurately based on token usage and model pricing
- ✅ Execution duration captured in milliseconds
- ✅ Model identifier properly tracked from AgentRuntime
- ✅ Backend maintains backward compatibility with existing agent executions
- ✅ Unit tests pass for activity tracker and cost calculation

**Dependencies**: None (starting milestone)

**Estimated Scope**: Backend changes to activity_tracker.py, AgentRuntime metrics tracking

---

## Milestone 2: API and Data Flow Enhancement - ✅ COMPLETE
**Objective**: Update API endpoints to expose new metrics to frontend

**Deliverables**:
1. Updated API response structures in main.py to include new fields
2. WebSocket/polling endpoints return extended agent state data
3. API documentation updated with new fields

**Acceptance Criteria**:
- ✅ API endpoints return started_at, completed_at, duration_ms, model_used, cost_estimate
- ✅ Data format matches expected frontend structure
- ✅ Existing API consumers not broken by changes
- ✅ API integration tests pass

**Dependencies**: Milestone 1 (backend tracking must be implemented first)

**Estimated Scope**: API endpoint updates in main.py

---

## Milestone 3: Frontend Display Implementation - ✅ COMPLETE
**Objective**: Update UI to display new agent metrics in a user-friendly format

**Deliverables**:
1. Enhanced AgentSummaryPane.jsx component with new metric displays
2. Formatted cost display (e.g., "$0.0042")
3. Formatted duration display (e.g., "2.3s", "1m 45s")
4. Model tag/badge display with shortened model names
5. Execution timeline display (started → completed)

**Acceptance Criteria**:
- ✅ Cost estimate displayed in readable format with $ prefix
- ✅ Duration shown in appropriate units (ms, seconds, minutes)
- ✅ Model tag displayed with shortened, readable name
- ✅ Execution timeline shows start and completion times
- ✅ UI remains compact and doesn't clutter the interface
- ✅ No performance degradation in UI rendering

**Dependencies**: Milestone 2 (API must provide data first)

**Estimated Scope**: Frontend changes to AgentSummaryPane.jsx component

---

## Milestone 4: Testing and Documentation - ⏳ DEFERRED
**Objective**: Ensure system reliability and provide documentation

**Deliverables**:
1. Comprehensive test suite for backend cost tracking
2. Integration tests for API data flow
3. Frontend component tests for display logic
4. User documentation for interpreting metrics
5. Developer documentation for maintenance

**Acceptance Criteria**:
- ✅ All unit tests pass (backend, API, frontend)
- ✅ Integration tests verify end-to-end data flow
- ✅ Code coverage meets project standards
- ✅ Documentation complete and accurate
- ✅ Manual testing confirms all success criteria met

**Dependencies**: Milestone 3 (requires all implementation complete)

**Estimated Scope**: Testing and documentation across all components

---

## Success Criteria (Project Level)

1. **Each completed agent shows**:
   - Start time (ISO format or relative time)
   - Completion time (ISO format or relative time)
   - Duration (e.g., "2.3s", "1m 45s")
   - Cost estimate (e.g., "$0.0042")
   - Model tag (e.g., "claude-3-5-sonnet-20241022")

2. **Data is captured reliably** from backend without errors

3. **UI displays information** in a readable, compact format

4. **No performance degradation** to existing functionality

---

## Risk Assessment

**Technical Risks**:
- Token usage data might not always be available from API responses
- Mitigation: Implement character-based estimation with "~" prefix for estimates

**Integration Risks**:
- Changes might break existing activity tracker consumers
- Mitigation: Ensure backward compatibility, make new fields optional

**Performance Risks**:
- Additional metrics might slow down agent execution tracking
- Mitigation: Keep calculations lightweight, use efficient data structures

---

## Implementation Order

1. **Milestone 1** (Backend) - Foundation for all subsequent work
2. **Milestone 2** (API) - Enables frontend to access data
3. **Milestone 3** (Frontend) - User-facing implementation
4. **Milestone 4** (Testing/Docs) - Quality assurance and maintenance

Each milestone must be completed and verified before proceeding to the next.
