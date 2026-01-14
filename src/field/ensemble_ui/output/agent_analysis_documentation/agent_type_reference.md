# Agent Type Quick Reference

## Overview
This document provides a quick reference for correct agent type usage in the ensemble system. **Always use full path format: `tier/agent_name`**

## Agent Hierarchy

```
Leadership Tier
  └── leadership/executive_director      (Meta-orchestrator)
  └── leadership/development_manager     (Implementation coordinator)

Coordination Tier (spawned by Development Manager)
  └── coordination/backend_coordinator   (Backend implementation)
  └── coordination/frontend_coordinator  (Frontend implementation)  
  └── coordination/tdd_coordinator       (Test-driven development)
  └── coordination/devops_coordinator    (DevOps/deployment)

Specialist Tier (spawned by Coordinators)
  └── specialist/system_architect        (Architecture design)
  └── specialist/backend_section_tech_lead
  └── specialist/frontend_section_tech_lead
  └── specialist/unit_test_lead
  └── specialist/integration_test_lead
  └── specialist/code_writer
  └── specialist/code_tester

Infrastructure Tier (spawned by Specialists)
  └── infrastructure/junior_developer
  └── infrastructure/code_reviewer
  └── infrastructure/documentation_writer
```

## Who Can Spawn Whom

| **Your Role** | **Can Spawn** |
|---------------|---------------|
| Executive Director | `leadership/development_manager` ONLY |
| Development Manager | `coordination/*`, `specialist/system_architect` |
| Backend Coordinator | `specialist/backend_section_tech_lead` |
| Frontend Coordinator | `specialist/frontend_section_tech_lead` |
| TDD Coordinator | `specialist/unit_test_lead`, `specialist/integration_test_lead` |
| Section Tech Leads | `infrastructure/junior_developer`, `infrastructure/code_reviewer` |

## Common Mistakes

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| `development_manager` | `leadership/development_manager` |
| `program_coordinator` | `leadership/development_manager` |
| `backend_lead` | `coordination/backend_coordinator` |
| `code_writer` (from ED) | Delegate to `leadership/development_manager` |
| `system_architect` (from ED) | Delegate to `leadership/development_manager` |

## Required Input Fields for Development Manager

```json
{
  "agent_type": "leadership/development_manager",
  "input_data": {
    "requirements_file": "/full/path/to/requirements.md",
    "output_directory": "/output/unique_project_name",
    "project_name": "Clear Project Name"
  }
}
```

**All three fields are REQUIRED.**

## Quick Validation Checklist

Before any `spawn_agent` call:
- [ ] Agent type has tier prefix (e.g., `leadership/`)
- [ ] You are authorized to spawn this agent type
- [ ] All required input fields provided
- [ ] Output directory is project-specific (not shared)
