"""
Self-Improvement Loop Engine

This module implements the critical feedback loop that transforms collected metrics
into actionable improvements for agent definitions. It closes the loop between
performance data and agent behavior.

Components:
1. PerformanceAnalyzer - Analyzes metrics.db to identify patterns and issues
2. RecommendationEngine - Generates specific improvement recommendations
3. FeedbackInjector - Provides agents with their own performance history
4. DefinitionUpdater - Updates agent definitions (with human approval)
5. ImprovementTracker - Tracks whether changes improve performance
"""

import json
import logging
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Types of improvement recommendations."""
    # Original types
    MODEL_UPGRADE = "model_upgrade"       # Suggest using a better model
    MODEL_DOWNGRADE = "model_downgrade"   # Suggest using a cheaper model (when success is high)
    DEFINITION_TWEAK = "definition_tweak" # Minor definition change
    DEFINITION_MAJOR = "definition_major" # Major definition rewrite
    ITERATION_INCREASE = "iteration_increase"  # Increase max iterations
    ITERATION_DECREASE = "iteration_decrease"  # Decrease max iterations
    COMPLEXITY_CHANGE = "complexity_change"    # Change task complexity rating
    ALERT = "alert"                            # Something needs human attention

    # New specialized improvement types
    PROMPT_REFINEMENT = "prompt_refinement"     # Improve system prompt for clarity and effectiveness
    TOOL_OPTIMIZATION = "tool_optimization"     # Optimize tool usage patterns and reduce unnecessary calls
    CONTEXT_WINDOW_TUNING = "context_tuning"   # Adjust context usage (too much vs too little)
    OUTPUT_FORMAT_IMPROVEMENT = "output_format" # Improve output structure and parsing reliability
    ERROR_HANDLING_ENHANCEMENT = "error_handling"  # Better error recovery and graceful degradation
    SPECIALIZATION_FOCUS = "specialization"    # Narrow agent focus for better performance in domain
    COLLABORATION_IMPROVEMENT = "collaboration"  # Better handoff/coordination with other agents
    MEMORY_STRATEGY = "memory_strategy"        # Improve context retention across iterations
    TASK_DECOMPOSITION = "task_decomposition"  # Better breaking down complex tasks into subtasks
    VALIDATION_ENHANCEMENT = "validation"      # Better self-validation of outputs before completion


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"  # Agent consistently failing
    HIGH = "high"          # Significant performance issue
    MEDIUM = "medium"      # Moderate optimization opportunity
    LOW = "low"            # Minor improvement suggestion


@dataclass
class PerformanceIssue:
    """Represents a detected performance issue."""
    agent_name: str
    issue_type: str
    severity: RecommendationPriority
    evidence: Dict[str, Any]
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Recommendation:
    """A specific improvement recommendation."""
    id: str
    agent_name: str
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    evidence: Dict[str, Any]
    suggested_changes: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # pending, approved, rejected, applied, superseded
    applied_at: Optional[str] = None


@dataclass
class AgentFeedback:
    """Performance feedback to inject into an agent's context."""
    agent_name: str
    success_rate: float
    avg_iterations: float
    common_errors: List[str]
    recent_self_analyses: List[str]
    improvement_tips: List[str]
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class PerformanceAnalyzer:
    """Analyzes agent metrics to identify patterns and issues."""

    # Performance thresholds
    CRITICAL_SUCCESS_THRESHOLD = 50.0   # Below this = critical issue
    WARNING_SUCCESS_THRESHOLD = 75.0    # Below this = warning
    HIGH_PERFORMER_THRESHOLD = 95.0     # Above this = high performer

    MIN_EXECUTIONS_FOR_ANALYSIS = 3     # Need at least this many runs to analyze

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".ensemble" / "metrics.db"
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def analyze_all_agents(self, days: int = 30) -> List[PerformanceIssue]:
        """Analyze all agents for performance issues."""
        issues = []
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get per-agent statistics
            cursor.execute("""
                SELECT
                    agent_name,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms,
                    ROUND(AVG(iterations), 1) as avg_iterations,
                    MAX(iterations) as max_iterations_used,
                    GROUP_CONCAT(DISTINCT error_type) as error_types
                FROM agent_executions
                WHERE created_at >= ?
                GROUP BY agent_name
                HAVING total_executions >= ?
            """, (cutoff_date, self.MIN_EXECUTIONS_FOR_ANALYSIS))

            for row in cursor.fetchall():
                agent_name = row['agent_name']
                success_rate = row['success_rate'] or 0
                total = row['total_executions']
                avg_iterations = row['avg_iterations'] or 0
                max_iterations_used = row['max_iterations_used'] or 0
                error_types = row['error_types'] or ""

                # Critical: Very low success rate
                if success_rate < self.CRITICAL_SUCCESS_THRESHOLD:
                    issues.append(PerformanceIssue(
                        agent_name=agent_name,
                        issue_type="critical_failure_rate",
                        severity=RecommendationPriority.CRITICAL,
                        evidence={
                            "success_rate": success_rate,
                            "total_executions": total,
                            "failed_count": row['failed'],
                            "error_types": error_types,
                            "avg_iterations": avg_iterations
                        }
                    ))

                # Warning: Moderate success rate issues
                elif success_rate < self.WARNING_SUCCESS_THRESHOLD:
                    issues.append(PerformanceIssue(
                        agent_name=agent_name,
                        issue_type="low_success_rate",
                        severity=RecommendationPriority.HIGH,
                        evidence={
                            "success_rate": success_rate,
                            "total_executions": total,
                            "error_types": error_types
                        }
                    ))

                # High performer - potential for cost optimization
                elif success_rate >= self.HIGH_PERFORMER_THRESHOLD and total >= 5:
                    issues.append(PerformanceIssue(
                        agent_name=agent_name,
                        issue_type="high_performer_optimization",
                        severity=RecommendationPriority.LOW,
                        evidence={
                            "success_rate": success_rate,
                            "total_executions": total,
                            "avg_duration_ms": row['avg_duration_ms']
                        }
                    ))

                # Additional checks for all agents regardless of success rate:

                # High iteration usage - agent may need more capacity or better instructions
                if avg_iterations > 8 and max_iterations_used >= 10:
                    issues.append(PerformanceIssue(
                        agent_name=agent_name,
                        issue_type="high_iteration_usage",
                        severity=RecommendationPriority.MEDIUM,
                        evidence={
                            "avg_iterations": avg_iterations,
                            "max_iterations_used": max_iterations_used,
                            "success_rate": success_rate,
                            "total_executions": total
                        }
                    ))

                # Recurring error patterns - needs error handling improvement
                if error_types and len(error_types.split(",")) >= 2:
                    issues.append(PerformanceIssue(
                        agent_name=agent_name,
                        issue_type="recurring_errors",
                        severity=RecommendationPriority.MEDIUM,
                        evidence={
                            "error_types": error_types,
                            "failed_count": row['failed'],
                            "success_rate": success_rate
                        }
                    ))

            # Check for spawn failures and tool usage from swarm_state.db if available
            try:
                swarm_db_path = Path.home() / ".ensemble" / "swarm_state.db"
                if swarm_db_path.exists():
                    with sqlite3.connect(str(swarm_db_path)) as swarm_conn:
                        swarm_conn.row_factory = sqlite3.Row
                        swarm_cursor = swarm_conn.cursor()

                        # Check for spawn failures (collaboration issues)
                        swarm_cursor.execute("""
                            SELECT
                                agent_name,
                                COUNT(*) as spawn_failures
                            FROM tool_executions
                            WHERE tool_name = 'spawn_agent'
                              AND success = 0
                              AND created_at >= ?
                            GROUP BY agent_name
                            HAVING spawn_failures >= 2
                        """, (cutoff_date,))

                        for row in swarm_cursor.fetchall():
                            issues.append(PerformanceIssue(
                                agent_name=row['agent_name'],
                                issue_type="spawn_failures",
                                severity=RecommendationPriority.HIGH,
                                evidence={
                                    "spawn_failures": row['spawn_failures'],
                                    "issue": "Agent has recurring spawn_agent failures"
                                }
                            ))

                        # Check for agents with high tool call counts
                        swarm_cursor.execute("""
                            SELECT
                                agent_name,
                                ROUND(AVG(tool_count), 1) as avg_tool_calls
                            FROM (
                                SELECT agent_name, COUNT(*) as tool_count
                                FROM tool_executions
                                WHERE created_at >= ?
                                GROUP BY agent_name, session_id
                            )
                            GROUP BY agent_name
                            HAVING avg_tool_calls > 20
                        """, (cutoff_date,))

                        for row in swarm_cursor.fetchall():
                            issues.append(PerformanceIssue(
                                agent_name=row['agent_name'],
                                issue_type="excessive_tool_usage",
                                severity=RecommendationPriority.LOW,
                                evidence={
                                    "avg_tool_calls": row['avg_tool_calls'],
                                    "recommendation": "Consider optimizing tool usage patterns"
                                }
                            ))
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.debug(f"Could not query swarm_state.db for tool data: {e}")

        return issues

    def analyze_model_effectiveness(self, days: int = 30) -> Dict[str, Any]:
        """Analyze which models work best for which agents."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        results = {"agent_model_performance": [], "recommendations": []}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get agent-model combinations
            cursor.execute("""
                SELECT
                    agent_name,
                    model_used,
                    COUNT(*) as runs,
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 2) as success_rate,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms
                FROM agent_executions
                WHERE created_at >= ?
                GROUP BY agent_name, model_used
                HAVING runs >= 2
                ORDER BY agent_name, success_rate DESC
            """, (cutoff_date,))

            current_agent = None
            agent_models = []

            for row in cursor.fetchall():
                if current_agent != row['agent_name']:
                    if current_agent and len(agent_models) > 1:
                        # Check if there's a clear winner
                        best = agent_models[0]
                        worst = agent_models[-1]
                        if best['success_rate'] - worst['success_rate'] > 20:
                            results["recommendations"].append({
                                "agent": current_agent,
                                "recommend_model": best['model'],
                                "avoid_model": worst['model'],
                                "improvement": f"+{best['success_rate'] - worst['success_rate']:.1f}% success rate"
                            })

                    current_agent = row['agent_name']
                    agent_models = []

                agent_models.append({
                    "model": row['model_used'],
                    "success_rate": row['success_rate'],
                    "runs": row['runs']
                })

            results["agent_model_performance"] = agent_models

        return results

    def extract_self_analysis_patterns(self, agent_name: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Extract patterns from agent self-analyses."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT agent_name, self_analysis, performance_analysis, success, error_type
                FROM agent_executions
                WHERE (self_analysis IS NOT NULL AND self_analysis != '')
            """
            params = []

            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            patterns = {
                "common_issues": {},
                "improvement_suggestions": [],
                "bottlenecks": [],
                "success_patterns": []
            }

            for row in cursor.fetchall():
                analysis = row['self_analysis'] or ""
                perf_analysis = row['performance_analysis'] or ""

                # Extract common phrases indicating issues
                issue_keywords = ['slow', 'fail', 'error', 'wrong', 'bad', 'unclear', 'confus']
                success_keywords = ['success', 'efficient', 'good', 'fast', 'clean', 'clear']

                combined_text = (analysis + " " + perf_analysis).lower()

                for keyword in issue_keywords:
                    if keyword in combined_text:
                        patterns["common_issues"][keyword] = patterns["common_issues"].get(keyword, 0) + 1

                # Extract improvement suggestions
                if 'next time' in combined_text or 'should' in combined_text or 'recommend' in combined_text:
                    # Extract the sentence containing improvement suggestion
                    sentences = re.split(r'[.!?]', combined_text)
                    for sent in sentences:
                        if any(word in sent for word in ['next time', 'should', 'recommend', 'improve']):
                            patterns["improvement_suggestions"].append(sent.strip())

                # Track successful patterns
                if row['success'] and any(kw in combined_text for kw in success_keywords):
                    patterns["success_patterns"].append({
                        "agent": row['agent_name'],
                        "pattern": analysis[:200]  # First 200 chars
                    })

            return patterns


class RecommendationEngine:
    """Generates specific improvement recommendations from analysis."""

    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer
        self.recommendations_path = Path.home() / ".ensemble" / "recommendations"
        self.recommendations_path.mkdir(parents=True, exist_ok=True)

    def generate_recommendations(self, days: int = 30) -> List[Recommendation]:
        """Generate all recommendations based on current metrics."""
        recommendations = []

        # Get existing pending/in_progress recommendations to avoid duplicates
        existing_keys = self._get_existing_recommendation_keys()

        # Analyze performance issues
        issues = self.analyzer.analyze_all_agents(days)

        for issue in issues:
            rec = self._issue_to_recommendation(issue)
            if rec:
                # Create a dedup key based on agent + type
                dedup_key = f"{rec.agent_name}_{rec.recommendation_type.value}"
                if dedup_key not in existing_keys:
                    recommendations.append(rec)
                    existing_keys.add(dedup_key)

        # Analyze model effectiveness
        model_analysis = self.analyzer.analyze_model_effectiveness(days)
        for rec_data in model_analysis.get("recommendations", []):
            dedup_key = f"{rec_data['agent']}_model_upgrade"
            if dedup_key not in existing_keys:
                # Determine if this is an upgrade or just optimization
                recommend_model = rec_data.get('recommend_model', 'unknown')
                avoid_model = rec_data.get('avoid_model', 'unknown')
                improvement = rec_data.get('improvement', 'improved performance')

                # Determine capability tier description
                tier_desc = "higher capability tier" if "opus" in recommend_model.lower() or "sonnet" in recommend_model.lower() else "optimal model tier"

                recommendations.append(Recommendation(
                    id=f"model_{rec_data['agent']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    agent_name=rec_data['agent'],
                    recommendation_type=RecommendationType.MODEL_UPGRADE,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"Model tier optimization for {rec_data['agent']}",
                    description=f"Analysis shows this agent performs better with a {tier_desc}. "
                               f"Expected improvement: {improvement}. "
                               f"Adjusting model tier to better match task complexity.",
                    evidence=rec_data,
                    suggested_changes={
                        "target_tier": recommend_model,
                        "current_tier": avoid_model,
                        "reason": "Performance data indicates better results with adjusted model capability"
                    }
                ))
                existing_keys.add(dedup_key)

        # Only save if there are new recommendations
        if recommendations:
            self._save_recommendations(recommendations)

        return recommendations

    def _get_existing_recommendation_keys(self) -> set:
        """Get keys for existing pending/in_progress recommendations for deduplication."""
        keys = set()
        for filepath in self.recommendations_path.glob("recommendations_*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                for item in data:
                    # Only consider pending or in_progress recommendations
                    if item.get("status") in ("pending", "in_progress"):
                        key = f"{item['agent_name']}_{item['type']}"
                        keys.add(key)
            except (json.JSONDecodeError, IOError):
                continue
        return keys

    def _issue_to_recommendation(self, issue: PerformanceIssue) -> Optional[Recommendation]:
        """Convert a performance issue into a recommendation."""

        if issue.issue_type == "critical_failure_rate":
            return Recommendation(
                id=f"critical_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.DEFINITION_MAJOR,
                priority=RecommendationPriority.CRITICAL,
                title=f"CRITICAL: {issue.agent_name} needs capability upgrade ({issue.evidence['success_rate']}% success)",
                description=f"Agent {issue.agent_name} is struggling with its assigned tasks, failing "
                           f"{100-issue.evidence['success_rate']:.1f}% of the time. "
                           f"This agent needs enhanced reasoning capabilities to handle its workload effectively. "
                           f"Common issues: {issue.evidence.get('error_types', 'unknown')}.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "enhance_agent_capabilities",
                    "check_points": [
                        "Agent may need stronger reasoning - upgrading model tier",
                        "Review if instructions are clear and unambiguous",
                        "Verify input/output formats are correct",
                        "Check if tool permissions are sufficient",
                        "Confirm max_iterations allows enough processing time"
                    ],
                    "upgrade_model_tier": True
                }
            )

        elif issue.issue_type == "low_success_rate":
            return Recommendation(
                id=f"warning_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.DEFINITION_TWEAK,
                priority=RecommendationPriority.HIGH,
                title=f"Performance improvement needed: {issue.agent_name} ({issue.evidence['success_rate']}% success)",
                description=f"Agent {issue.agent_name} is underperforming with a success rate below target. "
                           f"May benefit from enhanced capabilities or refined instructions.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "improve_agent_effectiveness",
                    "potential_fixes": [
                        "Refine instructions for clarity",
                        "Allow more processing iterations",
                        "Consider upgrading model capability tier"
                    ]
                }
            )

        elif issue.issue_type == "high_performer_optimization":
            return Recommendation(
                id=f"optimize_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.MODEL_DOWNGRADE,
                priority=RecommendationPriority.LOW,
                title=f"Cost optimization opportunity: {issue.agent_name} performing excellently",
                description=f"Agent {issue.agent_name} achieves {issue.evidence['success_rate']}% success rate. "
                           f"This consistent high performance indicates the agent may work well with a more "
                           f"cost-efficient model tier while maintaining quality.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "optimize_cost_efficiency",
                    "current_performance": issue.evidence['success_rate'],
                    "note": "Reducing model tier for cost savings while maintaining quality"
                }
            )

        elif issue.issue_type == "high_iteration_usage":
            return Recommendation(
                id=f"iterations_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.ITERATION_INCREASE,
                priority=RecommendationPriority.MEDIUM,
                title=f"Iteration capacity needed: {issue.agent_name} (avg {issue.evidence['avg_iterations']:.1f} iterations)",
                description=f"Agent {issue.agent_name} frequently uses many iterations (avg: {issue.evidence['avg_iterations']:.1f}, "
                           f"max: {issue.evidence['max_iterations_used']}). Consider increasing max_iterations or improving "
                           f"task decomposition to reduce per-task complexity.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "increase_iteration_capacity",
                    "new_max_iterations": max(20, int(issue.evidence['max_iterations_used'] * 1.5)),
                    "alternative": "Review if tasks can be decomposed into smaller subtasks"
                }
            )

        elif issue.issue_type == "recurring_errors":
            return Recommendation(
                id=f"errors_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.ERROR_HANDLING_ENHANCEMENT,
                priority=RecommendationPriority.MEDIUM,
                title=f"Error handling needed: {issue.agent_name} has recurring failures",
                description=f"Agent {issue.agent_name} experiences multiple error types: {issue.evidence['error_types']}. "
                           f"Adding specific error handling guidance can improve resilience.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "add_error_handling",
                    "error_types": issue.evidence['error_types'],
                    "add_sections": ["Error Recovery", "Error Handling Guidelines"]
                }
            )

        elif issue.issue_type == "spawn_failures":
            return Recommendation(
                id=f"collab_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.COLLABORATION_IMPROVEMENT,
                priority=RecommendationPriority.HIGH,
                title=f"Spawn failures: {issue.agent_name} has {issue.evidence['spawn_failures']} failed spawns",
                description=f"Agent {issue.agent_name} has recurring spawn_agent failures. This indicates issues with "
                           f"agent path references, parameter validation, or spawn permission configuration.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "improve_collaboration",
                    "check_points": [
                        "Verify agent paths are correct (e.g., 'developers/backend_developer')",
                        "Ensure all required parameters are provided",
                        "Check spawn permissions in agent definition",
                        "Add collaboration protocol section"
                    ]
                }
            )

        elif issue.issue_type == "excessive_tool_usage":
            return Recommendation(
                id=f"tools_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.TOOL_OPTIMIZATION,
                priority=RecommendationPriority.LOW,
                title=f"Tool optimization: {issue.agent_name} (avg {issue.evidence['avg_tool_calls']:.0f} tool calls)",
                description=f"Agent {issue.agent_name} makes an above-average number of tool calls ({issue.evidence['avg_tool_calls']:.0f}). "
                           f"Consider batching operations or optimizing tool usage patterns.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "optimize_tool_usage",
                    "recommendations": [
                        "Batch related file operations",
                        "Use specific tools instead of generic ones",
                        "Cache results when possible",
                        "Add tool usage optimization section"
                    ]
                }
            )

        return None

    def _save_recommendations(self, recommendations: List[Recommendation]):
        """Save recommendations to disk."""
        filename = f"recommendations_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = self.recommendations_path / filename

        data = []
        for rec in recommendations:
            data.append({
                "id": rec.id,
                "agent_name": rec.agent_name,
                "type": rec.recommendation_type.value,
                "priority": rec.priority.value,
                "title": rec.title,
                "description": rec.description,
                "evidence": rec.evidence,
                "suggested_changes": rec.suggested_changes,
                "created_at": rec.created_at,
                "status": rec.status
            })

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(recommendations)} recommendations to {filepath}")

    def get_pending_recommendations(self) -> List[Recommendation]:
        """Get all pending (unapproved) recommendations."""
        recommendations = []

        for filepath in sorted(self.recommendations_path.glob("recommendations_*.json"), reverse=True):
            with open(filepath) as f:
                data = json.load(f)
                for item in data:
                    if item.get("status") == "pending":
                        recommendations.append(Recommendation(
                            id=item["id"],
                            agent_name=item["agent_name"],
                            recommendation_type=RecommendationType(item["type"]),
                            priority=RecommendationPriority(item["priority"]),
                            title=item["title"],
                            description=item["description"],
                            evidence=item["evidence"],
                            suggested_changes=item["suggested_changes"],
                            created_at=item["created_at"],
                            status=item["status"]
                        ))

        return recommendations


class FeedbackInjector:
    """Generates contextual feedback to inject into agent prompts."""

    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer

    def get_agent_feedback(self, agent_name: str, days: int = 30) -> AgentFeedback:
        """Generate feedback summary for an agent to include in its prompt."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self.analyzer._get_connection() as conn:
            cursor = conn.cursor()

            # Get basic stats
            cursor.execute("""
                SELECT
                    ROUND(AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END), 1) as success_rate,
                    ROUND(AVG(iterations), 1) as avg_iterations,
                    COUNT(*) as total_runs
                FROM agent_executions
                WHERE agent_name = ? AND created_at >= ?
            """, (agent_name, cutoff_date))

            row = cursor.fetchone()
            success_rate = row['success_rate'] or 0
            avg_iterations = row['avg_iterations'] or 0

            # Get common errors
            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM agent_executions
                WHERE agent_name = ? AND success = 0 AND error_type IS NOT NULL
                  AND created_at >= ?
                GROUP BY error_type
                ORDER BY count DESC
                LIMIT 3
            """, (agent_name, cutoff_date))

            common_errors = [row['error_type'] for row in cursor.fetchall()]

            # Get recent self-analyses (successful ones)
            cursor.execute("""
                SELECT self_analysis
                FROM agent_executions
                WHERE agent_name = ? AND success = 1
                  AND self_analysis IS NOT NULL AND self_analysis != ''
                ORDER BY created_at DESC
                LIMIT 3
            """, (agent_name,))

            recent_analyses = [row['self_analysis'] for row in cursor.fetchall()]

        # Generate improvement tips based on data
        tips = []
        if success_rate < 75:
            tips.append("Focus on completing tasks successfully - your success rate needs improvement.")
        if avg_iterations > 10:
            tips.append("Try to be more efficient - you're using more iterations than typical.")
        if common_errors:
            tips.append(f"Watch out for these common errors: {', '.join(common_errors[:2])}")
        if success_rate >= 90:
            tips.append("Great work! Maintain your high performance standards.")

        return AgentFeedback(
            agent_name=agent_name,
            success_rate=success_rate,
            avg_iterations=avg_iterations,
            common_errors=common_errors,
            recent_self_analyses=recent_analyses,
            improvement_tips=tips
        )

    def format_feedback_for_prompt(self, feedback: AgentFeedback) -> str:
        """Format feedback into a string suitable for prompt injection."""
        lines = [
            "## Your Performance History",
            f"- Success rate: {feedback.success_rate}%",
            f"- Average iterations per task: {feedback.avg_iterations}",
        ]

        if feedback.common_errors:
            lines.append(f"- Common errors to avoid: {', '.join(feedback.common_errors)}")

        if feedback.improvement_tips:
            lines.append("\n**Tips for this run:**")
            for tip in feedback.improvement_tips:
                lines.append(f"- {tip}")

        if feedback.recent_self_analyses:
            lines.append("\n**Learnings from your recent runs:**")
            for analysis in feedback.recent_self_analyses[:2]:
                # Truncate long analyses
                if len(analysis) > 200:
                    analysis = analysis[:200] + "..."
                lines.append(f"- {analysis}")

        return "\n".join(lines)


class SelfImprovementLoop:
    """
    Main orchestrator for the self-improvement system.

    This ties together:
    - Performance analysis
    - Recommendation generation
    - Feedback injection
    - Definition updates (with approval)
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.analyzer = PerformanceAnalyzer(db_path)
        self.recommendation_engine = RecommendationEngine(self.analyzer)
        self.feedback_injector = FeedbackInjector(self.analyzer)

        # Path to agent definitions
        self.definitions_base = Path("/Users/mattbillock/Development/ai_exploration/ensemble")

    def run_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Run complete analysis and generate recommendations."""
        logger.info(f"Running self-improvement analysis for last {days} days")

        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(days)

        # Extract patterns from self-analyses
        patterns = self.analyzer.extract_self_analysis_patterns(limit=100)

        # Model effectiveness
        model_analysis = self.analyzer.analyze_model_effectiveness(days)

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "period_days": days,
            "recommendations_count": len(recommendations),
            "recommendations": [
                {
                    "id": r.id,
                    "agent": r.agent_name,
                    "priority": r.priority.value,
                    "title": r.title,
                    "description": r.description
                }
                for r in recommendations
            ],
            "critical_issues": len([r for r in recommendations if r.priority == RecommendationPriority.CRITICAL]),
            "patterns_found": {
                "common_issues": patterns["common_issues"],
                "improvement_suggestions_count": len(patterns["improvement_suggestions"])
            },
            "model_recommendations": model_analysis.get("recommendations", [])
        }

    def get_feedback_for_agent(self, agent_name: str) -> str:
        """Get formatted feedback to inject into an agent's prompt."""
        feedback = self.feedback_injector.get_agent_feedback(agent_name)
        return self.feedback_injector.format_feedback_for_prompt(feedback)

    def get_pending_recommendations(self) -> List[Dict[str, Any]]:
        """Get pending recommendations for UI display."""
        recommendations = self.recommendation_engine.get_pending_recommendations()
        return [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "type": r.recommendation_type.value,
                "priority": r.priority.value,
                "title": r.title,
                "description": r.description,
                "suggested_changes": r.suggested_changes,
                "created_at": r.created_at
            }
            for r in recommendations
        ]

    def get_recommendation_by_id(self, recommendation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific recommendation by ID."""
        for filepath in self.recommendation_engine.recommendations_path.glob("recommendations_*.json"):
            with open(filepath) as f:
                data = json.load(f)
            for item in data:
                if item["id"] == recommendation_id:
                    return item
        return None

    def mark_recommendation_in_progress(self, recommendation_id: str) -> Dict[str, Any]:
        """Mark a recommendation as being implemented (agent spawned)."""
        for filepath in self.recommendation_engine.recommendations_path.glob("recommendations_*.json"):
            with open(filepath) as f:
                data = json.load(f)

            updated = False
            for item in data:
                if item["id"] == recommendation_id:
                    item["status"] = "in_progress"
                    item["implementation_started_at"] = datetime.now().isoformat()
                    updated = True
                    break

            if updated:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                return {"success": True, "message": f"Recommendation {recommendation_id} marked as in progress"}

        return {"success": False, "message": "Recommendation not found"}

    def approve_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """Mark a recommendation as approved (human in the loop)."""
        # Find and update the recommendation
        for filepath in self.recommendation_engine.recommendations_path.glob("recommendations_*.json"):
            with open(filepath) as f:
                data = json.load(f)

            updated = False
            for item in data:
                if item["id"] == recommendation_id:
                    item["status"] = "approved"
                    item["approved_at"] = datetime.now().isoformat()
                    updated = True
                    break

            if updated:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                return {"success": True, "message": f"Recommendation {recommendation_id} approved"}

        return {"success": False, "message": "Recommendation not found"}

    def reject_recommendation(self, recommendation_id: str, reason: str = "") -> Dict[str, Any]:
        """Mark a recommendation as rejected."""
        for filepath in self.recommendation_engine.recommendations_path.glob("recommendations_*.json"):
            with open(filepath) as f:
                data = json.load(f)

            updated = False
            for item in data:
                if item["id"] == recommendation_id:
                    item["status"] = "rejected"
                    item["rejected_at"] = datetime.now().isoformat()
                    item["rejection_reason"] = reason
                    updated = True
                    break

            if updated:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                return {"success": True, "message": f"Recommendation {recommendation_id} rejected"}

        return {"success": False, "message": "Recommendation not found"}

    def apply_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """Actually apply a recommendation by modifying agent definitions."""
        # Find the recommendation
        recommendation = None
        rec_filepath = None

        for filepath in self.recommendation_engine.recommendations_path.glob("recommendations_*.json"):
            with open(filepath) as f:
                data = json.load(f)
            for item in data:
                if item["id"] == recommendation_id:
                    recommendation = item
                    rec_filepath = filepath
                    break
            if recommendation:
                break

        if not recommendation:
            return {"success": False, "message": "Recommendation not found"}

        # Get agent definition path
        agent_name = recommendation["agent_name"]
        agent_def_path = self._find_agent_definition(agent_name)

        if not agent_def_path:
            return {"success": False, "message": f"Agent definition not found for {agent_name}"}

        rec_type = recommendation["type"]
        changes = recommendation.get("suggested_changes", {})
        applied_changes = []

        try:
            # Read current definition
            content = agent_def_path.read_text()
            original_content = content

            # Apply changes based on recommendation type
            if rec_type == "model_upgrade":
                new_model = changes.get("target_tier", changes.get("new_model", "sonnet"))
                content = self._update_model_preference(content, new_model)
                tier_name = {"opus": "high", "sonnet": "standard", "haiku": "fast"}.get(new_model, new_model)
                applied_changes.append(f"Enhanced reasoning capability - agent now uses {tier_name}-tier model for better task handling")

            elif rec_type == "model_downgrade":
                new_model = changes.get("new_model", "haiku")
                content = self._update_model_preference(content, new_model)
                applied_changes.append(f"Optimized for cost efficiency - agent performs well with faster model tier")

            elif rec_type == "iteration_increase":
                new_iterations = changes.get("new_max_iterations", 15)
                content = self._update_max_iterations(content, new_iterations)
                applied_changes.append(f"Increased max iterations to {new_iterations}")

            elif rec_type == "iteration_decrease":
                new_iterations = changes.get("new_max_iterations", 5)
                content = self._update_max_iterations(content, new_iterations)
                applied_changes.append(f"Decreased max iterations to {new_iterations}")

            elif rec_type in ["definition_tweak", "definition_major"]:
                # For underperforming agents, make targeted changes based on evidence
                evidence = recommendation.get("evidence", {})
                success_rate = evidence.get("success_rate", 100)
                error_types = evidence.get("error_types", "")
                avg_iterations = evidence.get("avg_iterations", 0)

                # If critical failure, upgrade to highest capability tier
                if success_rate < 50:
                    content = self._update_model_preference(content, "opus")
                    applied_changes.append("Enhanced reasoning capability (upgraded to high-tier model) due to complex task requirements")

                # If moderate failure, upgrade to mid-tier
                elif success_rate < 75:
                    # Check current model first
                    if "haiku" in content.lower():
                        content = self._update_model_preference(content, "sonnet")
                        applied_changes.append("Improved reasoning capability (upgraded to mid-tier model) for better task handling")

                # If running out of iterations, increase them
                if avg_iterations and avg_iterations > 8:
                    content = self._update_max_iterations(content, 20)
                    applied_changes.append("Extended processing capacity to 20 iterations (agent was hitting limits)")

                # Add specific error handling based on error types
                if error_types:
                    error_section = self._generate_error_handling_section(error_types)
                    if error_section:
                        content = self._insert_section(content, "## Error Handling Guidelines", error_section)
                        applied_changes.append(f"Added error handling for: {error_types}")

            elif rec_type == "prompt_refinement":
                # Analyze and improve the instructions section
                evidence = recommendation.get("evidence", {})
                # Add explicit decisiveness instructions
                decisiveness_section = """
## Decision Making
- Make reasonable assumptions for standard implementation details
- Do NOT ask users for choices that have obvious defaults
- When in doubt, pick the most common/standard approach and proceed
- Only ask clarifying questions for genuinely ambiguous requirements
"""
                content = self._insert_section(content, "## Decision Making", decisiveness_section)
                applied_changes.append("Added explicit decision-making guidelines")

            elif rec_type == "tool_optimization":
                # Add tool usage best practices
                evidence = recommendation.get("evidence", {})
                tool_section = """
## Tool Usage Optimization
- Batch related operations when possible
- Prefer specific tools over generic ones (e.g., use write_file, not bash echo)
- Check tool results before proceeding
- Minimize redundant tool calls
"""
                content = self._insert_section(content, "## Tool Usage Optimization", tool_section)
                applied_changes.append("Added tool optimization guidelines")

            elif rec_type == "context_tuning":
                # Adjust context window usage
                evidence = recommendation.get("evidence", {})
                if evidence.get("context_too_large"):
                    # Add instructions to be more concise
                    content = self._insert_section(content, "## Context Management",
                        "- Keep responses focused and concise\n- Summarize long outputs\n- Don't repeat information unnecessarily")
                    applied_changes.append("Added context management guidelines (reduce verbosity)")

            elif rec_type == "output_format":
                # Improve output structure
                format_section = """
## Output Format Requirements
- Structure outputs clearly with headers/sections
- Use consistent formatting throughout
- Validate output format before returning
- Include all required fields in responses
"""
                content = self._insert_section(content, "## Output Format Requirements", format_section)
                applied_changes.append("Added output format requirements")

            elif rec_type == "error_handling":
                # Add comprehensive error handling
                evidence = recommendation.get("evidence", {})
                error_types = evidence.get("error_types", "general")
                error_section = self._generate_error_handling_section(error_types)
                if error_section:
                    content = self._insert_section(content, "## Error Recovery", error_section)
                    applied_changes.append("Added error recovery procedures")

            elif rec_type == "specialization":
                # Narrow agent focus
                evidence = recommendation.get("evidence", {})
                spec_section = """
## Focus Area
- Stay strictly within your designated responsibilities
- Delegate tasks outside your specialty to appropriate agents
- Do not attempt tasks beyond your defined scope
"""
                content = self._insert_section(content, "## Focus Area", spec_section)
                applied_changes.append("Added specialization focus guidelines")

            elif rec_type == "collaboration":
                # Improve handoffs
                collab_section = """
## Collaboration Protocol
- Provide complete context when spawning sub-agents
- Include clear success criteria in delegated tasks
- Wait for and verify sub-agent completion before proceeding
- Report blockers immediately to parent agent
"""
                content = self._insert_section(content, "## Collaboration Protocol", collab_section)
                applied_changes.append("Added collaboration protocol")

            elif rec_type == "memory_strategy":
                # Add context retention guidance
                memory_section = """
## Context Retention
- Track key decisions made in previous iterations
- Summarize progress at each milestone
- Don't repeat work already completed
- Reference previous outputs when relevant
"""
                content = self._insert_section(content, "## Context Retention", memory_section)
                applied_changes.append("Added context retention guidelines")

            elif rec_type == "task_decomposition":
                # Add task breakdown guidance
                decomp_section = """
## Task Breakdown Strategy
- Break complex tasks into 3-5 subtasks maximum
- Each subtask should be independently verifiable
- Complete subtasks sequentially, verify each before proceeding
- Report progress after each subtask completion
"""
                content = self._insert_section(content, "## Task Breakdown Strategy", decomp_section)
                applied_changes.append("Added task decomposition strategy")

            elif rec_type == "validation":
                # Add validation steps
                valid_section = """
## Output Validation
- Verify all required deliverables are complete before reporting success
- Test outputs when possible (run code, validate formats)
- Double-check critical values and configurations
- Never report success if any validation fails
"""
                content = self._insert_section(content, "## Output Validation", valid_section)
                applied_changes.append("Added output validation requirements")

            # Write updated definition if changed
            if content != original_content:
                # Backup original
                backup_path = agent_def_path.with_suffix('.md.pre_improvement')
                backup_path.write_text(original_content)

                # Write new content
                agent_def_path.write_text(content)
                logger.info(f"Applied recommendation {recommendation_id} to {agent_def_path}")

            # Update recommendation status
            with open(rec_filepath) as f:
                data = json.load(f)
            for item in data:
                if item["id"] == recommendation_id:
                    item["status"] = "applied"
                    item["applied_at"] = datetime.now().isoformat()
                    item["applied_changes"] = applied_changes
                    break
            with open(rec_filepath, 'w') as f:
                json.dump(data, f, indent=2)

            return {
                "success": True,
                "message": f"Applied recommendation to {agent_name}",
                "changes": applied_changes,
                "agent_path": str(agent_def_path)
            }

        except Exception as e:
            logger.error(f"Failed to apply recommendation: {e}")
            return {"success": False, "message": str(e)}

    def _find_agent_definition(self, agent_name: str) -> Optional[Path]:
        """Find the agent definition file for a given agent name."""
        # Agent definitions are in leadership/, coordinators/, developers/, testers/, designers/
        base_path = Path(__file__).parent.parent.parent.parent
        search_dirs = ["leadership", "coordinators", "developers", "testers", "designers"]

        # Convert agent name to potential file patterns
        # e.g., "Executive Director" -> "executive_director.md"
        file_name = agent_name.lower().replace(" ", "_").replace("-", "_") + ".md"

        for dir_name in search_dirs:
            potential_path = base_path / dir_name / file_name
            if potential_path.exists():
                return potential_path

        # Also try without directory prefix (if agent_name includes path)
        if "/" in agent_name:
            potential_path = base_path / f"{agent_name}.md"
            if potential_path.exists():
                return potential_path

        return None

    def _update_model_preference(self, content: str, new_model: str) -> str:
        """Update the model preference in agent definition content."""
        # Look for ## Model Preference section
        pattern = r'(## Model Preference\n)(\w+)'
        replacement = f'\\1{new_model}'
        return re.sub(pattern, replacement, content)

    def _update_max_iterations(self, content: str, new_iterations: int) -> str:
        """Update max iterations in agent definition content."""
        # Look for ## Max Iterations section
        pattern = r'(## Max Iterations\n)(\d+)'
        replacement = f'\\g<1>{new_iterations}'
        return re.sub(pattern, replacement, content)

    def _insert_section(self, content: str, section_header: str, section_content: str) -> str:
        """
        Insert a new section into agent definition, avoiding duplicates.

        Inserts before the "## Model Preference" section if it exists,
        otherwise appends to the end.
        """
        # Check if section already exists (avoid duplicates)
        if section_header in content:
            logger.info(f"Section {section_header} already exists, skipping")
            return content

        # Find a good insertion point - before Model Preference or at end
        insert_markers = ["## Model Preference", "## Max Iterations", "## Can Write Code"]

        for marker in insert_markers:
            if marker in content:
                # Insert before this marker
                parts = content.split(marker)
                new_content = parts[0].rstrip() + "\n\n" + section_header + "\n" + section_content.strip() + "\n\n" + marker + parts[1]
                return new_content

        # No marker found, append to end
        return content.rstrip() + "\n\n" + section_header + "\n" + section_content.strip() + "\n"

    def _generate_error_handling_section(self, error_types: str) -> str:
        """
        Generate specific error handling instructions based on observed error types.
        """
        if not error_types:
            return ""

        error_list = [e.strip() for e in error_types.split(",") if e.strip()]
        if not error_list:
            return ""

        lines = ["## Error Handling Guidelines\n"]

        error_handlers = {
            "api_error": "- **API Errors**: Retry with exponential backoff, check rate limits, validate request format",
            "timeout": "- **Timeouts**: Break large operations into smaller chunks, add progress checkpoints",
            "validation_error": "- **Validation Errors**: Verify input/output formats before processing, use schema validation",
            "spawn_error": "- **Spawn Errors**: Verify agent definitions exist, check permissions, validate parameters",
            "tool_error": "- **Tool Errors**: Validate tool inputs, handle missing files gracefully, check permissions",
            "parse_error": "- **Parse Errors**: Use try/catch for parsing, validate JSON/YAML before processing",
            "permission_error": "- **Permission Errors**: Check file/directory permissions, verify agent capabilities",
            "network_error": "- **Network Errors**: Implement retry logic, check connectivity, use timeouts",
            "rate_limit": "- **Rate Limits**: Implement backoff, batch requests, cache results when possible",
        }

        for error_type in error_list:
            error_key = error_type.lower().replace(" ", "_").replace("-", "_")
            if error_key in error_handlers:
                lines.append(error_handlers[error_key])
            else:
                # Generic handler for unknown error types
                lines.append(f"- **{error_type}**: Log error details, attempt recovery, escalate if unrecoverable")

        lines.append("- **General**: Always log errors with context, never silently fail")

        return "\n".join(lines)

    def _add_performance_note(self, content: str, note: str) -> str:
        """
        DEPRECATED: This method injected useless "Performance Insight" text into agent
        definitions, which cluttered them without providing actionable value.

        Agent improvements should be made through:
        1. Actual code/configuration changes (model, iterations, etc.)
        2. Human review and manual definition updates
        3. NOT by injecting vague "think about this" guidance

        This method now returns content unchanged.
        """
        logger.warning("_add_performance_note is deprecated - not injecting text")
        return content  # Return unchanged - don't inject garbage

    def auto_approve_and_apply_all(self) -> Dict[str, Any]:
        """Auto-approve and apply all pending recommendations."""
        pending = self.get_pending_recommendations()
        results = {
            "approved": 0,
            "applied": 0,
            "failed": 0,
            "details": []
        }

        for rec in pending:
            rec_id = rec["id"]
            # First approve
            approve_result = self.approve_recommendation(rec_id)
            if approve_result.get("success"):
                results["approved"] += 1
                # Then apply
                apply_result = self.apply_recommendation(rec_id)
                if apply_result.get("success"):
                    results["applied"] += 1
                    results["details"].append({
                        "id": rec_id,
                        "agent": rec["agent_name"],
                        "status": "applied",
                        "changes": apply_result.get("changes", [])
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "id": rec_id,
                        "agent": rec["agent_name"],
                        "status": "apply_failed",
                        "error": apply_result.get("message")
                    })
            else:
                results["failed"] += 1
                results["details"].append({
                    "id": rec_id,
                    "agent": rec["agent_name"],
                    "status": "approve_failed",
                    "error": approve_result.get("message")
                })

        logger.info(f"Auto-apply complete: {results['applied']} applied, {results['failed']} failed")
        return results


# Singleton instance for easy access
_improvement_loop: Optional[SelfImprovementLoop] = None


def get_improvement_loop() -> SelfImprovementLoop:
    """Get the singleton self-improvement loop instance."""
    global _improvement_loop
    if _improvement_loop is None:
        _improvement_loop = SelfImprovementLoop()
    return _improvement_loop
