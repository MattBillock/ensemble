# AI Provider Enhancement System - Milestone Plan

## Project Overview
**Project ID**: 3cd35d78
**Created**: 2026-01-13
**Status**: Planning

---

## Milestone 1: CLI Provider Integration
**Duration**: 2-3 days
**Priority**: Highest

### Objective
Implement CLI provider adapter system that detects and uses locally installed Claude CLI and ChatGPT CLI tools as preferred API alternatives.

### Deliverables
1. `provider_manager.py` - AI provider abstraction and detection system
2. `cli_provider.py` - CLI provider implementations for Claude and ChatGPT
3. Updated `runtime.py` - Integration with provider manager
4. Unit tests for provider detection and execution

### Acceptance Criteria
- [ ] Claude CLI at `/opt/homebrew/bin/claude` is detected automatically
- [ ] CLI provider executes prompts using `claude --print` flag
- [ ] Graceful fallback to Anthropic API when CLI unavailable
- [ ] Provider success/failure metrics tracked in database
- [ ] No increase in execution latency >10%

### Dependencies
- Existing runtime.py infrastructure
- Claude CLI installed at `/opt/homebrew/bin/claude`

---

## Milestone 2: Cost Estimation Module
**Duration**: 2-3 days
**Priority**: High

### Objective
Implement comprehensive pre-execution cost estimation and post-execution cost tracking with dashboard integration.

### Deliverables
1. `cost_estimator.py` - Pre-execution cost estimation based on task complexity
2. Enhanced `cost_calculator.py` - Extended with estimation capabilities
3. Updated `metrics.py` - Cost tracking fields and aggregation queries
4. Cost API endpoints for dashboard

### Acceptance Criteria
- [ ] Pre-execution cost estimates available before spawning agents
- [ ] Estimates within 50% of actual costs
- [ ] Cost aggregation by project, agent type, and time period
- [ ] Cost fields added to agent_executions table
- [ ] API endpoints expose cost data to dashboard

### Dependencies
- Milestone 1 (provider tracking needed for CLI vs API cost differentiation)
- Existing cost_calculator.py

---

## Milestone 3: Smart Agent Router
**Duration**: 2-3 days
**Priority**: Medium-High

### Objective
Implement intelligent agent-task routing based on historical performance metrics.

### Deliverables
1. `agent_router.py` - Performance analysis and routing recommendations
2. Updated agent execution flow to use router recommendations
3. Routing analytics API endpoints
4. Dashboard widget for routing explanations

### Acceptance Criteria
- [ ] Agent recommendations based on historical performance from metrics.db
- [ ] Routing considers success rate (50%), cost efficiency (30%), speed (20%)
- [ ] Agent specialization bonuses applied (e.g., code_writer +10% for code tasks)
- [ ] Override capability for manual agent selection
- [ ] 10% improvement in overall success rate (measurable after deployment)

### Dependencies
- Milestone 2 (cost data needed for cost efficiency calculations)
- Populated metrics.db with historical data

---

## Milestone 4: Project Recovery & Dashboard Integration
**Duration**: 2-3 days
**Priority**: Medium

### Objective
Restart 10 stalled projects and integrate all new features into the dashboard.

### Deliverables
1. `recovery_orchestrator.py` - Project recovery logic
2. Recovery execution report
3. Dashboard integration for provider, cost, and routing features
4. Updated frontend components

### Acceptance Criteria
- [ ] All 10 stalled projects attempted for restart
- [ ] Recovery report generated with outcomes per project
- [ ] Independent error boundaries (one failure doesn't stop others)
- [ ] Dashboard shows provider usage, cost trends, routing info
- [ ] Provider success rates visible in dashboard

### Dependencies
- Milestones 1-3 completed
- Access to project tracking system

---

## Milestone Summary

| Milestone | Objective | Duration | Dependencies |
|-----------|-----------|----------|--------------|
| 1 | CLI Provider Integration | 2-3 days | None |
| 2 | Cost Estimation Module | 2-3 days | Milestone 1 |
| 3 | Smart Agent Router | 2-3 days | Milestone 2 |
| 4 | Project Recovery & Dashboard | 2-3 days | Milestones 1-3 |

**Total Estimated Duration**: 8-12 days

---

## Technical Decisions Made

### TD1: Provider Selection Strategy
- **Decision**: CLI preferred over API when available
- **Rationale**: CLI tools use user's existing subscription, avoiding API costs

### TD2: Cost Estimation Approach
- **Decision**: Use task complexity heuristics for output token estimation
- **Rationale**: More accurate than fixed estimates, calibrated to task types

### TD3: Routing Algorithm Weights
- **Decision**: 50% success rate, 30% cost efficiency, 20% speed
- **Rationale**: Reliability most important, then cost, then speed

### TD4: Recovery Sequence
- **Decision**: Sequential processing, not parallel
- **Rationale**: Easier debugging, independent error boundaries, API rate limits

---

## Files to Create
- `src/runtime/agents/provider_manager.py`
- `src/runtime/agents/cli_provider.py`
- `src/runtime/agents/cost_estimator.py`
- `src/runtime/agents/agent_router.py`
- `src/runtime/agents/recovery_orchestrator.py`

## Files to Modify
- `src/runtime/agents/runtime.py`
- `src/runtime/agents/metrics.py`
- `src/field/ensemble_ui/backend/main.py`
- `src/field/ensemble_ui/frontend/src/App.jsx`

---

**Document Status**: Complete
**Next Step**: System Architecture
