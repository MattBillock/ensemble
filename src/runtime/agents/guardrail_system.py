"""
Negative Guardrail System - Learn from failures and reinforce agent definitions.

This system:
1. Tracks guardrails that have proven effective
2. Learns from failures to generate new guardrails
3. Applies guardrails dynamically to prompts and agent definitions
4. Provides recommendations for agent definition improvements
"""
import json
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class GuardrailCategory(Enum):
    """Categories of negative guardrails."""
    SCOPE = "scope"                # Prevent scope creep
    QUALITY = "quality"            # Ensure quality standards
    PROCESS = "process"            # Enforce process discipline
    RESOURCE = "resource"          # Limit resource usage
    SAFETY = "safety"              # Prevent dangerous operations
    COMPLETENESS = "completeness"  # Ensure task completion
    FOCUS = "focus"                # Maintain focus on task


@dataclass
class Guardrail:
    """A negative guardrail rule."""
    id: str
    text: str
    category: GuardrailCategory
    agent_types: List[str]  # Which agent types this applies to ("*" for all)
    severity: str  # "critical", "important", "advisory"
    success_rate: float = 0.0  # How often this guardrail prevents failures
    times_applied: int = 0
    times_helped: int = 0
    created_at: str = ""
    source: str = ""  # "manual", "learned", "imported"


@dataclass
class FailurePattern:
    """A pattern extracted from agent failures."""
    pattern_id: str
    failure_type: str
    description: str
    agent_types: List[str]
    occurrences: int = 0
    suggested_guardrail: str = ""
    confidence: float = 0.0


# Standard guardrails that should be applied universally
UNIVERSAL_GUARDRAILS = [
    Guardrail(
        id="scope_001",
        text="Do NOT implement features not explicitly requested in the task",
        category=GuardrailCategory.SCOPE,
        agent_types=["*"],
        severity="critical",
        source="manual"
    ),
    Guardrail(
        id="scope_002",
        text="NEVER modify files outside the explicitly specified scope",
        category=GuardrailCategory.SCOPE,
        agent_types=["*"],
        severity="critical",
        source="manual"
    ),
    Guardrail(
        id="scope_003",
        text="Do NOT add 'nice to have' improvements or refactoring beyond the task",
        category=GuardrailCategory.SCOPE,
        agent_types=["*"],
        severity="important",
        source="manual"
    ),
    Guardrail(
        id="quality_001",
        text="NEVER leave placeholder code, TODOs, or incomplete implementations",
        category=GuardrailCategory.QUALITY,
        agent_types=["developers/*"],
        severity="critical",
        source="manual"
    ),
    Guardrail(
        id="quality_002",
        text="Do NOT skip error handling or edge cases mentioned in requirements",
        category=GuardrailCategory.QUALITY,
        agent_types=["developers/*"],
        severity="important",
        source="manual"
    ),
    Guardrail(
        id="process_001",
        text="NEVER proceed with ambiguous requirements - ask for clarification instead",
        category=GuardrailCategory.PROCESS,
        agent_types=["*"],
        severity="critical",
        source="manual"
    ),
    Guardrail(
        id="process_002",
        text="Do NOT retry the same approach more than 3 times without changing strategy",
        category=GuardrailCategory.PROCESS,
        agent_types=["*"],
        severity="important",
        source="manual"
    ),
    Guardrail(
        id="resource_001",
        text="NEVER create more than 10 files in a single task without explicit approval",
        category=GuardrailCategory.RESOURCE,
        agent_types=["developers/*"],
        severity="important",
        source="manual"
    ),
    Guardrail(
        id="resource_002",
        text="Do NOT spawn more than 5 sub-agents without completing and reviewing first",
        category=GuardrailCategory.RESOURCE,
        agent_types=["leadership/*", "coordinators/*"],
        severity="important",
        source="manual"
    ),
    Guardrail(
        id="completeness_001",
        text="NEVER consider a task complete without verifying all explicit requirements are met",
        category=GuardrailCategory.COMPLETENESS,
        agent_types=["*"],
        severity="critical",
        source="manual"
    ),
    Guardrail(
        id="completeness_002",
        text="Do NOT move on from a step until it is fully implemented and tested",
        category=GuardrailCategory.COMPLETENESS,
        agent_types=["developers/*"],
        severity="important",
        source="manual"
    ),
    Guardrail(
        id="focus_001",
        text="NEVER work on tangential improvements - stay focused on the explicit task",
        category=GuardrailCategory.FOCUS,
        agent_types=["*"],
        severity="important",
        source="manual"
    ),
    Guardrail(
        id="safety_001",
        text="Do NOT execute destructive operations without explicit confirmation",
        category=GuardrailCategory.SAFETY,
        agent_types=["*"],
        severity="critical",
        source="manual"
    ),
    Guardrail(
        id="safety_002",
        text="NEVER store or log sensitive data (passwords, API keys, tokens)",
        category=GuardrailCategory.SAFETY,
        agent_types=["*"],
        severity="critical",
        source="manual"
    ),
]

# Agent-specific guardrails
AGENT_SPECIFIC_GUARDRAILS = {
    "developers/code_writer": [
        Guardrail(
            id="cw_001",
            text="Do NOT add dependencies not already in requirements.txt or package.json",
            category=GuardrailCategory.SCOPE,
            agent_types=["developers/code_writer"],
            severity="important",
            source="manual"
        ),
        Guardrail(
            id="cw_002",
            text="NEVER modify existing tests unless explicitly asked to do so",
            category=GuardrailCategory.SCOPE,
            agent_types=["developers/code_writer"],
            severity="important",
            source="manual"
        ),
        Guardrail(
            id="cw_003",
            text="Do NOT create abstractions or utilities for single-use code",
            category=GuardrailCategory.QUALITY,
            agent_types=["developers/code_writer"],
            severity="advisory",
            source="manual"
        ),
    ],
    "developers/refactoring_specialist": [
        Guardrail(
            id="rs_001",
            text="NEVER change public API signatures without explicit approval",
            category=GuardrailCategory.SCOPE,
            agent_types=["developers/refactoring_specialist"],
            severity="critical",
            source="manual"
        ),
        Guardrail(
            id="rs_002",
            text="Do NOT remove existing functionality, even if it seems unused",
            category=GuardrailCategory.SAFETY,
            agent_types=["developers/refactoring_specialist"],
            severity="critical",
            source="manual"
        ),
    ],
    "testers/unit_test_writer": [
        Guardrail(
            id="ut_001",
            text="NEVER modify production code - only create test files",
            category=GuardrailCategory.SCOPE,
            agent_types=["testers/unit_test_writer"],
            severity="critical",
            source="manual"
        ),
        Guardrail(
            id="ut_002",
            text="Do NOT use real external services or credentials in tests",
            category=GuardrailCategory.SAFETY,
            agent_types=["testers/unit_test_writer"],
            severity="critical",
            source="manual"
        ),
    ],
    "leadership/executive_director": [
        Guardrail(
            id="ed_001",
            text="NEVER write code directly - always delegate to appropriate specialists",
            category=GuardrailCategory.PROCESS,
            agent_types=["leadership/executive_director"],
            severity="critical",
            source="manual"
        ),
        Guardrail(
            id="ed_002",
            text="Do NOT spawn all agents at once - coordinate sequentially when tasks depend on each other",
            category=GuardrailCategory.RESOURCE,
            agent_types=["leadership/executive_director"],
            severity="important",
            source="manual"
        ),
    ],
}


class GuardrailSystem:
    """
    Central system for managing and applying negative guardrails.

    Features:
    - Stores and retrieves guardrails from SQLite
    - Learns new guardrails from failure patterns
    - Applies guardrails to prompts dynamically
    - Tracks effectiveness of guardrails
    """

    _instance = None

    def __new__(cls, db_path: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[Path] = None):
        if self._initialized:
            return

        self.db_path = db_path or Path.home() / ".ensemble" / "guardrails.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        self._load_standard_guardrails()
        self._initialized = True

        logger.info(f"GuardrailSystem initialized with database: {self.db_path}")

    def _init_database(self):
        """Initialize the guardrails database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS guardrails (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    category TEXT NOT NULL,
                    agent_types TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.0,
                    times_applied INTEGER DEFAULT 0,
                    times_helped INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT DEFAULT 'manual'
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS failure_patterns (
                    id TEXT PRIMARY KEY,
                    failure_type TEXT NOT NULL,
                    description TEXT,
                    agent_types TEXT NOT NULL,
                    occurrences INTEGER DEFAULT 0,
                    suggested_guardrail TEXT,
                    confidence REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS guardrail_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guardrail_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    session_id TEXT,
                    result TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guardrail_id) REFERENCES guardrails(id)
                )
            """)

            conn.commit()

    def _load_standard_guardrails(self):
        """Load standard guardrails into the database if not present."""
        with sqlite3.connect(str(self.db_path)) as conn:
            for g in UNIVERSAL_GUARDRAILS:
                conn.execute("""
                    INSERT OR IGNORE INTO guardrails
                    (id, text, category, agent_types, severity, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (g.id, g.text, g.category.value, json.dumps(g.agent_types),
                      g.severity, g.source))

            for agent_type, guardrails in AGENT_SPECIFIC_GUARDRAILS.items():
                for g in guardrails:
                    conn.execute("""
                        INSERT OR IGNORE INTO guardrails
                        (id, text, category, agent_types, severity, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (g.id, g.text, g.category.value, json.dumps(g.agent_types),
                          g.severity, g.source))

            conn.commit()

    def get_guardrails_for_agent(
        self,
        agent_type: str,
        categories: Optional[List[GuardrailCategory]] = None,
        severity_min: str = "advisory"
    ) -> List[Guardrail]:
        """Get applicable guardrails for a specific agent type."""
        severity_order = {"advisory": 0, "important": 1, "critical": 2}
        min_severity = severity_order.get(severity_min, 0)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute("""
                SELECT * FROM guardrails
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 0
                        WHEN 'important' THEN 1
                        ELSE 2
                    END,
                    success_rate DESC
            """).fetchall()

            guardrails = []
            for row in rows:
                row_dict = dict(row)
                agent_types = json.loads(row_dict['agent_types'])

                # Check if this guardrail applies to this agent
                applies = False
                for at in agent_types:
                    if at == "*":
                        applies = True
                        break
                    if at.endswith("/*"):
                        # Wildcard match for category
                        prefix = at[:-1]  # Remove "*"
                        if agent_type.startswith(prefix):
                            applies = True
                            break
                    if at == agent_type:
                        applies = True
                        break

                if not applies:
                    continue

                # Check severity
                if severity_order.get(row_dict['severity'], 0) < min_severity:
                    continue

                # Check category filter
                if categories:
                    if row_dict['category'] not in [c.value for c in categories]:
                        continue

                guardrails.append(Guardrail(
                    id=row_dict['id'],
                    text=row_dict['text'],
                    category=GuardrailCategory(row_dict['category']),
                    agent_types=agent_types,
                    severity=row_dict['severity'],
                    success_rate=row_dict['success_rate'],
                    times_applied=row_dict['times_applied'],
                    times_helped=row_dict['times_helped'],
                    created_at=row_dict['created_at'],
                    source=row_dict['source']
                ))

            return guardrails

    def apply_guardrails_to_prompt(
        self,
        prompt: str,
        agent_type: str,
        categories: Optional[List[GuardrailCategory]] = None,
        max_guardrails: int = 10
    ) -> Tuple[str, List[str]]:
        """
        Apply guardrails to a prompt, returning the enhanced prompt.

        Returns:
            Tuple of (enhanced_prompt, list_of_applied_guardrail_ids)
        """
        guardrails = self.get_guardrails_for_agent(
            agent_type,
            categories=categories,
            severity_min="important"
        )[:max_guardrails]

        if not guardrails:
            return prompt, []

        # Build guardrails section
        guardrail_text = "\n\n**CRITICAL CONSTRAINTS (Do NOT violate these):**\n"
        applied_ids = []

        for g in guardrails:
            guardrail_text += f"- {g.text}\n"
            applied_ids.append(g.id)

        # Insert guardrails after the first paragraph or at the end
        if "\n\n" in prompt:
            parts = prompt.split("\n\n", 1)
            enhanced_prompt = parts[0] + guardrail_text + "\n" + parts[1]
        else:
            enhanced_prompt = prompt + guardrail_text

        # Update application count
        self._record_guardrail_applications(applied_ids)

        return enhanced_prompt, applied_ids

    def _record_guardrail_applications(self, guardrail_ids: List[str]):
        """Record that guardrails were applied."""
        with sqlite3.connect(str(self.db_path)) as conn:
            for gid in guardrail_ids:
                conn.execute("""
                    UPDATE guardrails
                    SET times_applied = times_applied + 1
                    WHERE id = ?
                """, (gid,))
            conn.commit()

    def record_guardrail_outcome(
        self,
        guardrail_ids: List[str],
        agent_id: str,
        session_id: str,
        success: bool
    ):
        """Record whether guardrails helped prevent failure."""
        with sqlite3.connect(str(self.db_path)) as conn:
            result = "success" if success else "failure"

            for gid in guardrail_ids:
                conn.execute("""
                    INSERT INTO guardrail_applications
                    (guardrail_id, agent_id, session_id, result)
                    VALUES (?, ?, ?, ?)
                """, (gid, agent_id, session_id, result))

                if success:
                    conn.execute("""
                        UPDATE guardrails
                        SET times_helped = times_helped + 1
                        WHERE id = ?
                    """, (gid,))

            # Recalculate success rates
            for gid in guardrail_ids:
                row = conn.execute("""
                    SELECT times_applied, times_helped FROM guardrails
                    WHERE id = ?
                """, (gid,)).fetchone()

                if row and row[0] > 0:
                    success_rate = row[1] / row[0]
                    conn.execute("""
                        UPDATE guardrails SET success_rate = ? WHERE id = ?
                    """, (success_rate, gid))

            conn.commit()

    def learn_from_failure(
        self,
        agent_type: str,
        failure_type: str,
        failure_description: str,
        context: Dict[str, Any]
    ) -> Optional[Guardrail]:
        """
        Learn a new guardrail from a failure.

        Returns the newly created guardrail if one was learned.
        """
        # Analyze failure and generate guardrail
        suggested_guardrail = self._generate_guardrail_from_failure(
            agent_type, failure_type, failure_description, context
        )

        if not suggested_guardrail:
            return None

        # Record the pattern
        pattern_id = f"pattern_{failure_type}_{hash(failure_description) % 10000:04d}"

        with sqlite3.connect(str(self.db_path)) as conn:
            # Check if pattern exists
            existing = conn.execute("""
                SELECT occurrences FROM failure_patterns WHERE id = ?
            """, (pattern_id,)).fetchone()

            if existing:
                # Update occurrence count
                conn.execute("""
                    UPDATE failure_patterns
                    SET occurrences = occurrences + 1
                    WHERE id = ?
                """, (pattern_id,))

                # If pattern is common enough, promote guardrail
                if existing[0] >= 2:
                    self._promote_learned_guardrail(pattern_id, suggested_guardrail)
            else:
                # Insert new pattern
                conn.execute("""
                    INSERT INTO failure_patterns
                    (id, failure_type, description, agent_types, suggested_guardrail, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pattern_id, failure_type, failure_description,
                      json.dumps([agent_type]), suggested_guardrail, 0.5))

            conn.commit()

        logger.info(f"Learned from failure: {failure_type} for {agent_type}")
        return None  # Guardrail will be promoted after enough occurrences

    def _generate_guardrail_from_failure(
        self,
        agent_type: str,
        failure_type: str,
        description: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Generate a guardrail text from a failure pattern."""

        # Map common failure types to guardrail templates
        templates = {
            "scope_creep": "Do NOT implement features beyond: {scope_hint}",
            "max_iterations": "NEVER continue past {max_iter} iterations without producing output",
            "no_activity": "Do NOT stall - if blocked, immediately request clarification",
            "incomplete": "NEVER mark task complete without: {completion_criteria}",
            "file_sprawl": "Do NOT create more than {file_limit} files per task",
            "dependency_overload": "NEVER add new dependencies for simple tasks",
            "error_loop": "Do NOT retry the same failing approach - change strategy after 2 failures",
        }

        template = templates.get(failure_type)
        if not template:
            # Generic template
            template = f"Do NOT repeat this error pattern: {description[:100]}"

        # Fill in template with context
        guardrail = template.format(
            scope_hint=context.get("scope", "the explicit task requirements"),
            max_iter=context.get("max_iterations", 10),
            completion_criteria=context.get("criteria", "all requirements verified"),
            file_limit=context.get("file_limit", 5),
        )

        return guardrail

    def _promote_learned_guardrail(self, pattern_id: str, guardrail_text: str):
        """Promote a frequently-seen pattern to a permanent guardrail."""
        guardrail_id = f"learned_{pattern_id}"

        with sqlite3.connect(str(self.db_path)) as conn:
            # Get pattern details
            row = conn.execute("""
                SELECT agent_types, failure_type FROM failure_patterns WHERE id = ?
            """, (pattern_id,)).fetchone()

            if not row:
                return

            agent_types = json.loads(row[0])
            failure_type = row[1]

            # Determine category from failure type
            category_map = {
                "scope_creep": GuardrailCategory.SCOPE,
                "max_iterations": GuardrailCategory.RESOURCE,
                "no_activity": GuardrailCategory.PROCESS,
                "incomplete": GuardrailCategory.COMPLETENESS,
                "file_sprawl": GuardrailCategory.RESOURCE,
                "error_loop": GuardrailCategory.PROCESS,
            }
            category = category_map.get(failure_type, GuardrailCategory.PROCESS)

            # Insert as permanent guardrail
            conn.execute("""
                INSERT OR IGNORE INTO guardrails
                (id, text, category, agent_types, severity, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guardrail_id, guardrail_text, category.value,
                  json.dumps(agent_types), "important", "learned"))

            conn.commit()
            logger.info(f"Promoted learned guardrail: {guardrail_id}")

    def get_guardrail_stats(self) -> Dict[str, Any]:
        """Get statistics about guardrail effectiveness."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            total = conn.execute("SELECT COUNT(*) FROM guardrails").fetchone()[0]
            learned = conn.execute(
                "SELECT COUNT(*) FROM guardrails WHERE source = 'learned'"
            ).fetchone()[0]

            # Get most effective guardrails
            effective = conn.execute("""
                SELECT id, text, success_rate, times_applied
                FROM guardrails
                WHERE times_applied > 5
                ORDER BY success_rate DESC
                LIMIT 5
            """).fetchall()

            # Get category breakdown
            categories = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM guardrails
                GROUP BY category
            """).fetchall()

            return {
                "total_guardrails": total,
                "learned_guardrails": learned,
                "manual_guardrails": total - learned,
                "most_effective": [dict(row) for row in effective],
                "by_category": {row['category']: row['count'] for row in categories}
            }

    def format_guardrails_for_agent_definition(
        self,
        agent_type: str,
        format_style: str = "markdown"
    ) -> str:
        """Format guardrails as text for inclusion in agent definitions."""
        guardrails = self.get_guardrails_for_agent(agent_type)

        if not guardrails:
            return ""

        # Group by category
        by_category: Dict[GuardrailCategory, List[Guardrail]] = {}
        for g in guardrails:
            if g.category not in by_category:
                by_category[g.category] = []
            by_category[g.category].append(g)

        if format_style == "markdown":
            output = "### Anti-Patterns (What NOT to Do)\n\n"

            for category, items in by_category.items():
                output += f"**{category.value.title()} Constraints:**\n"
                for g in items:
                    marker = "🚫" if g.severity == "critical" else "⚠️"
                    output += f"- {marker} {g.text}\n"
                output += "\n"

            return output
        else:
            # Plain text format
            output = "WHAT NOT TO DO:\n\n"
            for g in guardrails:
                output += f"- {g.text}\n"
            return output


# Singleton accessor
_guardrail_system: Optional[GuardrailSystem] = None


def get_guardrail_system() -> GuardrailSystem:
    """Get the global guardrail system instance."""
    global _guardrail_system
    if _guardrail_system is None:
        _guardrail_system = GuardrailSystem()
    return _guardrail_system
