"""
Agent Name Generator

Generates whimsical, memorable names for agent instances.
Uses the name_data module to assign unique names to agents during execution.

Example usage:
    generator = NameGenerator()
    name = generator.get_name("Executive Director")  # Returns "Lumawick-Director-4729"
"""

import random
from datetime import datetime
from .name_data import WHIMSICAL_NAMES


class NameGenerator:
    """Generates whimsical names for agent instances."""

    def __init__(self, use_whimsical_names: bool = True):
        """
        Initialize the name generator.

        Args:
            use_whimsical_names: If True, use whimsical names. If False, use default naming.
        """
        self.use_whimsical_names = use_whimsical_names
        self._used_names = set()
        self._name_index = 0

    def get_name(self, agent_type: str, parent_id: str = None) -> str:
        """
        Generate a unique, whimsical name for an agent.

        Args:
            agent_type: The type of agent (e.g., "Executive Director", "Frontend Developer")
            parent_id: Optional parent agent ID for hierarchical naming

        Returns:
            A unique agent name like "Lumawick-Director-4729" or
            "Executive Director_1234567890.123" (if whimsical names disabled)

        Examples:
            >>> gen = NameGenerator()
            >>> gen.get_name("Executive Director")
            'Lumawick-Director-4729'
            >>> gen.get_name("Frontend Developer", parent_id="Lumawick-Director-4729")
            'Bramblejay-FrontendDev-4730'
        """
        if not self.use_whimsical_names:
            # Fall back to default naming
            return f"{agent_type}_{datetime.now().timestamp()}"

        # Get whimsical base name
        whimsical_name = self._get_next_whimsical_name()

        # Shorten agent type for compact names
        short_type = self._shorten_agent_type(agent_type)

        # Generate unique suffix
        suffix = self._generate_unique_suffix()

        # Construct full name: WhimsicalName-ShortType-Suffix
        full_name = f"{whimsical_name}-{short_type}-{suffix}"

        # Ensure uniqueness
        while full_name in self._used_names:
            suffix = self._generate_unique_suffix()
            full_name = f"{whimsical_name}-{short_type}-{suffix}"

        self._used_names.add(full_name)
        return full_name

    def _get_next_whimsical_name(self) -> str:
        """
        Get the next whimsical name from the list.

        Returns sequential names from WHIMSICAL_NAMES, wrapping around when exhausted.
        """
        name = WHIMSICAL_NAMES[self._name_index % len(WHIMSICAL_NAMES)]
        self._name_index += 1
        return name

    def _shorten_agent_type(self, agent_type: str) -> str:
        """
        Shorten agent type name for compact display.

        Args:
            agent_type: Full agent type like "Executive Director"

        Returns:
            Shortened version like "Director" or "FrontendDev"

        Examples:
            >>> gen = NameGenerator()
            >>> gen._shorten_agent_type("Executive Director")
            'Director'
            >>> gen._shorten_agent_type("Frontend Developer")
            'FrontendDev'
            >>> gen._shorten_agent_type("TDD Coordinator")
            'TDDCoord'
        """
        # Common mappings
        mappings = {
            "Executive Director": "Director",
            "Development Manager": "DevMgr",
            "TDD Coordinator": "TDDCoord",
            "System Architect": "Architect",
            "Frontend Developer": "FrontendDev",
            "Backend Developer": "BackendDev",
            "API Developer": "APIDev",
            "Frontend Lead": "FrontendLead",
            "Backend Lead": "BackendLead",
            "API Lead": "APILead",
            "Unit Test Writer": "UnitTest",
            "Unit Test Lead": "UnitTestLead",
            "Integration Test Writer": "IntTest",
            "Integration Test Lead": "IntTestLead",
            "Frontend Coordinator": "FrontendCoord",
            "Backend Coordinator": "BackendCoord",
            "Test Coordinator": "TestCoord",
        }

        if agent_type in mappings:
            return mappings[agent_type]

        # Fallback: Remove common words and camelcase
        words = agent_type.replace("_", " ").split()
        # Remove common words
        filtered = [w for w in words if w.lower() not in ["the", "a", "an"]]
        # Join without spaces
        return "".join(filtered)

    def _generate_unique_suffix(self) -> str:
        """
        Generate a short unique suffix for the name.

        Returns:
            A 4-digit number string like "4729"
        """
        return str(random.randint(1000, 9999))

    def reset(self):
        """Reset the name generator state (for testing)."""
        self._used_names = set()
        self._name_index = 0


# Global singleton instance
_generator = None


def get_generator(use_whimsical_names: bool = True) -> NameGenerator:
    """
    Get the global name generator instance.

    Args:
        use_whimsical_names: If True, use whimsical names. If False, use default naming.

    Returns:
        The global NameGenerator instance
    """
    global _generator
    if _generator is None:
        _generator = NameGenerator(use_whimsical_names=use_whimsical_names)
    return _generator


def generate_agent_name(agent_type: str, parent_id: str = None, use_whimsical: bool = True) -> str:
    """
    Convenience function to generate an agent name.

    Args:
        agent_type: The type of agent (e.g., "Executive Director")
        parent_id: Optional parent agent ID
        use_whimsical: If True, use whimsical names. If False, use default naming.

    Returns:
        A unique agent name

    Examples:
        >>> generate_agent_name("Executive Director")
        'Lumawick-Director-4729'
        >>> generate_agent_name("Frontend Developer", parent_id="Lumawick-Director-4729")
        'Bramblejay-FrontendDev-4730'
    """
    generator = get_generator(use_whimsical_names=use_whimsical)
    return generator.get_name(agent_type, parent_id)
