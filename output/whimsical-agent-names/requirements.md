# Whimsical Agent Names Feature - Requirements

## Vision
Replace cryptic alphanumeric agent identifiers (like `exec_dir_1`, `dev_mgr_abc123`) with whimsical, memorable, American pop culture-inspired names that are family-friendly and fun.

## Objectives
1. Create a name generation system that produces consistent, memorable names for agents
2. Display whimsical names prominently in the UI while keeping technical IDs available for debugging
3. Ensure names are deterministic - same agent ID always maps to the same whimsical name

## Design Decisions (Pre-Made)

### Name Format
Names will follow the pattern: **[Adjective] [Noun]**

Examples:
- "Cheerful Penguin"
- "Cosmic Astronaut"  
- "Mighty Unicorn"
- "Jazzy Robot"
- "Groovy Panda"

### Word Lists - American Pop Culture Theme
**Adjectives** (family-friendly, upbeat):
- Cosmic, Groovy, Jazzy, Mighty, Stellar, Radical, Tubular, Gnarly, Bodacious, Wicked
- Fantastic, Amazing, Super, Ultra, Mega, Epic, Legendary, Awesome, Marvelous, Incredible
- Sparkly, Nifty, Snazzy, Zippy, Zesty, Funky, Peppy, Perky, Chipper, Spunky
- Rockin', Jammin', Kickin', Swingin', Cruisin', Chillin', Vibin', Rollin', Bouncin', Groovin'

**Nouns** (pop culture icons, characters, objects):
- Astronaut, Robot, Unicorn, Wizard, Ninja, Pirate, Superhero, Viking, Cowboy, Samurai
- Panda, Penguin, Phoenix, Dragon, Tiger, Eagle, Falcon, Wolf, Bear, Lion
- Rockstar, DJ, Dancer, Magician, Acrobat, Champion, Hero, Legend, Maverick, Ace
- Comet, Meteor, Galaxy, Nebula, Supernova, Stardust, Moonbeam, Sunray, Rainbow, Thunder

### Implementation Approach
1. **Frontend utility function** in JavaScript that:
   - Takes an agent ID string
   - Hashes it deterministically
   - Uses the hash to select adjective and noun from word lists
   - Returns the whimsical name

2. **UI Integration**:
   - Display whimsical name as the primary identifier
   - Show technical ID in smaller/muted text or tooltip
   - Apply in these components:
     - `AgentHierarchyTree.jsx` - tree view of agents
     - `AgentStatusPane.jsx` - detailed agent view
     - `AgentSummaryPane.jsx` - summary cards
     - `ActivityFeed.jsx` - activity entries

### Visual Design
- Whimsical name: Bold, primary text color
- Technical ID: Small, muted gray, shown below or in parentheses
- Optional: Add emoji based on agent type (e.g., 👑 for executive, 🔧 for developer)

## Technical Requirements

### New Files
1. `frontend/src/utils/whimsicalNames.js` - Name generation utility

### Modified Files
1. `frontend/src/components/AgentHierarchyTree.jsx` - Use whimsical names
2. `frontend/src/components/AgentStatusPane.jsx` - Use whimsical names
3. `frontend/src/components/AgentSummaryPane.jsx` - Use whimsical names
4. `frontend/src/components/ActivityFeed.jsx` - Use whimsical names

## Success Criteria
1. ✅ All agent identifiers display whimsical names in the UI
2. ✅ Names are deterministic (same ID = same name every time)
3. ✅ Technical IDs remain accessible (tooltip or secondary text)
4. ✅ Names are family-friendly American pop culture references
5. ✅ All existing tests pass
6. ✅ UI remains functional with no regressions

## Out of Scope
- Backend changes (names are UI-only display transformation)
- Persisting name mappings (calculated on-the-fly from hash)
- User customization of names
- Agent "avatars" or icons (beyond simple emojis)

## Constraints
- Must not break existing functionality
- Must maintain ability to debug using technical IDs
- Names must be consistent across page refreshes
