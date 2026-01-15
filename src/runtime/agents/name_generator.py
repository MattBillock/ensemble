"""
Family Name Generator

Generates whimsical family names for agent groups to provide visual cohesion
and enable tracking of collective achievements across the ensemble.
"""

import random
from typing import Optional


class FamilyNameGenerator:
    """
    Generates unique, whimsical family names for agent groups.

    Family names consist of two parts: a first name and a last name.
    All agents spawned for a given task share the same family (last) name.
    """

    # Whimsical first name components (adjectives/descriptive)
    FIRST_NAMES = [
        # Celestial
        "Stellar", "Lunar", "Solar", "Cosmic", "Nebula", "Aurora",
        "Astral", "Comet", "Galaxy", "Quasar", "Pulsar", "Nova",
        # Nature
        "Misty", "Sunny", "Stormy", "Frosty", "Breezy", "Dewy",
        "Meadow", "Willow", "River", "Ocean", "Forest", "Mountain",
        # Whimsical
        "Whimsy", "Sparkle", "Shimmer", "Glimmer", "Twinkle", "Dazzle",
        "Flutter", "Whisper", "Echo", "Ripple", "Bubble", "Fizzy",
        # Colors/Light
        "Azure", "Coral", "Amber", "Violet", "Indigo", "Crimson",
        "Golden", "Silver", "Bronze", "Copper", "Jade", "Pearl",
        # Abstract
        "Swift", "Nimble", "Clever", "Bright", "Bold", "Gentle",
        "Noble", "Merry", "Jolly", "Witty", "Lucky", "Plucky",
        # Elements
        "Crystal", "Diamond", "Ruby", "Sapphire", "Emerald", "Opal",
        "Granite", "Marble", "Obsidian", "Quartz", "Topaz", "Onyx",
    ]

    # Whimsical last name components (nouns/occupational)
    LAST_NAMES = [
        # Nature creatures
        "Finch", "Sparrow", "Robin", "Wren", "Lark", "Swift",
        "Falcon", "Hawk", "Raven", "Owl", "Dove", "Crane",
        "Fox", "Wolf", "Bear", "Deer", "Hare", "Badger",
        "Otter", "Beaver", "Squirrel", "Hedgehog", "Mouse", "Mole",
        # Occupational
        "Smith", "Wright", "Mason", "Cooper", "Fletcher", "Thatcher",
        "Weaver", "Potter", "Baker", "Brewer", "Miller", "Shepherd",
        "Fisher", "Hunter", "Ranger", "Warden", "Keeper", "Guard",
        # Fantasy/Whimsical
        "Cloud", "Storm", "Thunder", "Lightning", "Rain", "Snow",
        "Frost", "Flame", "Ember", "Spark", "Glow", "Shine",
        "Moon", "Star", "Sun", "Sky", "Dawn", "Dusk",
        # Botanical
        "Oak", "Pine", "Birch", "Maple", "Willow", "Cedar",
        "Rose", "Lily", "Ivy", "Fern", "Sage", "Moss",
        "Thorn", "Bloom", "Petal", "Leaf", "Blossom", "Branch",
        # Terrain
        "Hill", "Dale", "Glen", "Vale", "Brook", "Stream",
        "Pond", "Lake", "Ridge", "Peak", "Cliff", "Shore",
        "Field", "Grove", "Glade", "Heath", "Marsh", "Wood",
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the name generator.

        Args:
            seed: Optional random seed for reproducible generation
        """
        self._rng = random.Random(seed)
        self._used_names: set = set()

    def generate_name(self) -> str:
        """
        Generate a unique whimsical name.

        Returns:
            A string in the format "FirstName LastName"
        """
        # Try to generate a unique name
        max_attempts = 100
        for _ in range(max_attempts):
            first = self._rng.choice(self.FIRST_NAMES)
            last = self._rng.choice(self.LAST_NAMES)
            name = f"{first} {last}"

            if name not in self._used_names:
                self._used_names.add(name)
                return name

        # If we've exhausted common combinations, add a unique suffix
        # This ensures we can always generate a unique name
        first = self._rng.choice(self.FIRST_NAMES)
        last = self._rng.choice(self.LAST_NAMES)
        suffix = self._generate_suffix()
        name = f"{first}{suffix} {last}"
        self._used_names.add(name)
        return name

    def _generate_suffix(self) -> str:
        """Generate a unique alphabetic suffix for name disambiguation."""
        # Use short, pronounceable suffixes
        suffixes = ["us", "ia", "io", "ar", "en", "on", "is", "os", "ix", "ax"]
        return self._rng.choice(suffixes)

    def generate_family_name(self) -> str:
        """
        Generate a family (last) name only.

        This is useful when you want all agents in a group to share
        the same family name but have different first names.

        Returns:
            A single family name string
        """
        return self._rng.choice(self.LAST_NAMES)

    def generate_first_name(self) -> str:
        """
        Generate a first name only.

        Returns:
            A single first name string
        """
        return self._rng.choice(self.FIRST_NAMES)

    def generate_name_with_family(self, family_name: str) -> str:
        """
        Generate a full name using a specific family name.

        Args:
            family_name: The family (last) name to use

        Returns:
            A string in the format "FirstName FamilyName"
        """
        first = self._rng.choice(self.FIRST_NAMES)
        return f"{first} {family_name}"

    def reset(self) -> None:
        """Clear the used names cache to allow name reuse."""
        self._used_names.clear()

    @property
    def total_combinations(self) -> int:
        """Get the total number of possible name combinations."""
        return len(self.FIRST_NAMES) * len(self.LAST_NAMES)

    @property
    def names_generated(self) -> int:
        """Get the count of unique names generated so far."""
        return len(self._used_names)
