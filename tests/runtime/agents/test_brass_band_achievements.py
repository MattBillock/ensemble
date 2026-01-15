"""
Unit tests for BRASS_BAND achievement category and brass band achievements.

Tests verify that all 15 brass band achievements are properly defined with correct
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
        'silver_band',
        'principal_cornet',
        'adjudicator',
        'test_piece',
        'bandroom_practice',
        'promotion',
        'brass_section_harmony',
        'march_on_stage',
        'quick_march',
        'hymn_tune_encore',
        'grand_shield',
        'fanfare',
        'youth_band_graduate',
        'national_finals'
    ]
    
    achievement_ids = [achievement.id for achievement in ACHIEVEMENTS]
    
    for expected_id in expected_achievement_ids:
        assert expected_id in achievement_ids, f"Achievement '{expected_id}' not found in ACHIEVEMENTS"


def test_brass_band_achievements_category():
    """Test that each brass band achievement has category=AchievementCategory.BRASS_BAND."""
    brass_band_achievement_ids = [
        'championship_section',
        'silver_band',
        'principal_cornet',
        'adjudicator',
        'test_piece',
        'bandroom_practice',
        'promotion',
        'brass_section_harmony',
        'march_on_stage',
        'quick_march',
        'hymn_tune_encore',
        'grand_shield',
        'fanfare',
        'youth_band_graduate',
        'national_finals'
    ]
    
    for achievement in ACHIEVEMENTS:
        if achievement.id in brass_band_achievement_ids:
            assert achievement.category == AchievementCategory.BRASS_BAND, \
                f"Achievement '{achievement.id}' should have category BRASS_BAND, got {achievement.category}"


def test_brass_band_achievements_rarity():
    """Test that brass band achievements have correct rarities."""
    rarity_mapping = {
        # LEGENDARY
        'championship_section': AchievementRarity.LEGENDARY,
        'national_finals': AchievementRarity.LEGENDARY,
        # EPIC
        'promotion': AchievementRarity.EPIC,
        'grand_shield': AchievementRarity.EPIC,
        # RARE
        'silver_band': AchievementRarity.RARE,
        'adjudicator': AchievementRarity.RARE,
        'brass_section_harmony': AchievementRarity.RARE,
        'quick_march': AchievementRarity.RARE,
        'fanfare': AchievementRarity.RARE,
        # UNCOMMON
        'principal_cornet': AchievementRarity.UNCOMMON,
        'test_piece': AchievementRarity.UNCOMMON,
        'hymn_tune_encore': AchievementRarity.UNCOMMON,
        'youth_band_graduate': AchievementRarity.UNCOMMON,
        # COMMON
        'bandroom_practice': AchievementRarity.COMMON,
        'march_on_stage': AchievementRarity.COMMON
    }
    
    for achievement in ACHIEVEMENTS:
        if achievement.id in rarity_mapping:
            expected_rarity = rarity_mapping[achievement.id]
            assert achievement.rarity == expected_rarity, \
                f"Achievement '{achievement.id}' should have rarity {expected_rarity}, got {achievement.rarity}"


def test_brass_band_achievements_points():
    """Test that brass band achievements have correct point values."""
    points_mapping = {
        'championship_section': 200,
        'silver_band': 50,
        'principal_cornet': 30,
        'adjudicator': 60,
        'test_piece': 25,
        'bandroom_practice': 15,
        'promotion': 100,
        'brass_section_harmony': 45,
        'march_on_stage': 10,
        'quick_march': 40,
        'hymn_tune_encore': 35,
        'grand_shield': 120,
        'fanfare': 55,
        'youth_band_graduate': 20,
        'national_finals': 150
    }
    
    for achievement in ACHIEVEMENTS:
        if achievement.id in points_mapping:
            expected_points = points_mapping[achievement.id]
            assert achievement.points == expected_points, \
                f"Achievement '{achievement.id}' should have {expected_points} points, got {achievement.points}"


def test_brass_band_achievements_agent_classes():
    """Test that each brass band achievement has agent_classes=['*']."""
    brass_band_achievement_ids = [
        'championship_section',
        'silver_band',
        'principal_cornet',
        'adjudicator',
        'test_piece',
        'bandroom_practice',
        'promotion',
        'brass_section_harmony',
        'march_on_stage',
        'quick_march',
        'hymn_tune_encore',
        'grand_shield',
        'fanfare',
        'youth_band_graduate',
        'national_finals'
    ]
    
    for achievement in ACHIEVEMENTS:
        if achievement.id in brass_band_achievement_ids:
            assert achievement.agent_classes == ['*'], \
                f"Achievement '{achievement.id}' should have agent_classes=['*'], got {achievement.agent_classes}"
