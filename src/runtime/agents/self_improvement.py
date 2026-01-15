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
    MODEL_UPGRADE = "model_upgrade"       # Suggest using a better model
    MODEL_DOWNGRADE = "model_downgrade"   # Suggest using a cheaper model (when success is high)
    DEFINITION_TWEAK = "definition_tweak" # Minor definition change
    DEFINITION_MAJOR = "definition_major" # Major definition rewrite
    ITERATION_INCREASE = "iteration_increase"  # Increase max iterations
    ITERATION_DECREASE = "iteration_decrease"  # Decrease max iterations
    COMPLEXITY_CHANGE = "complexity_change"    # Change task complexity rating
    ALERT = "alert"                            # Something needs human attention


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
                            "error_types": row['error_types'],
                            "avg_iterations": row['avg_iterations']
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
                            "error_types": row['error_types']
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
                recommendations.append(Recommendation(
                    id=f"model_{rec_data['agent']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    agent_name=rec_data['agent'],
                    recommendation_type=RecommendationType.MODEL_UPGRADE,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"Model optimization for {rec_data['agent']}",
                    description=f"Consider using {rec_data['recommend_model']} instead of {rec_data['avoid_model']}. Expected improvement: {rec_data['improvement']}",
                    evidence=rec_data,
                    suggested_changes={
                        "preferred_model": rec_data['recommend_model'],
                        "avoid_model": rec_data['avoid_model']
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
                title=f"CRITICAL: {issue.agent_name} has {issue.evidence['success_rate']}% success rate",
                description=f"Agent {issue.agent_name} is failing {100-issue.evidence['success_rate']:.1f}% of the time. "
                           f"Common errors: {issue.evidence.get('error_types', 'unknown')}. "
                           f"Immediate review of agent definition required.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "review_definition",
                    "check_points": [
                        "Are instructions clear and unambiguous?",
                        "Is the model appropriate for task complexity?",
                        "Are input/output formats correct?",
                        "Are tool permissions sufficient?",
                        "Is max_iterations high enough?"
                    ],
                    "consider_model_upgrade": True
                }
            )

        elif issue.issue_type == "low_success_rate":
            return Recommendation(
                id=f"warning_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.DEFINITION_TWEAK,
                priority=RecommendationPriority.HIGH,
                title=f"Warning: {issue.agent_name} underperforming ({issue.evidence['success_rate']}% success)",
                description=f"Agent {issue.agent_name} has a success rate below 75%. "
                           f"Consider reviewing recent failures and adjusting definition.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "review_recent_failures",
                    "potential_fixes": [
                        "Add more specific instructions",
                        "Increase max_iterations",
                        "Consider model upgrade for complex tasks"
                    ]
                }
            )

        elif issue.issue_type == "high_performer_optimization":
            return Recommendation(
                id=f"optimize_{issue.agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                agent_name=issue.agent_name,
                recommendation_type=RecommendationType.MODEL_DOWNGRADE,
                priority=RecommendationPriority.LOW,
                title=f"Cost optimization: {issue.agent_name} consistently succeeds",
                description=f"Agent {issue.agent_name} has {issue.evidence['success_rate']}% success rate. "
                           f"Consider using a cheaper/faster model to reduce costs.",
                evidence=issue.evidence,
                suggested_changes={
                    "action": "consider_model_downgrade",
                    "current_performance": issue.evidence['success_rate'],
                    "note": "Only if cost savings are meaningful"
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
                new_model = changes.get("new_model", "sonnet")
                content = self._update_model_preference(content, new_model)
                applied_changes.append(f"Updated model to {new_model}")

            elif rec_type == "model_downgrade":
                new_model = changes.get("new_model", "haiku")
                content = self._update_model_preference(content, new_model)
                applied_changes.append(f"Downgraded model to {new_model}")

            elif rec_type == "iteration_increase":
                new_iterations = changes.get("new_max_iterations", 15)
                content = self._update_max_iterations(content, new_iterations)
                applied_changes.append(f"Increased max iterations to {new_iterations}")

            elif rec_type == "iteration_decrease":
                new_iterations = changes.get("new_max_iterations", 5)
                content = self._update_max_iterations(content, new_iterations)
                applied_changes.append(f"Decreased max iterations to {new_iterations}")

            elif rec_type in ["definition_tweak", "definition_major"]:
                # For definition changes, add guardrails/notes to instructions
                note = changes.get("note", recommendation.get("description", ""))
                if note:
                    content = self._add_performance_note(content, note)
                    applied_changes.append("Added performance guidance to instructions")

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

    def _add_performance_note(self, content: str, note: str) -> str:
        """Add a performance note to the instructions section."""
        # Find the Instructions section and add note at the end
        marker = "## Instructions"
        if marker in content:
            # Find next section after Instructions
            parts = content.split(marker)
            if len(parts) >= 2:
                # Find the next ## header in the second part
                instruction_content = parts[1]
                next_section_match = re.search(r'\n## [A-Z]', instruction_content)
                if next_section_match:
                    insert_pos = next_section_match.start()
                    note_section = f"\n\n**Performance Insight (Auto-Applied):**\n{note}\n"
                    new_instruction = instruction_content[:insert_pos] + note_section + instruction_content[insert_pos:]
                    return parts[0] + marker + new_instruction
        return content

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
