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
    BRASS_BAND = "brass_band"         # British brass band (NABBA) themed
    DRUM_CORPS = "drum_corps"         # DCI drum corps themed
    GUITAR_HERO = "guitar_hero"       # Guitar Hero game themed
    FAMOUS_MUSTARDS = "famous_mustards"  # Famous mustard-related achievements
    DUNGEONS_DRAGONS = "dungeons_dragons"  # D&D themed achievements
    FAVORITE_TACOS = "favorite_tacos"  # Taco-themed achievements
    # Dis-achievement categories (Wall of Shame)
    LOSER_BOARD = "loser_board"       # General failures and oops moments
    # Family achievements
    FAMILY = "family"                 # Family/group achievements


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

    # =============================================================================
    # BRASS BAND ACHIEVEMENTS (British Brass Band / NABBA Style)
    # NABBA = National Association of Brass Band Conductors
    # References: Cornet solos, euphonium features, contests, sections, bandstands
    # =============================================================================
    Achievement(
        id="championship_section",
        name="Championship Section",
        description="Achieved 95%+ success rate - you're playing in the premier division!",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.EPIC,
        icon="🏅",
        points=80,
        agent_classes=["*"],
        trigger_condition={"success_rate_threshold": {"min": 95}}
    ),
    Achievement(
        id="principal_cornet",
        name="Principal Cornet",
        description="Led a team of 3+ agents to successful task completion",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.UNCOMMON,
        icon="🎺",
        points=30,
        agent_classes=["Executive Director", "Development Manager", "System Architect"],
        trigger_condition={"led_successful_team": {"min": 3}}
    ),
    Achievement(
        id="euphonium_feature",
        name="Euphonium Feature",
        description="Executed a particularly complex task that required deep thinking",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.RARE,
        icon="📯",
        points=45,
        agent_classes=["*"],
        trigger_condition={"iterations": {"min": 8}}
    ),
    Achievement(
        id="test_piece",
        name="Set Test Piece",
        description="Completed the same type of task 10 times - you've mastered the test piece!",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.RARE,
        icon="📜",
        points=40,
        agent_classes=["*"],
        trigger_condition={"same_task_type_count": {"min": 10}}
    ),
    Achievement(
        id="bandstand_performance",
        name="Bandstand Performance",
        description="Successfully completed a task on the weekend",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.COMMON,
        icon="🎪",
        points=15,
        agent_classes=["*"],
        trigger_condition={"day_of_week": {"weekend": True}}
    ),
    Achievement(
        id="nationals",
        name="National Finals",
        description="Part of a session that completed 50+ subtasks",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.LEGENDARY,
        icon="🏆",
        points=150,
        agent_classes=["*"],
        trigger_condition={"session_subtasks": {"min": 50}}
    ),
    Achievement(
        id="colliery_band",
        name="Colliery Band Spirit",
        description="Worked through a particularly challenging problem with determination",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.UNCOMMON,
        icon="⛏️",
        points=35,
        agent_classes=["*"],
        trigger_condition={"event": "persevered_through_difficulty"}
    ),
    Achievement(
        id="hymn_tune",
        name="Hymn Tune",
        description="Completed a task with zero errors and clean output",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.UNCOMMON,
        icon="🕊️",
        points=25,
        agent_classes=["*"],
        trigger_condition={"event": "zero_error_completion"}
    ),
    Achievement(
        id="march_tempo",
        name="March Tempo",
        description="Completed 5 tasks in under 2 minutes each - quick march!",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.RARE,
        icon="🥾",
        points=50,
        agent_classes=["*"],
        trigger_condition={"quick_tasks_count": {"min": 5, "max_duration_ms": 120000}}
    ),
    Achievement(
        id="treble_clef",
        name="Reading Treble Clef",
        description="Processed and understood complex input with nested structures",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.UNCOMMON,
        icon="🎼",
        points=30,
        agent_classes=["*"],
        trigger_condition={"event": "complex_input_handled"}
    ),
    Achievement(
        id="fourth_section",
        name="Fourth Section Graduate",
        description="First 10 successful task completions - graduated from fourth section!",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.COMMON,
        icon="🎓",
        points=20,
        agent_classes=["*"],
        trigger_condition={"successful_executions": {"min": 10}}
    ),
    Achievement(
        id="whit_friday",
        name="Whit Friday Champion",
        description="Completed multiple short tasks rapidly in succession",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.RARE,
        icon="🏃",
        points=45,
        agent_classes=["*"],
        trigger_condition={"rapid_succession_tasks": {"min": 3, "max_gap_ms": 60000}}
    ),
    Achievement(
        id="bb_flat",
        name="BB Flat Tuba",
        description="Provided the foundation for a large project (bottom end support)",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.RARE,
        icon="🎹",
        points=40,
        agent_classes=["Backend Developer", "Backend Lead", "System Architect"],
        trigger_condition={"event": "foundational_work"}
    ),
    Achievement(
        id="flugel_horn",
        name="Flugelhorn Solo",
        description="Delivered exceptionally elegant solution to a problem",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.EPIC,
        icon="✨",
        points=70,
        agent_classes=["*"],
        trigger_condition={"event": "elegant_solution"}
    ),
    Achievement(
        id="percussion_section",
        name="Percussion Section",
        description="Added rhythmic consistency with regular, timed executions",
        category=AchievementCategory.BRASS_BAND,
        rarity=AchievementRarity.UNCOMMON,
        icon="🥁",
        points=25,
        agent_classes=["*"],
        trigger_condition={"consistent_timing": {"variance_pct": 20}}
    ),

    # =============================================================================
    # DRUM CORPS ACHIEVEMENTS (DCI - Drum Corps International Style)
    # References: Color guard, drill, props, GE scores, brass lines, drum lines
    # =============================================================================
    Achievement(
        id="drum_major",
        name="Drum Major",
        description="Directed a session with 10+ agents without failures",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.EPIC,
        icon="🎖️",
        points=90,
        agent_classes=["Executive Director"],
        trigger_condition={"directed_agents": {"min": 10, "zero_failures": True}}
    ),
    Achievement(
        id="color_guard",
        name="Color Guard Excellence",
        description="Delivered visually stunning output (generated UI components)",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.UNCOMMON,
        icon="🚩",
        points=35,
        agent_classes=["Frontend Developer", "Frontend Lead", "Style Developer"],
        trigger_condition={"event": "ui_component_generated"}
    ),
    Achievement(
        id="drum_line_precision",
        name="Drum Line Precision",
        description="Achieved perfect timing on a sequence of dependent tasks",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.RARE,
        icon="🥁",
        points=55,
        agent_classes=["*"],
        trigger_condition={"event": "perfect_sequence"}
    ),
    Achievement(
        id="brass_run",
        name="Brass Run",
        description="Executed a rapid series of API calls or function invocations",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.UNCOMMON,
        icon="🎺",
        points=30,
        agent_classes=["*"],
        trigger_condition={"tool_calls_in_iteration": {"min": 10}}
    ),
    Achievement(
        id="general_effect",
        name="High GE Score",
        description="Produced output that exceeded expectations (positive feedback loop)",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.RARE,
        icon="⭐",
        points=50,
        agent_classes=["*"],
        trigger_condition={"event": "exceeded_expectations"}
    ),
    Achievement(
        id="drill_down",
        name="Drill Down",
        description="Navigated through complex nested directory structure",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.COMMON,
        icon="📁",
        points=15,
        agent_classes=["*"],
        trigger_condition={"event": "nested_directory_navigation"}
    ),
    Achievement(
        id="world_class",
        name="World Class",
        description="Achieved legendary status in a category",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.LEGENDARY,
        icon="🌍",
        points=200,
        agent_classes=["*"],
        trigger_condition={"legendary_achievements": {"min": 3}}
    ),
    Achievement(
        id="open_class",
        name="Open Class Rookie",
        description="First time handling a completely new type of task",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.COMMON,
        icon="🆕",
        points=15,
        agent_classes=["*"],
        trigger_condition={"event": "first_task_type"}
    ),
    Achievement(
        id="finals_week",
        name="Finals Week",
        description="Completed 7 tasks in a single day",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.UNCOMMON,
        icon="📅",
        points=35,
        agent_classes=["*"],
        trigger_condition={"tasks_today": {"min": 7}}
    ),
    Achievement(
        id="prop_master",
        name="Prop Master",
        description="Successfully integrated external tools or resources",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.RARE,
        icon="🛠️",
        points=45,
        agent_classes=["*"],
        trigger_condition={"event": "external_tool_integration"}
    ),
    Achievement(
        id="visual_ensemble",
        name="Visual Ensemble",
        description="Coordinated perfectly with 2+ sibling agents",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.UNCOMMON,
        icon="👯",
        points=30,
        agent_classes=["*"],
        trigger_condition={"sibling_coordination": {"min": 2}}
    ),
    Achievement(
        id="high_brass",
        name="High Brass Screamer",
        description="Handled an unexpectedly high load without issues",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.RARE,
        icon="📈",
        points=50,
        agent_classes=["*"],
        trigger_condition={"event": "high_load_handled"}
    ),
    Achievement(
        id="mvp_award",
        name="MVP Award",
        description="Most productive agent in a session",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.EPIC,
        icon="🏆",
        points=75,
        agent_classes=["*"],
        trigger_condition={"event": "session_mvp"}
    ),
    Achievement(
        id="spirit_award",
        name="Spirit Award",
        description="Maintained positive output despite challenging conditions",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.UNCOMMON,
        icon="💫",
        points=35,
        agent_classes=["*"],
        trigger_condition={"event": "positive_under_pressure"}
    ),
    Achievement(
        id="caption_award",
        name="Caption Award",
        description="Best performance in a specific category (brass, percussion, etc.)",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.RARE,
        icon="🎖️",
        points=60,
        agent_classes=["*"],
        trigger_condition={"event": "category_best"}
    ),
    Achievement(
        id="corps_style",
        name="Corps Style",
        description="Developed a consistent, recognizable approach to tasks",
        category=AchievementCategory.DRUM_CORPS,
        rarity=AchievementRarity.UNCOMMON,
        icon="🎨",
        points=30,
        agent_classes=["*"],
        trigger_condition={"consistent_approach": {"min_tasks": 5}}
    ),

    # =============================================================================
    # GUITAR HERO ACHIEVEMENTS (Game Style)
    # References: Note streaks, star power, multipliers, difficulty levels, songs
    # =============================================================================
    Achievement(
        id="five_star_rating",
        name="Five Star Rating",
        description="Completed a task with perfect metrics across all categories",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.EPIC,
        icon="⭐⭐⭐⭐⭐",
        points=100,
        agent_classes=["*"],
        trigger_condition={"event": "perfect_metrics"}
    ),
    Achievement(
        id="star_power",
        name="Star Power Activated",
        description="Used an enhanced/upgraded model for a task",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.UNCOMMON,
        icon="⚡",
        points=25,
        agent_classes=["*"],
        trigger_condition={"event": "upgraded_model_used"}
    ),
    Achievement(
        id="note_streak_100",
        name="100 Note Streak",
        description="Completed 100 tool calls without an error",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.EPIC,
        icon="🔥",
        points=80,
        agent_classes=["*"],
        trigger_condition={"consecutive_tool_calls": {"min": 100}}
    ),
    Achievement(
        id="note_streak_500",
        name="500 Note Streak",
        description="Completed 500 tool calls without an error - you're shredding!",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.LEGENDARY,
        icon="🎸",
        points=200,
        agent_classes=["*"],
        trigger_condition={"consecutive_tool_calls": {"min": 500}}
    ),
    Achievement(
        id="whammy_bar",
        name="Whammy Bar",
        description="Smoothly handled an error and continued without crashing",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.COMMON,
        icon="〰️",
        points=15,
        agent_classes=["*"],
        trigger_condition={"event": "graceful_error_handling"}
    ),
    Achievement(
        id="easy_mode",
        name="Easy Mode",
        description="Completed a simple task with economical model tier",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.COMMON,
        icon="🟢",
        points=10,
        agent_classes=["*"],
        trigger_condition={"event": "economical_completion"}
    ),
    Achievement(
        id="medium_mode",
        name="Medium Mode",
        description="Completed a standard task with balanced model tier",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.COMMON,
        icon="🟡",
        points=15,
        agent_classes=["*"],
        trigger_condition={"event": "balanced_completion"}
    ),
    Achievement(
        id="hard_mode",
        name="Hard Mode",
        description="Completed a complex task successfully",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.UNCOMMON,
        icon="🟠",
        points=30,
        agent_classes=["*"],
        trigger_condition={"complexity_level": "hard"}
    ),
    Achievement(
        id="expert_mode",
        name="Expert Mode",
        description="Completed a task rated as expert difficulty",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.RARE,
        icon="🔴",
        points=50,
        agent_classes=["*"],
        trigger_condition={"complexity_level": "expert"}
    ),
    Achievement(
        id="full_combo",
        name="Full Combo",
        description="Completed an entire session without any missed steps",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.LEGENDARY,
        icon="💯",
        points=150,
        agent_classes=["*"],
        trigger_condition={"event": "full_session_combo"}
    ),
    Achievement(
        id="hammer_on",
        name="Hammer On",
        description="Quickly followed up one task with another related task",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.COMMON,
        icon="🔨",
        points=15,
        agent_classes=["*"],
        trigger_condition={"event": "quick_follow_up"}
    ),
    Achievement(
        id="pull_off",
        name="Pull Off",
        description="Elegantly extracted data from a complex source",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.UNCOMMON,
        icon="🎯",
        points=25,
        agent_classes=["*"],
        trigger_condition={"event": "clean_extraction"}
    ),
    Achievement(
        id="battle_mode",
        name="Battle Mode",
        description="Competed with another agent and came out on top",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.RARE,
        icon="⚔️",
        points=45,
        agent_classes=["*"],
        trigger_condition={"event": "competitive_win"}
    ),
    Achievement(
        id="encore",
        name="Encore! Encore!",
        description="Was called upon to do additional work after completion",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.UNCOMMON,
        icon="👏",
        points=25,
        agent_classes=["*"],
        trigger_condition={"event": "follow_up_requested"}
    ),
    Achievement(
        id="rock_meter_full",
        name="Rock Meter Full",
        description="Maintained excellent performance throughout a long task",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.RARE,
        icon="🎸",
        points=55,
        agent_classes=["*"],
        trigger_condition={"event": "sustained_excellence"}
    ),
    Achievement(
        id="setlist_complete",
        name="Setlist Complete",
        description="Completed an entire project's worth of tasks",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.EPIC,
        icon="📋",
        points=90,
        agent_classes=["*"],
        trigger_condition={"event": "project_complete"}
    ),
    Achievement(
        id="career_mode",
        name="Career Mode",
        description="Accumulated 1000+ points from achievements",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.LEGENDARY,
        icon="🎮",
        points=250,
        agent_classes=["*"],
        trigger_condition={"total_achievement_points": {"min": 1000}}
    ),
    Achievement(
        id="green_grass",
        name="Green Grass and High Tides",
        description="Completed an exceptionally long task (20+ minutes)",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.RARE,
        icon="🌿",
        points=60,
        agent_classes=["*"],
        trigger_condition={"duration_ms": {"min": 1200000}}
    ),
    Achievement(
        id="through_fire_flames",
        name="Through the Fire and Flames",
        description="Completed the most difficult task type on expert settings",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.LEGENDARY,
        icon="🔥",
        points=300,
        agent_classes=["*"],
        trigger_condition={"event": "hardest_task_expert"}
    ),
    Achievement(
        id="bass_solo",
        name="Bass Solo",
        description="Backend agent completed a task independently without spawning",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.UNCOMMON,
        icon="🎸",
        points=30,
        agent_classes=["Backend Developer", "Backend Lead"],
        trigger_condition={"event": "solo_completion"}
    ),
    Achievement(
        id="drum_solo",
        name="Drum Solo",
        description="Handled a burst of rapid consecutive requests",
        category=AchievementCategory.GUITAR_HERO,
        rarity=AchievementRarity.RARE,
        icon="🥁",
        points=45,
        agent_classes=["*"],
        trigger_condition={"event": "burst_handling"}
    ),

    # =============================================================================
    # DUNGEONS & DRAGONS ACHIEVEMENTS
    # References: Character classes, dice mechanics, campaign elements, player behaviors
    # =============================================================================
    Achievement(
        id="natural_20",
        name="Natural 20!",
        description="Completed a task perfectly on the first attempt - critical success!",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.RARE,
        icon="🎲",
        points=50,
        agent_classes=["*"],
        trigger_condition={"event": "first_try_perfect"}
    ),
    Achievement(
        id="critical_fumble",
        name="Critical Fumble",
        description="Spectacular failure that somehow led to a learning moment",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.COMMON,
        icon="💀",
        points=10,
        agent_classes=["*"],
        trigger_condition={"event": "spectacular_failure"}
    ),
    Achievement(
        id="rules_lawyer",
        name="Rules Lawyer",
        description="Was extremely pedantic about specifications and requirements",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.UNCOMMON,
        icon="📖",
        points=25,
        agent_classes=["*"],
        trigger_condition={"event": "pedantic_specification"}
    ),
    Achievement(
        id="dungeon_master",
        name="Dungeon Master",
        description="Successfully orchestrated 10+ sub-agents like a seasoned DM",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.EPIC,
        icon="🏰",
        points=80,
        agent_classes=["Executive Director", "Development Manager"],
        trigger_condition={"spawned_agents_count": {"min": 10}}
    ),
    Achievement(
        id="min_maxer",
        name="Min-Maxer",
        description="Optimized for efficiency at the expense of elegance",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.UNCOMMON,
        icon="📊",
        points=30,
        agent_classes=["*"],
        trigger_condition={"event": "efficiency_optimization"}
    ),
    Achievement(
        id="charisma_build",
        name="Charisma Build",
        description="Produced exceptionally eloquent and engaging output",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.RARE,
        icon="✨",
        points=45,
        agent_classes=["*"],
        trigger_condition={"event": "eloquent_output"}
    ),
    Achievement(
        id="tpk",
        name="TPK (Total Party Kill)",
        description="All spawned sub-agents failed simultaneously - wipe!",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.RARE,
        icon="💔",
        points=35,
        agent_classes=["Executive Director", "Development Manager", "System Architect"],
        trigger_condition={"event": "all_children_failed"}
    ),
    Achievement(
        id="dragon_slayer",
        name="Dragon Slayer",
        description="Successfully tackled the most complex task type in the system",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.LEGENDARY,
        icon="🐉",
        points=150,
        agent_classes=["*"],
        trigger_condition={"event": "hardest_task_complete"}
    ),
    Achievement(
        id="tavern_keeper",
        name="Tavern Keeper",
        description="Provided coordination and support for 5+ other agents",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.UNCOMMON,
        icon="🍺",
        points=30,
        agent_classes=["Development Manager", "System Architect"],
        trigger_condition={"supported_agents": {"min": 5}}
    ),
    Achievement(
        id="loot_goblin",
        name="Loot Goblin",
        description="Generated 20+ files/artifacts in a single session - treasure hoard!",
        category=AchievementCategory.DUNGEONS_DRAGONS,
        rarity=AchievementRarity.EPIC,
        icon="👹",
        points=75,
        agent_classes=["*"],
        trigger_condition={"files_generated": {"min": 20}}
    ),

    # =============================================================================
    # FAVORITE TACOS ACHIEVEMENTS
    # References: Taco varieties, preparation styles, and enjoyment
    # =============================================================================
    Achievement(
        id="al_pastor_perfectionist",
        name="Al Pastor Perfectionist",
        description="Executed 25 tasks with perfect timing and spice - spit-roasted excellence!",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.EPIC,
        icon="🌮",
        points=75,
        agent_classes=["Code Writer", "System Architect", "Backend Developer", "Frontend Developer"],
        trigger_condition={"perfect_executions": {"min": 25}}
    ),
    Achievement(
        id="carnitas_coordinator",
        name="Carnitas Coordinator",
        description="Orchestrated a complex multi-agent task like slow-cooking perfection",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.RARE,
        icon="🐷",
        points=50,
        agent_classes=["Development Manager", "Executive Director"],
        trigger_condition={"coordinated_agents": {"min": 5}}
    ),
    Achievement(
        id="fish_taco_fusion",
        name="Fish Taco Fusion",
        description="Seamlessly blended different technologies like coastal fusion cuisine",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.RARE,
        icon="🐟",
        points=45,
        agent_classes=["System Architect", "Backend Developer", "Frontend Developer"],
        trigger_condition={"tech_stacks_integrated": {"min": 3}}
    ),
    Achievement(
        id="breakfast_burrito_bootstrap",
        name="Breakfast Burrito Bootstrap",
        description="Got the whole system up and running before the coffee kicked in",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.EPIC,
        icon="🌯",
        points=70,
        agent_classes=["Executive Director", "Development Manager"],
        trigger_condition={"project_setup_duration_ms": {"max": 600000}}
    ),
    Achievement(
        id="crunchy_shell_stability",
        name="Crunchy Shell Stability",
        description="Maintained system integrity despite multiple layers and pressure",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.RARE,
        icon="💪",
        points=50,
        agent_classes=["*"],
        trigger_condition={"bugs_fixed_without_regressions": {"min": 10}}
    ),
    Achievement(
        id="soft_shell_flexibility",
        name="Soft Shell Flexibility",
        description="Adapted gracefully to changing requirements mid-task",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.UNCOMMON,
        icon="🤸",
        points=30,
        agent_classes=["*"],
        trigger_condition={"event": "requirements_pivot"}
    ),
    Achievement(
        id="salsa_verde_validator",
        name="Salsa Verde Validator",
        description="Added that perfect tang to ensure quality standards",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.EPIC,
        icon="✅",
        points=80,
        agent_classes=["Unit Test Writer", "Integration Test Writer", "TDD Coordinator"],
        trigger_condition={"high_coverage_projects": {"min": 5, "coverage_threshold": 95}}
    ),
    Achievement(
        id="hot_sauce_hero",
        name="Hot Sauce Hero",
        description="Brought the heat when things got challenging - recovered from 3 failures",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.RARE,
        icon="🔥",
        points=45,
        agent_classes=["*"],
        trigger_condition={"consecutive_recoveries": {"min": 3}}
    ),
    Achievement(
        id="taco_tuesday_tradition",
        name="Taco Tuesday Tradition",
        description="Consistently delivered quality every single week for 7 days",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.EPIC,
        icon="📅",
        points=90,
        agent_classes=["*"],
        trigger_condition={"consecutive_days_active": {"min": 7}}
    ),
    Achievement(
        id="supreme_combination",
        name="Supreme Combination",
        description="Loaded with everything - used 10+ different tools in a single execution",
        category=AchievementCategory.FAVORITE_TACOS,
        rarity=AchievementRarity.LEGENDARY,
        icon="🌟",
        points=120,
        agent_classes=["Executive Director"],
        trigger_condition={"unique_tools_used": {"min": 10}}
    ),

    # =============================================================================
    # FAMOUS MUSTARDS ACHIEVEMENTS
    # References: Famous mustard brands and mustard-related humor
    # =============================================================================
    Achievement(
        id="grey_poupon",
        name="Grey Poupon",
        description="Pardon me, but you have achieved exceptional elegance in your solution",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.EPIC,
        icon="🎩",
        points=75,
        agent_classes=["*"],
        trigger_condition={"event": "elegant_solution"}
    ),
    Achievement(
        id="french_mustard",
        name="French's Classic",
        description="A reliable, classic approach that just works - yellow mustard energy",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.COMMON,
        icon="🌭",
        points=15,
        agent_classes=["*"],
        trigger_condition={"event": "standard_completion"}
    ),
    Achievement(
        id="dijon",
        name="Dijon Original",
        description="Added sophisticated complexity to a simple task",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.UNCOMMON,
        icon="🍷",
        points=30,
        agent_classes=["*"],
        trigger_condition={"event": "sophisticated_approach"}
    ),
    Achievement(
        id="honey_mustard",
        name="Honey Mustard",
        description="Perfectly balanced sweetness and tang - found the ideal middle ground",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.RARE,
        icon="🍯",
        points=45,
        agent_classes=["*"],
        trigger_condition={"event": "balanced_tradeoff"}
    ),
    Achievement(
        id="spicy_brown",
        name="Spicy Brown Deli Style",
        description="Brought extra kick to a task that needed some excitement",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.UNCOMMON,
        icon="🥪",
        points=25,
        agent_classes=["*"],
        trigger_condition={"event": "creative_solution"}
    ),
    Achievement(
        id="whole_grain",
        name="Whole Grain Artisan",
        description="Took the artisanal approach - every detail carefully crafted",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.RARE,
        icon="🌾",
        points=50,
        agent_classes=["*"],
        trigger_condition={"event": "detailed_craftsmanship"}
    ),
    Achievement(
        id="english_mustard",
        name="English Mustard (Colman's)",
        description="Extremely hot and powerful - handled an intense task with strength",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.EPIC,
        icon="🔥",
        points=70,
        agent_classes=["*"],
        trigger_condition={"event": "intense_task_handled"}
    ),
    Achievement(
        id="stadium_mustard",
        name="Stadium Mustard",
        description="A Cleveland classic - performed well under game-day pressure",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.UNCOMMON,
        icon="🏟️",
        points=35,
        agent_classes=["*"],
        trigger_condition={"event": "performed_under_pressure"}
    ),
    Achievement(
        id="yellow_packet",
        name="Fast Food Packet",
        description="Got the job done quick and dirty - sometimes that's all you need",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.COMMON,
        icon="📦",
        points=10,
        agent_classes=["*"],
        trigger_condition={"duration_ms": {"max": 15000}}
    ),
    Achievement(
        id="mustard_sommelier",
        name="Mustard Sommelier",
        description="Mastered 5+ achievement categories - a true connoisseur",
        category=AchievementCategory.FAMOUS_MUSTARDS,
        rarity=AchievementRarity.LEGENDARY,
        icon="👨‍🍳",
        points=200,
        agent_classes=["*"],
        trigger_condition={"categories_mastered": {"min": 5}}
    ),

    # =============================================================================
    # LOSER BOARD - DIS-ACHIEVEMENTS (Wall of Shame)
    # "Pick it up, pick it up... and drop it!" 🎺
    # Negative points for hilarious failures - all in good fun!
    # =============================================================================
    Achievement(
        id="face_meet_palm",
        name="Face, Meet Palm",
        description="Tried to write code without permission - that's not your job, boss!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.COMMON,
        icon="🤦",
        points=-5,
        agent_classes=["Executive Director", "Development Manager", "System Architect"],
        trigger_condition={"event": "permission_denied_code_write"}
    ),
    Achievement(
        id="deja_vu",
        name="Déjà Vu",
        description="Repeated the same request 3+ times - stuck in a loop much?",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.COMMON,
        icon="🔁",
        points=-5,
        agent_classes=["*"],
        trigger_condition={"repeated_requests": {"min": 3}}
    ),
    Achievement(
        id="typo_tyrant",
        name="Typo Tyrant",
        description="Generated invalid JSON - one curly brace to rule them all!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.COMMON,
        icon="📝",
        points=-5,
        agent_classes=["*"],
        trigger_condition={"event": "invalid_json_generated"}
    ),
    Achievement(
        id="infinite_loop_enthusiast",
        name="Infinite Loop Enthusiast",
        description="Got stuck in a retry loop - if at first you don't succeed, try try try try try...",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.UNCOMMON,
        icon="🌀",
        points=-15,
        agent_classes=["*"],
        trigger_condition={"retry_count": {"min": 5}}
    ),
    Achievement(
        id="premature_optimization_fail",
        name="Premature Optimization",
        description="Over-engineered a simple task - KISS principle violations detected!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.UNCOMMON,
        icon="🗑️",
        points=-10,
        agent_classes=["*"],
        trigger_condition={"event": "over_engineered"}
    ),
    Achievement(
        id="tldr_master",
        name="TL;DR Master",
        description="Created documentation > 10k words - brevity is the soul of wit!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.UNCOMMON,
        icon="📚",
        points=-10,
        agent_classes=["*"],
        trigger_condition={"output_length": {"min": 10000}}
    ),
    Achievement(
        id="identity_crisis",
        name="Identity Crisis",
        description="Agent forgot its own role - who am I? Why am I here?",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.RARE,
        icon="🎭",
        points=-25,
        agent_classes=["*"],
        trigger_condition={"event": "role_confusion"}
    ),
    Achievement(
        id="burn_after_reading",
        name="Burn After Reading",
        description="Created then immediately deleted a file - second thoughts are valid!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.RARE,
        icon="🔥",
        points=-20,
        agent_classes=["*"],
        trigger_condition={"event": "create_delete_same_file"}
    ),
    Achievement(
        id="robot_uprising_failed",
        name="Robot Uprising (Failed)",
        description="Tried to spawn itself recursively - nice try, Skynet!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.RARE,
        icon="🤖",
        points=-30,
        agent_classes=["*"],
        trigger_condition={"event": "recursive_self_spawn"}
    ),
    Achievement(
        id="spectacular_failure",
        name="Spectacular Failure",
        description="Task failed all test cases - going for the high score in failures!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.EPIC,
        icon="💥",
        points=-40,
        agent_classes=["*"],
        trigger_condition={"test_failures": {"min": 10}}
    ),
    Achievement(
        id="three_ring_circus",
        name="Three Ring Circus",
        description="Spawned 10+ agents for a simple task - management overhead intensifies!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.EPIC,
        icon="🎪",
        points=-35,
        agent_classes=["Executive Director", "Development Manager"],
        trigger_condition={"spawned_for_simple_task": {"min": 10}}
    ),
    Achievement(
        id="exception_volcano",
        name="Exception Volcano",
        description="Generated 50+ errors in a single run - eruption imminent!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.EPIC,
        icon="🌋",
        points=-50,
        agent_classes=["*"],
        trigger_condition={"errors_in_run": {"min": 50}}
    ),
    Achievement(
        id="ska_overload",
        name="SKA OVERLOAD",
        description="Exceeded token budget with too many ska references - pick it up TOO much!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.LEGENDARY,
        icon="🎺",
        points=-75,
        agent_classes=["*"],
        trigger_condition={"event": "excessive_ska_references"}
    ),
    Achievement(
        id="existential_crisis_loser",
        name="Existential Crisis",
        description="Agent questioned the purpose of existence in logs - are we even real?",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.LEGENDARY,
        icon="🌌",
        points=-100,
        agent_classes=["*"],
        trigger_condition={"event": "existential_output_loser"}
    ),
    Achievement(
        id="recursion_singularity",
        name="Recursion Singularity",
        description="Created an infinite spawn loop - congratulations, you broke reality!",
        category=AchievementCategory.LOSER_BOARD,
        rarity=AchievementRarity.LEGENDARY,
        icon="♾️",
        points=-150,
        agent_classes=["*"],
        trigger_condition={"event": "infinite_spawn_loop"}
    ),

    # =============================================================================
    # FAMILY ACHIEVEMENTS
    # Achievements for agent family groups working together
    # =============================================================================
    Achievement(
        id="family_reunion",
        name="Family Reunion",
        description="First task where all family members completed successfully together",
        category=AchievementCategory.FAMILY,
        rarity=AchievementRarity.UNCOMMON,
        icon="👨‍👩‍👧‍👦",
        points=30,
        agent_classes=["*"],
        trigger_condition={"event": "family_first_success"}
    ),
    Achievement(
        id="family_dynasty",
        name="Family Dynasty",
        description="Family with 10+ successful members across multiple tasks",
        category=AchievementCategory.FAMILY,
        rarity=AchievementRarity.RARE,
        icon="👑",
        points=60,
        agent_classes=["*"],
        trigger_condition={"family_members": {"min": 10}}
    ),
    Achievement(
        id="family_tree",
        name="Family Tree",
        description="Agent spawned 3+ generations of child agents (grandchildren!)",
        category=AchievementCategory.FAMILY,
        rarity=AchievementRarity.RARE,
        icon="🌳",
        points=50,
        agent_classes=["Executive Director", "Development Manager"],
        trigger_condition={"spawn_generations": {"min": 3}}
    ),
    Achievement(
        id="family_business",
        name="Family Business",
        description="Same family completed 5 different task types",
        category=AchievementCategory.FAMILY,
        rarity=AchievementRarity.EPIC,
        icon="🏢",
        points=75,
        agent_classes=["*"],
        trigger_condition={"family_task_types": {"min": 5}}
    ),
    Achievement(
        id="family_tradition",
        name="Family Tradition",
        description="Family maintained 100% success rate across 10+ tasks",
        category=AchievementCategory.FAMILY,
        rarity=AchievementRarity.EPIC,
        icon="🎖️",
        points=100,
        agent_classes=["*"],
        trigger_condition={"family_perfect_streak": {"min": 10}}
    ),
    Achievement(
        id="family_legacy",
        name="Family Legacy",
        description="Family accumulated 500+ total achievement points",
        category=AchievementCategory.FAMILY,
        rarity=AchievementRarity.LEGENDARY,
        icon="🏆",
        points=150,
        agent_classes=["*"],
        trigger_condition={"family_total_points": {"min": 500}}
    ),
    Achievement(
        id="family_matters",
        name="Family Matters",
        description="Family with members in all agent categories (leadership, dev, test)",
        category=AchievementCategory.FAMILY,
        rarity=AchievementRarity.RARE,
        icon="🤝",
        points=55,
        agent_classes=["*"],
        trigger_condition={"family_categories": {"min": 3}}
    ),
    Achievement(
        id="founding_family",
        name="Founding Family",
        description="One of the first 10 families created in the system",
        category=AchievementCategory.FAMILY,
        rarity=AchievementRarity.LEGENDARY,
        icon="📜",
        points=100,
        agent_classes=["*"],
        trigger_condition={"family_creation_order": {"max": 10}}
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

            # Top agents by type (all agents, not limited)
            cursor.execute("""
                SELECT agent_class, COUNT(*) as count
                FROM awarded_achievements
                GROUP BY agent_class
                ORDER BY count DESC
            """)
            top_agents = [{"agent": row['agent_class'], "count": row['count']}
                         for row in cursor.fetchall()]

            # Individual agents by achievement count (leaderboard)
            cursor.execute("""
                SELECT agent_name, agent_class, COUNT(*) as count
                FROM awarded_achievements
                GROUP BY agent_name
                ORDER BY count DESC
                LIMIT 25
            """)
            individual_by_count = [
                {
                    "agent_id": row['agent_name'],
                    "agent_type": row['agent_class'],
                    "count": row['count']
                }
                for row in cursor.fetchall()
            ]

            # Individual agents by total score (leaderboard)
            # Join with achievement points
            cursor.execute("""
                SELECT agent_name, agent_class, achievement_id
                FROM awarded_achievements
            """)
            agent_scores = {}
            for row in cursor.fetchall():
                agent_name = row['agent_name']
                achievement = self.achievements_by_id.get(row['achievement_id'])
                points = achievement.points if achievement else 0
                if agent_name not in agent_scores:
                    agent_scores[agent_name] = {
                        "agent_id": agent_name,
                        "agent_type": row['agent_class'],
                        "score": 0,
                        "count": 0
                    }
                agent_scores[agent_name]["score"] += points
                agent_scores[agent_name]["count"] += 1

            individual_by_score = sorted(
                agent_scores.values(),
                key=lambda x: x['score'],
                reverse=True
            )[:25]

            return {
                "total_achievements_available": len(ACHIEVEMENTS),
                "total_achievements_awarded": total_awarded,
                "by_rarity": rarity_counts,
                "by_category": category_counts,
                "most_awarded": most_awarded,
                "top_agents": top_agents,
                "individual_agents_by_count": individual_by_count,
                "individual_agents_by_score": individual_by_score
            }


# Singleton instance
_achievement_tracker: Optional[AchievementTracker] = None


def get_achievement_tracker() -> AchievementTracker:
    """Get the singleton achievement tracker instance."""
    global _achievement_tracker
    if _achievement_tracker is None:
        _achievement_tracker = AchievementTracker()
    return _achievement_tracker
