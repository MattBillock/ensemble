"""Unit tests for name_data module."""
import pytest
from src.runtime.agents.naming.name_data import WHIMSICAL_NAMES


def test_whimsical_names_exists():
    """Test that WHIMSICAL_NAMES list exists."""
    assert WHIMSICAL_NAMES is not None


def test_whimsical_names_length():
    """Test that WHIMSICAL_NAMES contains exactly 1000 names."""
    assert len(WHIMSICAL_NAMES) == 1000


def test_whimsical_names_all_strings():
    """Test that all entries in WHIMSICAL_NAMES are non-empty strings."""
    assert all(isinstance(name, str) and len(name) > 0 for name in WHIMSICAL_NAMES)


def test_whimsical_names_unique_count():
    """Test that there are exactly 60 unique names in WHIMSICAL_NAMES."""
    unique_names = set(WHIMSICAL_NAMES)
    assert len(unique_names) == 60
