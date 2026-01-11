# File Organization Plan

## Current State
The root directory contains 51+ files, making it difficult to find what's needed and distinguish between active code, documentation, utilities, and deprecated content.

## Proposed Structure

```
ensemble/
├── README.md                          # Main project readme
├── QUICKSTART.md                      # Getting started guide
├── requirements.md                    # Core project requirements
├── .env, .env.example, .gitignore    # Config files (keep in root)
│
├── src/                              # Source code (already exists)
│   ├── runtime/agents/               # Agent runtime
│   └── field/ensemble_ui/            # UI application
│
├── leadership/                       # Agent definitions (already exists)
├── coordinators/                     # Agent definitions (already exists)
├── developers/                       # Agent definitions (already exists)
├── testers/                          # Agent definitions (already exists)
├── designers/                        # Agent definitions (already exists)
│
├── docs/                             # Documentation (NEW)
│   ├── current/                      # Active documentation
│   │   ├── DIAGNOSTIC_REPORT.md
│   │   ├── COMPREHENSIVE_SYSTEM_REVIEW.md
│   │   ├── AGENT_REGISTRY.md
│   │   └── FUTURE_FEATURES.md
│   └── archive/                      # Historical documentation
│       ├── MILESTONE_*.md
│       ├── PIPELINE_*.md
│       ├── REFACTORING_*.md
│       └── ITERATIVE_IMPROVEMENT_PLAN.md
│
├── scripts/                          # Utility scripts (NEW)
│   ├── deployment/                   # Deployment scripts
│   │   ├── start_backend.sh
│   │   ├── start_frontend.sh
│   │   └── run_ensemble_ui.sh
│   ├── development/                  # Development utilities
│   │   ├── test_*.py
│   │   ├── create_model_selector.py
│   │   ├── update_agent_permissions.py
│   │   └── rename_agents.py
│   └── deprecated/                   # Old scripts no longer used
│       ├── cli_pipeline.py
│       ├── build_milestone2.py
│       ├── complete_milestone2_frontend.py
│       └── continue_ensemble.py
│
└── logs/                             # Log files (NEW)
    ├── cli_pipeline_run.log
    ├── ui_pipeline_run.log
    ├── milestone_0_pipeline_run.log
    └── model_selector_pipeline.log
```

## Categorization

### Keep in Root (6 files)
- README.md
- QUICKSTART.md
- requirements.md
- .env, .env.example
- .gitignore, .clinerules

### docs/current/ (Active Documentation - 5 files)
- DIAGNOSTIC_REPORT.md
- COMPREHENSIVE_SYSTEM_REVIEW.md
- AGENT_REGISTRY.md
- FUTURE_FEATURES.md
- SELF_IMPROVEMENT_TEMPLATE.md

### docs/archive/ (Historical Documentation - 15 files)
- MILESTONE_*.md (4 files)
- *_REQUIREMENTS.md (3 files: CLI, MODEL_SELECTOR, MILESTONE_0)
- PIPELINE_*.md (2 files)
- AGENT_*.md (2 files: PIPELINE_LEARNINGS, SWARM_ANALYSIS)
- COMPREHENSIVE_REVIEW.md
- REFACTORING_ANALYSIS.md
- ITERATIVE_IMPROVEMENT_PLAN.md
- NAMING_REFACTOR_PLAN.md
- FIX_COORDINATION_ISSUE.md

### scripts/deployment/ (Active Deployment Scripts - 3 files)
- start_backend.sh
- start_frontend.sh
- run_ensemble_ui.sh

### scripts/development/ (Active Development Scripts - 7 files)
- test_executive_director.py
- test_full_ensemble.py
- test_logistics_manager.py
- test_rogue_detection.py
- create_model_selector.py
- update_agent_permissions.py
- rename_agents.py

### scripts/deprecated/ (Old/Unused Scripts - 10 files)
- cli_pipeline.py
- build_milestone2.py
- complete_milestone2_frontend.py
- complete_ui_pipeline.py
- continue_ensemble.py
- milestone_0_pipeline.py
- add_fail_fast_rules.py
- analyze_milestone.py
- cleanup_drum_corps.sh
- consolidate_agents.sh

### logs/ (Log Files - 4 files)
- cli_pipeline_run.log
- ui_pipeline_run.log
- milestone_0_pipeline_run.log
- model_selector_pipeline.log

### Move to docs/ (Already Processed - 3 files)
- architecture.md
- backend_tasks.md
- test_tasks.md

## Implementation Steps

1. Create directory structure
2. Move files to appropriate locations
3. Update any hardcoded paths in scripts
4. Update .gitignore if needed
5. Commit changes

## Benefits

- **Clarity**: Easy to find active vs historical content
- **Maintainability**: Clear separation of concerns
- **Onboarding**: New developers can quickly understand project structure
- **Git History**: Cleaner root directory makes git status more useful
