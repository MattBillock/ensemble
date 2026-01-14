# Requirements: Executive Director Delegation Guardrails

## Vision
Ensure the Executive Director agent properly delegates work to specialized agents and never does implementation work itself. Each agent in the ensemble must focus solely on its core strength, with complete guardrails preventing role violations.

## Problem Statement
Currently, there's a risk that the Executive Director may be doing too much work directly instead of orchestrating other agents. We need to verify and strengthen guardrails that enforce proper delegation patterns.

## Objectives
1. **Verify Executive Director boundaries**: Ensure ED only writes requirements docs and status reports, never implementation code
2. **Strengthen delegation guardrails**: Add validation, checks, and fail-safes to prevent ED from doing implementation work
3. **Document agent responsibilities**: Clear delineation of what each agent type should and should not do
4. **Enforce tool-specific strengths**: Each agent focuses on its specialty only
5. **Validate orchestration patterns**: Ensure ED properly uses spawn_agent for all implementation work

## Scope

### In Scope
- Review and enhance Executive Director agent instructions/prompts
- Add validation logic to detect when ED attempts implementation work
- Create clear responsibility matrices for all agent types
- Add pre-checks before ED can proceed without delegation
- Implement warnings/errors if ED tries to write .py, .js, .jsx, .ts, .tsx files
- Document proper delegation workflows
- Add examples of correct vs incorrect delegation patterns
- Strengthen the "NEVER write implementation code" guardrails

### Out of Scope
- Changing the overall ensemble architecture
- Modifying other agent types (unless for delegation-related improvements)
- Adding new agent types
- Performance optimization unrelated to delegation
- UI/UX changes to the ensemble interface

## User Stories

### As an Executive Director agent:
- I should only write requirements.md and status reports
- I must spawn Development Manager for all implementation work
- I should be blocked from creating .py, .js, .jsx, .ts, .tsx files
- I need clear validation feedback if I attempt implementation work
- I should have pre-flight checks before proceeding without delegation

### As a Development Manager:
- I should receive well-formed requirements from ED
- I should be responsible for ALL implementation coordination
- I should spawn appropriate specialized agents for actual coding

### As a Code Writer agent:
- I should only write implementation code
- I should never write requirements or orchestration logic

### As a system user:
- I want confidence that work is being done by the right specialist
- I want to see clear delegation patterns in execution logs
- I want validation errors if improper delegation occurs

## Technical Requirements

### Validation Requirements
1. **Pre-spawn validation**: ED must verify requirements exist before spawning Development Manager
2. **File type restrictions**: ED cannot write files with implementation extensions (.py, .js, .jsx, .ts, .tsx, .java, .cpp, etc.)
3. **Spawn failure handling**: If spawn_agent fails, ED must error (not implement itself)
4. **Parameter validation**: Ensure all required fields passed to Development Manager (requirements_file, output_directory, project_name)

### Documentation Requirements
1. **Responsibility Matrix**: Document what each agent type should/shouldn't do
2. **Delegation Flowcharts**: Visual representation of proper orchestration
3. **Anti-patterns**: Examples of incorrect delegation to avoid
4. **Best Practices**: Guidelines for proper agent orchestration

### Guardrail Requirements
1. **Explicit CRITICAL warnings**: Multiple clear warnings in ED instructions about never implementing
2. **Validation checkpoints**: Specific validation steps ED must complete before proceeding
3. **Error handling patterns**: Clear rules for what ED does when agents fail
4. **Escalation paths**: When to ask user vs when to fail fast

## Constraints

### Technical Constraints
- Must work within existing ensemble architecture
- Cannot break existing delegation patterns that work correctly
- Must maintain backward compatibility with existing projects
- Changes should be additive (add guardrails, not remove capabilities)

### Process Constraints
- ED must always delegate to Development Manager for implementation
- Development Manager must always delegate to specialized coordinators
- Code Writers must only write code, never orchestrate

## Success Criteria

### Validation Success
- [ ] ED cannot create files with implementation extensions
- [ ] ED errors appropriately when spawn_agent fails (doesn't implement itself)
- [ ] ED validates requirements exist before spawning
- [ ] All required parameters validated before spawning Development Manager

### Documentation Success
- [ ] Clear responsibility matrix exists for all agent types
- [ ] Examples of correct delegation patterns documented
- [ ] Anti-patterns clearly identified with explanations
- [ ] Instructions contain multiple explicit warnings against implementation

### Behavioral Success
- [ ] ED only writes requirements.md and status reports
- [ ] All implementation work goes through Development Manager
- [ ] Each agent stays within its defined role
- [ ] Proper error handling when delegation fails

### Testing Success
- [ ] Can verify ED refuses to write .py files
- [ ] Can verify ED errors when spawn fails
- [ ] Can verify ED validates before spawning
- [ ] Can verify proper delegation chain works end-to-end

## Assumptions
1. The existing ensemble architecture supports agent delegation
2. The spawn_agent function works as documented
3. Development Manager properly coordinates implementation
4. File system operations are reliable
5. Agents have access to their instruction sets

## Risks
1. **Over-restrictive guardrails**: Could prevent legitimate ED activities
   - Mitigation: Carefully define what ED should write (requirements, reports only)
   
2. **Validation overhead**: Too many checks could slow execution
   - Mitigation: Keep validations simple and fast (file existence, parameter checks)
   
3. **Edge cases**: Legitimate scenarios where ED needs flexibility
   - Mitigation: Document exceptions clearly, default to strict delegation

4. **False positives**: Blocking ED from writing legitimate documentation
   - Mitigation: Whitelist allowed file types (.md, .txt, .json reports)

## Open Questions
None - proceeding with implementation of guardrail enhancements.

## Definition of Done
1. Executive Director instructions contain explicit, multiple warnings against implementation
2. Validation logic prevents ED from writing implementation files
3. Pre-spawn validation ensures requirements exist and parameters are complete
4. Error handling properly escalates when delegation fails
5. Documentation exists showing correct delegation patterns
6. Responsibility matrix clearly defines all agent roles
7. All changes committed to version control
8. Guardrails tested and verified working
