"""
Unit tests for BRASS_BAND achievement category and brass band achievements.

Tests verify that all brass band achievements are properly defined with correct
categories, rarities, points, and agent classes.
"""

import pytest
from src.runtime.agents.achievements import (
    AchievementCategory,
    AchievementRarity,
    Achievement,
    ACHIEVEMENTS
)


def test_brass_band_category_exists():
    """Test that AchievementCategory.BRASS_BAND enum exists with value 'brass_band'."""
    assert hasattr(AchievementCategory, 'BRASS_BAND')
    assert AchievementCategory.BRASS_BAND.value == 'brass_band'


def test_brass_band_achievements_exist():
    """Test that all 15 brass band achievement IDs exist in ACHIEVEMENTS list."""
    expected_achievement_ids = [
        'championship_section',
        'principal_cornet',
        'euphonium_feature',
        'test_piece',
        'bandstand_performance',
        'nationals',
        'colliery_band',
        'hymn_tune',
        'march_tempo',
        'treble_clef',
        'fourth_section',
        'whit_friday',
        'bb_flat',
        'flugel_horn',
        'percussion_section',
    ]

    achievement_ids = [achievement.id for achievement in ACHIEVEMENTS]

    for expected_id in expected_achievement_ids:
        assert expected_id in achievement_ids, f"Achievement '{expected_id}' not found in ACHIEVEMENTS"


def test_brass_band_achievements_category():
    """Test that each brass band achievement has category=AchievementCategory.BRASS_BAND."""
    brass_band_achievement_ids = [
        'championship_section',
        'principal_cornet',
        'euphonium_feature',
        'test_piece',
        'bandstand_performance',
        'nationals',
        'colliery_band',
        'hymn_tune',
        'march_tempo',
        'treble_clef',
        'fourth_section',
        'whit_friday',
        'bb_flat',
        'flugel_horn',
        'percussion_section',
    ]

    for achievement in ACHIEVEMENTS:
        if achievement.id in brass_band_achievement_ids:
            assert achievement.category == AchievementCategory.BRASS_BAND, \
                f"Achievement '{achievement.id}' should have category BRASS_BAND, got {achievement.category}"


def test_brass_band_achievements_rarity():
    """Test that brass band achievements have correct rarities."""
    rarity_mapping = {
        # LEGENDARY
        'nationals': AchievementRarity.LEGENDARY,
        # EPIC
        'championship_section': AchievementRarity.EPIC,
        'flugel_horn': AchievementRarity.EPIC,
        # RARE
        'euphonium_feature': AchievementRarity.RARE,
        'test_piece': AchievementRarity.RARE,
        'march_tempo': AchievementRarity.RARE,
        'whit_friday': AchievementRarity.RARE,
        'bb_flat': AchievementRarity.RARE,
        # UNCOMMON
        'principal_cornet': AchievementRarity.UNCOMMON,
        'colliery_band': AchievementRarity.UNCOMMON,
        'hymn_tune': AchievementRarity.UNCOMMON,
        'treble_clef': AchievementRarity.UNCOMMON,
        'percussion_section': AchievementRarity.UNCOMMON,
        # COMMON
        'bandstand_performance': AchievementRarity.COMMON,
        'fourth_section': AchievementRarity.COMMON,
    }

    for achievement in ACHIEVEMENTS:
        if achievement.id in rarity_mapping:
            expected_rarity = rarity_mapping[achievement.id]
            assert achievement.rarity == expected_rarity, \
                f"Achievement '{achievement.id}' should have rarity {expected_rarity}, got {achievement.rarity}"


def test_brass_band_achievements_points():
    """Test that brass band achievements have correct point values."""
    points_mapping = {
        'championship_section': 80,
        'principal_cornet': 30,
        'euphonium_feature': 45,
        'test_piece': 40,
        'bandstand_performance': 15,
        'nationals': 150,
        'colliery_band': 35,
        'hymn_tune': 25,
        'march_tempo': 50,
        'treble_clef': 30,
        'fourth_section': 20,
        'whit_friday': 45,
        'bb_flat': 40,
        'flugel_horn': 70,
        'percussion_section': 25,
    }

    for achievement in ACHIEVEMENTS:
        if achievement.id in points_mapping:
            expected_points = points_mapping[achievement.id]
            assert achievement.points == expected_points, \
                f"Achievement '{achievement.id}' should have {expected_points} points, got {achievement.points}"


def test_brass_band_achievements_agent_classes():
    """Test that brass band achievements have correct agent_classes."""
    # Most are ['*'], but some have specific agent classes
    specific_agent_classes = {
        'principal_cornet': ['Executive Director', 'Development Manager', 'System Architect'],
        'bb_flat': ['Backend Developer', 'Backend Lead', 'System Architect'],
    }

    # All others should be ['*']
    default_agent_classes = [
        'championship_section',
        'euphonium_feature',
        'test_piece',
        'bandstand_performance',
        'nationals',
        'colliery_band',
        'hymn_tune',
        'march_tempo',
        'treble_clef',
        'fourth_section',
        'whit_friday',
        'flugel_horn',
        'percussion_section',
    ]

    for achievement in ACHIEVEMENTS:
        if achievement.id in specific_agent_classes:
            expected = specific_agent_classes[achievement.id]
            assert achievement.agent_classes == expected, \
                f"Achievement '{achievement.id}' should have agent_classes={expected}, got {achievement.agent_classes}"
        elif achievement.id in default_agent_classes:
            assert achievement.agent_classes == ['*'], \
                f"Achievement '{achievement.id}' should have agent_classes=['*'], got {achievement.agent_classes}"
