# Whimsical Agent Names - Architecture Document

## Overview
This document describes the architecture for the Whimsical Agent Names feature, which transforms cryptic agent IDs into memorable, family-friendly names.

## Architecture Principles
1. **Frontend-Only**: No backend changes required; all name generation happens client-side
2. **Deterministic**: Same agent ID always produces the same whimsical name
3. **Non-Intrusive**: Technical IDs remain available for debugging
4. **Performant**: Hash-based lookup is O(1) with minimal memory footprint

## Component Architecture

### New Components

#### `frontend/src/utils/whimsicalNames.js`
Core utility module for name generation.

```
┌─────────────────────────────────────────────────────────────┐
│                    whimsicalNames.js                         │
├─────────────────────────────────────────────────────────────┤
│  WORD_LISTS                                                  │
│  ├── ADJECTIVES: string[]  (40 words)                       │
│  └── NOUNS: string[]       (40 words)                       │
├─────────────────────────────────────────────────────────────┤
│  FUNCTIONS                                                   │
│  ├── hashString(str): number                                │
│  │   └── Deterministic hash using djb2 algorithm            │
│  ├── generateWhimsicalName(agentId): string                 │
│  │   └── Returns "[Adjective] [Noun]" format                │
│  └── getAgentEmoji(agentType): string                       │
│      └── Returns emoji based on agent role                  │
└─────────────────────────────────────────────────────────────┘
```

### Modified Components

#### `AgentHierarchyTree.jsx`
**Changes**:
- Import `generateWhimsicalName` utility
- Replace agent ID display with whimsical name
- Add tooltip or secondary text showing technical ID

#### `AgentStatusPane.jsx`
**Changes**:
- Import `generateWhimsicalName` and `getAgentEmoji`
- Display whimsical name as primary header
- Show technical ID in muted text below
- Optional: Add emoji prefix based on agent type

#### `AgentSummaryPane.jsx`
**Changes**:
- Import `generateWhimsicalName`
- Update card title to show whimsical name
- Keep technical ID accessible in detail view

#### `ActivityFeed.jsx`
**Changes**:
- Import `generateWhimsicalName`
- Replace agent ID in activity entries with whimsical name
- Consider showing technical ID in expandable detail

## Data Flow

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│   Agent ID   │────▶│ generateWhimsical │────▶│  Whimsical Name  │
│   (string)   │     │    Name(id)       │     │    (string)      │
└──────────────┘     └───────────────────┘     └──────────────────┘
                              │
                              ▼
                     ┌───────────────────┐
                     │   Hash Function   │
                     │   (djb2 algo)     │
                     └───────────────────┘
                              │
                              ▼
                     ┌───────────────────┐
                     │  Index Selection  │
                     │  adj = hash % 40  │
                     │  noun = hash/40%40│
                     └───────────────────┘
```

## Hash Algorithm: djb2

The djb2 hash is chosen for:
- Simplicity and speed
- Good distribution
- Deterministic results
- Browser compatibility

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

## Word Lists

### Adjectives (40 words)
From requirements - American pop culture themed:
- Cosmic, Groovy, Jazzy, Mighty, Stellar, Radical, Tubular, Gnarly, Bodacious, Wicked
- Fantastic, Amazing, Super, Ultra, Mega, Epic, Legendary, Awesome, Marvelous, Incredible
- Sparkly, Nifty, Snazzy, Zippy, Zesty, Funky, Peppy, Perky, Chipper, Spunky
- Rockin, Jammin, Kickin, Swingin, Cruisin, Chillin, Vibin, Rollin, Bouncin, Groovin

### Nouns (40 words)
From requirements - pop culture icons:
- Astronaut, Robot, Unicorn, Wizard, Ninja, Pirate, Superhero, Viking, Cowboy, Samurai
- Panda, Penguin, Phoenix, Dragon, Tiger, Eagle, Falcon, Wolf, Bear, Lion
- Rockstar, DJ, Dancer, Magician, Acrobat, Champion, Hero, Legend, Maverick, Ace
- Comet, Meteor, Galaxy, Nebula, Supernova, Stardust, Moonbeam, Sunray, Rainbow, Thunder

### Combination Space
40 adjectives × 40 nouns = 1,600 unique name combinations

## Agent Type Emojis

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

## Visual Design Implementation

### Primary Display Pattern
```jsx
<div className="agent-identity">
  <span className="agent-emoji">{emoji}</span>
  <span className="agent-name">{whimsicalName}</span>
  <span className="agent-id-secondary">({technicalId})</span>
</div>
```

### CSS Considerations
```css
.agent-name {
  font-weight: bold;
  color: var(--text-primary);
}

.agent-id-secondary {
  font-size: 0.85em;
  color: var(--text-muted);
  margin-left: 0.5em;
}
```

## Testing Strategy

### Unit Tests (whimsicalNames.test.js)
1. **Determinism Test**: Same input always produces same output
2. **Format Test**: Output matches "[Adjective] [Noun]" pattern
3. **Distribution Test**: Different inputs produce different outputs
4. **Edge Cases**: Empty string, null, undefined, special characters
5. **Emoji Mapping**: Correct emojis for each agent type

### Component Tests
1. Verify whimsical names render correctly
2. Verify technical IDs remain accessible
3. Verify no regressions in existing functionality
4. Verify emoji display for different agent types

## Performance Considerations
- Hash calculation: O(n) where n is string length (typically < 50 chars)
- Word list lookup: O(1) array index access
- Memory: ~2KB for word lists (static, loaded once)
- No caching needed due to fast hash calculation

## File Structure
```
frontend/src/
├── utils/
│   ├── whimsicalNames.js          # NEW
│   └── __tests__/
│       └── whimsicalNames.test.js # NEW
├── components/
│   ├── AgentHierarchyTree.jsx     # MODIFIED
│   ├── AgentStatusPane.jsx        # MODIFIED
│   ├── AgentSummaryPane.jsx       # MODIFIED
│   └── ActivityFeed.jsx           # MODIFIED
```

## Integration Points
- Components import from `../utils/whimsicalNames.js`
- No backend integration required
- No state management changes needed
- No routing changes required

## Risks and Mitigations
| Risk | Mitigation |
|------|------------|
| Name collisions | 1,600 combinations is sufficient for typical agent counts |
| Hash inconsistency across browsers | djb2 uses only basic JS operations |
| Breaking existing tests | Update tests to expect new name format |
| Performance impact | Hash is O(n) and very fast |

## Future Considerations (Out of Scope)
- User-customizable names
- Persistent name mappings
- Avatar/icon system
- Name preferences/themes
