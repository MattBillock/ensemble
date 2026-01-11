# Ensemble CLI - Interactive Agent Interface Requirements

## Project Vision
Create an interactive command-line interface (CLI) tool that allows users to submit problems to the Ensemble multi-agent system, monitor agent execution in real-time, query status, view results, and debug agent behavior.

## Core Objectives
1. Provide intuitive problem submission workflow
2. Display real-time agent execution status
3. Visualize agent hierarchy and progress
4. Enable debugging and troubleshooting
5. Support both interactive and non-interactive modes
6. Integrate seamlessly with existing Ensemble agent runtime

## Key Features

### 1. Problem Submission
- Interactive mode: Prompt user for problem description, context, constraints
- File mode: Accept requirements from .md or .txt file
- Quick mode: One-line problem submission
- Validation: Check problem description is sufficient before spawning agents

### 2. Real-Time Monitoring
- Live agent status display (which agents are running)
- Agent hierarchy tree view (parent-child relationships)
- Progress indicators for each agent
- Iteration count tracking
- Tool usage logging (what tools each agent is calling)

### 3. Status Queries
- Current execution status (running/complete/failed)
- Agent hierarchy snapshot
- Detailed agent information (model, iterations, permissions)
- Deliverables list (files created so far)
- Error history

### 4. Results Display
- Final execution summary
- All deliverables with file paths
- Success/failure status
- Execution metrics (time, API calls, cost estimate)
- Recommendations or next steps

### 5. Debug Mode
- Verbose logging of all agent interactions
- API request/response inspection
- Agent reasoning display (thinking, tool calls)
- State inspection at any point
- Ability to pause/resume execution
- Manual intervention capability

### 6. Session Management
- Save session state for recovery
- Resume interrupted sessions
- Session history (past executions)
- Export session logs

## User Experience

### Interactive Mode Flow
```
$ ensemble
Welcome to Ensemble - Multi-Agent Development System

What would you like to build? (or type 'help' for options)
> I want to create a REST API for managing tasks

Got it! Let me gather some details...

What's your desired tech stack? (or press Enter for auto-selection)
> Python FastAPI

Where should I create the project?
> ./task-api

Output directory: ./task-api
Tech stack: Python FastAPI
Problem: Create a REST API for managing tasks

Ready to start? (y/n)
> y

🚀 Spawning Executive Director...
├─ Executive Director [running] iteration 1/20
│  └─ Tool: write_file → requirements.md
├─ Executive Director [running] iteration 2/20
│  └─ Tool: spawn_agent → Development Manager
   ├─ Development Manager [running] iteration 1/100
   │  └─ Tool: spawn_agent → System Architect
      └─ System Architect [running] iteration 1/15
         └─ Tool: write_file → architecture.md
...

✅ Execution complete!

📦 Deliverables:
  - ./task-api/requirements.md
  - ./task-api/architecture.md
  - ./task-api/backend/main.py
  - ./task-api/backend/models.py
  - ./task-api/tests/test_main.py

💬 Summary:
Created a REST API for task management with FastAPI, SQLAlchemy models,
CRUD endpoints, and comprehensive test coverage.

Next steps:
  - Review generated code
  - Run tests: pytest
  - Start server: uvicorn main:app --reload
```

### Quick Mode
```
$ ensemble --quick "build a CLI calculator in Python"
🚀 Processing: build a CLI calculator in Python
...
✅ Complete! See ./calculator/
```

### File Mode
```
$ ensemble --requirements ./my-project-requirements.md --output ./my-project
🚀 Processing requirements from ./my-project-requirements.md
...
```

### Status Check
```
$ ensemble status
📊 Current Execution: task-api

Status: Running
Phase: Implementation
Active Agents: 3
  └─ Executive Director → Development Manager → Frontend Developer

Progress: 65% (estimated)
Elapsed: 2m 34s

Recent Activity:
  [03:42:15] Frontend Developer: Creating component Dashboard.jsx
  [03:42:03] Backend Developer: Implementing auth middleware
  [03:41:58] Unit Test Writer: Writing tests for user model
```

### Debug Mode
```
$ ensemble debug --session task-api
🐛 Debug Mode - Session: task-api

[Agent: Frontend Developer] Iteration 3/10
Thinking: I need to create the Dashboard component with props for...
Tool Call: write_file
  file_path: frontend/Dashboard.jsx
  content: import React from 'react'...
API Response: Success

[Agent: Frontend Developer] Iteration 4/10
Thinking: Now I should add prop validation...

Commands:
  (s)tep - advance one iteration
  (c)ontinue - run to completion
  (i)nspect <agent> - view agent state
  (q)uit

>
```

## Technical Requirements

### Architecture
- Built on existing Ensemble agent runtime
- Uses AgentRuntime and AgentDefinition classes
- Leverages existing tool system (read_file, write_file, spawn_agent, run_command)
- State persistence for session recovery

### Tech Stack
- Language: Python 3.11+
- CLI Framework: Click or Typer (for rich command-line features)
- Display: Rich library (for colored output, progress bars, tree views)
- State Storage: JSON files or SQLite for session persistence

### Commands Structure
```
ensemble                    # Interactive mode (default)
ensemble --quick <problem>  # Quick submission
ensemble --requirements <file> --output <dir>  # File mode
ensemble status [--session <name>]  # Check status
ensemble list              # List past sessions
ensemble resume <session>  # Resume session
ensemble debug <session>   # Debug mode
ensemble logs <session>    # View logs
ensemble help              # Help documentation
```

## Success Criteria
1. User can submit problem in < 30 seconds (interactive mode)
2. Real-time agent status updates within 1 second
3. Clear, readable output with colors and formatting
4. Comprehensive error handling with helpful messages
5. Debug mode allows inspection of any agent at any time
6. Session state can be saved and resumed
7. Works with existing Ensemble agent system without modification
8. All tests pass
9. Help documentation is clear and complete

## Constraints
- Use existing Ensemble agent runtime (no modifications to core agents)
- Must work from command line (no GUI)
- Cross-platform support (Linux, macOS, Windows)
- Minimal dependencies (use stdlib where possible)
- Follow Test-Driven Development
- Clean, maintainable code

## Out of Scope (for initial version)
- Web-based interface (CLI only)
- Multi-user support
- Cloud deployment
- Agent marketplace or plugins
- Cost tracking per session
- AI-powered CLI suggestions

## Non-Functional Requirements
- Performance: Status updates refresh in < 1 second
- Usability: New users should understand without reading docs
- Reliability: Gracefully handle network errors, API failures
- Maintainability: Modular design, comprehensive tests
- Documentation: Help text for all commands, usage examples

## Testing Requirements
- Unit tests for all CLI commands
- Integration tests with agent runtime
- Mock API calls for deterministic testing
- Test interactive flows with simulated input
- Test session persistence and recovery
- Test error handling scenarios

## Example Use Cases

### Use Case 1: First-Time User
```
$ ensemble
Welcome! I see this is your first time.
Let's build something together. What do you want to create?
> a simple web scraper for news articles

Great! A web scraper for news articles. Any specific sites?
> reddit and hacker news

Got it. I'll create a Python scraper for Reddit and Hacker News.
Where should I put the project?
> ./news-scraper

🚀 Starting...
```

### Use Case 2: Experienced User (Quick Mode)
```
$ ensemble --quick "REST API for user authentication with JWT" --output ./auth-api
```

### Use Case 3: Debugging Failed Execution
```
$ ensemble list
Sessions:
  - task-api (failed) - 10 minutes ago
  - calculator (success) - 2 hours ago

$ ensemble debug task-api
Last error: Unit Test Writer failed - missing task_description field

[showing agent hierarchy and last known state]
```

## Deliverables

### Phase 1: Core CLI (MVP)
1. Interactive problem submission
2. Real-time agent status display
3. Results summary
4. Session persistence
5. Basic help documentation

### Phase 2: Advanced Features
6. Debug mode
7. Status queries
8. Session management (list, resume)
9. Detailed logging

### Phase 3: Polish
10. Enhanced UI with Rich library
11. Comprehensive error handling
12. Progress estimation
13. Cost estimation
14. Usage analytics

## Priority
Start with Phase 1 (MVP) - get core functionality working first.
