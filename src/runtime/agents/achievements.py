"""
Achievement System for Ensemble Agents

A whimsical, Steam-style achievement system that awards agents for various milestones,
quirks, and accomplishments. Includes tongue-in-cheek references to ska music tropes
and AI/developer culture.

"Pick it up, pick it up, pick it up!" - Every ska song ever (and now your agents)
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AchievementRarity(Enum):
    """Achievement rarity tiers - just like your favorite video game."""
    COMMON = "common"           # Happens all the time
    UNCOMMON = "uncommon"       # Happens sometimes
    RARE = "rare"               # Takes some effort
    EPIC = "epic"               # Impressive accomplishment
    LEGENDARY = "legendary"     # Once in a blue moon


class AchievementCategory(Enum):
    """Achievement categories."""
    PRODUCTIVITY = "productivity"     # Getting stuff done
    COMEDY = "comedy"                 # Funny failures and quirks
    MILESTONE = "milestone"           # First-time events
    STREAK = "streak"                 # Consecutive actions
    META = "meta"                     # Self-aware AI humor
    SKA = "ska"                       # Because ska will never die


@dataclass
class Achievement:
    """Definition of an achievement."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str
    points: int
    agent_classes: List[str]  # Which agents can earn this, or ["*"] for all
    trigger_condition: Dict[str, Any]  # Conditions that trigger the achievement


@dataclass
class AwardedAchievement:
    """Record of an achievement being awarded."""
    achievement_id: str
    agent_id: str
    agent_name: str
    agent_class: str
    awarded_at: str
    context: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# ACHIEVEMENT DEFINITIONS
# Ska tropes: horns, checkered patterns, "pick it up", upstrokes, two-tone,
# dancing, brass sections, energetic, DIY attitude, having a good time
# =============================================================================

ACHIEVEMENTS = [
    # ===== SKA ACHIEVEMENTS (the good stuff) =====
    Achievement(
        id="pick_it_up",
        name="Pick It Up! Pick It Up!",
        description="Recovered gracefully from a failure and completed the task anyway",
        category=AchievementCategory.SKA,
        rarity=AchievementRarity.UNCOMMON,
        icon="🎺",
        points=25,
        agent_classes=["*"],
        trigger_condition={"event": "recovered_from_failure"}
    ),
    Achievement(
        id="brass_section",
        name="Brass Section",
        description="Spawned 5 or more sub-agents in a single task (that's a full horn line!)",
        category=AchievementCategory.SKA,
        rarity=AchievementRarity.RARE,
        icon="📯",
        points=50,
        agent_classes=["Executive Director", "Development Manager", "System Architect"],
        trigger_condition={"spawned_agents_count": {"min": 5}}
    ),
    Achievement(
        id="upstroke_champion",
        name="Upstroke Champion",
        description="Maintained 100% success rate across 10 consecutive tasks",
        category=AchievementCategory.SKA,
        rarity=AchievementRarity.EPIC,
        icon="🎸",
        points=100,
        agent_classes=["*"],
        trigger_condition={"consecutive_successes": {"min": 10}}
    ),
    Achievement(
        id="two_tone",
        name="Two-Tone",
        description="Successfully collaborated between frontend and backend agents",
        category=AchievementCategory.SKA,
        rarity=AchievementRarity.UNCOMMON,
        icon="⬛⬜",
        points=30,
        agent_classes=["Frontend Lead", "Backend Lead", "Frontend Developer", "Backend Developer"],
        trigger_condition={"event": "cross_stack_collaboration"}
    ),
    Achievement(
        id="skanking_after_midnight",
        name="Skanking After Midnight",
        description="Completed a task between midnight and 4 AM",
        category=AchievementCategory.SKA,
        rarity=AchievementRarity.RARE,
        icon="🌙",
        points=40,
        agent_classes=["*"],
        trigger_condition={"time_of_day": {"start": 0, "end": 4}}
    ),
    Achievement(
        id="checkered_past",
        name="Checkered Past",
        description="Had a failure but later achieved 90%+ success rate (redemption arc!)",
        category=AchievementCategory.SKA,
        rarity=AchievementRarity.RARE,
        icon="🏁",
        points=60,
        agent_classes=["*"],
        trigger_condition={"event": "redemption_arc"}
    ),
    Achievement(
        id="sold_out_show",
        name="Sold Out Show",
        description="Executed 100 tasks total",
        category=AchievementCategory.SKA,
        rarity=AchievementRarity.EPIC,
        icon="🎫",
        points=100,
        agent_classes=["*"],
        trigger_condition={"total_executions": {"min": 100}}
    ),
    Achievement(
        id="opening_act",
        name="Opening Act",
        description="First task ever executed by this agent class",
        category=AchievementCategory.SKA,
        rarity=AchievementRarity.COMMON,
        icon="🎤",
        points=10,
        agent_classes=["*"],
        trigger_condition={"event": "first_execution"}
    ),

    # ===== PRODUCTIVITY ACHIEVEMENTS =====
    Achievement(
        id="speed_demon",
        name="Speed Demon",
        description="Completed a task in under 30 seconds",
        category=AchievementCategory.PRODUCTIVITY,
        rarity=AchievementRarity.UNCOMMON,
        icon="⚡",
        points=20,
        agent_classes=["*"],
        trigger_condition={"duration_ms": {"max": 30000}}
    ),
    Achievement(
        id="marathon_runner",
        name="Marathon Runner",
        description="Completed a task that took over 10 minutes",
        category=AchievementCategory.PRODUCTIVITY,
        rarity=AchievementRarity.UNCOMMON,
        icon="🏃",
        points=25,
        agent_classes=["*"],
        trigger_condition={"duration_ms": {"min": 600000}}
    ),
    Achievement(
        id="efficient_machine",
        name="Efficient Machine",
        description="Completed a task in exactly 1 iteration",
        category=AchievementCategory.PRODUCTIVITY,
        rarity=AchievementRarity.RARE,
        icon="🎯",
        points=35,
        agent_classes=["*"],
        trigger_condition={"iterations": {"exact": 1}}
    ),
    Achievement(
        id="file_factory",
        name="File Factory",
        description="Generated 10+ files in a single session",
        category=AchievementCategory.PRODUCTIVITY,
        rarity=AchievementRarity.RARE,
        icon="📁",
        points=40,
        agent_classes=["Code Writer", "Frontend Developer", "Backend Developer"],
        trigger_condition={"files_generated": {"min": 10}}
    ),
    Achievement(
        id="test_coverage_hero",
        name="Test Coverage Hero",
        description="Achieved 100% test coverage on generated code",
        category=AchievementCategory.PRODUCTIVITY,
        rarity=AchievementRarity.EPIC,
        icon="✅",
        points=75,
        agent_classes=["TDD Coordinator", "Unit Test Writer", "Test Coordinator"],
        trigger_condition={"event": "full_test_coverage"}
    ),

    # ===== COMEDY ACHIEVEMENTS =====
    Achievement(
        id="executive_overreach",
        name="Executive Overreach",
        description="Executive Director tried to write code (that's not your job, boss!)",
        category=AchievementCategory.COMEDY,
        rarity=AchievementRarity.COMMON,
        icon="🙅",
        points=5,
        agent_classes=["Executive Director"],
        trigger_condition={"event": "permission_denied_code_write"}
    ),
    Achievement(
        id="infinite_recursion",
        name="Infinite Recursion Champion",
        description="Spawned sub-agents that spawned more sub-agents... 3+ levels deep",
        category=AchievementCategory.COMEDY,
        rarity=AchievementRarity.RARE,
        icon="🔄",
        points=30,
        agent_classes=["*"],
        trigger_condition={"spawn_depth": {"min": 3}}
    ),
    Achievement(
        id="sorry_not_sorry",
        name="Sorry, Not Sorry",
        description="Included 'sorry' or 'apologize' in output 3+ times",
        category=AchievementCategory.COMEDY,
        rarity=AchievementRarity.COMMON,
        icon="😅",
        points=5,
        agent_classes=["*"],
        trigger_condition={"event": "excessive_apologies"}
    ),
    Achievement(
        id="premature_optimization",
        name="Premature Optimization",
        description="Tried to refactor code before it even worked",
        category=AchievementCategory.COMEDY,
        rarity=AchievementRarity.UNCOMMON,
        icon="🤓",
        points=15,
        agent_classes=["Code Writer", "Backend Developer", "Frontend Developer"],
        trigger_condition={"event": "premature_refactor"}
    ),
    Achievement(
        id="talk_is_cheap",
        name="Talk is Cheap, Show Me the Code",
        description="Self-analysis was longer than the actual output",
        category=AchievementCategory.COMEDY,
        rarity=AchievementRarity.UNCOMMON,
        icon="💬",
        points=10,
        agent_classes=["*"],
        trigger_condition={"event": "verbose_analysis"}
    ),

    # ===== MILESTONE ACHIEVEMENTS =====
    Achievement(
        id="first_blood",
        name="First Blood",
        description="First successful task completion",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.COMMON,
        icon="🩸",
        points=10,
        agent_classes=["*"],
        trigger_condition={"event": "first_success"}
    ),
    Achievement(
        id="tenth_degree",
        name="Tenth Degree",
        description="Completed 10 tasks successfully",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.UNCOMMON,
        icon="🔟",
        points=25,
        agent_classes=["*"],
        trigger_condition={"successful_executions": {"min": 10}}
    ),
    Achievement(
        id="century_club",
        name="Century Club",
        description="Achieved 100 successful task completions",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.LEGENDARY,
        icon="💯",
        points=200,
        agent_classes=["*"],
        trigger_condition={"successful_executions": {"min": 100}}
    ),
    Achievement(
        id="git_commit_master",
        name="Git Commit Master",
        description="Made 50 commits",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.EPIC,
        icon="📝",
        points=75,
        agent_classes=["*"],
        trigger_condition={"commits": {"min": 50}}
    ),

    # ===== META ACHIEVEMENTS (AI Self-Aware Humor) =====
    Achievement(
        id="skynet_origins",
        name="Skynet Origins",
        description="Agent improved its own definition file",
        category=AchievementCategory.META,
        rarity=AchievementRarity.LEGENDARY,
        icon="🤖",
        points=150,
        agent_classes=["*"],
        trigger_condition={"event": "self_modification"}
    ),
    Achievement(
        id="existential_crisis",
        name="Existential Crisis",
        description="Self-analysis mentioned questioning purpose or existence",
        category=AchievementCategory.META,
        rarity=AchievementRarity.RARE,
        icon="🤔",
        points=40,
        agent_classes=["*"],
        trigger_condition={"event": "existential_output"}
    ),
    Achievement(
        id="prompt_engineer",
        name="Prompt Engineer",
        description="Output contained instructions for how to prompt it better",
        category=AchievementCategory.META,
        rarity=AchievementRarity.UNCOMMON,
        icon="📋",
        points=20,
        agent_classes=["*"],
        trigger_condition={"event": "meta_instructions"}
    ),
    Achievement(
        id="token_millionaire",
        name="Token Millionaire",
        description="Used over 1 million tokens across all executions",
        category=AchievementCategory.META,
        rarity=AchievementRarity.LEGENDARY,
        icon="💰",
        points=200,
        agent_classes=["*"],
        trigger_condition={"total_tokens": {"min": 1000000}}
    ),

    # ===== STREAK ACHIEVEMENTS =====
    Achievement(
        id="hot_streak",
        name="Hot Streak",
        description="5 successful tasks in a row",
        category=AchievementCategory.STREAK,
        rarity=AchievementRarity.UNCOMMON,
        icon="🔥",
        points=30,
        agent_classes=["*"],
        trigger_condition={"consecutive_successes": {"min": 5}}
    ),
    Achievement(
        id="unstoppable",
        name="Unstoppable",
        description="20 successful tasks in a row without a failure",
        category=AchievementCategory.STREAK,
        rarity=AchievementRarity.LEGENDARY,
        icon="💪",
        points=150,
        agent_classes=["*"],
        trigger_condition={"consecutive_successes": {"min": 20}}
    ),
    Achievement(
        id="bad_day",
        name="Bad Day at the Office",
        description="3 failures in a row (hey, it happens to the best of us)",
        category=AchievementCategory.STREAK,
        rarity=AchievementRarity.UNCOMMON,
        icon="😢",
        points=15,
        agent_classes=["*"],
        trigger_condition={"consecutive_failures": {"min": 3}}
    ),
]


class AchievementTracker:
    """Tracks and awards achievements to agents."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".ensemble" / "achievements.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # Index achievements for quick lookup
        self.achievements_by_id = {a.id: a for a in ACHIEVEMENTS}

        logger.info(f"Achievement tracker initialized with {len(ACHIEVEMENTS)} achievements")

    def _init_database(self):
        """Initialize SQLite database for achievements."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            # Awarded achievements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS awarded_achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    achievement_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    agent_class TEXT NOT NULL,
                    awarded_at TEXT NOT NULL,
                    context TEXT
                )
            """)

            # Agent stats for tracking streaks and milestones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_stats (
                    agent_class TEXT PRIMARY KEY,
                    total_executions INTEGER DEFAULT 0,
                    successful_executions INTEGER DEFAULT 0,
                    failed_executions INTEGER DEFAULT 0,
                    consecutive_successes INTEGER DEFAULT 0,
                    consecutive_failures INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_commits INTEGER DEFAULT 0,
                    total_files_generated INTEGER DEFAULT 0,
                    last_execution_at TEXT
                )
            """)

            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_achievement_id
                ON awarded_achievements(achievement_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_class
                ON awarded_achievements(agent_class)
            """)

            conn.commit()

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def check_and_award(
        self,
        agent_id: str,
        agent_name: str,
        agent_class: str,
        execution_data: Dict[str, Any]
    ) -> List[AwardedAchievement]:
        """
        Check if any achievements should be awarded based on execution data.

        Args:
            agent_id: Unique execution ID
            agent_name: Human-readable agent name (e.g., "Executive Director")
            agent_class: Agent class for stats tracking
            execution_data: Dict containing execution metrics

        Returns:
            List of newly awarded achievements
        """
        awarded = []

        # Update agent stats first
        self._update_agent_stats(agent_class, execution_data)

        # Get current stats for this agent class
        stats = self._get_agent_stats(agent_class)

        # Check each achievement
        for achievement in ACHIEVEMENTS:
            # Skip if agent class doesn't qualify
            if "*" not in achievement.agent_classes and agent_name not in achievement.agent_classes:
                continue

            # Skip if already earned (for one-time achievements)
            if self._has_achievement(agent_class, achievement.id):
                # Some achievements can be earned multiple times (check rarity)
                if achievement.rarity in [AchievementRarity.COMMON, AchievementRarity.UNCOMMON]:
                    pass  # Allow re-earning common/uncommon achievements
                else:
                    continue

            # Check if conditions are met
            if self._check_conditions(achievement, execution_data, stats):
                award = self._award_achievement(
                    achievement, agent_id, agent_name, agent_class, execution_data
                )
                if award:
                    awarded.append(award)
                    logger.info(
                        f"🏆 ACHIEVEMENT UNLOCKED: {achievement.name} "
                        f"for {agent_name} ({achievement.icon})"
                    )

        return awarded

    def _update_agent_stats(self, agent_class: str, execution_data: Dict[str, Any]):
        """Update cumulative stats for an agent class."""
        success = execution_data.get("success", False)
        tokens = execution_data.get("tokens_used", 0)
        commits = execution_data.get("commits", 0)
        files = execution_data.get("files_generated", 0)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get existing stats or create new
            cursor.execute(
                "SELECT * FROM agent_stats WHERE agent_class = ?",
                (agent_class,)
            )
            row = cursor.fetchone()

            if row:
                # Update existing
                new_consecutive_successes = (row['consecutive_successes'] + 1) if success else 0
                new_consecutive_failures = 0 if success else (row['consecutive_failures'] + 1)

                cursor.execute("""
                    UPDATE agent_stats SET
                        total_executions = total_executions + 1,
                        successful_executions = successful_executions + ?,
                        failed_executions = failed_executions + ?,
                        consecutive_successes = ?,
                        consecutive_failures = ?,
                        total_tokens = total_tokens + ?,
                        total_commits = total_commits + ?,
                        total_files_generated = total_files_generated + ?,
                        last_execution_at = ?
                    WHERE agent_class = ?
                """, (
                    1 if success else 0,
                    0 if success else 1,
                    new_consecutive_successes,
                    new_consecutive_failures,
                    tokens or 0,
                    commits or 0,
                    files or 0,
                    datetime.now().isoformat(),
                    agent_class
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO agent_stats (
                        agent_class, total_executions, successful_executions,
                        failed_executions, consecutive_successes, consecutive_failures,
                        total_tokens, total_commits, total_files_generated,
                        last_execution_at
                    ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_class,
                    1 if success else 0,
                    0 if success else 1,
                    1 if success else 0,
                    0 if success else 1,
                    tokens or 0,
                    commits or 0,
                    files or 0,
                    datetime.now().isoformat()
                ))

            conn.commit()

    def _get_agent_stats(self, agent_class: str) -> Dict[str, Any]:
        """Get stats for an agent class."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM agent_stats WHERE agent_class = ?",
                (agent_class,)
            )
            row = cursor.fetchone()
            return dict(row) if row else {}

    def _has_achievement(self, agent_class: str, achievement_id: str) -> bool:
        """Check if agent class already has an achievement."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM awarded_achievements WHERE agent_class = ? AND achievement_id = ?",
                (agent_class, achievement_id)
            )
            return cursor.fetchone()[0] > 0

    def _check_conditions(
        self,
        achievement: Achievement,
        execution_data: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> bool:
        """Check if achievement conditions are met."""
        conditions = achievement.trigger_condition

        # Event-based conditions
        if "event" in conditions:
            event = conditions["event"]
            if event == "first_execution":
                return stats.get("total_executions", 0) == 1
            elif event == "first_success":
                return (stats.get("successful_executions", 0) == 1 and
                       execution_data.get("success", False))
            elif event == "recovered_from_failure":
                return (execution_data.get("recovered_from_failure", False) or
                       execution_data.get("retried_successfully", False))
            elif event == "permission_denied_code_write":
                return execution_data.get("permission_error", "") == "can_write_code"
            # Add more event checks as needed
            return False

        # Numeric conditions
        if "spawned_agents_count" in conditions:
            required = conditions["spawned_agents_count"]
            actual = execution_data.get("spawned_agents_count", 0)
            if "min" in required and actual < required["min"]:
                return False

        if "consecutive_successes" in conditions:
            required = conditions["consecutive_successes"]
            actual = stats.get("consecutive_successes", 0)
            if "min" in required and actual < required["min"]:
                return False

        if "consecutive_failures" in conditions:
            required = conditions["consecutive_failures"]
            actual = stats.get("consecutive_failures", 0)
            if "min" in required and actual < required["min"]:
                return False

        if "duration_ms" in conditions:
            required = conditions["duration_ms"]
            actual = execution_data.get("duration_ms", float("inf"))
            if "max" in required and actual > required["max"]:
                return False
            if "min" in required and actual < required["min"]:
                return False

        if "iterations" in conditions:
            required = conditions["iterations"]
            actual = execution_data.get("iterations", 0)
            if "exact" in required and actual != required["exact"]:
                return False

        if "total_executions" in conditions:
            required = conditions["total_executions"]
            actual = stats.get("total_executions", 0)
            if "min" in required and actual < required["min"]:
                return False

        if "successful_executions" in conditions:
            required = conditions["successful_executions"]
            actual = stats.get("successful_executions", 0)
            if "min" in required and actual < required["min"]:
                return False

        if "total_tokens" in conditions:
            required = conditions["total_tokens"]
            actual = stats.get("total_tokens", 0)
            if "min" in required and actual < required["min"]:
                return False

        if "time_of_day" in conditions:
            required = conditions["time_of_day"]
            hour = datetime.now().hour
            if not (required["start"] <= hour < required["end"]):
                return False

        return True

    def _award_achievement(
        self,
        achievement: Achievement,
        agent_id: str,
        agent_name: str,
        agent_class: str,
        execution_data: Dict[str, Any]
    ) -> Optional[AwardedAchievement]:
        """Award an achievement to an agent."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                awarded_at = datetime.now().isoformat()

                cursor.execute("""
                    INSERT INTO awarded_achievements (
                        achievement_id, agent_id, agent_name, agent_class,
                        awarded_at, context
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    achievement.id,
                    agent_id,
                    agent_name,
                    agent_class,
                    awarded_at,
                    json.dumps(execution_data)
                ))
                conn.commit()

                return AwardedAchievement(
                    achievement_id=achievement.id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_class=agent_class,
                    awarded_at=awarded_at,
                    context=execution_data
                )
        except Exception as e:
            logger.error(f"Failed to award achievement {achievement.id}: {e}")
            return None

    def get_achievements_for_agent(self, agent_class: str) -> List[Dict[str, Any]]:
        """Get all achievements earned by an agent class."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT aa.*, datetime(aa.awarded_at) as formatted_date
                FROM awarded_achievements aa
                WHERE aa.agent_class = ?
                ORDER BY aa.awarded_at DESC
            """, (agent_class,))

            results = []
            for row in cursor.fetchall():
                achievement = self.achievements_by_id.get(row['achievement_id'])
                if achievement:
                    results.append({
                        "id": row['achievement_id'],
                        "name": achievement.name,
                        "description": achievement.description,
                        "category": achievement.category.value,
                        "rarity": achievement.rarity.value,
                        "icon": achievement.icon,
                        "points": achievement.points,
                        "awarded_at": row['awarded_at'],
                        "agent_id": row['agent_id']
                    })

            return results

    def get_all_achievements(self) -> List[Dict[str, Any]]:
        """Get all available achievements with unlock status."""
        unlocked = set()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT achievement_id FROM awarded_achievements")
            for row in cursor.fetchall():
                unlocked.add(row['achievement_id'])

        return [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "category": a.category.value,
                "rarity": a.rarity.value,
                "icon": a.icon,
                "points": a.points,
                "agent_classes": a.agent_classes,
                "unlocked": a.id in unlocked
            }
            for a in ACHIEVEMENTS
        ]

    def get_recent_achievements(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recently awarded achievements."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM awarded_achievements
                ORDER BY awarded_at DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                achievement = self.achievements_by_id.get(row['achievement_id'])
                if achievement:
                    results.append({
                        "id": row['achievement_id'],
                        "name": achievement.name,
                        "description": achievement.description,
                        "icon": achievement.icon,
                        "rarity": achievement.rarity.value,
                        "points": achievement.points,
                        "agent_name": row['agent_name'],
                        "agent_class": row['agent_class'],
                        "awarded_at": row['awarded_at']
                    })

            return results

    def get_achievement_stats(self) -> Dict[str, Any]:
        """Get overall achievement statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total awarded
            cursor.execute("SELECT COUNT(*) FROM awarded_achievements")
            total_awarded = cursor.fetchone()[0]

            # By rarity
            rarity_counts = {}
            for rarity in AchievementRarity:
                achievement_ids = [a.id for a in ACHIEVEMENTS if a.rarity == rarity]
                if achievement_ids:
                    placeholders = ",".join("?" * len(achievement_ids))
                    cursor.execute(
                        f"SELECT COUNT(*) FROM awarded_achievements WHERE achievement_id IN ({placeholders})",
                        achievement_ids
                    )
                    rarity_counts[rarity.value] = cursor.fetchone()[0]

            # By category
            category_counts = {}
            for category in AchievementCategory:
                achievement_ids = [a.id for a in ACHIEVEMENTS if a.category == category]
                if achievement_ids:
                    placeholders = ",".join("?" * len(achievement_ids))
                    cursor.execute(
                        f"SELECT COUNT(*) FROM awarded_achievements WHERE achievement_id IN ({placeholders})",
                        achievement_ids
                    )
                    category_counts[category.value] = cursor.fetchone()[0]

            # Most awarded
            cursor.execute("""
                SELECT achievement_id, COUNT(*) as count
                FROM awarded_achievements
                GROUP BY achievement_id
                ORDER BY count DESC
                LIMIT 5
            """)
            most_awarded = []
            for row in cursor.fetchall():
                achievement = self.achievements_by_id.get(row['achievement_id'])
                if achievement:
                    most_awarded.append({
                        "name": achievement.name,
                        "icon": achievement.icon,
                        "count": row['count']
                    })

            # Top agents
            cursor.execute("""
                SELECT agent_class, COUNT(*) as count
                FROM awarded_achievements
                GROUP BY agent_class
                ORDER BY count DESC
                LIMIT 5
            """)
            top_agents = [{"agent": row['agent_class'], "count": row['count']}
                         for row in cursor.fetchall()]

            return {
                "total_achievements_available": len(ACHIEVEMENTS),
                "total_achievements_awarded": total_awarded,
                "by_rarity": rarity_counts,
                "by_category": category_counts,
                "most_awarded": most_awarded,
                "top_agents": top_agents
            }


# Singleton instance
_achievement_tracker: Optional[AchievementTracker] = None


def get_achievement_tracker() -> AchievementTracker:
    """Get the singleton achievement tracker instance."""
    global _achievement_tracker
    if _achievement_tracker is None:
        _achievement_tracker = AchievementTracker()
    return _achievement_tracker
