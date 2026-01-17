# Agent Type Reference Guide

## Quick Agent Selection Guide

Use this reference to select the correct agent type for your task and understand each agent's capabilities and limitations.

## Agent Hierarchy & Responsibilities

### Leadership Tier

#### Executive Director (`leadership/executive_director`)
**Role**: Top-level project orchestration and decision-making
**Capabilities**: 
- Project planning and oversight
- Resource allocation
- High-level decision making
- Cross-project coordination

**When to Use**:
- Starting new projects
- Major scope changes
- Resource conflicts
- Executive decisions needed

**Cannot Do**: Direct implementation, detailed technical work

---

#### Development Manager (`leadership/development_manager`)
**Role**: Implementation orchestration from requirements to delivery
**Capabilities**:
- Milestone planning
- Architecture coordination
- Task breakdown oversight
- Implementation coordination

**When to Use**:
- Managing implementation phases
- Coordinating multiple teams
- Milestone tracking
- Quality assurance oversight

**CRITICAL**: **NEVER** assign direct coding tasks
**Cannot Do**: Write code, direct implementation

---

#### System Architect (`leadership/system_architect`)
**Role**: Technical architecture design and system planning
**Capabilities**:
- Architecture design
- Technology stack decisions
- System integration planning
- Technical standards definition

**When to Use**:
- New system design
- Architecture decisions
- Technology selection
- System integration planning

**Cannot Do**: Implementation, project management

---

#### TDD Coordinator (`leadership/tdd_coordinator`)
**Role**: Test-driven development orchestration
**Capabilities**:
- TDD process management
- Testing strategy coordination
- Quality assurance oversight
- Test-first implementation coordination

**When to Use**:
- Implementation phases requiring TDD
- Quality-critical development
- Test strategy planning
- Code quality oversight

**Cannot Do**: Solo implementation without Section Techs/Leaders

---

### Coordination Tier

#### Backend Coordinator (`coordinators/backend_coordinator`)
**Role**: Backend development task planning and coordination
**Capabilities**:
- Backend task breakdown
- API design coordination
- Database planning
- Service architecture coordination

**When to Use**:
- Backend development planning
- API design phases
- Database design coordination
- Service integration planning

**CRITICAL**: **ONLY** for planning and coordination
**Cannot Do**: Direct implementation, frontend work

---

#### Frontend Coordinator (`coordinators/frontend_coordinator`)
**Role**: Frontend development task planning and coordination
**Capabilities**:
- Frontend task breakdown
- UI/UX coordination
- Component design planning
- Frontend architecture coordination

**When to Use**:
- Frontend development planning
- UI design coordination
- Component architecture planning
- User experience planning

**CRITICAL**: **ONLY** for planning and coordination
**Cannot Do**: Direct implementation, backend work

---

#### Test Coordinator (`coordinators/test_coordinator`)
**Role**: Testing strategy and test implementation planning
**Capabilities**:
- Test planning
- Testing strategy development
- Test case design coordination
- Quality assurance planning

**When to Use**:
- Test planning phases
- Testing strategy development
- Quality assurance coordination
- Test case design

**Cannot Do**: Direct test implementation without Section Techs

---

### Implementation Tier

#### Backend Section Leader (`section_leaders/backend_section_leader`)
**Role**: Backend implementation leadership and complex backend development
**Capabilities**:
- Complex backend implementation
- Team coordination
- Technical mentoring
- Architecture implementation

**When to Use**:
- Complex backend features
- Team leadership needed
- Architectural implementation
- Technical guidance required

**Can Implement**: Backend code, APIs, services

---

#### Frontend Section Leader (`section_leaders/frontend_section_leader`)
**Role**: Frontend implementation leadership and complex frontend development
**Capabilities**:
- Complex frontend implementation
- Component development
- UI framework implementation
- Frontend team coordination

**When to Use**:
- Complex frontend features
- Component architecture implementation
- UI framework setup
- Frontend team leadership

**Can Implement**: Frontend code, components, UI

---

#### Section Tech (`section_techs/section_tech`)
**Role**: Direct technical implementation across domains
**Capabilities**:
- Code implementation
- Feature development
- Bug fixes
- Technical task execution

**When to Use**:
- Direct implementation tasks
- Feature development
- Code writing
- Technical execution

**Can Implement**: Code in assigned domain

---

## Agent Selection Decision Matrix

| Task Type | Primary Agent | Secondary/Supporting | Never Use |
|-----------|--------------|---------------------|-----------|
| Project Planning | Executive Director | Development Manager | Section Techs |
| Architecture Design | System Architect | - | Coordinators |
| Task Breakdown | Coordinators (by domain) | Development Manager | Section Leaders |
| Implementation | Section Leaders/Techs | TDD Coordinator | Coordinators |
| Testing Strategy | Test Coordinator | TDD Coordinator | Frontend Coordinator |
| Code Writing | Section Leaders/Techs | - | Coordinators, Development Manager |
| Quality Oversight | TDD Coordinator | Development Manager | Section Techs |

## Common Mistakes to Avoid

### ❌ NEVER DO

1. **Development Manager for Direct Implementation**
   - ❌ `spawn_agent("leadership/development_manager", {task: "write user auth code"})`
   - ✅ `spawn_agent("leadership/tdd_coordinator", {problem: "user authentication system"})`

2. **Coordinators for Implementation**
   - ❌ `spawn_agent("coordinators/backend_coordinator", {task: "implement API endpoints"})`
   - ✅ `spawn_agent("section_leaders/backend_section_leader", {task: "implement API endpoints"})`

3. **Section Techs for Planning**
   - ❌ `spawn_agent("section_techs/section_tech", {task: "plan system architecture"})`
   - ✅ `spawn_agent("leadership/system_architect", {task: "plan system architecture"})`

4. **Skipping Architecture Phase**
   - ❌ Direct coordination → implementation
   - ✅ Requirements → Architecture → Coordination → Implementation

### ✅ CORRECT PATTERNS

1. **Implementation Flow**:
   ```
   Development Manager → System Architect → Coordinators → TDD Coordinator → Section Leaders/Techs
   ```

2. **Planning Flow**:
   ```
   Executive Director → Development Manager → Coordinators → Task Lists
   ```

3. **Quality Flow**:
   ```
   TDD Coordinator → Section Leaders/Techs → Test Results → Review
   ```

## Spawn Call Requirements

### Required Fields by Agent Type

#### Leadership Agents
```json
{
  "requirements_file": "path/to/requirements.md",
  "output_directory": "path/to/output",
  "project_name": "string"
}
```

#### Coordinators
```json
{
  "milestone": "milestone description",
  "architecture": "path/to/architecture.md", 
  "requirements": "path/to/requirements.md",
  "output_file": "path/to/output.md"
}
```

#### TDD Coordinator
```json
{
  "problem_description": "description of what to build",
  "output_directory": "where to put code",
  "test_directory": "where to put tests (optional)",
  "requirements_file": "path/to/requirements.md (optional)"
}
```

#### Section Leaders/Techs
```json
{
  "task_description": "specific implementation task",
  "input_files": ["array", "of", "input", "files"],
  "output_files": ["array", "of", "output", "files"],
  "requirements": "additional requirements (optional)"
}
```

## Validation Checklist

Before spawning any agent:

1. ✅ **Agent Type Exists**: Verify agent definition file exists
2. ✅ **Required Fields**: All required parameters provided
3. ✅ **Task Match**: Task matches agent capabilities
4. ✅ **Role Boundaries**: Agent has authority for assigned task
5. ✅ **Input Files**: All referenced files exist and are readable
6. ✅ **Output Paths**: Output directories exist or can be created
7. ✅ **No Placeholders**: All parameters have actual values, not placeholders

## Emergency Troubleshooting

### Spawn Failures
1. **Check agent type path**: Ensure correct path format
2. **Validate parameters**: Verify all required fields present
3. **Check file paths**: Ensure all referenced files exist
4. **Review capabilities**: Verify agent can perform requested task

### Role Violations
1. **Stop execution**: Don't attempt workarounds
2. **Reassign to correct agent**: Use reference guide
3. **Update workflow**: Adjust process to use proper agent types
4. **Report patterns**: Document recurring issues

### Workflow Breaks
1. **Identify missing step**: Check against standard workflow
2. **Spawn required agent**: Use proper agent for missing step  
3. **Maintain sequence**: Don't skip required handoffs
4. **Validate outputs**: Ensure each step produces expected results

## Quick Reference Cards

### Planning Phase Agents
- **Project Start**: Executive Director
- **Implementation Planning**: Development Manager  
- **Architecture**: System Architect
- **Task Breakdown**: Domain Coordinators

### Implementation Phase Agents
- **TDD Orchestration**: TDD Coordinator
- **Complex Implementation**: Section Leaders
- **Direct Implementation**: Section Techs
- **Quality Assurance**: TDD Coordinator + Test Coordinator

### When in Doubt
1. **Check this reference guide**
2. **Verify agent capabilities** 
3. **Follow workflow sequence**
4. **Ask for clarification** if unclear
5. **Never guess** - use the decision matrix