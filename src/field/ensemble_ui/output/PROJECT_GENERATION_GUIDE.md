# Ensemble Project Generation Guide
## How to Generate New Software Applications with Ensemble

---

## Quick Start (5 minutes)

### Step 1: Create Your Requirements File

Create a `requirements.md` file describing your project:

```markdown
# My New Application - Requirements

## Project Name
My New Application

## Vision Statement
A brief description of what this application does.

## Objectives
1. First major objective
2. Second major objective

## Scope

### In Scope
- Feature 1
- Feature 2

### Out of Scope
- Things you're not building

## Technical Constraints
- Python 3.9+ / React 18+
- PostgreSQL database
- REST API

## Requirements

### Functional Requirements
- **FR-1**: User can do X
- **FR-2**: System displays Y

### Non-Functional Requirements
- **NFR-1**: Response time < 200ms
- **NFR-2**: Support 100 concurrent users

## Success Criteria
1. All tests pass
2. Documentation complete
```

### Step 2: Run Ensemble

```bash
# Set up environment
cd /path/to/ensemble
source venv/bin/activate

# Run with Executive Director
python -m src.cli.main generate \
  --requirements /path/to/your/requirements.md \
  --output /path/to/new_project \
  --project-name "My New Application"
```

Or using Python directly:

```python
from src.runtime.agents.runtime import AgentRuntime

runtime = AgentRuntime()
result = runtime.run_agent(
    agent_path="leadership/executive_director",
    input_data={
        "requirements_file": "/path/to/requirements.md",
        "output_directory": "/path/to/new_project",
        "project_name": "My New Application"
    }
)
```

### Step 3: Wait for Completion

Ensemble will:
1. Analyze your requirements
2. Create project milestones
3. Design architecture
4. Break down tasks
5. Implement code using TDD
6. Generate documentation

**Typical completion time**: 30 minutes to 2 hours depending on project size.

---

## Detailed Guide

### Understanding the Agent Hierarchy

```
Executive Director
    └── Receives your requirements, validates, and spawns Development Manager
    
Development Manager
    └── Creates milestones, spawns System Architect and Coordinators
    
System Architect
    └── Designs architecture, defines project structure
    
Coordinators (Backend, Frontend, Test)
    └── Break milestones into implementable tasks
    
TDD Coordinator
    └── Orchestrates test-driven development cycle
    
Leads & Developers
    └── Write actual code following TDD (test first, then implement)
    
Testers
    └── Write comprehensive test suites
```

### Input Format

Your requirements file should follow this structure:

```markdown
# [Project Name] - Requirements

## Project Name
[Name of your project]

## Vision Statement
[1-2 sentences describing the purpose]

## Background
[Optional: Context and why this project exists]

## Objectives
### Primary Objectives
1. [Main goal 1]
2. [Main goal 2]

### Secondary Objectives
- [Nice to have 1]
- [Nice to have 2]

## Scope
### In Scope
- [Feature/component 1]
- [Feature/component 2]

### Out of Scope
- [What you're NOT building]

## Technical Constraints
- [Technology requirement 1]
- [Technology requirement 2]

## Requirements
### Functional Requirements
- **FR-1.1**: [Description]
- **FR-1.2**: [Description]

### Non-Functional Requirements
- **NFR-1**: [Performance/Security/etc.]

## Success Criteria
1. [Measurable criterion 1]
2. [Measurable criterion 2]

## Deliverables
1. [Output 1]
2. [Output 2]

## Assumptions
- [Assumption 1]
- [Assumption 2]

## Dependencies
- [External dependency 1]
```

### Output Structure

After generation, your project directory will contain:

```
new_project/
├── src/                    # Source code
│   ├── backend/           # Python backend (if applicable)
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── ...
│   └── frontend/          # React frontend (if applicable)
│       ├── src/
│       │   ├── App.tsx
│       │   └── ...
│       └── package.json
├── tests/                  # Test suite
│   ├── unit/
│   └── integration/
├── docs/                   # Documentation
│   ├── architecture.md
│   ├── api.md
│   └── user_guide.md
├── requirements.md         # Your original requirements
├── milestones.md          # Generated milestones
├── README.md              # Project README
└── ...
```

---

## Configuration Options

### Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="your-api-key"

# Optional
export ENSEMBLE_LOG_LEVEL="DEBUG"
export ENSEMBLE_MAX_ITERATIONS="100"
export ENSEMBLE_TIMEOUT="3600"
```

### Custom Agent Behavior

You can customize agent behavior by modifying agent definition files in:
- `leadership/` - Strategic agents
- `coordinators/` - Task breakdown agents
- `developers/` - Implementation agents
- `testers/` - Testing agents

---

## Best Practices

### Writing Good Requirements

1. **Be Specific**: "Users can log in with email/password" > "Users can authenticate"
2. **Be Measurable**: Include acceptance criteria
3. **Prioritize**: Mark requirements as must-have vs. nice-to-have
4. **Include Constraints**: Tech stack, performance requirements

### Project Size Guidelines

| Project Type | Recommended Scope |
|--------------|-------------------|
| Prototype | 3-5 features, 1 milestone |
| Small App | 5-10 features, 2-3 milestones |
| Medium App | 10-20 features, 3-5 milestones |
| Large App | Consider breaking into phases |

### Common Pitfalls

1. **Vague requirements**: Leads to ambiguous implementation
2. **Too many features**: Start small, iterate
3. **Missing constraints**: Be explicit about tech stack
4. **No success criteria**: How do you know it's done?

---

## Troubleshooting

### Common Issues

#### "Agent not found" Error
```
Error: Could not find agent: coordinators/backend_coordinator
```
**Solution**: Ensure all agent files exist in the correct directories.

#### "Timeout" Error
```
Error: Agent execution timed out after 3600 seconds
```
**Solution**: Increase timeout or reduce project scope.

#### "API Rate Limit" Error
```
Error: Rate limit exceeded
```
**Solution**: Wait and retry, or reduce parallelism.

### Getting Help

1. Check agent output logs in the output directory
2. Review individual agent status files
3. Examine the `implementation_status.md` if present

---

## Examples

### Example 1: Simple API

```markdown
# Todo API - Requirements

## Project Name
Todo API

## Vision Statement
A simple REST API for managing todo items.

## Objectives
1. CRUD operations for todos
2. User authentication
3. API documentation

## Technical Constraints
- Python 3.9+
- FastAPI framework
- SQLite database

## Functional Requirements
- **FR-1**: Create todo with title and description
- **FR-2**: List all todos for a user
- **FR-3**: Update todo status
- **FR-4**: Delete todo

## Success Criteria
1. All CRUD endpoints working
2. 90%+ test coverage
3. OpenAPI documentation generated
```

### Example 2: Full-Stack App

```markdown
# Blog Platform - Requirements

## Project Name
Blog Platform

## Vision Statement
A modern blog platform with React frontend and Python backend.

## Objectives
1. User can create and publish blog posts
2. Readers can view and comment on posts
3. Admin can moderate content

## Technical Constraints
- Python 3.9+ / FastAPI backend
- React 18+ / TypeScript frontend
- PostgreSQL database

## Functional Requirements
- **FR-1**: User registration and login
- **FR-2**: Create/edit/delete blog posts
- **FR-3**: Comment on posts
- **FR-4**: Search posts by title/content

## Success Criteria
1. All user stories implemented
2. Responsive design
3. 85%+ test coverage
```

---

## Reference

### Agent Input/Output Contracts

#### Executive Director
**Input**:
```json
{
  "requirements_file": "string - path to requirements.md",
  "output_directory": "string - where to create project",
  "project_name": "string - name of the project"
}
```
**Output**: Project completion status

#### Development Manager
**Input**:
```json
{
  "requirements_file": "string - path to requirements.md",
  "output_directory": "string - project directory",
  "project_name": "string - name of the project"
}
```
**Output**: Milestone completion status

#### TDD Coordinator
**Input**:
```json
{
  "problem_description": "string - what to implement",
  "output_directory": "string - where to put code",
  "test_directory": "string - where to put tests (optional)",
  "requirements_file": "string - path to requirements (optional)"
}
```
**Output**: Implementation completion status

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-10 | Initial guide |

---

*This guide is part of the Ensemble Project Generation Capability (EPGC)*
