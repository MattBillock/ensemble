# Frontend Tasks - Milestone 1: Core Name Generation Utility

## Overview
This milestone focuses on creating the core `whimsicalNames.js` utility module with deterministic name generation capabilities. This is a pure JavaScript utility with no UI dependencies, making it ideal for TDD implementation.

## Architecture Context
- **Location**: `frontend/src/utils/whimsicalNames.js`
- **Purpose**: Transform agent IDs into whimsical, memorable names
- **Approach**: Hash-based deterministic selection from curated word lists
- **Dependencies**: None (pure JavaScript utility)

---

## Task Breakdown

### Task 1: Create Word List Constants
**Priority**: High (Foundation)  
**Complexity**: Simple  
**Estimated Effort**: 30 minutes  

**Description**:
Create the ADJECTIVES and NOUNS constant arrays in `whimsicalNames.js` containing the curated word lists from requirements.

**Acceptance Criteria**:
- [ ] ADJECTIVES array contains exactly 40 words from requirements
- [ ] NOUNS array contains exactly 40 words from requirements
- [ ] Words are properly formatted (consistent capitalization)
- [ ] Arrays are exported for testing
- [ ] All words are family-friendly and match American pop culture theme
- [ ] Words maintain order specified in requirements for reproducibility

**Word Lists** (from requirements):

*Adjectives (40 words)*:
Cosmic, Groovy, Jazzy, Mighty, Stellar, Radical, Tubular, Gnarly, Bodacious, Wicked, Fantastic, Amazing, Super, Ultra, Mega, Epic, Legendary, Awesome, Marvelous, Incredible, Sparkly, Nifty, Snazzy, Zippy, Zesty, Funky, Peppy, Perky, Chipper, Spunky, Rockin, Jammin, Kickin, Swingin, Cruisin, Chillin, Vibin, Rollin, Bouncin, Groovin

*Nouns (40 words)*:
Astronaut, Robot, Unicorn, Wizard, Ninja, Pirate, Superhero, Viking, Cowboy, Samurai, Panda, Penguin, Phoenix, Dragon, Tiger, Eagle, Falcon, Wolf, Bear, Lion, Rockstar, DJ, Dancer, Magician, Acrobat, Champion, Hero, Legend, Maverick, Ace, Comet, Meteor, Galaxy, Nebula, Supernova, Stardust, Moonbeam, Sunray, Rainbow, Thunder

**Dependencies**: None

**Test Coverage Required**:
- Verify exact word count (40 each)
- Verify no duplicate words
- Verify all words are non-empty strings

---

### Task 2: Implement djb2 Hash Function
**Priority**: High (Core Algorithm)  
**Complexity**: Simple  
**Estimated Effort**: 45 minutes  

**Description**:
Implement the `hashString(str)` function using the djb2 algorithm for deterministic hash generation from agent ID strings.

**Acceptance Criteria**:
- [ ] Function accepts string input
- [ ] Returns positive integer
- [ ] Implements djb2 algorithm correctly (initial hash = 5381, formula: `hash = ((hash << 5) + hash) + charCode`)
- [ ] Converts to 32-bit integer using bitwise AND
- [ ] Returns absolute value (no negative hashes)
- [ ] Same input always produces same output (deterministic)
- [ ] Different inputs produce different outputs (good distribution)
- [ ] Handles edge cases: empty string, special characters, Unicode

**Algorithm Specification** (from architecture):
```javascript
function hashString(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}
```

**Dependencies**: None

**Test Coverage Required**:
- Determinism: Same input produces same output (test with multiple calls)
- Distribution: Different inputs produce different hashes
- Edge cases: empty string, null, undefined
- Special characters: handle hyphens, underscores, numbers
- Unicode: handle emoji and international characters
- Type safety: handle non-string inputs gracefully

---

### Task 3: Implement generateWhimsicalName Function
**Priority**: High (Core Feature)  
**Complexity**: Medium  
**Estimated Effort**: 1 hour  

**Description**:
Implement the main `generateWhimsicalName(agentId)` function that takes an agent ID and returns a whimsical name in "[Adjective] [Noun]" format.

**Acceptance Criteria**:
- [ ] Function accepts agentId string as parameter
- [ ] Returns string in format "[Adjective] [Noun]"
- [ ] Uses hashString() to generate hash from agentId
- [ ] Selects adjective using modulo: `hash % 40`
- [ ] Selects noun using division and modulo: `Math.floor(hash / 40) % 40`
- [ ] Same agentId always returns same name (deterministic)
- [ ] Different agentIds produce different names (with high probability)
- [ ] Handles edge cases: empty string, null, undefined
- [ ] Returns fallback name for invalid inputs (e.g., "Unknown Agent")

**Algorithm Specification**:
1. Hash the agent ID using `hashString(agentId)`
2. Calculate adjective index: `hash % ADJECTIVES.length`
3. Calculate noun index: `Math.floor(hash / ADJECTIVES.length) % NOUNS.length`
4. Return `${adjective} ${noun}`

**Dependencies**: 
- Task 1 (Word Lists)
- Task 2 (Hash Function)

**Test Coverage Required**:
- Format validation: Output matches "[Adjective] [Noun]" pattern
- Determinism: Same ID produces same name across multiple calls
- Distribution: Different IDs produce different names
- Edge cases: null, undefined, empty string, whitespace-only
- Boundary testing: Very long strings, special characters
- Collision testing: Verify hash distribution leads to name variety
- Integration: Verify adjective and noun come from correct word lists

**Example Expected Outputs**:
- `generateWhimsicalName("exec_dir_1")` → e.g., "Cosmic Astronaut"
- `generateWhimsicalName("dev_mgr_abc123")` → e.g., "Groovy Panda"
- Names should be different for different IDs but consistent for same ID

---

### Task 4: Implement getAgentEmoji Helper Function
**Priority**: Medium (Enhancement)  
**Complexity**: Simple  
**Estimated Effort**: 30 minutes  

**Description**:
Implement the `getAgentEmoji(agentType)` helper function that returns an appropriate emoji based on agent role/type.

**Acceptance Criteria**:
- [ ] Function accepts agentType string as parameter
- [ ] Returns single emoji character (string)
- [ ] Implements emoji mapping from architecture specification
- [ ] Returns default emoji (🤖) for unknown agent types
- [ ] Handles null/undefined inputs gracefully
- [ ] Case-insensitive matching (e.g., "executive_director" or "Executive_Director")
- [ ] All emoji characters are valid Unicode and display correctly

**Emoji Mapping** (from architecture):
```javascript
const AGENT_EMOJIS = {
  'executive_director': '👑',
  'development_manager': '📋',
  'system_architect': '🏗️',
  'tdd_coordinator': '🧪',
  'backend_coordinator': '⚙️',
  'frontend_coordinator': '🎨',
  'test_coordinator': '✅',
  'code_writer': '💻',
  'code_tester': '🔬',
  'section_tech': '🔧',
  'section_leader': '📊',
  'default': '🤖'
};
```

**Dependencies**: None

**Test Coverage Required**:
- Valid agent types: Return correct emoji for each type
- Unknown types: Return default emoji (🤖)
- Edge cases: null, undefined, empty string → default emoji
- Case insensitivity: Handle mixed case inputs
- Type validation: Non-string inputs handled gracefully

---

### Task 5: Create Module Exports and Documentation
**Priority**: High (Integration)  
**Complexity**: Simple  
**Estimated Effort**: 30 minutes  

**Description**:
Create proper ES6 module exports and JSDoc documentation for all public functions in `whimsicalNames.js`.

**Acceptance Criteria**:
- [ ] All public functions exported using named exports
- [ ] JSDoc comments for all exported functions
- [ ] Parameter types documented with @param
- [ ] Return types documented with @return
- [ ] Usage examples provided in JSDoc @example tags
- [ ] Module-level documentation explaining purpose
- [ ] Word lists exported for testing purposes
- [ ] Hash function exported (may be useful for debugging)

**Export Structure**:
```javascript
export {
  generateWhimsicalName,
  getAgentEmoji,
  hashString,        // For testing/debugging
  ADJECTIVES,        // For testing
  NOUNS              // For testing
};
```

**JSDoc Example**:
```javascript
/**
 * Generates a whimsical name from an agent ID using deterministic hash-based selection.
 * 
 * @param {string} agentId - The technical agent identifier (e.g., "exec_dir_1")
 * @returns {string} A whimsical name in "[Adjective] [Noun]" format
 * @example
 * generateWhimsicalName("exec_dir_1") // Returns e.g., "Cosmic Astronaut"
 */
```

**Dependencies**: 
- Task 1 (Word Lists)
- Task 2 (Hash Function)
- Task 3 (Generate Name)
- Task 4 (Get Emoji)

**Test Coverage Required**:
- Verify all exports are accessible
- Verify imports work in test files
- Documentation examples should be executable and accurate

---

## Testing Strategy

### Unit Test File: `frontend/src/utils/__tests__/whimsicalNames.test.js`

**Test Suites**:

1. **Word Lists Tests**
   - Verify ADJECTIVES has 40 words
   - Verify NOUNS has 40 words
   - Verify no duplicate words in each list
   - Verify all words are non-empty strings

2. **Hash Function Tests**
   - Determinism: Same input → same output
   - Distribution: Different inputs → different outputs
   - Edge cases: empty string, null, undefined
   - Special characters: handle properly
   - Performance: Fast enough for real-time use

3. **Generate Name Tests**
   - Format: Output matches "[Adjective] [Noun]"
   - Determinism: Same ID → same name
   - Distribution: Different IDs → different names (spot check)
   - Edge cases: null, undefined, empty string
   - Integration: Uses correct word lists

4. **Get Emoji Tests**
   - Known types: Return correct emoji
   - Unknown types: Return default emoji
   - Edge cases: null, undefined, empty string
   - Case sensitivity: Handle mixed case

5. **Integration Tests**
   - Generate 100 different names, verify format
   - Check for reasonable distribution (no single name dominates)
   - Verify all exported functions work together

---

## File Structure

```
frontend/src/
├── utils/
│   ├── whimsicalNames.js          # NEW - Main utility module
│   └── __tests__/
│       └── whimsicalNames.test.js # NEW - Unit tests
```

---

## Definition of Done

This milestone is complete when:

✅ **All 5 tasks implemented and passing tests**
✅ **Unit test coverage ≥ 95% for whimsicalNames.js**
✅ **All tests passing with no warnings**
✅ **JSDoc documentation complete for all exports**
✅ **Code follows project style guidelines (ESLint passes)**
✅ **Determinism verified: Same inputs always produce same outputs**
✅ **Edge cases handled gracefully**
✅ **Module can be imported and used in other files**

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Hash collisions | 40 × 40 = 1,600 combinations sufficient for typical agent counts |
| Browser compatibility | djb2 uses only basic JS operations supported everywhere |
| Performance concerns | Hash is O(n) on string length, very fast for typical agent IDs |
| Unicode handling | Use charCodeAt() which handles all valid JS strings |

---

## Next Steps After M1

After completing this milestone, the utility will be ready for integration into UI components in Milestone 2:
- Integrate into `AgentHierarchyTree.jsx`
- Integrate into `AgentStatusPane.jsx`
- Integrate into `AgentSummaryPane.jsx`
- Integrate into `ActivityFeed.jsx`

---

## Notes for TDD Coordinator

- **Start with Task 1** (word lists) as it has no dependencies
- **Tasks 2-4 can be done in TDD red-green-refactor cycles**
- **Task 5** should be done last to document the complete API
- **All functions are pure** (no side effects), making them ideal for TDD
- **Focus on determinism** - this is critical for user experience
- **Edge case handling is important** - don't assume valid inputs
