# Independent Project Generation System - Architecture

## Overview
This document outlines the architecture for enabling Ensemble to generate completely independent software projects with clear delineation between UI-initiated tasks and external independent projects.

## Problem Statement
Currently, Ensemble can work on tasks submitted via the UI, but there's no clear distinction between:
1. **UI-Initiated Tasks** - Modifications or additions to the Ensemble system itself
2. **Independent Projects** - Completely separate software applications that Ensemble generates

This creates confusion and potential for cross-contamination between system improvements and external deliverables.

## Solution Architecture

### 1. Project Source Classification

Every project will be tagged with a `project_source` field:

```python
class ProjectSource(Enum):
    UI_SUGGESTION = "ui_suggestion"      # From Ensemble UI for system improvements
    EXTERNAL_PROJECT = "external_project" # Independent project generation
    REPORT_FOLLOWUP = "report_followup"   # Follow-up from completed report
```

### 2. Output Directory Strategy

```
ensemble/
├── src/field/ensemble_ui/output/          # UI suggestions (system improvements)
│   ├── completed/                          # Completed system improvements
│   ├── <project-name>/                     # Active system improvement projects
│   └── ...
│
└── generated_projects/                     # External independent projects
    ├── <project-name>/                     # Each independent project
    │   ├── README.md
    │   ├── requirements.txt
    │   ├── src/
    │   ├── tests/
    │   └── docs/
    └── ...
```

### 3. Request Metadata Enhancement

Enhance the request tracking system to include:

```json
{
  "request_id": "abc123",
  "project_source": "external_project",
  "project_type": "independent_application",
  "output_directory": "/path/to/generated_projects/my-app",
  "isolation_level": "complete",
  "git_repository": {
    "initialized": true,
    "remote_url": null,
    "initial_commit": "abc123def"
  }
}
```

### 4. UI Enhancement

Add a **Project Type Selector** to the UI submission form:

```
┌─────────────────────────────────────────┐
│ Submit New Task                         │
├─────────────────────────────────────────┤
│                                         │
│ Project Type:                           │
│ ○ System Improvement                    │
│   (Improvements to Ensemble itself)     │
│                                         │
│ ● Independent Project                   │
│   (Generate a new standalone app)       │
│                                         │
│ Project Name: ________________          │
│                                         │
│ Description:                            │
│ ┌─────────────────────────────────────┐ │
│ │                                     │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Submit]                                │
└─────────────────────────────────────────┘
```

### 5. Executive Director Enhancement

Update `executive_director.md` to recognize project type and adjust behavior:

**For UI Suggestions:**
- Output to `src/field/ensemble_ui/output/<project-name>/`
- Can modify Ensemble codebase
- Create pending reviews for system changes

**For Independent Projects:**
- Output to `generated_projects/<project-name>/`
- Initialize as standalone git repository
- Generate complete project structure
- Include comprehensive documentation
- Never modify Ensemble codebase

### 6. Spawn Agent Tool Enhancement

```python
class SpawnAgentTool:
    def __init__(self, ..., project_source: ProjectSource = None):
        self.project_source = project_source
        
    def execute(self, agent_type: str, input_data: dict):
        # Propagate project_source to all child agents
        input_data['project_source'] = self.project_source
        input_data['output_directory'] = self._determine_output_dir(
            project_source=self.project_source,
            project_name=input_data.get('project_name')
        )
```

### 7. Activity Tracking Enhancement

Track project source in all activities:

```python
activity_tracker.record_request_started(
    request_id=request_id,
    prompt=problem_description,
    project_source=ProjectSource.EXTERNAL_PROJECT,
    output_directory="/path/to/generated_projects/my-app"
)
```

## Implementation Phases

### Phase 1: Core Infrastructure (This Phase)
- [ ] Create `ProjectSource` enum
- [ ] Update request tracking to include `project_source`
- [ ] Create output directory structure
- [ ] Update activity tracker schemas

### Phase 2: Backend Integration
- [ ] Update `AgentOrchestrator.spawn_executive_director()` to accept `project_source`
- [ ] Update `SpawnAgentTool` to propagate project source
- [ ] Add output directory determination logic
- [ ] Update Executive Director prompt to recognize project types

### Phase 3: UI Integration
- [ ] Add project type selector to submission form
- [ ] Update API endpoint to accept project type
- [ ] Add project source filter to timeline view
- [ ] Create "Generated Projects" tab in UI

### Phase 4: Documentation & Templates
- [ ] Create project generation guide
- [ ] Create independent project template
- [ ] Update user documentation
- [ ] Add example workflows

### Phase 5: Testing & Validation
- [ ] Test UI suggestion flow (existing behavior)
- [ ] Test independent project generation
- [ ] Verify output isolation
- [ ] Validate git repository initialization

## Key Design Decisions

### 1. Why Two Output Directories?
- **Clarity**: Users immediately know where to find system improvements vs. generated projects
- **Safety**: Prevents accidental modification of Ensemble codebase when generating external projects
- **Organization**: Clean separation of concerns

### 2. Why Project Source Enum?
- **Extensibility**: Easy to add new project types (e.g., `PLUGIN`, `EXTENSION`)
- **Type Safety**: Prevents invalid project type values
- **Consistency**: All agents and tools use the same classification system

### 3. Why Git Initialization for Independent Projects?
- **Best Practice**: Independent projects should be standalone repositories
- **Portability**: Users can immediately push to their own remote
- **History**: Complete project generation history from inception

## Data Flow

```
User Submits Task
       ↓
[UI: Project Type Selection]
       ↓
API: /api/generate-solution
  project_source = EXTERNAL_PROJECT
       ↓
AgentOrchestrator.spawn_executive_director()
  output_dir = generated_projects/<name>
       ↓
Executive Director
  - Reads project_source
  - Adjusts output strategy
  - Spawns appropriate agents
       ↓
Child Agents
  - Inherit project_source
  - Write to isolated output_dir
  - Never touch Ensemble codebase
       ↓
Project Complete
  - Git repository initialized
  - README.md generated
  - Complete standalone project
```

## Security Considerations

1. **Path Traversal Prevention**: Validate project names to prevent `../` attacks
2. **Output Isolation**: Strict separation between Ensemble and generated projects
3. **Permission Validation**: Agents cannot modify Ensemble when `project_source=EXTERNAL_PROJECT`

## Success Metrics

1. ✅ Users can clearly specify project type
2. ✅ Independent projects are completely isolated
3. ✅ No cross-contamination between system improvements and external projects
4. ✅ Generated projects are immediately usable standalone applications
5. ✅ Clear documentation for both workflow types

## Next Steps

1. Implement Phase 1 infrastructure changes
2. Update backend to support project source classification
3. Enhance UI with project type selector
4. Create comprehensive documentation
5. Test both workflows thoroughly
