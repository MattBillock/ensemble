"""
Unit tests for achievements module.

Tests the AchievementTracker class and related components.
"""

import pytest
import tempfile
from pathlib import Path


class TestAchievementRarity:
    """Test AchievementRarity enum."""

    def test_rarity_values(self):
        """Test all rarity values."""
        from src.runtime.agents.achievements import AchievementRarity

        assert AchievementRarity.COMMON.value == "common"
        assert AchievementRarity.UNCOMMON.value == "uncommon"
        assert AchievementRarity.RARE.value == "rare"
        assert AchievementRarity.EPIC.value == "epic"
        assert AchievementRarity.LEGENDARY.value == "legendary"


class TestAchievementCategory:
    """Test AchievementCategory enum."""

    def test_category_values(self):
        """Test some category values."""
        from src.runtime.agents.achievements import AchievementCategory

        assert AchievementCategory.PRODUCTIVITY.value == "productivity"
        assert AchievementCategory.COMEDY.value == "comedy"
        assert AchievementCategory.SKA.value == "ska"
        assert AchievementCategory.FAMILY.value == "family"
        assert AchievementCategory.LOSER_BOARD.value == "loser_board"


class TestAchievement:
    """Test Achievement dataclass."""

    def test_achievement_creation(self):
        """Test creating an Achievement."""
        from src.runtime.agents.achievements import (
            Achievement, AchievementCategory, AchievementRarity
        )

        achievement = Achievement(
            id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            category=AchievementCategory.PRODUCTIVITY,
            rarity=AchievementRarity.COMMON,
            icon="🏆",
            points=10,
            agent_classes=["*"],
            trigger_condition={"event": "test"}
        )

        assert achievement.id == "test_achievement"
        assert achievement.name == "Test Achievement"
        assert achievement.points == 10
        assert achievement.agent_classes == ["*"]


class TestAwardedAchievement:
    """Test AwardedAchievement dataclass."""

    def test_awarded_achievement_creation(self):
        """Test creating an AwardedAchievement."""
        from src.runtime.agents.achievements import AwardedAchievement

        awarded = AwardedAchievement(
            achievement_id="test_achievement",
            agent_id="agent-123",
            agent_name="Test Agent",
            agent_class="Developer",
            awarded_at="2024-01-01T00:00:00",
            context={"key": "value"}
        )

        assert awarded.achievement_id == "test_achievement"
        assert awarded.agent_id == "agent-123"
        assert awarded.context == {"key": "value"}


class TestAchievementsList:
    """Test ACHIEVEMENTS list."""

    def test_achievements_list_not_empty(self):
        """Test that ACHIEVEMENTS list has items."""
        from src.runtime.agents.achievements import ACHIEVEMENTS

        assert len(ACHIEVEMENTS) > 0

    def test_achievements_have_required_fields(self):
        """Test all achievements have required fields."""
        from src.runtime.agents.achievements import ACHIEVEMENTS

        for achievement in ACHIEVEMENTS:
            assert achievement.id
            assert achievement.name
            assert achievement.description
            assert achievement.category
            assert achievement.rarity
            assert achievement.icon
            assert isinstance(achievement.points, int)
            assert isinstance(achievement.agent_classes, list)
            assert isinstance(achievement.trigger_condition, dict)


class TestAchievementTracker:
    """Test AchievementTracker class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        try:
            db_path.unlink()
        except:
            pass

    @pytest.fixture
    def tracker(self, temp_db):
        """Create an AchievementTracker instance."""
        from src.runtime.agents.achievements import AchievementTracker

        return AchievementTracker(db_path=temp_db)

    def test_init_creates_database(self, temp_db):
        """Test that initialization creates database."""
        from src.runtime.agents.achievements import AchievementTracker

        tracker = AchievementTracker(db_path=temp_db)

        assert temp_db.exists()

        # Verify tables created
        with tracker._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            assert "awarded_achievements" in tables
            assert "agent_stats" in tables

    def test_check_and_award_empty_agent_name(self, tracker):
        """Test that empty agent name skips check."""
        awarded = tracker.check_and_award(
            agent_id="agent-1",
            agent_name="",
            agent_class="Developer",
            execution_data={"success": True}
        )

        assert awarded == []

    def test_check_and_award_empty_agent_class(self, tracker):
        """Test that empty agent class skips check."""
        awarded = tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="",
            execution_data={"success": True}
        )

        assert awarded == []

    def test_check_and_award_first_execution(self, tracker):
        """Test awarding first execution achievement."""
        awarded = tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True}
        )

        # Should get "opening_act" achievement
        achievement_ids = [a.achievement_id for a in awarded]
        assert "opening_act" in achievement_ids

    def test_check_and_award_speed_demon(self, tracker):
        """Test awarding speed demon achievement."""
        # First execution
        tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True}
        )

        # Second execution with fast duration
        awarded = tracker.check_and_award(
            agent_id="agent-2",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True, "duration_ms": 5000}
        )

        # Check for speed_demon
        achievement_ids = [a.achievement_id for a in awarded]
        assert "speed_demon" in achievement_ids

    def test_check_and_award_marathon_runner(self, tracker):
        """Test awarding marathon runner achievement."""
        # First execution
        tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True}
        )

        # Second execution with long duration
        awarded = tracker.check_and_award(
            agent_id="agent-2",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True, "duration_ms": 700000}
        )

        # Check for marathon_runner
        achievement_ids = [a.achievement_id for a in awarded]
        assert "marathon_runner" in achievement_ids

    def test_update_agent_stats(self, tracker):
        """Test that stats are updated on execution."""
        tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True, "tokens_used": 100}
        )

        stats = tracker._get_agent_stats("Developer")

        assert stats["total_executions"] == 1
        assert stats["successful_executions"] == 1
        assert stats["total_tokens"] == 100
        assert stats["consecutive_successes"] == 1

    def test_update_agent_stats_failure(self, tracker):
        """Test stats update on failure."""
        tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": False}
        )

        stats = tracker._get_agent_stats("Developer")

        assert stats["failed_executions"] == 1
        assert stats["consecutive_failures"] == 1

    def test_has_achievement_false(self, tracker):
        """Test has_achievement returns False for unknown."""
        result = tracker._has_achievement("Developer", "unknown_achievement")

        assert result is False

    def test_has_achievement_true(self, tracker):
        """Test has_achievement returns True after award."""
        tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True}
        )

        result = tracker._has_achievement("Developer", "opening_act")

        assert result is True

    def test_check_conditions_event_first_execution(self, tracker):
        """Test checking first_execution event condition."""
        from src.runtime.agents.achievements import Achievement, AchievementCategory, AchievementRarity

        achievement = Achievement(
            id="test",
            name="Test",
            description="Test",
            category=AchievementCategory.MILESTONE,
            rarity=AchievementRarity.COMMON,
            icon="🎯",
            points=10,
            agent_classes=["*"],
            trigger_condition={"event": "first_execution"}
        )

        result = tracker._check_conditions(
            achievement,
            {},
            {"total_executions": 1}
        )

        assert result is True

    def test_check_conditions_duration_max(self, tracker):
        """Test checking duration_ms max condition."""
        from src.runtime.agents.achievements import Achievement, AchievementCategory, AchievementRarity

        achievement = Achievement(
            id="test",
            name="Test",
            description="Test",
            category=AchievementCategory.PRODUCTIVITY,
            rarity=AchievementRarity.COMMON,
            icon="⚡",
            points=10,
            agent_classes=["*"],
            trigger_condition={"duration_ms": {"max": 30000}}
        )

        # Should pass - duration under max
        result = tracker._check_conditions(
            achievement,
            {"duration_ms": 10000},
            {}
        )
        assert result is True

        # Should fail - duration over max
        result = tracker._check_conditions(
            achievement,
            {"duration_ms": 50000},
            {}
        )
        assert result is False

    def test_check_conditions_consecutive_successes(self, tracker):
        """Test checking consecutive_successes condition."""
        from src.runtime.agents.achievements import Achievement, AchievementCategory, AchievementRarity

        achievement = Achievement(
            id="test",
            name="Test",
            description="Test",
            category=AchievementCategory.STREAK,
            rarity=AchievementRarity.RARE,
            icon="🔥",
            points=50,
            agent_classes=["*"],
            trigger_condition={"consecutive_successes": {"min": 10}}
        )

        # Should pass
        result = tracker._check_conditions(
            achievement,
            {},
            {"consecutive_successes": 15}
        )
        assert result is True

        # Should fail
        result = tracker._check_conditions(
            achievement,
            {},
            {"consecutive_successes": 5}
        )
        assert result is False

    def test_get_achievements_for_agent(self, tracker):
        """Test getting achievements for an agent."""
        tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True}
        )

        achievements = tracker.get_achievements_for_agent("Developer")

        assert len(achievements) >= 1
        assert any(a["id"] == "opening_act" for a in achievements)

    def test_get_all_achievements(self, tracker):
        """Test getting all achievements."""
        achievements = tracker.get_all_achievements()

        assert len(achievements) > 0
        assert all("id" in a for a in achievements)
        assert all("unlocked" in a for a in achievements)

    def test_get_recent_achievements(self, tracker):
        """Test getting recent achievements."""
        tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True}
        )

        recent = tracker.get_recent_achievements(limit=10)

        assert len(recent) >= 1
        assert "awarded_at" in recent[0]

    def test_get_achievement_stats(self, tracker):
        """Test getting achievement statistics."""
        # Award some achievements
        tracker.check_and_award(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_class="Developer",
            execution_data={"success": True}
        )

        stats = tracker.get_achievement_stats()

        assert "total_achievements_available" in stats
        assert "total_achievements_awarded" in stats
        assert "by_rarity" in stats
        assert "by_category" in stats
        assert stats["total_achievements_awarded"] >= 1


class TestGetAchievementTracker:
    """Test get_achievement_tracker function."""

    def test_get_achievement_tracker_returns_instance(self):
        """Test get_achievement_tracker returns instance."""
        import src.runtime.agents.achievements as module
        module._achievement_tracker = None

        from src.runtime.agents.achievements import get_achievement_tracker

        tracker = get_achievement_tracker()

        assert tracker is not None

        # Cleanup
        module._achievement_tracker = None

    def test_get_achievement_tracker_returns_same_instance(self):
        """Test get_achievement_tracker returns same instance."""
        import src.runtime.agents.achievements as module
        module._achievement_tracker = None

        from src.runtime.agents.achievements import get_achievement_tracker

        tracker1 = get_achievement_tracker()
        tracker2 = get_achievement_tracker()

        assert tracker1 is tracker2

        # Cleanup
        module._achievement_tracker = None
