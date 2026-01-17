# Whimsical Name Enhancement - Backend Tasks (Milestone 1)

## Milestone 1: Expand Name Database

### Overview
Create comprehensive name databases from specified creative domains. All names must be original (not copyrighted), family-friendly, whimsical, and pronounceable.

---

## Task 1.1: Create Fantasy/Mythology Names Module
**File**: `src/runtime/agents/naming/categories/fantasy.py`

**Requirements**:
- Create 100+ unique fantasy first names
- Create 50+ fantasy-themed family names
- Organize by subcategory (tolkien_style, greek_adapted, norse_adapted, general_fantasy)

**Name Guidelines**:
- Tolkien-style: compound words with magical/nature elements (e.g., Starweaver, Moonwhisper, Shadowmere)
- Greek-adapted: classical sounds made whimsical (e.g., Olympius, Apollight, Zepher)
- Norse-adapted: strong sounds with soft endings (e.g., Thorwind, Freyashine, Lokimist)

**Example Structure**:
```python
FANTASY_FIRST_NAMES = {
    "tolkien_style": ["Starweaver", "Moonwhisper", "Shadowmere", ...],
    "greek_adapted": ["Olympius", "Apollight", "Zepher", ...],
    "norse_adapted": ["Thorwind", "Freyashine", "Lokimist", ...],
    "general_fantasy": ["Mysticfall", "Enchantra", "Spellbound", ...]
}

FANTASY_FAMILY_NAMES = [
    "Dragonheart", "Elfwood", "Wizardly", "Fairydust", ...
]
```

---

## Task 1.2: Create Science Fiction Names Module
**File**: `src/runtime/agents/naming/categories/scifi.py`

**Requirements**:
- Create 100+ unique sci-fi first names
- Create 50+ sci-fi themed family names
- Organize by subcategory (space, cyberpunk, classic_scifi)

**Name Guidelines**:
- Space-themed: cosmic, stellar elements (e.g., Nebulox, Stardrift, Cosmweaver)
- Cyberpunk: tech + energy words (e.g., Neonflux, Circuitblaze, Dataweave)
- Classic sci-fi: time/dimension concepts (e.g., Chronoshift, Voidwalker, Stellarforge)

**Example Structure**:
```python
SCIFI_FIRST_NAMES = {
    "space": ["Nebulox", "Stardrift", "Quasarwind", ...],
    "cyberpunk": ["Neonflux", "Circuitblaze", "Dataweave", ...],
    "classic_scifi": ["Chronoshift", "Voidwalker", "Stellarforge", ...]
}

SCIFI_FAMILY_NAMES = [
    "Starbound", "Nebulon", "Quantumleap", "Warpfield", ...
]
```

---

## Task 1.3: Create Roman Politics Names Module (Whimsical)
**File**: `src/runtime/agents/naming/categories/roman.py`

**Requirements**:
- Create 50+ unique Roman-inspired first names (made whimsical)
- Create 30+ Roman-themed family names (playful versions)
- Key: Take serious Roman titles/names and add whimsy

**Name Guidelines**:
- Titles made playful: Consul → Consul Sparkle, Tribune → Tribune Giggles
- Names adapted: Maximus → Maximus Bubbles, Aurelius → Aurelius Twinkle
- Military terms softened: Centurion → Centurion Whisper, Legatus → Legatus Breeze

**Example Structure**:
```python
ROMAN_FIRST_NAMES = [
    "Consul", "Tribune", "Centurion", "Legatus", "Praetor",
    "Maximus", "Aurelius", "Cassius", "Bruticus", "Octavian", ...
]

# These are the whimsical suffixes/modifiers
ROMAN_WHIMSY_MODIFIERS = [
    "Sparkle", "Giggles", "Bubbles", "Twinkle", "Breeze",
    "Whisper", "Sunshine", "Starlight", "Dewdrop", ...
]

ROMAN_FAMILY_NAMES = [
    "Glorius", "Magnificus", "Splendidus", "Jovialis", ...
]
```

---

## Task 1.4: Create Gaming Names Module
**File**: `src/runtime/agents/naming/categories/gaming.py`

**Requirements**:
- Create 100+ unique gaming-inspired first names
- Create 50+ gaming-themed family names
- Organize by subcategory (rpg, adventure, puzzle, general_gaming)

**Name Guidelines**:
- RPG-style: class/skill based (e.g., Bladesinger, Spellweaver, Loremaster)
- Adventure: action/quest themed (e.g., Questkeeper, Trailblazer, Pathfinder)
- Puzzle: logic/pattern based (e.g., Puzzlewing, Codebreaker, Riddlesmith)

**Example Structure**:
```python
GAMING_FIRST_NAMES = {
    "rpg": ["Bladesinger", "Spellweaver", "Loremaster", ...],
    "adventure": ["Questkeeper", "Trailblazer", "Levelup", ...],
    "puzzle": ["Puzzlewing", "Codebreaker", "Riddlesmith", ...],
    "general_gaming": ["Respawnix", "Saveslot", "Highscore", ...]
}

GAMING_FAMILY_NAMES = [
    "Powerup", "Checkpoint", "Bonusstage", "Multiball", ...
]
```

---

## Task 1.5: Create Creative Names Module
**File**: `src/runtime/agents/naming/categories/creative.py`

**Requirements**:
- Create 50+ unique creative-inspired first names
- Create 30+ creative-themed family names
- Organize by subcategory (animation, comics, literature)

**Name Guidelines**:
- Animation: movement/visual (e.g., Toonglow, Frameleap, Sketchwind)
- Comics: panel/art (e.g., Panelstorm, Inkblaze, Speechbubble)
- Literature: book/writing (e.g., Quillwhisper, Pageturn, Bookwind)

**Example Structure**:
```python
CREATIVE_FIRST_NAMES = {
    "animation": ["Toonglow", "Frameleap", "Sketchwind", ...],
    "comics": ["Panelstorm", "Inkblaze", "Speechbubble", ...],
    "literature": ["Quillwhisper", "Pageturn", "Bookwind", ...]
}

CREATIVE_FAMILY_NAMES = [
    "Storyline", "Plottwist", "Narrative", "Epilogue", ...
]
```

---

## Task 1.6: Create Expanded Family Names Module
**File**: `src/runtime/agents/naming/family_names.py`

**Requirements**:
- Consolidate all family names from category modules
- Add additional general-purpose family names
- Total 310+ unique family names
- Organize by style (creature, occupational, fantasy, botanical, terrain, cosmic, tech)

**Structure**:
```python
from .categories import fantasy, scifi, roman, gaming, creative

ALL_FAMILY_NAMES = {
    "creature": [...],      # Nature creatures (existing + new)
    "occupational": [...],  # Job-based names (existing + new)
    "fantasy": [...],       # From fantasy module
    "botanical": [...],     # Plant-based (existing + new)
    "terrain": [...],       # Landscape (existing + new)
    "cosmic": [...],        # From scifi module
    "tech": [...],          # From scifi/gaming modules
}

def get_all_family_names() -> List[str]:
    """Return flattened list of all family names."""
    
def get_family_names_by_style(style: str) -> List[str]:
    """Return family names for a specific style."""
```

---

## Task 1.7: Create Categories Package Init
**File**: `src/runtime/agents/naming/categories/__init__.py`

**Requirements**:
- Export all category modules
- Provide unified access to name data
- Include category enum

**Structure**:
```python
from enum import Enum
from typing import Dict, List

class NameCategory(Enum):
    FANTASY = "fantasy"
    SCIFI = "scifi"
    ROMAN = "roman"
    GAMING = "gaming"
    CREATIVE = "creative"
    CLASSIC = "classic"

def get_first_names(category: NameCategory) -> List[str]:
    """Get all first names for a category."""
    
def get_family_names(category: NameCategory) -> List[str]:
    """Get all family names for a category."""
    
def get_all_first_names() -> Dict[NameCategory, List[str]]:
    """Get all first names organized by category."""
```

---

## Acceptance Criteria for Milestone 1

1. [ ] All category modules created with required number of names
2. [ ] All names are original (no copyrighted characters)
3. [ ] All names are family-friendly and appropriate
4. [ ] All names are pronounceable (no random letter combinations)
5. [ ] Names are organized by category and subcategory
6. [ ] Package structure allows easy import and access
7. [ ] Documentation includes examples and guidelines

## Quality Checklist for Each Name
- [ ] Not a copyrighted character name
- [ ] Family-friendly (no offensive meanings in any language)
- [ ] Pronounceable in English
- [ ] Whimsical/fun sounding
- [ ] Memorable and distinctive
- [ ] Fits the category theme
