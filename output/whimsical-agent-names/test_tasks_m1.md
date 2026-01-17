# Test Tasks - Milestone 1: Core Name Generation Utility

## Overview
This document outlines the test strategy for the whimsicalNames.js utility module. Tests will follow TDD principles and ensure comprehensive coverage of all functionality.

## Test File Location
`frontend/src/utils/__tests__/whimsicalNames.test.js`

---

## Test Suite 1: Word Lists Validation

### Test 1.1: ADJECTIVES Array Validation
**Description**: Verify ADJECTIVES array structure and contents
**Tests**:
- [ ] ADJECTIVES array exists and is an array
- [ ] ADJECTIVES has exactly 40 words
- [ ] All adjectives are non-empty strings
- [ ] No duplicate adjectives in the list
- [ ] All adjectives match words from requirements

### Test 1.2: NOUNS Array Validation
**Description**: Verify NOUNS array structure and contents
**Tests**:
- [ ] NOUNS array exists and is an array
- [ ] NOUNS has exactly 40 words
- [ ] All nouns are non-empty strings
- [ ] No duplicate nouns in the list
- [ ] All nouns match words from requirements

---

## Test Suite 2: Hash Function (hashString)

### Test 2.1: Determinism
**Description**: Verify same input always produces same output
**Tests**:
- [ ] `hashString("test")` returns same value on multiple calls
- [ ] `hashString("agent_123")` returns same value on multiple calls
- [ ] `hashString("exec_dir_abc")` returns same value on multiple calls

### Test 2.2: Output Properties
**Description**: Verify hash function output characteristics
**Tests**:
- [ ] Returns a number
- [ ] Returns a positive integer
- [ ] Returns value >= 0 (no negative hashes)
- [ ] Returns finite number (not Infinity)

### Test 2.3: Distribution
**Description**: Verify different inputs produce different outputs
**Tests**:
- [ ] `hashString("a")` ≠ `hashString("b")`
- [ ] `hashString("test1")` ≠ `hashString("test2")`
- [ ] `hashString("agent_1")` ≠ `hashString("agent_2")`
- [ ] 10 random strings produce 10 different hashes

### Test 2.4: Edge Cases
**Description**: Verify handling of edge case inputs
**Tests**:
- [ ] Empty string returns a valid number
- [ ] String with only spaces returns a valid number
- [ ] String with special characters (!, @, #, etc.) works
- [ ] String with numbers works
- [ ] Very long strings (1000+ chars) work without error
- [ ] Unicode characters work correctly
- [ ] String with emoji works

### Test 2.5: Type Safety
**Description**: Verify handling of invalid input types
**Tests**:
- [ ] null input is handled gracefully (returns number or throws meaningful error)
- [ ] undefined input is handled gracefully
- [ ] Number input is handled (converted to string or throws)
- [ ] Object input is handled gracefully

---

## Test Suite 3: Generate Whimsical Name

### Test 3.1: Output Format
**Description**: Verify output matches expected format
**Tests**:
- [ ] Returns a string
- [ ] Output contains exactly one space
- [ ] First word is from ADJECTIVES list
- [ ] Second word is from NOUNS list
- [ ] Output matches regex `/^[A-Z][a-z]+ [A-Z][a-z]+$/`

### Test 3.2: Determinism
**Description**: Verify same agent ID always produces same name
**Tests**:
- [ ] `generateWhimsicalName("test")` returns same name on multiple calls
- [ ] `generateWhimsicalName("agent_123")` returns same name on multiple calls
- [ ] Same name after page refresh simulation (fresh function call)
- [ ] 100 calls with same ID produce identical results

### Test 3.3: Distribution
**Description**: Verify different agent IDs produce different names
**Tests**:
- [ ] `generateWhimsicalName("agent_1")` ≠ `generateWhimsicalName("agent_2")`
- [ ] 100 different agent IDs produce varied names (not all the same)
- [ ] Sequential IDs (agent_1, agent_2, ..., agent_10) produce 10 different names

### Test 3.4: Edge Cases
**Description**: Verify handling of edge case inputs
**Tests**:
- [ ] Empty string input returns valid name or fallback
- [ ] null input returns fallback name "Unknown Agent" or similar
- [ ] undefined input returns fallback name
- [ ] Very long string input works correctly
- [ ] String with special characters works
- [ ] String with only whitespace is handled

### Test 3.5: Integration
**Description**: Verify integration with word lists and hash function
**Tests**:
- [ ] All returned adjectives exist in ADJECTIVES array
- [ ] All returned nouns exist in NOUNS array
- [ ] Name generation uses hashString internally

---

## Test Suite 4: Get Agent Emoji

### Test 4.1: Known Agent Types
**Description**: Verify correct emoji for each known agent type
**Tests**:
- [ ] `getAgentEmoji("executive_director")` returns "👑"
- [ ] `getAgentEmoji("development_manager")` returns "📋"
- [ ] `getAgentEmoji("system_architect")` returns "🏗️"
- [ ] `getAgentEmoji("tdd_coordinator")` returns "🧪"
- [ ] `getAgentEmoji("backend_coordinator")` returns "⚙️"
- [ ] `getAgentEmoji("frontend_coordinator")` returns "🎨"
- [ ] `getAgentEmoji("test_coordinator")` returns "✅"
- [ ] `getAgentEmoji("code_writer")` returns "💻"
- [ ] `getAgentEmoji("code_tester")` returns "🔬"
- [ ] `getAgentEmoji("section_tech")` returns "🔧"
- [ ] `getAgentEmoji("section_leader")` returns "📊"

### Test 4.2: Default Emoji
**Description**: Verify default emoji for unknown types
**Tests**:
- [ ] Unknown type "unknown_agent" returns "🤖"
- [ ] Random string "xyz" returns "🤖"
- [ ] Empty string returns "🤖"

### Test 4.3: Edge Cases
**Description**: Verify edge case handling
**Tests**:
- [ ] null input returns default emoji "🤖"
- [ ] undefined input returns default emoji "🤖"
- [ ] Case insensitive: "Executive_Director" returns "👑"
- [ ] Case insensitive: "DEVELOPMENT_MANAGER" returns "📋"
- [ ] Mixed case: "System_ARCHITECT" returns "🏗️"

### Test 4.4: Output Properties
**Description**: Verify emoji output characteristics
**Tests**:
- [ ] Returns a string
- [ ] Returns non-empty string
- [ ] Returned string is a valid emoji (single emoji character/sequence)

---

## Test Suite 5: Module Exports

### Test 5.1: Named Exports
**Description**: Verify all functions are properly exported
**Tests**:
- [ ] `generateWhimsicalName` is exported and callable
- [ ] `getAgentEmoji` is exported and callable
- [ ] `hashString` is exported and callable
- [ ] `ADJECTIVES` is exported and is an array
- [ ] `NOUNS` is exported and is an array

### Test 5.2: Import Patterns
**Description**: Verify different import patterns work
**Tests**:
- [ ] Named import: `import { generateWhimsicalName } from './whimsicalNames'`
- [ ] Multiple named imports work
- [ ] Default import NOT expected (should use named exports)

---

## Test Suite 6: Integration Tests

### Test 6.1: Bulk Name Generation
**Description**: Test generating many names at once
**Tests**:
- [ ] Generate 100 names, all are valid format
- [ ] Generate 1000 names, no errors thrown
- [ ] Performance: 1000 names generated in < 100ms

### Test 6.2: Name Distribution
**Description**: Verify reasonable distribution of names
**Tests**:
- [ ] 100 sequential IDs (agent_0 to agent_99) produce at least 80 unique names
- [ ] Both adjectives and nouns show variety across 100 names
- [ ] No single adjective appears more than 10% of time in 100 random names

### Test 6.3: Persistence Simulation
**Description**: Verify names are consistent over time
**Tests**:
- [ ] Store 10 names, compare against regenerated names - all match
- [ ] Simulated "page refresh" produces same names

---

## Definition of Done

Test suite is complete when:
- [ ] All test suites pass (100% green)
- [ ] Code coverage >= 95% for whimsicalNames.js
- [ ] Edge cases thoroughly tested
- [ ] No flaky tests (all deterministic)
- [ ] Tests run in < 2 seconds total
- [ ] Tests work in CI environment

---

## Test Commands

```bash
# Run all whimsicalNames tests
npm test -- --testPathPattern=whimsicalNames

# Run with coverage
npm test -- --testPathPattern=whimsicalNames --coverage

# Run in watch mode during development
npm test -- --testPathPattern=whimsicalNames --watch
```

---

## Notes for TDD Implementation

1. **Write tests BEFORE implementation** - Red-Green-Refactor cycle
2. **Start with simplest tests** - Word list validation
3. **Progress to core functionality** - Hash function, then generate name
4. **Edge cases last** - After happy path works
5. **Keep tests independent** - No test should depend on another
6. **Use descriptive test names** - `it('should return same name for same agent ID')`
