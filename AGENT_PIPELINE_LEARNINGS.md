# Agent Pipeline Learnings

## When to Use the Agent Pipeline

### ✅ EXCELLENT For:
1. **New Feature Development** - Creating new modules, functions, classes from scratch
2. **Planning & Architecture** - System design, task breakdown, requirements analysis  
3. **Documentation** - Writing comprehensive docs, READMEs, guides
4. **Test Creation** - Writing tests for new code (within TDD workflow)

### ⚠️ LIMITED For:
5. **Structural Refactoring** - Deleting files, merging files, renaming directories
6. **Search & Replace** - Mass text replacements across many files
7. **Configuration Changes** - Updating .gitignore, CI configs, etc.

### 🔴 NOT SUITABLE For:
8. **Permission Changes** - Modifying the permission system itself
9. **Agent Self-Modification** - Agents editing their own definitions
10. **File System Restructuring** - Major directory reorganizations

## Milestone 0 Experience

**Attempted**: Use agent pipeline for foundation fixes (cleanup, consolidation, refactoring)

**Result**: Planning phase succeeded brilliantly, but implementation hit limits:
- ✅ Created excellent architecture.md, backend_tasks.md, test_tasks.md
- ⚠️ Couldn't delete/merge agent files (structural changes)
- ⚠️ Couldn't do mass search-replace (drum corps cleanup)
- ✅ Permission system correctly blocked inappropriate actions

**Lesson**: Agent pipeline is for **creation**, manual work is for **restructuring**.

## Updated Workflow

### For New Development (Milestones 1-4):
1. Create requirements.md
2. Run agent pipeline
3. Review and test deliverables
4. Commit and analyze

### For Refactoring (like Milestone 0):
1. Create requirements.md
2. Run agent pipeline for **planning only**
3. **Manually implement** structural changes
4. Use agents for **new code** (ModelSelector, domain layer, etc.)
5. Commit and analyze

## Action Plan for Milestone 0

**Phase 1: Manual Structural Changes** (Now)
- Delete AGENT_ROSTER.md
- Merge and delete agent files (23 → 14)
- Mass search-replace drum corps terminology
- Fix Executive Director coordination bug

**Phase 2: Agent-Driven New Code** (After structural fixes)
- Use agents to create ModelSelector
- Use agents to create domain layer
- Use agents to write tests for new code

This hybrid approach leverages strengths of both manual and agent-driven work.
