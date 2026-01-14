"""
Unit tests for name_generator module.

Tests the whimsical name generation system for agent instances.
"""

import pytest
from src.runtime.agents.naming.name_generator import (
    NameGenerator,
    generate_agent_name,
    get_generator
)
from src.runtime.agents.naming.name_data import WHIMSICAL_NAMES


class TestNameGenerator:
    """Test NameGenerator class."""

    def test_generator_initialization(self):
        """Test basic initialization."""
        gen = NameGenerator()
        assert gen.use_whimsical_names is True
        assert len(gen._used_names) == 0
        assert gen._name_index == 0

    def test_generator_initialization_no_whimsical(self):
        """Test initialization with whimsical names disabled."""
        gen = NameGenerator(use_whimsical_names=False)
        assert gen.use_whimsical_names is False

    def test_get_name_basic(self):
        """Test basic name generation."""
        gen = NameGenerator()
        name = gen.get_name("Executive Director")

        assert isinstance(name, str)
        assert len(name) > 0
        # Should have format: WhimsicalName-ShortType-Suffix
        parts = name.split("-")
        assert len(parts) == 3
        assert parts[1] == "Director"  # Shortened type
        assert len(parts[2]) == 4  # 4-digit suffix

    def test_get_name_uses_whimsical_names(self):
        """Test that generated names use whimsical base names."""
        gen = NameGenerator()
        name = gen.get_name("Executive Director")

        # Extract whimsical part
        whimsical_part = name.split("-")[0]

        # Should be one of the whimsical names
        assert whimsical_part in WHIMSICAL_NAMES

    def test_get_name_uniqueness(self):
        """Test that generated names are unique."""
        gen = NameGenerator()

        names = set()
        for i in range(100):
            name = gen.get_name("Frontend Developer")
            assert name not in names, f"Duplicate name generated: {name}"
            names.add(name)

    def test_get_name_fallback_mode(self):
        """Test name generation with whimsical names disabled."""
        gen = NameGenerator(use_whimsical_names=False)
        name = gen.get_name("Executive Director")

        # Should use default format
        assert "Executive Director_" in name
        assert "." in name  # timestamp has decimal

    def test_get_name_with_parent(self):
        """Test name generation with parent ID."""
        gen = NameGenerator()
        parent_name = gen.get_name("Executive Director")
        child_name = gen.get_name("Frontend Developer", parent_id=parent_name)

        assert isinstance(child_name, str)
        assert len(child_name) > 0
        # Both should have proper format
        assert len(parent_name.split("-")) == 3
        assert len(child_name.split("-")) == 3

    def test_shorten_agent_type(self):
        """Test agent type shortening."""
        gen = NameGenerator()

        # Test known mappings
        assert gen._shorten_agent_type("Executive Director") == "Director"
        assert gen._shorten_agent_type("Development Manager") == "DevMgr"
        assert gen._shorten_agent_type("TDD Coordinator") == "TDDCoord"
        assert gen._shorten_agent_type("Frontend Developer") == "FrontendDev"
        assert gen._shorten_agent_type("Backend Developer") == "BackendDev"
        assert gen._shorten_agent_type("API Developer") == "APIDev"

    def test_shorten_agent_type_unmapped(self):
        """Test agent type shortening for unmapped types."""
        gen = NameGenerator()

        # Should still produce something reasonable
        result = gen._shorten_agent_type("Custom Agent Type")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_unique_suffix(self):
        """Test unique suffix generation."""
        gen = NameGenerator()

        suffixes = set()
        for i in range(100):
            suffix = gen._generate_unique_suffix()
            assert len(suffix) == 4
            assert suffix.isdigit()
            assert 1000 <= int(suffix) <= 9999
            suffixes.add(suffix)

        # Should have many unique suffixes
        assert len(suffixes) > 90

    def test_get_next_whimsical_name_sequential(self):
        """Test that whimsical names are retrieved sequentially."""
        gen = NameGenerator()

        # Get first 5 names
        names = [gen._get_next_whimsical_name() for _ in range(5)]

        # Should be first 5 from WHIMSICAL_NAMES
        assert names == WHIMSICAL_NAMES[:5]

    def test_get_next_whimsical_name_wraps_around(self):
        """Test that name retrieval wraps around when exhausted."""
        gen = NameGenerator()

        # Advance to near the end
        gen._name_index = len(WHIMSICAL_NAMES) - 2

        # Get 5 more names (should wrap around)
        names = [gen._get_next_whimsical_name() for _ in range(5)]

        # Last 2 from list, then first 3 again
        expected = WHIMSICAL_NAMES[-2:] + WHIMSICAL_NAMES[:3]
        assert names == expected

    def test_reset(self):
        """Test generator reset."""
        gen = NameGenerator()

        # Generate some names
        gen.get_name("Executive Director")
        gen.get_name("Frontend Developer")

        assert len(gen._used_names) > 0
        assert gen._name_index > 0

        # Reset
        gen.reset()

        assert len(gen._used_names) == 0
        assert gen._name_index == 0

    def test_multiple_agents_same_type(self):
        """Test generating multiple names for the same agent type."""
        gen = NameGenerator()

        names = [gen.get_name("Frontend Developer") for _ in range(10)]

        # All should be unique
        assert len(names) == len(set(names))

        # All should have same shortened type
        for name in names:
            parts = name.split("-")
            assert parts[1] == "FrontendDev"


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_generate_agent_name(self):
        """Test generate_agent_name convenience function."""
        name = generate_agent_name("Executive Director")

        assert isinstance(name, str)
        parts = name.split("-")
        assert len(parts) == 3
        assert parts[1] == "Director"

    def test_generate_agent_name_no_whimsical(self):
        """Test generate_agent_name with whimsical disabled."""
        name = generate_agent_name("Executive Director", use_whimsical=False)

        assert "Executive Director_" in name

    def test_generate_agent_name_with_parent(self):
        """Test generate_agent_name with parent ID."""
        parent = generate_agent_name("Executive Director")
        child = generate_agent_name("Frontend Developer", parent_id=parent)

        assert isinstance(child, str)
        assert len(child.split("-")) == 3

    def test_get_generator_singleton(self):
        """Test that get_generator returns singleton instance."""
        gen1 = get_generator()
        gen2 = get_generator()

        assert gen1 is gen2

    def test_get_generator_creates_instance(self):
        """Test that get_generator creates instance on first call."""
        # Reset global state
        import src.runtime.agents.naming.name_generator as module
        module._generator = None

        gen = get_generator()

        assert gen is not None
        assert isinstance(gen, NameGenerator)


class TestAgentTypeShortening:
    """Test agent type shortening for all known types."""

    def test_all_leadership_agents(self):
        """Test shortening for all leadership agents."""
        gen = NameGenerator()

        assert gen._shorten_agent_type("Executive Director") == "Director"
        assert gen._shorten_agent_type("Development Manager") == "DevMgr"
        assert gen._shorten_agent_type("TDD Coordinator") == "TDDCoord"
        assert gen._shorten_agent_type("System Architect") == "Architect"

    def test_all_developer_agents(self):
        """Test shortening for all developer agents."""
        gen = NameGenerator()

        assert gen._shorten_agent_type("Frontend Developer") == "FrontendDev"
        assert gen._shorten_agent_type("Backend Developer") == "BackendDev"
        assert gen._shorten_agent_type("API Developer") == "APIDev"

    def test_all_lead_agents(self):
        """Test shortening for all lead agents."""
        gen = NameGenerator()

        assert gen._shorten_agent_type("Frontend Lead") == "FrontendLead"
        assert gen._shorten_agent_type("Backend Lead") == "BackendLead"
        assert gen._shorten_agent_type("API Lead") == "APILead"

    def test_all_tester_agents(self):
        """Test shortening for all tester agents."""
        gen = NameGenerator()

        assert gen._shorten_agent_type("Unit Test Writer") == "UnitTest"
        assert gen._shorten_agent_type("Unit Test Lead") == "UnitTestLead"
        assert gen._shorten_agent_type("Integration Test Writer") == "IntTest"
        assert gen._shorten_agent_type("Integration Test Lead") == "IntTestLead"

    def test_all_coordinator_agents(self):
        """Test shortening for all coordinator agents."""
        gen = NameGenerator()

        assert gen._shorten_agent_type("Frontend Coordinator") == "FrontendCoord"
        assert gen._shorten_agent_type("Backend Coordinator") == "BackendCoord"
        assert gen._shorten_agent_type("Test Coordinator") == "TestCoord"


class TestNameFormat:
    """Test that generated names have consistent format."""

    def test_name_parts_count(self):
        """Test that names always have 3 parts."""
        gen = NameGenerator()

        for agent_type in ["Executive Director", "Frontend Developer", "Unit Test Writer"]:
            name = gen.get_name(agent_type)
            parts = name.split("-")
            assert len(parts) == 3, f"Expected 3 parts for {agent_type}, got {len(parts)}: {name}"

    def test_name_suffix_format(self):
        """Test that suffix is always 4 digits."""
        gen = NameGenerator()

        for i in range(20):
            name = gen.get_name("Frontend Developer")
            suffix = name.split("-")[2]
            assert len(suffix) == 4
            assert suffix.isdigit()

    def test_name_no_spaces(self):
        """Test that generated names have no spaces."""
        gen = NameGenerator()

        for agent_type in ["Executive Director", "Frontend Developer", "Unit Test Writer"]:
            name = gen.get_name(agent_type)
            assert " " not in name

    def test_name_readable_length(self):
        """Test that names are reasonably short."""
        gen = NameGenerator()

        for agent_type in ["Executive Director", "Frontend Developer", "Unit Test Lead"]:
            name = gen.get_name(agent_type)
            # Should be under 40 chars for readability
            assert len(name) < 40
