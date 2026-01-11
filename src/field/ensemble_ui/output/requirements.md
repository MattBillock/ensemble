# Project Requirements: Executive Director Project Awareness

## Vision
Add project awareness capabilities to Executive Director agents, enabling them to maintain a persistent understanding of their current project through descriptive naming and historical note-keeping.

## Problem Statement
Currently, Executive Directors operate without explicit project context awareness. They process tasks but don't maintain:
- A descriptive project name/identity
- Historical record of completed tasks
- Notes or proto-history about the project
- Tracking of remaining work

This limits the agent's ability to:
- Provide meaningful status reports referencing the project by name
- Resume work with full context awareness
- Track progress over time
- Make informed decisions based on project history

## Objectives
1. **Project Identity**: Executive Directors should identify and name projects descriptively
2. **Task History**: Maintain a record of completed tasks with timestamps
3. **Progress Notes**: Keep running notes about the project (decisions, context, observations)
4. **Remaining Work Tracking**: Track what tasks are pending or incomplete
5. **Persistence**: Enable context to persist across agent iterations and potential resumptions

## Core Features

### F1: Project Context Object
A structured data object that contains:
- `project_name`: Descriptive name derived from user vision
- `project_description`: Brief summary of what the project is about
- `created_at`: When the project started
- `current_phase`: Current development phase
- `status`: Current status (active, paused, completed)

### F2: Task History
Track completed work:
- `completed_tasks`: Array of completed task entries
  - `task_id`: Unique identifier
  - `description`: What was done
  - `completed_at`: Timestamp
  - `completed_by`: Agent that completed it (if applicable)
  - `outcome`: Result/notes about completion

### F3: Progress Notes / Proto-History
Running log of project-related notes:
- `notes`: Array of note entries
  - `timestamp`: When note was added
  - `author`: Who added the note (Executive Director or sub-agent)
  - `category`: Type of note (decision, observation, blocker, etc.)
  - `content`: The note content

### F4: Remaining Work Tracker
- `pending_tasks`: Array of tasks yet to be completed
  - `task_id`: Unique identifier
  - `description`: What needs to be done
  - `priority`: Priority level
  - `estimated_by`: Who estimated this task
  - `dependencies`: Other tasks this depends on (if any)

### F5: Project Context File
A `project_context.json` file written alongside `requirements.md` that persists this information between executions.

## Technical Approach

### Option A: Embedded in Agent State
Extend the existing `StateManager` to include project context fields.

**Pros**: Uses existing infrastructure, automatic persistence
**Cons**: May complicate state management, less visible to other agents

### Option B: Separate Project Context File (Recommended)
Create a dedicated `project_context.json` file in the output directory.

**Pros**: Explicit, easy to read/debug, shareable across agents
**Cons**: Additional file management

### Option C: Extended Agent Definition
Add project context fields to the Executive Director's output format.

**Pros**: Leverages existing output structure
**Cons**: Only persists through output, not introspectable during execution

## Implementation Requirements

### 1. Project Context Manager (New Component)
- Python class `ProjectContextManager`
- Methods:
  - `initialize_project(name, description)` - Create new project context
  - `load_context(path)` - Load existing context from file
  - `save_context(path)` - Save context to file
  - `add_completed_task(task_entry)` - Record completed work
  - `add_note(note_entry)` - Add a note to history
  - `add_pending_task(task_entry)` - Add pending work
  - `remove_pending_task(task_id)` - Remove completed pending task
  - `get_summary()` - Return human-readable summary
  - `to_dict()` / `from_dict()` - Serialization

### 2. Tool Integration
New tool `manage_project_context` available to Executive Director:
- Actions: `init`, `add_task`, `complete_task`, `add_note`, `get_status`
- Automatically available in Executive Director's tool registry

### 3. Executive Director Updates
Modify `executive_director.md` agent definition:
- Add tool to Available Tools section
- Update Instructions to use project context
- Include in output format for visibility

### 4. Integration with Activity Tracker
- New activity type: `PROJECT_CONTEXT_UPDATE`
- Record project context changes in activity log

## Success Criteria
1. Executive Director can name a project descriptively at start
2. Completed tasks are recorded with timestamps
3. Notes can be added throughout execution
4. Remaining work is tracked
5. Context persists in a readable JSON file
6. Context can be loaded on subsequent executions
7. Activity tracker shows context updates

## Out of Scope
- Multi-project support (one context per execution)
- Project context visualization in UI (future enhancement)
- Context sharing across different Executive Director instances
- Automated context merging on conflicts

## Assumptions
1. One project context per output directory
2. Executive Director is responsible for maintaining context
3. Sub-agents may read but not directly modify context
4. JSON format is sufficient for storage
5. Context file is `project_context.json` in output directory

## Constraints
- Must integrate with existing agent runtime system
- Must not break existing agent execution flow
- Tool must follow existing tool patterns in `tools.py`
- Changes to Executive Director definition must be minimal and targeted

## Technology Stack
- Python (consistent with existing runtime)
- JSON for persistence (human-readable)
- Integration with existing `ToolRegistry` pattern
