# Requirements: Ensemble AI Provider Enhancement System

## Vision
Enhance the ensemble system to support local CLI-based AI providers (Claude CLI, ChatGPT CLI) as preferred alternatives to direct API calls, implement comprehensive cost estimation and tracking, enable intelligent agent-task routing based on performance metrics, and resume previously paused work across 10 stalled projects.

## Executive Summary
This project addresses four key user needs:
1. **Local CLI Providers**: Use locally installed Claude/ChatGPT CLI tools as API substitutes, with preference for local tools when available and functional
2. **Cost Estimation**: Comprehensive pre-execution cost estimation and post-execution tracking
3. **Smart Agent Routing**: Data-driven routing to match agents with suitable work based on historical performance
4. **Work Resume**: Restart 10 previously stalled projects that were paused due to API credit issues

## Objectives

### O1: Local CLI Provider Integration
- Detect locally installed Claude CLI (`/opt/homebrew/bin/claude` - confirmed present)
- Detect locally installed ChatGPT CLI (if available)
- Create adapter layer to use CLI tools as API substitutes
- Prefer CLI tools over API when available and functional
- Track success/failure statistics for CLI providers on metrics dashboard

### O2: Cost Estimation Enhancement
- Pre-execution cost estimates based on task complexity and model selection
- Real-time cost tracking during execution
- Post-execution cost reporting
- Cost aggregation by project, agent type, and time period
- Cost visibility in metrics dashboard

### O3: Intelligent Agent Routing
- Analyze historical agent performance data from metrics.db
- Route tasks to agents with best success rates for similar work
- Consider agent specialization (e.g., code_writer for code, tester for tests)
- Factor in cost efficiency when making routing decisions
- Provide routing recommendations with explanations

### O4: Resume Paused Work
- Restart 10 stalled projects identified in task_recovery_analysis.md
- Sequential processing with independent error boundaries
- Generate recovery report documenting success/failure per project

## Scope

### In Scope

#### Feature 1: CLI Provider Adapter System
- Auto-detect installed CLI tools on system startup
- Abstract provider interface supporting both API and CLI execution
- CLI provider for Claude (using `claude --print` or equivalent flags)
- CLI provider for ChatGPT (if available)
- Fallback chain: CLI → API → Error
- Provider health checks and availability testing
- Success/failure metrics per provider in dashboard

#### Feature 2: Cost Estimation Module
- Pre-execution cost estimator based on:
  - Selected model (from model_selector.py)
  - Estimated input tokens (from prompt size)
  - Estimated output tokens (from task type heuristics)
- Cost tracking integration with existing cost_calculator.py
- Cost aggregation and reporting APIs
- Dashboard widgets for cost visualization
- Project-level cost attribution

#### Feature 3: Smart Agent Router
- Performance analytics from metrics.db
- Agent-task matching algorithm considering:
  - Historical success rate per agent type
  - Task complexity vs agent capability
  - Cost efficiency per agent
  - Recent error patterns
- Routing recommendation API
- Override capability for manual agent selection

#### Feature 4: Project Recovery Orchestration
- Parse task_recovery_analysis.md for 10 stalled projects
- Categorize by priority:
  - Priority 1: 3 in_progress tasks (likely stalled)
  - Priority 2: 5 todo tasks (not started)
  - Priority 3: 2 projects with no tasks
- Execute recovery sequentially
- Generate comprehensive recovery report

### Out of Scope
- Custom CLI tool development (use existing tools)
- Real-time API cost limits/caps (future enhancement)
- Parallel recovery execution (sequential for V1)
- CLI tool installation automation

## Technical Design Overview

### F1: CLI Provider Adapter

#### Architecture
```
┌─────────────────────────────────────────────────┐
│              AgentRuntime.execute()             │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│           AIProviderManager (New)               │
│  ┌──────────────────────────────────────────┐   │
│  │ detect_providers()                       │   │
│  │ get_best_provider(model, task)           │   │
│  │ execute(provider, prompt, model)         │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────┘
          ┌───────────┼───────────┐
          ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ ClaudeCLI   │ │ ChatGPTCLI  │ │ AnthropicAPI│
│ Provider    │ │ Provider    │ │ Provider    │
└─────────────┘ └─────────────┘ └─────────────┘
```

#### CLI Detection
```python
# Detect Claude CLI
which_claude = subprocess.run(["which", "claude"], capture_output=True)
claude_available = which_claude.returncode == 0

# Test Claude CLI functionality
test_result = subprocess.run(
    ["claude", "--print", "-p", "Hello"],
    capture_output=True, timeout=10
)
claude_functional = test_result.returncode == 0
```

#### Provider Interface
```python
class AIProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool: ...
    
    @abstractmethod
    def execute(self, prompt: str, model: str, max_tokens: int) -> ProviderResponse: ...
    
    @abstractmethod
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float: ...
```

#### Metrics Integration
- Track per-provider: success_count, failure_count, avg_response_time, total_tokens
- Add provider_type field to agent_executions table
- Dashboard: Provider usage pie chart, success rates comparison

### F2: Cost Estimation Module

#### Pre-Execution Estimation
```python
class CostEstimator:
    def estimate_task_cost(
        self,
        model: str,
        prompt: str,
        task_complexity: str,
        expected_iterations: int = 1
    ) -> CostEstimate:
        """
        Estimate cost before execution.
        
        Uses:
        - Actual prompt token count (tiktoken or approximation)
        - Task complexity to estimate output tokens
        - Model pricing from cost_calculator.py
        """
```

#### Task Complexity Heuristics
- **Strategic** tasks: Expect 4000-8000 output tokens
- **Creative** tasks: Expect 2000-4000 output tokens  
- **Routine** tasks: Expect 500-2000 output tokens

#### Dashboard Integration
- Pre-execution estimate shown before spawning agents
- Running cost tracker during execution
- Final cost comparison (estimated vs actual)
- Cost trends over time (daily, weekly, monthly)

### F3: Smart Agent Router

#### Performance Analysis
```python
class AgentRouter:
    def get_best_agent_for_task(
        self,
        task_type: str,
        task_complexity: str,
        available_agents: List[str]
    ) -> AgentRecommendation:
        """
        Analyze metrics.db to find best agent for task.
        
        Considers:
        - Success rate for similar tasks
        - Average duration for task type
        - Cost efficiency
        - Recent error patterns
        """
```

#### Routing Algorithm
1. Query metrics.db for agent performance on similar tasks
2. Calculate composite score: `success_rate * 0.5 + cost_efficiency * 0.3 + speed * 0.2`
3. Apply specialization bonuses (e.g., code_writer +10% for code tasks)
4. Return ranked recommendations with explanations

#### Agent Specialization Map
```python
AGENT_SPECIALIZATIONS = {
    "code_writer": ["implementation", "refactoring", "bug_fix"],
    "code_tester": ["unit_test", "integration_test", "test_fix"],
    "system_architect": ["architecture", "design", "planning"],
    "frontend_developer": ["ui", "ux", "react", "styling"],
    "backend_developer": ["api", "database", "server", "performance"]
}
```

### F4: Project Recovery

#### Recovery Targets (from task_recovery_analysis.md)
| Priority | Project ID | Project Name | Issue |
|----------|------------|--------------|-------|
| 1 | bb528d28 | Local Weather Display Widget | Dev Manager stalled |
| 1 | 0114ab16 | Ensemble UI Enhancements | Architecture mismatch |
| 1 | 4af1c241 | Agent Hierarchy Organization | Dev Manager incomplete |
| 2 | 84dd6401 | Agent Tracking Metrics | Task not started |
| 2 | 5f5892f3 | Agent Cost Tracking - Frontend | Task not started |
| 2 | 66af6b69 | Agent Cost Tracking - Backend | Tasks not started |
| 2 | d863e0cc | Agent Completion Visibility | Tasks not started |
| 2 | ea916e81 | Ensemble UI Completion | Tasks not started |
| 3 | e30078c1 | Verifier Agent Swarm | No tasks created |
| 3 | 168565b8 | UI Activity Pane Graph | No tasks created |

#### Recovery Strategy
- Priority 1: Spawn Development Manager to restart
- Priority 2: Spawn appropriate coordinator
- Priority 3: Spawn Executive Director for requirements

## Users
- **Primary**: Ensemble system (automated provider selection, routing)
- **Secondary**: Developers (cost monitoring, performance analysis)
- **Tertiary**: End users (dashboard visibility)

## Constraints
- Must not break existing agent execution flow
- CLI providers must fall back gracefully to API
- Cost estimates should be within 50% of actual
- Recovery must be sequential (no parallel spawning)

## Success Criteria

### SC1: CLI Provider Integration
- [ ] Claude CLI detected and usable when available
- [ ] Graceful fallback to API when CLI unavailable
- [ ] Provider success/failure metrics visible in dashboard
- [ ] No increase in execution latency >10%

### SC2: Cost Estimation
- [ ] Pre-execution cost estimates available for all tasks
- [ ] Estimates within 50% of actual costs
- [ ] Cost aggregation by project and time period
- [ ] Dashboard shows cost trends and breakdowns

### SC3: Smart Agent Routing
- [ ] Agent recommendations based on historical performance
- [ ] Routing considers success rate, cost, and speed
- [ ] Override capability for manual selection
- [ ] 10% improvement in overall success rate

### SC4: Project Recovery
- [ ] All 10 stalled projects restarted
- [ ] Recovery report generated with outcomes
- [ ] Independent error boundaries (one failure doesn't stop others)
- [ ] Progress visible in project tracking

## Technical Assumptions
1. Claude CLI at `/opt/homebrew/bin/claude` supports `--print` flag for non-interactive mode
2. Existing metrics.db schema can be extended (add provider_type column)
3. Model pricing in cost_calculator.py is current
4. Project tracking system can update existing project IDs

## Files to Create
- `src/runtime/agents/provider_manager.py` - Provider abstraction and detection
- `src/runtime/agents/cli_provider.py` - CLI provider implementations
- `src/runtime/agents/cost_estimator.py` - Pre-execution cost estimation
- `src/runtime/agents/agent_router.py` - Smart agent routing
- `src/runtime/agents/recovery_orchestrator.py` - Project recovery logic

## Files to Modify
- `src/runtime/agents/runtime.py` - Integrate provider manager
- `src/runtime/agents/metrics.py` - Add provider tracking fields
- `src/field/ensemble_ui/backend/main.py` - Expose cost/routing APIs
- `src/field/ensemble_ui/frontend/src/App.jsx` - Dashboard widgets

## Dependencies
- Claude CLI (`/opt/homebrew/bin/claude`) - confirmed available
- ChatGPT CLI (optional, detect if present)
- Existing ensemble infrastructure (runtime.py, metrics.py, etc.)
- SQLite database (~/.ensemble/metrics.db)

## Risks and Mitigations
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| CLI output format changes | High | Low | Parse flexibly, validate structure |
| CLI rate limiting | Medium | Medium | Implement backoff, fall back to API |
| Cost estimates significantly off | Medium | Medium | Calibrate with actual data |
| Recovery spawns fail | Medium | Medium | Independent boundaries, continue on error |

---

**Document Status**: Complete
**Created**: 2026-01-13
**Author**: Executive Director
**Version**: 1.0
**Project ID**: fcf1193e
