# Architecture Document: Task Recovery Analysis Implementation

**Project ID**: 3f1c6153  
**System Architect**: Task Recovery Analysis Implementation  
**Date**: 2026-01-13

---

## 1. Executive Summary

This document defines the architecture for a task recovery orchestration system that systematically restarts 10 stalled/incomplete projects. The system parses recovery data, structures it by priority, and orchestrates Executive Director spawning for each project requiring recovery.

**Architecture Pattern**: Pipeline Architecture with Sequential Orchestration
**Technology Stack**: Python 3.x, JSON data interchange, Markdown reporting
**Core Principle**: Independent error boundaries - one failure doesn't cascade to others

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Recovery Orchestrator                     │
│                    (Main Entry Point)                        │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐       ┌──────────────────┐
│  Data Parser  │       │  Action Executor │
│   Module      │──────▶│     Module       │
└───────────────┘       └──────────────────┘
        │                       │
        │                       ├──▶ Priority 1 (in_progress)
        │                       ├──▶ Priority 2 (todo)
        │                       └──▶ Priority 3 (no tasks)
        │                       
        ▼                       ▼
┌───────────────┐       ┌──────────────────┐
│ Structured    │       │  Recovery Report │
│ Recovery Data │       │   Generator      │
└───────────────┘       └──────────────────┘
```

### 2.2 Component Architecture

#### **Component 1: Recovery Data Parser**
**Purpose**: Extract and structure recovery data from task_recovery_analysis.md

**Responsibilities**:
- Read task_recovery_analysis.md
- Parse project IDs, task IDs, status, and recommended actions
- Validate data completeness (all 10 projects)
- Categorize by priority (1, 2, 3)
- Generate structured JSON output

**Inputs**: 
- task_recovery_analysis.md (source document)

**Outputs**:
- recovery_actions/priority1_in_progress.json
- recovery_actions/priority2_todo.json
- recovery_actions/priority3_no_tasks.json

**Data Structure**:
```python
RecoveryProject = {
    "project_id": str,
    "project_name": str,
    "task_id": str | None,
    "status": str,
    "issue": str,
    "action": str,
    "priority": int,
    "assigned_to": str | None
}
```

#### **Component 2: Action Mapper**
**Purpose**: Map recovery priorities to specific agent invocations

**Responsibilities**:
- Determine which agent type to spawn per project
- Generate proper input data format for Executive Director
- Map actions:
  - Priority 1 → Development Manager restart
  - Priority 2 → Appropriate coordinator (TDD/Backend/Frontend)
  - Priority 3 → Requirements phase initiation

**Inputs**: Structured recovery data (JSON)

**Outputs**: Executive Director invocation specifications

**Action Mapping Logic**:
```python
def map_recovery_action(project: RecoveryProject) -> InvocationSpec:
    if project.priority == 1:
        return development_manager_restart_spec(project)
    elif project.priority == 2:
        return coordinator_start_spec(project)
    else:  # priority == 3
        return requirements_phase_spec(project)
```

#### **Component 3: Recovery Executor**
**Purpose**: Execute recovery actions by spawning Executive Directors

**Responsibilities**:
- Process projects sequentially by priority
- Generate proper Executive Director input for each project
- Spawn Executive Director agents (via spawn_agent tool)
- Handle errors with independent boundaries
- Log progress and outcomes

**Inputs**: Invocation specifications from Action Mapper

**Outputs**: 
- Recovery execution logs
- Success/failure tracking per project

**Error Handling**:
- Try/catch around each spawn_agent call
- Continue processing on individual failures
- Log errors without stopping overall process

#### **Component 4: Progress Tracker**
**Purpose**: Track recovery progress and generate reporting data

**Responsibilities**:
- Log each recovery attempt with timestamp
- Track success/failure per project
- Aggregate statistics
- Provide data for recovery report

**Data Structure**:
```python
RecoveryResult = {
    "project_id": str,
    "project_name": str,
    "action_taken": str,
    "timestamp": datetime,
    "status": "success" | "failed" | "error",
    "error_message": str | None,
    "executive_director_spawned": bool
}
```

#### **Component 5: Report Generator**
**Purpose**: Create comprehensive recovery report

**Responsibilities**:
- Aggregate recovery results
- Generate recovery_report.md
- Summarize success/failure rates
- Document errors and recommendations

**Outputs**: recovery_report.md

---

## 3. Data Flow

### 3.1 Overall Pipeline

```
task_recovery_analysis.md
        ↓
[Data Parser Module]
        ↓
Structured JSON (priority1.json, priority2.json, priority3.json)
        ↓
[Action Mapper]
        ↓
Executive Director Invocation Specs
        ↓
[Recovery Executor] → spawn_agent(executive_director, ...)
        ↓
Recovery Results (logged)
        ↓
[Report Generator]
        ↓
recovery_report.md
```

### 3.2 Per-Project Recovery Flow

```
1. Load project data from structured JSON
2. Map to recovery action
3. Generate Executive Director input:
   {
     "user_vision": "Complete [project_name]",
     "output_directory": "[original_project_path]",
     "context": {
       "project_id": "...",
       "task_id": "...",
       "recovery_action": "...",
       "status": "..."
     }
   }
4. Spawn Executive Director
5. Log result
6. Continue to next project
```

---

## 4. Module Structure

```
recovery_orchestration/
├── __init__.py
├── parser.py              # RecoveryDataParser class
├── mapper.py              # ActionMapper class
├── executor.py            # RecoveryExecutor class
├── tracker.py             # ProgressTracker class
├── reporter.py            # ReportGenerator class
└── models.py              # Data models (RecoveryProject, RecoveryResult, etc.)

main.py                    # Entry point - orchestrates the pipeline
```

---

## 5. Class Design

### RecoveryDataParser
```python
class RecoveryDataParser:
    def __init__(self, input_file: str):
        self.input_file = input_file
        
    def parse(self) -> List[RecoveryProject]:
        """Parse task_recovery_analysis.md and extract projects"""
        
    def validate(self, projects: List[RecoveryProject]) -> bool:
        """Validate that all 10 projects are present"""
        
    def categorize_by_priority(self, projects: List[RecoveryProject]) -> Dict[int, List[RecoveryProject]]:
        """Group projects by priority (1, 2, 3)"""
        
    def save_structured_data(self, categorized: Dict[int, List[RecoveryProject]], output_dir: str):
        """Save to JSON files"""
```

### ActionMapper
```python
class ActionMapper:
    def map_action(self, project: RecoveryProject) -> dict:
        """Map project to Executive Director invocation spec"""
        
    def _priority1_spec(self, project: RecoveryProject) -> dict:
        """Generate spec for in_progress tasks"""
        
    def _priority2_spec(self, project: RecoveryProject) -> dict:
        """Generate spec for todo tasks"""
        
    def _priority3_spec(self, project: RecoveryProject) -> dict:
        """Generate spec for no-task projects"""
```

### RecoveryExecutor
```python
class RecoveryExecutor:
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
        
    def execute_recovery(self, projects: List[RecoveryProject]):
        """Execute recovery for all projects sequentially"""
        
    def _spawn_executive_director(self, invocation_spec: dict) -> RecoveryResult:
        """Spawn Executive Director with error handling"""
```

### ProgressTracker
```python
class ProgressTracker:
    def __init__(self):
        self.results: List[RecoveryResult] = []
        
    def log_attempt(self, project_id: str, action: str):
        """Log recovery attempt"""
        
    def log_result(self, result: RecoveryResult):
        """Log recovery result"""
        
    def get_statistics(self) -> dict:
        """Get success rate, failure count, etc."""
```

### ReportGenerator
```python
class ReportGenerator:
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
        
    def generate_report(self, output_file: str):
        """Generate comprehensive recovery report"""
```

---

## 6. Error Handling Strategy

### Independent Error Boundaries
- Each project recovery attempt wrapped in try/except
- Failures logged but don't stop overall process
- Continue to next project on error

### Error Categories
1. **Parse Errors**: Missing project data, invalid format
   - Log error, skip project
2. **Mapping Errors**: Unable to determine action
   - Log error, use default action or skip
3. **Spawn Errors**: spawn_agent fails
   - Log error, mark as failed, continue
4. **System Errors**: File I/O, permissions
   - Log error, attempt to continue

### Logging Strategy
- Timestamp all events
- Log levels: INFO, WARNING, ERROR
- Log to file: recovery_execution.log
- Include in recovery report

---

## 7. Configuration

### Constants
```python
PRIORITIES = {
    1: "in_progress (stalled)",
    2: "todo (not started)",
    3: "no tasks (planning stalled)"
}

EXPECTED_PROJECT_COUNT = 10

ACTION_TYPES = {
    "restart_dev_manager": "Restart Development Manager",
    "start_tdd_coordinator": "Start TDD Coordinator",
    "start_coordinator": "Start appropriate coordinator",
    "start_requirements": "Start requirements phase"
}
```

### File Paths
```python
INPUT_FILE = "task_recovery_analysis.md"
OUTPUT_DIR = "recovery_actions/"
REPORT_FILE = "recovery_report.md"
LOG_FILE = "recovery_execution.log"
```

---

## 8. Testing Strategy

### Unit Tests
- Test RecoveryDataParser: parsing accuracy, validation
- Test ActionMapper: correct action mapping per priority
- Test ProgressTracker: logging, statistics calculation
- Test ReportGenerator: report structure, data accuracy

### Integration Tests
- Test full pipeline with mock spawn_agent
- Verify all 10 projects processed
- Verify error handling (inject failures)
- Verify report generation

### Validation Tests
- Ensure all 10 projects extracted
- Ensure priority categorization correct (3, 5, 2)
- Ensure no duplicate project IDs
- Ensure all required fields present

---

## 9. Security & Constraints

### Constraints
1. **No manual code writing by Executive Director**
   - Recovery orchestrator delegates to spawned agents
   - No implementation code in recovery system
   
2. **Maintain original project structures**
   - Don't modify existing projects
   - Use original project IDs and paths
   
3. **Sequential processing only**
   - No parallel execution initially
   - Simpler error handling and logging

### Security
- Validate all project IDs before spawning
- Sanitize file paths to prevent path traversal
- Log all actions for audit trail

---

## 10. Performance Considerations

### Expected Load
- 10 projects total
- Sequential processing
- Estimated 1-2 minutes per project spawn
- Total execution: 10-20 minutes

### Optimization Opportunities (Future)
- Parallel processing with thread pool
- Caching of parsed data
- Incremental recovery (resume from last failure)

---

## 11. Future Enhancements

1. **Recovery Resume**: Ability to resume from last successful recovery
2. **Parallel Execution**: Process multiple projects concurrently
3. **Real-time Monitoring**: UI/dashboard for recovery progress
4. **Recovery Patterns Library**: Reusable recovery strategies
5. **Automated Re-attempts**: Retry failed recoveries automatically

---

## 12. Dependencies

### External Dependencies
- Python 3.x standard library (json, logging, datetime)
- Existing project tracking system
- spawn_agent tool (from ensemble system)

### Internal Dependencies
- task_recovery_analysis.md (input document)
- Project tracking system API
- Executive Director agent interface

---

## 13. Deployment

### Execution
```bash
python main.py \
  --input task_recovery_analysis.md \
  --output-dir recovery_actions/ \
  --report recovery_report.md
```

### Verification
1. Check recovery_actions/ directory for JSON files
2. Review recovery_execution.log for errors
3. Read recovery_report.md for results
4. Verify 10/10 projects processed

---

## Document Control

**Version**: 1.0  
**Status**: Approved  
**Architect**: System Architect  
**Last Updated**: 2026-01-13
