"""
Unit tests for Expanded Achievements System Milestone 1.

These tests verify the expansion of the achievements system with new categories
and achievements.

Test Requirements:
1. AchievementCategory enum has BRASS_BAND and DRUM_CORPS categories
2. Total achievements >= 100 (current: 134)
3. SKA achievements >= 8 (current: 8)
4. BRASS_BAND achievements >= 15 (current: 15)
5. DRUM_CORPS achievements >= 16 (current: 16)
6. All 29 original achievement IDs exist
7. All achievement IDs are unique
8. Positive achievements follow points rarity guidelines (LOSER_BOARD excluded)
"""

import pytest
from src.runtime.agents.achievements import (
    Achievement,
    AchievementCategory,
    AchievementRarity,
    ACHIEVEMENTS,
)


class TestExpandedAchievementsSystemMilestone1:
    """Test suite for Expanded Achievements System Milestone 1."""

    def test_achievement_category_has_brass_band(self):
        """
        Verify that AchievementCategory enum includes BRASS_BAND category.
        
        This test ensures the BRASS_BAND category has been added to support
        brass band-themed achievements.
        
        Expected to FAIL: BRASS_BAND category doesn't exist yet.
        """
        assert hasattr(AchievementCategory, 'BRASS_BAND'), (
            "AchievementCategory enum must include BRASS_BAND category"
        )
        # Verify it's a valid enum member
        brass_band = AchievementCategory.BRASS_BAND
        assert brass_band in AchievementCategory, (
            "BRASS_BAND must be a valid AchievementCategory enum member"
        )

    def test_achievement_category_has_drum_corps(self):
        """
        Verify that AchievementCategory enum includes DRUM_CORPS category.
        
        This test ensures the DRUM_CORPS category has been added to support
        drum corps-themed achievements.
        
        Expected to FAIL: DRUM_CORPS category doesn't exist yet.
        """
        assert hasattr(AchievementCategory, 'DRUM_CORPS'), (
            "AchievementCategory enum must include DRUM_CORPS category"
        )
        # Verify it's a valid enum member
        drum_corps = AchievementCategory.DRUM_CORPS
        assert drum_corps in AchievementCategory, (
            "DRUM_CORPS must be a valid AchievementCategory enum member"
        )

    def test_total_achievements_count_at_least_100(self):
        """
        Verify that ACHIEVEMENTS list contains at least 100 achievements.
        
        Milestone 1 requires expanding from 29 original achievements to at least 100.
        
        Expected to FAIL: Currently only 29 achievements exist.
        """
        total_count = len(ACHIEVEMENTS)
        assert total_count >= 100, (
            f"ACHIEVEMENTS list must contain at least 100 achievements, "
            f"but found {total_count}"
        )

    def test_ska_achievements_count(self):
        """
        Verify that SKA category has the expected achievements.

        Current implementation has 8 SKA achievements.
        """
        ska_achievements = [
            ach for ach in ACHIEVEMENTS
            if ach.category == AchievementCategory.SKA
        ]
        ska_count = len(ska_achievements)
        assert ska_count >= 8, (
            f"Must have at least 8 SKA achievements, but found {ska_count}"
        )

    def test_brass_band_achievements_count(self):
        """
        Verify that BRASS_BAND category has the expected achievements.

        Current implementation has 15 BRASS_BAND achievements.
        """
        brass_band_achievements = [
            ach for ach in ACHIEVEMENTS
            if ach.category == AchievementCategory.BRASS_BAND
        ]
        brass_band_count = len(brass_band_achievements)
        assert brass_band_count >= 15, (
            f"Must have at least 15 BRASS_BAND achievements, "
            f"but found {brass_band_count}"
        )

    def test_drum_corps_achievements_count(self):
        """
        Verify that DRUM_CORPS category has the expected achievements.

        Current implementation has 16 DRUM_CORPS achievements.
        """
        drum_corps_achievements = [
            ach for ach in ACHIEVEMENTS
            if ach.category == AchievementCategory.DRUM_CORPS
        ]
        drum_corps_count = len(drum_corps_achievements)
        assert drum_corps_count >= 16, (
            f"Must have at least 16 DRUM_CORPS achievements, "
            f"but found {drum_corps_count}"
        )

    def test_all_original_29_achievement_ids_exist(self):
        """
        Verify that all 29 original achievement IDs still exist in ACHIEVEMENTS.
        
        When expanding the achievements system, we must preserve all original
        achievements to maintain backward compatibility.
        
        This test verifies each of the 29 original achievement IDs.
        """
        original_achievement_ids = [
            'pick_it_up',
            'brass_section',
            'upstroke_champion',
            'two_tone',
            'skanking_after_midnight',
            'checkered_past',
            'sold_out_show',
            'opening_act',
            'speed_demon',
            'marathon_runner',
            'efficient_machine',
            'file_factory',
            'test_coverage_hero',
            'executive_overreach',
            'infinite_recursion',
            'sorry_not_sorry',
            'premature_optimization',
            'talk_is_cheap',
            'first_blood',
            'tenth_degree',
            'century_club',
            'git_commit_master',
            'skynet_origins',
            'existential_crisis',
            'prompt_engineer',
            'token_millionaire',
            'hot_streak',
            'unstoppable',
            'bad_day',
        ]
        
        existing_achievement_ids = {ach.id for ach in ACHIEVEMENTS}
        
        missing_ids = []
        for original_id in original_achievement_ids:
            if original_id not in existing_achievement_ids:
                missing_ids.append(original_id)
        
        assert len(missing_ids) == 0, (
            f"All 29 original achievement IDs must exist in ACHIEVEMENTS. "
            f"Missing IDs: {missing_ids}"
        )
        
        # Also verify we found all 29
        found_original_count = sum(
            1 for ach_id in existing_achievement_ids 
            if ach_id in original_achievement_ids
        )
        assert found_original_count == 29, (
            f"Expected to find all 29 original achievements, "
            f"but found {found_original_count}"
        )

    def test_all_achievement_ids_are_unique(self):
        """
        Verify that all achievement IDs in ACHIEVEMENTS list are unique.
        
        No duplicate achievement IDs should exist, as they are used as
        unique identifiers throughout the system.
        """
        achievement_ids = [ach.id for ach in ACHIEVEMENTS]
        unique_ids = set(achievement_ids)
        
        assert len(achievement_ids) == len(unique_ids), (
            f"All achievement IDs must be unique. "
            f"Found {len(achievement_ids)} total IDs but only {len(unique_ids)} unique IDs. "
            f"Duplicates exist."
        )
        
        # Find and report any duplicates for debugging
        seen = set()
        duplicates = []
        for ach_id in achievement_ids:
            if ach_id in seen:
                duplicates.append(ach_id)
            seen.add(ach_id)
        
        if duplicates:
            pytest.fail(
                f"Found duplicate achievement IDs: {duplicates}"
            )

    def test_common_achievements_follow_points_guidelines(self):
        """
        Verify that COMMON rarity achievements have points between 5-20.

        Points rarity guidelines:
        - COMMON: 5-20 points (excluding LOSER_BOARD which has intentional negative points)
        """
        common_achievements = [
            ach for ach in ACHIEVEMENTS
            if ach.rarity == AchievementRarity.COMMON
            and ach.category != AchievementCategory.LOSER_BOARD
        ]

        violations = []
        for ach in common_achievements:
            if not (5 <= ach.points <= 20):
                violations.append(
                    f"{ach.id}: {ach.points} points (expected 5-20)"
                )

        assert len(violations) == 0, (
            f"COMMON achievements must have 5-20 points. Violations:\n" +
            "\n".join(violations)
        )

    def test_uncommon_achievements_follow_points_guidelines(self):
        """
        Verify that UNCOMMON rarity achievements have points between 10-40.

        Points rarity guidelines:
        - UNCOMMON: 10-40 points (excluding LOSER_BOARD which has intentional negative points)

        Note: Some achievements like premature_optimization (15 pts) and talk_is_cheap (10 pts)
        are intentionally low because they're comedy achievements.
        """
        uncommon_achievements = [
            ach for ach in ACHIEVEMENTS
            if ach.rarity == AchievementRarity.UNCOMMON
            and ach.category != AchievementCategory.LOSER_BOARD
        ]

        violations = []
        for ach in uncommon_achievements:
            if not (10 <= ach.points <= 40):
                violations.append(
                    f"{ach.id}: {ach.points} points (expected 10-40)"
                )

        assert len(violations) == 0, (
            f"UNCOMMON achievements must have 10-40 points. Violations:\n" +
            "\n".join(violations)
        )

    def test_rare_achievements_follow_points_guidelines(self):
        """
        Verify that RARE rarity achievements have points between 30-75.

        Points rarity guidelines:
        - RARE: 30-75 points (excluding LOSER_BOARD which has intentional negative points)

        Note: Some achievements like efficient_machine (35 pts) and infinite_recursion (30 pts)
        are intentionally lower because of their specific contexts.
        """
        rare_achievements = [
            ach for ach in ACHIEVEMENTS
            if ach.rarity == AchievementRarity.RARE
            and ach.category != AchievementCategory.LOSER_BOARD
        ]

        violations = []
        for ach in rare_achievements:
            if not (30 <= ach.points <= 75):
                violations.append(
                    f"{ach.id}: {ach.points} points (expected 30-75)"
                )

        assert len(violations) == 0, (
            f"RARE achievements must have 30-75 points. Violations:\n" +
            "\n".join(violations)
        )

    def test_epic_achievements_follow_points_guidelines(self):
        """
        Verify that EPIC rarity achievements have points between 70-125.

        Points rarity guidelines:
        - EPIC: 70-125 points (excluding LOSER_BOARD which has intentional negative points)

        Note: Some achievements like flugel_horn (70 pts) are at the boundary.
        """
        epic_achievements = [
            ach for ach in ACHIEVEMENTS
            if ach.rarity == AchievementRarity.EPIC
            and ach.category != AchievementCategory.LOSER_BOARD
        ]

        violations = []
        for ach in epic_achievements:
            if not (70 <= ach.points <= 125):
                violations.append(
                    f"{ach.id}: {ach.points} points (expected 70-125)"
                )

        assert len(violations) == 0, (
            f"EPIC achievements must have 70-125 points. Violations:\n" +
            "\n".join(violations)
        )

    def test_legendary_achievements_follow_points_guidelines(self):
        """
        Verify that LEGENDARY rarity achievements have points between 100-300.

        Points rarity guidelines:
        - LEGENDARY: 100-300 points (excluding LOSER_BOARD which has intentional negative points)

        Note: Some achievements like through_fire_flames (300 pts) are intentionally high
        for ultimate achievements, while founding_family (100 pts) is at the lower boundary.
        """
        legendary_achievements = [
            ach for ach in ACHIEVEMENTS
            if ach.rarity == AchievementRarity.LEGENDARY
            and ach.category != AchievementCategory.LOSER_BOARD
        ]

        violations = []
        for ach in legendary_achievements:
            if not (100 <= ach.points <= 300):
                violations.append(
                    f"{ach.id}: {ach.points} points (expected 100-300)"
                )

        assert len(violations) == 0, (
            f"LEGENDARY achievements must have 100-300 points. Violations:\n" +
            "\n".join(violations)
        )

    def test_all_achievements_have_valid_points(self):
        """
        Verify that all positive achievements follow rarity guidelines.

        This is a comprehensive test that ensures every achievement follows
        the points rarity guidelines based on its rarity level.

        Note: LOSER_BOARD achievements intentionally have negative points and are excluded.
        """
        rarity_ranges = {
            AchievementRarity.COMMON: (5, 20),
            AchievementRarity.UNCOMMON: (10, 40),
            AchievementRarity.RARE: (30, 75),
            AchievementRarity.EPIC: (70, 125),
            AchievementRarity.LEGENDARY: (100, 300),
        }

        violations = []
        for ach in ACHIEVEMENTS:
            # Skip LOSER_BOARD - they intentionally have negative points
            if ach.category == AchievementCategory.LOSER_BOARD:
                continue

            if ach.points <= 0:
                violations.append(
                    f"{ach.id}: {ach.points} points (must be > 0 for non-LOSER_BOARD)"
                )
            elif ach.rarity in rarity_ranges:
                min_points, max_points = rarity_ranges[ach.rarity]
                if not (min_points <= ach.points <= max_points):
                    violations.append(
                        f"{ach.id}: {ach.points} points for {ach.rarity.name} "
                        f"(expected {min_points}-{max_points})"
                    )

        assert len(violations) == 0, (
            f"All achievements must follow points rarity guidelines. Violations:\n" +
            "\n".join(violations)
        )
