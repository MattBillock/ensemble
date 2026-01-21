# Where to Find Incomplete Tasks

## Quick Answer

**The document for incomplete tasks doesn't exist yet** - but all incomplete task data is available in the project tracking system.

## Where Incomplete Task Information Lives

### 1. **Project Tracking System** (Primary Source)
- **Location**: `~/.ensemble/projects/*.json`
- **Contents**: All project metadata, tasks, and their statuses
- **Current Status**: 45 project files with 68 incomplete tasks across various projects

### 2. **How to Query Incomplete Tasks**

#### View All Incomplete Tasks:
```bash
# Count incomplete tasks
jq -r 'select(.tasks != null) | .tasks | to_entries[] | select(.value.status == "in_progress" or .value.status == "todo" or .value.status == "blocked") | .value.title' ~/.ensemble/projects/*.json

# Get project summaries with incomplete tasks
for f in ~/.ensemble/projects/*.json; do
  incomplete=$(jq '[.tasks | to_entries[] | select(.value.status == "in_progress" or .value.status == "todo" or .value.status == "blocked")] | length' "$f")
  if [ "$incomplete" -gt 0 ]; then
    name=$(jq -r '.project_name' "$f")
    echo "$name: $incomplete incomplete tasks"
  fi
done
```

### 3. **Related Projects Found**

The system has been working on several task-tracking related projects:
- **Project fea899b8**: "Incomplete Tasks Analysis" (Most Recent - Jan 13, 2026)
  - Started analyzing incomplete tasks
  - Identified 31 projects with incomplete tasks
  - Status: Active, generating recovery document
  
- **Project c3aaae0e**: "Task Recovery and Restart"
- **Project 42fdb8d6**: "Failed Task Cleanup System"
- **Project 3f1c6153**: "Task Recovery Analysis Implementation"
- **Project a466fb38**: "Failed Task Cleanup - Core Capture System"
- **Project e20ccb33**: "Failed Task Cleanup"

### 4. **What You're Likely Looking For**

Based on the project tracking history, it appears:
1. An analysis of incomplete tasks was started (project fea899b8)
2. It scanned 45 projects and identified 31 with incomplete tasks
3. It was in the process of generating a "comprehensive recovery document"
4. **This document was never completed**

## Recommended Next Steps

### Option A: Complete the Incomplete Tasks Analysis
Request: "Complete the incomplete tasks analysis project (fea899b8) and generate the recovery document"

### Option B: Generate Fresh Analysis
Request: "Analyze all incomplete tasks in the project tracking system and create a comprehensive report with:
- List of all incomplete tasks by project
- Task status breakdown (todo, in_progress, blocked)
- Priority/dependency analysis
- Recommended restart order"

### Option C: View Specific Project Tasks
If you know which project you're interested in, request:
"Show me incomplete tasks for [project_name]"

## Data Available Now

Without generating a full report, here's what exists:
- **68 incomplete tasks** across the project tracking system
- **45 total project files** 
- **Multiple task recovery projects** that themselves are incomplete
- **Task breakdowns** for various milestones in the output directory (backend_tasks_*.md, test_tasks_*.md, etc.)

## The Meta-Problem

You're experiencing the very issue these task recovery projects were trying to solve: tasks get started but not completed, leaving the user wondering "where did that go?"

The irony is that the "incomplete tasks analysis" project is itself incomplete!

---

**Would you like me to:**
1. Complete the incomplete tasks analysis and generate that document?
2. Create a fresh comprehensive report of all incomplete work?
3. Focus on a specific project's incomplete tasks?
