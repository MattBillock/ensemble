# Activity Tracking Fixes - Milestone Plan

## Project Overview
**Project Name:** Activity Tracking Fixes  
**Project ID:** 87cc4aaf  
**Created:** 2026-01-14

## Problem Summary
The Ensemble UI shows zero files generated and zero agent counts even when agents are actively producing files. This is a tracking/visibility bug - the agents ARE working but their activity is not being reported to the UI.

## Milestone Structure

### Milestone 1: Core Bug Fixes (Single Milestone)

**Objective:** Fix all three identified activity tracking bugs to enable proper visibility into agent activity.

**Duration:** Focused implementation - all fixes are interconnected and should be delivered together.

**Deliverables:**
1. Updated `src/runtime/agents/tools.py`:
   - Modify `WriteFileTool.__init__()` to accept tracking context parameters
   - Modify `WriteFileTool.execute()` to record file generation to ActivityTracker
   - Update `ToolRegistry.default()` to pass tracking context to WriteFileTool

2. Updated `src/runtime/agents/activity_tracker.py`:
   - Add auto-increment calls to `record_agent_started()`
   - Add auto-increment calls to `record_file_generated()`
   - Add auto-increment calls to `record_git_commit()`

3. Test file(s) verifying:
   - WriteFileTool records to activity tracker when context is provided
   - WriteFileTool works without context (backward compatibility)
   - increment_request_counts updates counters correctly
   - Integration: file generation flows through to activity APIs

**Acceptance Criteria:**
1. WriteFileTool accepts and uses agent_id, agent_name, request_id parameters
2. Files written by agents appear in `/api/activity/files` endpoint
3. Request timeline shows non-zero agent_count, file_count, commit_count
4. All existing tests continue to pass
5. Backward compatibility maintained - tools work without tracking context

**Dependencies:** None - this is the foundation fix

**Risk Assessment:**
- Low risk: Changes are localized to two files
- Circular import potential: Mitigated with local imports
- Performance: Minimal impact from tracking calls

---

## Implementation Strategy

Given that all three bugs are interconnected (files need to be tracked for counts to increment correctly), this is structured as a **single milestone** with coordinated changes:

1. **Bug #1 (HIGH)**: WriteFileTool tracking - enables file generation recording
2. **Bug #2 (MEDIUM)**: Auto-increment calls - ensures counters update automatically
3. **Bug #3 (LOW)**: Addressed implicitly - file tracking works everywhere WriteFileTool is used

The fixes build on each other:
- WriteFileTool calls `record_file_generated()`
- `record_file_generated()` calls `increment_request_counts(files=1)`
- Timeline and file APIs then return correct data

## Success Metrics

1. **Functional**: Run a test that creates files via WriteFileTool → verify files appear in activity tracker
2. **Counts**: Request timeline shows accurate agent/file/commit counts
3. **Regression**: All existing tests pass
4. **Compatibility**: Tools work with or without tracking context

---

*Plan created by Development Manager*
