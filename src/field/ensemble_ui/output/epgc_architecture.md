# Ensemble Project Generation Capability - Architecture

## Overview
This document outlines the architecture for enabling Ensemble to generate completely new, independent software applications with standardized naming conventions and comprehensive documentation.

## Current System Architecture

### Agent Hierarchy
```
┌─────────────────────────────────────────────────────────┐
│                    LEADERSHIP                            │
│  ┌─────────────────────────────────────────────────────┐│
│  │ executive_director.md - Strategic oversight          ││
│  │ development_manager.md - Project execution           ││
│  │ system_architect.md - Technical architecture         ││
│  │ tdd_coordinator.md - TDD process orchestration       ││
│  └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│                   COORDINATORS                           │
│  ┌─────────────────────────────────────────────────────┐│
│  │ backend_coordinator.md - Backend task breakdown      ││
│  │ frontend_coordinator.md - Frontend task breakdown    ││
│  │ test_coordinator.md - Test task breakdown            ││
│  └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│                   DEVELOPERS                             │
│  ┌─────────────────────────────────────────────────────┐│
│  │ backend_lead.md - Backend section leadership         ││
│  │ backend_developer.md - Backend implementation        ││
│  │ frontend_lead.md - Frontend section leadership       ││
│  │ frontend_developer.md - Frontend implementation      ││
│  └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│                     TESTERS                              │
│  ┌─────────────────────────────────────────────────────┐│
│  │ unit_test_lead.md - Unit test leadership             ││
│  │ unit_test_writer.md - Unit test implementation       ││
│  │ integration_test_lead.md - Integration test lead     ││
│  │ integration_test_writer.md - Integration test impl   ││
│  └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│                    DESIGNERS                             │
│  ┌─────────────────────────────────────────────────────┐│
│  │ style_developer.md - CSS/styling implementation      ││
│  └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│                     SUPPORT                              │
│  ┌─────────────────────────────────────────────────────┐│
│  │ drill_writer.md - ⚠️ NEEDS RENAME → documentation_writer.md ││
│  │ logistics_manager.md - ⚠️ NEEDS RENAME → project_manager.md ││
│  │ visual_tech.md - ⚠️ NEEDS RENAME → architect_assistant.md   ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Project Generation Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    PROJECT GENERATION FLOW                      │
└────────────────────────────────────────────────────────────────┘

User Input (requirements.md)
         │
         ▼
┌─────────────────────┐
│ Executive Director  │ ← Entry point for new projects
│ - Validates input   │
│ - Spawns managers   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Development Manager │ ← Drives implementation
│ - Creates milestones│
│ - Coordinates teams │
└─────────┬───────────┘
          │
          ├──────────────────────────────────────┐
          │                                      │
          ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│  System Architect   │              │    Coordinators     │
│ - Architecture docs │              │ - Task breakdown    │
│ - Tech decisions    │              │ - Work packages     │
└─────────────────────┘              └─────────┬───────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │   TDD Coordinator   │
                                    │ - Orchestrates TDD  │
                                    │ - Spawns dev teams  │
                                    └─────────┬───────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
          ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
          │ Backend Lead │          │Frontend Lead │          │ Test Leads   │
          └───────┬──────┘          └───────┬──────┘          └───────┬──────┘
                  │                         │                         │
                  ▼                         ▼                         ▼
          ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
          │   Backend    │          │  Frontend    │          │    Test      │
          │  Developers  │          │  Developers  │          │   Writers    │
          └──────────────┘          └──────────────┘          └──────────────┘
                  │                         │                         │
                  └─────────────────────────┼─────────────────────────┘
                                            │
                                            ▼
                                    ┌─────────────────────┐
                                    │   OUTPUT DIRECTORY  │
                                    │ - Isolated project  │
                                    │ - Tests + Code      │
                                    │ - Documentation     │
                                    └─────────────────────┘
```

## Key Components

### 1. Agent Runtime (`src/runtime/agents/`)
- **agent_runtime.py**: Core execution engine
- **spawn_agent()**: Tool for creating child agents
- **File operations**: read_file, write_file, run_command

### 2. Agent Definitions (Root folders)
- **leadership/**: Strategic and management agents
- **coordinators/**: Task breakdown specialists
- **developers/**: Code implementation agents
- **testers/**: Test writing agents
- **designers/**: UI/styling agents
- **support/**: Supporting utilities (needs rename)

### 3. Output Isolation
Projects are generated in a specified `output_directory`, ensuring:
- No pollution of Ensemble codebase
- Complete project isolation
- Configurable output paths

## Naming Standards

### Current State vs. Target State

| Category | Current | Target | Status |
|----------|---------|--------|--------|
| Leadership | executive_director.md | executive_director.md | ✅ OK |
| Leadership | development_manager.md | development_manager.md | ✅ OK |
| Leadership | system_architect.md | system_architect.md | ✅ OK |
| Leadership | tdd_coordinator.md | tdd_coordinator.md | ✅ OK |
| Coordinators | backend_coordinator.md | backend_coordinator.md | ✅ OK |
| Coordinators | frontend_coordinator.md | frontend_coordinator.md | ✅ OK |
| Coordinators | test_coordinator.md | test_coordinator.md | ✅ OK |
| Developers | backend_lead.md | backend_lead.md | ✅ OK |
| Developers | backend_developer.md | backend_developer.md | ✅ OK |
| Developers | frontend_lead.md | frontend_lead.md | ✅ OK |
| Developers | frontend_developer.md | frontend_developer.md | ✅ OK |
| Testers | unit_test_lead.md | unit_test_lead.md | ✅ OK |
| Testers | unit_test_writer.md | unit_test_writer.md | ✅ OK |
| Testers | integration_test_lead.md | integration_test_lead.md | ✅ OK |
| Testers | integration_test_writer.md | integration_test_writer.md | ✅ OK |
| Designers | style_developer.md | style_developer.md | ✅ OK |
| Support | drill_writer.md | documentation_writer.md | ⚠️ RENAME |
| Support | logistics_manager.md | project_manager.md | ⚠️ RENAME |
| Support | visual_tech.md | architect_assistant.md | ⚠️ RENAME |

## Technical Architecture

### Spawn Path Convention
```
spawn_agent("<category>/<agent_name>", {input_data})
```

Examples:
- `spawn_agent("leadership/development_manager", {...})`
- `spawn_agent("coordinators/backend_coordinator", {...})`
- `spawn_agent("developers/backend_lead", {...})`

### Input/Output Contracts

#### Executive Director Input
```json
{
  "requirements_file": "path/to/requirements.md",
  "output_directory": "path/to/output",
  "project_name": "string"
}
```

#### Development Manager Input
```json
{
  "requirements_file": "path/to/requirements.md",
  "output_directory": "path/to/output",
  "project_name": "string"
}
```

#### Coordinator Input
```json
{
  "milestone": "description of milestone",
  "architecture": "path/to/architecture.md",
  "requirements": "path/to/requirements.md",
  "output_file": "path/to/tasks.md"
}
```

#### TDD Coordinator Input
```json
{
  "problem_description": "what to build",
  "output_directory": "where to put code",
  "test_directory": "where to put tests (optional)",
  "requirements_file": "path/to/requirements.md (optional)"
}
```

## Deliverables for This Project

### Milestone 1: Naming Audit
- `NAMING_AUDIT_REPORT.md` - Comprehensive audit results

### Milestone 2: Naming Standardization
- Renamed support/ agents
- Updated spawn path references
- Verification tests

### Milestone 3: Feasibility Assessment
- `FEASIBILITY_ASSESSMENT.md` - Can Ensemble generate new projects?
- Gap analysis (if any)

### Milestone 4: Documentation
- `PROJECT_GENERATION_GUIDE.md` - Usage documentation
- Updated README if needed

## Risk Mitigation

### Breaking Changes
- Run all tests after any rename
- Update all spawn path references
- Maintain backward compatibility where possible

### Documentation Gaps
- Create clear step-by-step guides
- Include troubleshooting sections
- Provide example workflows

## Success Metrics
1. Zero drum corps references in active agent files
2. All support/ agents renamed to industry standards
3. PROJECT_GENERATION_GUIDE.md enables 10-minute onboarding
4. FEASIBILITY_ASSESSMENT.md provides clear yes/no answer
