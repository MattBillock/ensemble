# Source Control Permission System Requirements

## Vision
Extend the existing permission system to include source control operations (git commit/push), ensuring a clear separation of concerns where code writers cannot commit their own code, and only verification/testing agents can commit code after confirming tests pass and quality gates are met.

## Problem Statement
The current system has `can_write_code` and `can_write_tests` permissions that prevent supervisor/coordinator agents from writing implementation code. However, there is no control over who can commit code to source control. This creates a risk where:
- Code writers might commit untested code
- Supervisors might commit directly without verification
- No clear audit trail of who verified code before commit
- Testing and verification steps could be bypassed

## Objectives

### Primary Objectives
1. **Add Git Permission Controls**: Introduce `can_commit_code` and `can_push_code` permissions to the agent permission model
2. **Create Source Control Agent**: Implement a specialized agent responsible for git operations (commit, push, tag)
3. **Enforce Verification Workflow**: Ensure only verification/testing agents can trigger commits after confirming tests pass
4. **Maintain Audit Trail**: All commits should include metadata about which agent verified the code and what checks passed

### Secondary Objectives
1. **Support Emergency Override**: Allow designated agents (e.g., Executive Director) to commit in emergency situations with explicit justification
2. **Integration with Existing Tools**: Add git operations to the tool registry similar to existing file operations
3. **Commit Message Standards**: Enforce structured commit messages that include agent verification metadata

## Scope

### In Scope
1. **Permission Model Extensions**
   - Add `can_commit_code` permission flag to AgentDefinition
   - Add `can_push_code` permission flag to AgentDefinition
   - Update agent definition parser to read these permissions from markdown

2. **New Tools**
   - `GitCommitTool`: Commit changes with verification metadata
   - `GitPushTool`: Push commits to remote repository
   - `GitStatusTool`: Check repository status
   - `GitDiffTool`: View changes before commit

3. **Source Control Agent**
   - New agent type: `source_control_agent.md`
   - Responsibilities: Execute git operations, validate verification requirements
   - Inputs: files to commit, verification results, test status
   - Outputs: commit SHA, push status, error messages

4. **Agent Definition Updates**
   - Update verification/testing agents to have `can_commit_code=true`
   - Update code writers, coordinators, supervisors to have `can_commit_code=false`
   - Document which agents should have which permissions

5. **Verification Integration**
   - TDD Coordinator should trigger commits after tests pass
   - Verification agents should validate code quality before commit
   - Commit metadata should include test results and verification status

### Out of Scope
1. **Complex Git Workflows**: Branching strategies, merge conflict resolution, rebasing (Phase 2)
2. **Code Review Process**: PR creation, review assignment, approval workflows (Phase 2)
3. **CI/CD Integration**: Automated deployment pipelines, build servers (Phase 2)
4. **Git Hosting Integration**: GitHub/GitLab API integration for issues, PRs (Future)
5. **Multi-Repository Management**: Working across multiple repos (Future)

## Constraints

### Technical Constraints
1. Must integrate seamlessly with existing permission system in `tools.py` and `definition.py`
2. Git operations must work on local repositories initially (no remote required)
3. Should support common git configurations (user.name, user.email)
4. Must handle git errors gracefully (no repo, not initialized, conflicts)

### Security Constraints
1. No hardcoded credentials or tokens in code
2. SSH keys and credentials must be sourced from environment or git config
3. Agent permission violations must be logged and blocked (similar to code writing violations)

### Operational Constraints
1. Git must be installed and available on PATH
2. Repository must be initialized before operations
3. Working directory must be within a git repository

## Success Criteria

### Must Have (P0)
1. ✅ `can_commit_code` and `can_push_code` permissions added to AgentDefinition
2. ✅ GitCommitTool and GitPushTool implemented and integrated into ToolRegistry
3. ✅ Permission checks prevent unauthorized agents from committing
4. ✅ Source Control Agent created and tested
5. ✅ At least one verification agent (e.g., TDD Coordinator) updated to use commit permissions

### Should Have (P1)
1. ✅ GitStatusTool and GitDiffTool for pre-commit inspection
2. ✅ Structured commit messages with verification metadata
3. ✅ Emergency override mechanism documented
4. ✅ Integration tests demonstrating the full workflow
5. ✅ Documentation for agent developers on permission usage

### Nice to Have (P2)
1. Commit message templates based on agent type
2. Automatic tagging for milestone completions
3. Commit statistics and metrics in activity tracker
4. Git hook integration for additional validation

## Assumptions Made

### Technology Assumptions
1. **Git Available**: Git CLI is installed and accessible on all deployment environments
2. **Local Repository**: Initial implementation targets local git repositories
3. **Standard Git Config**: User will have configured git user.name and user.email

### Permission Assumptions
1. **Verification Agents Trust**: Agents with verification roles (TDD Coordinator, verification agents) are trusted to make commit decisions
2. **Supervisor Delegation**: Supervisors and coordinators will delegate to Source Control Agent rather than committing directly
3. **Default Deny**: New agents default to `can_commit_code=false` unless explicitly granted

### Workflow Assumptions
1. **Linear Workflow**: Initial implementation assumes linear commit history (no branches)
2. **Single Developer**: Repository is managed by the agent ensemble, not concurrent human developers
3. **Test-First Commits**: All commits should be preceded by passing tests (enforced by verification agents)

## Stakeholders
- **Primary**: Agent ensemble system (all agent types)
- **Development Manager**: Will coordinate implementation across agents
- **TDD Coordinator**: Primary user of commit permissions
- **Executive Director**: Oversight and emergency override authority
- **Code Writers**: Affected by permission restrictions (cannot commit own code)

## Risks and Mitigations

### Risk 1: Permission Bypass
**Risk**: Agents find ways to circumvent permission checks
**Mitigation**: 
- Comprehensive logging of all git operations
- Permission checks at tool level (similar to file writing)
- Regular audit of agent behaviors

### Risk 2: Uncommitted Work Loss
**Risk**: Verification fails repeatedly, work never committed
**Mitigation**:
- GitStatusTool to inspect uncommitted changes
- Emergency override mechanism for directors
- Automatic stashing or backup mechanisms

### Risk 3: Git State Corruption
**Risk**: Failed operations leave repository in bad state
**Mitigation**:
- Validate repository state before operations
- Graceful error handling and reporting
- Document recovery procedures

### Risk 4: Credential Management
**Risk**: Git operations fail due to auth issues with remote
**Mitigation**:
- Start with local-only operations
- Clear documentation on credential setup
- Error messages that guide credential configuration

## Open Questions
*None - all ambiguities resolved through reasonable defaults above*

## Related Documentation
- `/Users/mattbillock/Development/ai_exploration/ensemble/src/runtime/agents/tools.py` - Current permission system
- `/Users/mattbillock/Development/ai_exploration/ensemble/src/runtime/agents/definition.py` - Agent definition parser
- `/Users/mattbillock/Development/ai_exploration/ensemble/leadership/tdd_coordinator.md` - Primary consumer of commit permissions
