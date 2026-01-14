# Pre-Spawn Verification Checklist

## Executive Director → Development Manager Spawn

Before spawning `leadership/development_manager`, verify:

### 1. Requirements Document
- [ ] Requirements file exists at specified path
- [ ] File is readable (use `read_file` to verify)
- [ ] Contains: Vision, Objectives, Scope, Deliverables, Success Criteria

### 2. Output Directory
- [ ] Path is project-specific (e.g., `/output/my_project/`, NOT `/output/`)
- [ ] Directory is isolated from other projects
- [ ] No conflicting `architecture.md` from previous projects

### 3. Project Name
- [ ] Derived from user vision or context
- [ ] Clear and unambiguous
- [ ] Matches output directory name (recommended)

### 4. Input Data Structure
```json
{
  "agent_type": "leadership/development_manager",
  "input_data": {
    "requirements_file": "✅ Full absolute path",
    "output_directory": "✅ Project-specific path", 
    "project_name": "✅ Clear name"
  }
}
```

### 5. Agent Type Path
- [ ] Uses full path: `leadership/development_manager`
- [ ] NOT `development_manager` (missing prefix)
- [ ] NOT `program_coordinator` (deprecated)

---

## Development Manager → Coordinator Spawn

Before spawning coordinators, verify:

### 1. Architecture
- [ ] `architecture.md` exists and matches current project
- [ ] No stale architecture from previous projects

### 2. Milestones
- [ ] Development milestones defined
- [ ] Clear acceptance criteria for each phase

### 3. Coordinator Selection
- [ ] `coordination/backend_coordinator` for backend work
- [ ] `coordination/frontend_coordinator` for frontend work
- [ ] `coordination/tdd_coordinator` for test-driven development
- [ ] `coordination/devops_coordinator` for deployment

---

## Post-Completion Verification

After agent completes, verify actual deliverables:

### For TDD Coordinator
- [ ] Implementation files exist (`.py`, `.js`, `.jsx`)
- [ ] Test files exist
- [ ] Tests are runnable
- [ ] If no files → mark as FAILED, not completed

### For Backend/Frontend Coordinators
- [ ] Source files created in `src/` directory
- [ ] Files follow architecture patterns
- [ ] Basic functionality testable

---

## Error Recovery

### If Spawn Fails
1. Check agent type path (add tier prefix if missing)
2. Verify all required input fields provided
3. Ensure requirements file exists
4. Check output directory for conflicts

### If Agent Produces No Output
1. Check agent's notes/logs for errors
2. Verify input data was correctly formatted
3. Check for timeout issues
4. Retry with more specific instructions

### If Architecture Conflict
1. Check output directory for stale files
2. Remove or rename conflicting `architecture.md`
3. Use project-specific isolated directory
4. Respawn agent with clean environment
