# Pre-Spawn Verification Checklist

## Before Every Agent Spawn

Use this checklist to prevent spawn failures and ensure proper agent selection. **Complete ALL items** before calling `spawn_agent`.

---

## ✅ Agent Type Verification

### 1. Agent Type Existence
- [ ] **Agent type path is correct format** (e.g., `leadership/development_manager`)
- [ ] **Agent definition file exists** at specified path
- [ ] **No typos** in agent type name
- [ ] **Correct case sensitivity** (all lowercase with underscores)

### 2. Agent Capabilities Check
- [ ] **Task matches agent role** (see Agent Type Reference Guide)
- [ ] **Agent has required permissions** for assigned task
- [ ] **Agent scope covers task domain** (backend/frontend/testing/etc.)
- [ ] **No role boundary violations** (e.g., Coordinators doing implementation)

---

## ✅ Input Parameter Validation

### 3. Required Fields Present
- [ ] **All required parameters provided** (no missing fields)
- [ ] **Parameter types match expected** (string/array/object)
- [ ] **No placeholder values** (e.g., "path/to/file", "description here")
- [ ] **All values are actual/real** (not template examples)

### 4. File Path Validation
- [ ] **All input files exist** and are readable
- [ ] **File paths are absolute** (start with `/`)
- [ ] **Output directories exist** or can be created
- [ ] **No broken file references**

---

## ✅ Task Assignment Validation

### 5. Authority Check
- [ ] **Agent has authority** for decision-making required
- [ ] **Task within agent's domain** of expertise
- [ ] **No unauthorized delegation** (e.g., Section Tech making architecture decisions)
- [ ] **Proper escalation path** if authority insufficient

### 6. Workflow Sequence
- [ ] **Correct workflow order** (Architecture → Coordination → Implementation)
- [ ] **No skipped required steps** 
- [ ] **Proper handoff chain** maintained
- [ ] **Dependencies satisfied** before spawning

---

## ✅ Specific Agent Checklists

### For Development Manager
- [ ] **NOT assigned direct coding tasks**
- [ ] **Given orchestration/coordination role**
- [ ] **Requirements file exists and complete**
- [ ] **Output directory specified**

### For System Architect
- [ ] **Complex system design needed**
- [ ] **Architecture decisions required** 
- [ ] **Technical stack choices needed**
- [ ] **Requirements analysis completed**

### For Coordinators (Backend/Frontend/Test)
- [ ] **Architecture already completed**
- [ ] **Task breakdown/planning role only**
- [ ] **NOT assigned implementation**
- [ ] **Milestone clearly defined**

### For TDD Coordinator
- [ ] **Implementation phase starting**
- [ ] **Problem description specific**
- [ ] **Output directory for code specified**
- [ ] **Requirements available**

### For Section Leaders/Techs  
- [ ] **Specific implementation task defined**
- [ ] **Input files/specifications available**
- [ ] **Technical domain matches agent**
- [ ] **Clear deliverable expected**

---

## ✅ Common Error Prevention

### 7. Avoid These Patterns
- [ ] **Development Manager writing code** ❌
- [ ] **Coordinators doing implementation** ❌ 
- [ ] **Section Techs making architecture decisions** ❌
- [ ] **Skipping System Architect for complex projects** ❌
- [ ] **Using placeholder values in spawn calls** ❌
- [ ] **Spawning non-existent agent types** ❌

### 8. Input Data Validation
- [ ] **JSON structure is valid**
- [ ] **All strings are quoted properly**
- [ ] **Arrays have correct format**
- [ ] **No syntax errors in input data**

---

## 🚨 Pre-Spawn Validation Script

Before `spawn_agent(agent_type, input_data)`, run through:

```
1. Agent Type: _________________ 
   ✅ Exists? ✅ Correct role? ✅ Has authority?

2. Required Fields Check:
   ✅ All present? ✅ Correct types? ✅ No placeholders?

3. File Paths:
   ✅ Input files exist? ✅ Output paths valid? 

4. Task Validation:
   ✅ Matches capabilities? ✅ Within authority? ✅ Proper workflow?

5. Final Check:
   ✅ No common errors? ✅ JSON valid? ✅ Ready to spawn?
```

---

## 🔧 Quick Fixes for Common Issues

### Agent Type Not Found
1. **Check spelling** and case sensitivity
2. **Verify path format** (directory/agent_name)
3. **Confirm agent definition exists**
4. **Use exact agent types** from reference guide

### Missing Required Fields
1. **Review agent documentation** for required parameters
2. **Check input data structure** against requirements
3. **Ensure all fields have values** (not null/empty)
4. **Validate parameter types** match expected

### File Path Errors
1. **Use absolute paths** starting with `/`
2. **Verify files exist** before referencing
3. **Check file permissions** for readability
4. **Create output directories** if needed

### Role Boundary Violations
1. **Consult Agent Type Reference** for correct roles
2. **Reassign task** to appropriate agent type
3. **Follow proper workflow** sequence
4. **Don't bypass required steps**

---

## 📋 Post-Spawn Validation

After successful spawn:

- [ ] **Agent accepted task** without errors
- [ ] **Agent understood requirements** correctly  
- [ ] **Expected outputs being produced**
- [ ] **No immediate error messages**
- [ ] **Workflow proceeding as expected**

If any post-spawn issues:
1. **Review spawn parameters** used
2. **Check if task was properly scoped**
3. **Verify agent had all needed inputs**
4. **Consider if different agent type needed**

---

## 🎯 Success Indicators

You know verification was successful when:
- ✅ **Spawn call succeeds** on first attempt
- ✅ **Agent immediately begins** productive work
- ✅ **No error messages** or confusion from agent
- ✅ **Expected deliverables** start appearing
- ✅ **Workflow proceeds** smoothly to next step

---

## 📞 When to Escalate

Escalate to Executive Director when:
- **Multiple spawn failures** despite following checklist
- **Agent type seems missing** for required task
- **Workflow unclear** for current situation
- **Authority conflicts** between agents
- **Requirements insufficient** for proper agent selection

**Remember**: Following this checklist prevents 95% of spawn failures and workflow issues. Take the extra minute to verify - it saves hours of debugging!