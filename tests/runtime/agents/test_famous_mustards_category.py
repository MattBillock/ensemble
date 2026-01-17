"""
Unit tests for FAMOUS_MUSTARDS enum value in AchievementCategory enum.

This is the TDD RED phase - these tests are expected to fail initially
because the FAMOUS_MUSTARDS enum value doesn't exist yet in achievements.py.
"""

import pytest
from enum import Enum
from src.runtime.agents.achievements import AchievementCategory, Achievement, AchievementRarity


class TestFamousMustardsCategory:
    """Test suite for FAMOUS_MUSTARDS achievement category."""
    
    def test_famous_mustards_enum_exists(self):
        """Test that FAMOUS_MUSTARDS exists as a valid enum value."""
        # This will fail until FAMOUS_MUSTARDS is added to AchievementCategory
        assert hasattr(AchievementCategory, 'FAMOUS_MUSTARDS'), \
            "FAMOUS_MUSTARDS should exist as an enum value in AchievementCategory"
    
    def test_famous_mustards_string_value(self):
        """Test that FAMOUS_MUSTARDS has the correct string value 'famous_mustards'."""
        # This will fail until FAMOUS_MUSTARDS is added with correct value
        famous_mustards = AchievementCategory.FAMOUS_MUSTARDS
        assert famous_mustards.value == 'famous_mustards', \
            "FAMOUS_MUSTARDS enum value should equal 'famous_mustards'"
    
    def test_famous_mustards_is_enum_member(self):
        """Test that FAMOUS_MUSTARDS is a proper member of AchievementCategory enum."""
        # This will fail until FAMOUS_MUSTARDS is added
        assert AchievementCategory.FAMOUS_MUSTARDS in AchievementCategory, \
            "FAMOUS_MUSTARDS should be a valid member of AchievementCategory enum"
    
    def test_famous_mustards_in_enum_list(self):
        """Test that FAMOUS_MUSTARDS appears in the list of all enum values."""
        # This will fail until FAMOUS_MUSTARDS is added
        all_categories = list(AchievementCategory)
        assert AchievementCategory.FAMOUS_MUSTARDS in all_categories, \
            "FAMOUS_MUSTARDS should appear in the list of all AchievementCategory values"
    
    def test_famous_mustards_enum_comparison(self):
        """Test that FAMOUS_MUSTARDS can be compared with other enum values."""
        # This will fail until FAMOUS_MUSTARDS is added
        famous_mustards = AchievementCategory.FAMOUS_MUSTARDS
        ska_category = AchievementCategory.SKA
        
        # Should be able to compare enum values
        assert famous_mustards != ska_category, \
            "FAMOUS_MUSTARDS should be different from other enum values"
        assert famous_mustards == AchievementCategory.FAMOUS_MUSTARDS, \
            "FAMOUS_MUSTARDS should equal itself"
    
    def test_famous_mustards_in_achievement_definition(self):
        """Test that FAMOUS_MUSTARDS can be used in Achievement definitions."""
        # This will fail until FAMOUS_MUSTARDS is added
        try:
            # Should be able to create an Achievement with FAMOUS_MUSTARDS category
            test_achievement = Achievement(
                id="test_mustard_achievement",
                name="Test Mustard Achievement",
                description="Test achievement for mustard category",
                category=AchievementCategory.FAMOUS_MUSTARDS,
                rarity=AchievementRarity.COMMON,
                icon="🌭",
                points=10,
                agent_classes=["*"],
                trigger_condition={"event": "test_event"}
            )
            
            # Verify the category is correctly set
            assert test_achievement.category == AchievementCategory.FAMOUS_MUSTARDS, \
                "Achievement should be able to use FAMOUS_MUSTARDS as category"
            assert test_achievement.category.value == 'famous_mustards', \
                "Achievement category should have correct string value"
                
        except AttributeError as e:
            pytest.fail(f"Failed to create Achievement with FAMOUS_MUSTARDS category: {e}")
    
    def test_famous_mustards_enum_iteration(self):
        """Test that FAMOUS_MUSTARDS appears when iterating over AchievementCategory."""
        # This will fail until FAMOUS_MUSTARDS is added
        category_values = [category.value for category in AchievementCategory]
        assert 'famous_mustards' in category_values, \
            "FAMOUS_MUSTARDS value should appear when iterating over enum"
    
    def test_famous_mustards_enum_by_value_lookup(self):
        """Test that FAMOUS_MUSTARDS can be found by its string value."""
        # This will fail until FAMOUS_MUSTARDS is added
        try:
            famous_mustards = AchievementCategory('famous_mustards')
            assert famous_mustards == AchievementCategory.FAMOUS_MUSTARDS, \
                "Should be able to lookup FAMOUS_MUSTARDS by its string value"
        except ValueError as e:
            pytest.fail(f"Failed to lookup FAMOUS_MUSTARDS by value 'famous_mustards': {e}")
    
    def test_famous_mustards_enum_name_attribute(self):
        """Test that FAMOUS_MUSTARDS has the correct name attribute."""
        # This will fail until FAMOUS_MUSTARDS is added
        famous_mustards = AchievementCategory.FAMOUS_MUSTARDS
        assert famous_mustards.name == 'FAMOUS_MUSTARDS', \
            "FAMOUS_MUSTARDS enum should have name attribute 'FAMOUS_MUSTARDS'"
    
    def test_famous_mustards_enum_repr(self):
        """Test that FAMOUS_MUSTARDS has proper string representation."""
        # This will fail until FAMOUS_MUSTARDS is added
        famous_mustards = AchievementCategory.FAMOUS_MUSTARDS
        expected_repr = "<AchievementCategory.FAMOUS_MUSTARDS: 'famous_mustards'>"
        assert repr(famous_mustards) == expected_repr, \
            f"FAMOUS_MUSTARDS should have repr: {expected_repr}"
    
    def test_famous_mustards_enum_count(self):
        """Test that FAMOUS_MUSTARDS is included in the enum categories."""
        # Current categories include all the original plus expansions:
        # productivity, comedy, milestone, streak, meta, ska, brass_band, drum_corps,
        # guitar_hero, famous_mustards, dungeons_dragons, favorite_tacos, loser_board, family
        current_categories = [
            'productivity', 'comedy', 'milestone', 'streak', 'meta', 'ska',
            'brass_band', 'drum_corps', 'guitar_hero', 'famous_mustards',
            'dungeons_dragons', 'favorite_tacos', 'loser_board', 'family'
        ]

        all_categories = [category.value for category in AchievementCategory]

        # Should have 14 categories total
        expected_count = 14
        assert len(all_categories) == expected_count, \
            f"Enum should have {expected_count} values, found {len(all_categories)}"

        # Should include the famous_mustards category
        assert 'famous_mustards' in all_categories, \
            "FAMOUS_MUSTARDS should be included in all category values"