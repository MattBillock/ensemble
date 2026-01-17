# Whimsical Name Enhancement - Architecture Document

## A. Architecture Overview

The enhanced naming system will extend the existing modular architecture with a category-based name database and improved generation algorithm. The system maintains backward compatibility while significantly expanding name variety and reducing repetition.

## B. Current System Analysis

### Existing Components
1. **name_data.py** - Contains 60 base whimsical names repeated for a pool of 1000
2. **name_generator.py** (naming module) - Main generator with family name support
3. **name_generator.py** (agents module) - Legacy FamilyNameGenerator class

### Current Name Format
- Full name: `FirstName FamilyName-ShortType-Suffix` (e.g., "Bramblejay Sparrow-BackendDev-4730")
- Simple name: `WhimsicalName-ShortType-Suffix` (e.g., "Lumawick-Director-4729")

## C. Enhanced Architecture

### Module Structure
```
src/runtime/agents/naming/
├── __init__.py           # Module exports
├── name_generator.py     # Enhanced NameGenerator class
├── name_data.py          # Base whimsical names (existing)
├── categories/           # NEW: Category-based name modules
│   ├── __init__.py
│   ├── fantasy.py        # Fantasy/mythology names
│   ├── scifi.py          # Science fiction names
│   ├── roman.py          # Roman politics/military names (whimsical)
│   ├── gaming.py         # Video game inspired names
│   └── creative.py       # Animation, comics, literature names
├── family_names.py       # NEW: Expanded family name database
└── anti_repetition.py    # NEW: Repetition tracking and prevention
```

## D. Data Model

### Name Categories
```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class NameCategory(Enum):
    FANTASY = "fantasy"
    SCIFI = "scifi"
    ROMAN = "roman"
    GAMING = "gaming"
    CREATIVE = "creative"
    CLASSIC = "classic"  # Original whimsical names

@dataclass
class NameEntry:
    name: str
    category: NameCategory
    subcategory: Optional[str] = None  # e.g., "tolkien", "greek", "cyberpunk"
    tags: List[str] = None  # For filtering

@dataclass
class FamilyNameEntry:
    name: str
    category: NameCategory
    style: str  # "creature", "occupational", "fantasy", "botanical", "terrain"
```

### Category Databases (Target Counts)
| Category | First Names | Family Names | Total Unique Combinations |
|----------|-------------|--------------|---------------------------|
| Fantasy | 100+ | 50+ | 5,000+ |
| Sci-Fi | 100+ | 50+ | 5,000+ |
| Roman | 50+ | 30+ | 1,500+ |
| Gaming | 100+ | 50+ | 5,000+ |
| Creative | 50+ | 30+ | 1,500+ |
| Classic | 60 | 100 | 6,000 (existing) |
| **Total** | **460+** | **310+** | **24,000+** |

## E. Enhanced Generation Algorithm

### NameGenerator Class (Enhanced)
```python
class NameGenerator:
    def __init__(
        self,
        categories: List[NameCategory] = None,  # None = all categories
        anti_repetition_threshold: int = 100,   # Names before reuse
        category_weights: Dict[NameCategory, float] = None,
        use_whimsical_names: bool = True
    ):
        self.categories = categories or list(NameCategory)
        self.anti_repetition = AntiRepetitionTracker(threshold)
        self.category_weights = category_weights or self._default_weights()
    
    def generate_name(
        self,
        agent_type: str,
        family_name: str = None,
        preferred_category: NameCategory = None
    ) -> str:
        """Generate a unique name with anti-repetition."""
        ...
    
    def _select_category(self) -> NameCategory:
        """Select category using weights, avoiding recent categories."""
        ...
```

### Anti-Repetition Tracker
```python
class AntiRepetitionTracker:
    def __init__(self, threshold: int = 100, persist: bool = True):
        self.threshold = threshold
        self.recent_names: deque = deque(maxlen=threshold)
        self.recent_families: deque = deque(maxlen=threshold // 4)
        self.recent_categories: deque = deque(maxlen=10)
        self.persist = persist  # Save/load from disk for cross-session tracking
    
    def is_available(self, name: str) -> bool:
        return name not in self.recent_names
    
    def record_use(self, name: str, category: NameCategory):
        self.recent_names.append(name)
        self.recent_categories.append(category)
    
    def save_state(self):
        """Persist tracking state to ~/.ensemble/naming_state.json"""
        ...
    
    def load_state(self):
        """Load persisted tracking state"""
        ...
```

## F. API Design

### Public Functions (Backward Compatible)
```python
# Existing API (unchanged)
def generate_agent_name(agent_type: str, parent_id: str = None, 
                        use_whimsical: bool = True, family_name: str = None) -> str

def generate_family_name() -> str

# New API (additions)
def generate_agent_name_from_category(
    agent_type: str,
    category: NameCategory,
    family_name: str = None
) -> str

def get_available_categories() -> List[NameCategory]

def configure_naming(
    categories: List[NameCategory] = None,
    weights: Dict[NameCategory, float] = None,
    anti_repetition_threshold: int = 100
) -> None
```

## G. Name Sources and Examples

### Fantasy/Mythology
- **Tolkien-style**: Shadowmere, Lightweaver, Starkeeper, Moonblade
- **Greek-adapted**: Olympius, Titanwing, Zepher, Apollight
- **Norse-adapted**: Thorwind, Lokimist, Freyashine, Odindream

### Science Fiction
- **Space-themed**: Nebulox, Quasarwind, Stardrift, Cosmweaver
- **Cyberpunk**: Neonflux, Bytestorm, Circuitblaze, Dataweave
- **Classic sci-fi**: Chronoshift, Voidwalker, Stellarforge

### Roman Politics (Whimsical)
- **Titles**: Consul Sparkle, Tribune Giggles, Centurion Whisper
- **Names adapted**: Maximus Bubbles, Aurelius Twinkle, Cassius Breeze

### Gaming
- **RPG-style**: Bladesinger, Spellweaver, Questkeeper, Loremaster
- **Adventure**: Pixelbound, Questline, Levelup, Respawn

### Creative
- **Animation**: Toonglow, Sketchwind, Frameleap
- **Comics**: Panelstorm, Inkblaze, Speechbubble
- **Literature**: Quillwhisper, Bookwind, Pageturn

## H. Configuration System

### Default Configuration
```json
{
  "naming": {
    "enabled_categories": ["fantasy", "scifi", "roman", "gaming", "creative", "classic"],
    "category_weights": {
      "fantasy": 1.0,
      "scifi": 1.0,
      "roman": 0.5,
      "gaming": 1.0,
      "creative": 0.5,
      "classic": 1.0
    },
    "anti_repetition": {
      "threshold": 100,
      "persist_across_sessions": true
    },
    "family_name_mixing": true,
    "compound_names_enabled": false
  }
}
```

## I. Testing Strategy

1. **Unit Tests**
   - Name generation correctness
   - Category selection
   - Anti-repetition verification
   - Backward compatibility

2. **Variety Testing**
   - Generate 1000 names, verify no duplicates
   - Category distribution analysis
   - Family name variety

3. **Content Validation**
   - All names family-friendly
   - Pronounceability check
   - No copyrighted content

4. **Performance Testing**
   - Generation speed < 10ms
   - Memory usage acceptable
   - Persistence I/O minimal

## J. Migration Plan

1. **Phase 1**: Add new name categories alongside existing data
2. **Phase 2**: Update generator to use new category system
3. **Phase 3**: Add anti-repetition tracking
4. **Phase 4**: Full integration with existing codebase

## K. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backward compatibility break | High | Maintain all existing function signatures |
| Performance degradation | Medium | Lazy loading of categories, caching |
| Inappropriate content | High | Manual review of all names, automated filtering |
| Memory bloat | Low | Lazy loading, efficient data structures |

## L. Success Metrics

1. **Variety**: 460+ unique first names, 310+ family names
2. **No Repetition**: 100+ generations without repeating within same category
3. **Performance**: < 10ms generation time
4. **Coverage**: 6 categories with balanced representation
5. **Backward Compatibility**: All existing tests pass
