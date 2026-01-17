"""
Pending Review Scanner - Auto-detects files that need human review.

Uses two detection methods:
1. File type patterns (requirements.md, architecture.md, etc.)
2. YAML frontmatter with review metadata

Reports agents that generate reviewable files without explicit marking.
"""

import fnmatch
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


# File patterns that indicate reviewable deliverables
# Only process: architecture proposals, requirements docs, milestone plans
# Ignore task breakdowns, test plans, and other non-deliverable files
REVIEWABLE_FILE_PATTERNS = {
    "*_requirements.md": "requirements",
    "requirements*.md": "requirements",
    "*_architecture.md": "architecture",
    "architecture*.md": "architecture",
    "*_milestone*.md": "milestone",
    "milestone*.md": "milestone",
}

# Default actions for each review type
DEFAULT_ACTIONS = {
    "requirements": "start_implementation",
    "architecture": "start_implementation",
    "milestone": "start_implementation",
}


class PendingReviewScanner:
    """Scans for files that should go through human review."""

    def __init__(self, project_root: Path, output_dir: Optional[Path] = None):
        self.project_root = Path(project_root)
        self.output_dir = output_dir or (
            self.project_root / "src" / "field" / "ensemble_ui" / "output"
        )

    def parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content."""
        if not content.startswith('---'):
            return {}, content

        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].lstrip('\n')
            return frontmatter or {}, body
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse frontmatter: {e}")
            return {}, content

    def detect_file_type(self, file_path: Path) -> Optional[str]:
        """Detect review type from file name pattern."""
        filename = file_path.name.lower()

        for pattern, review_type in REVIEWABLE_FILE_PATTERNS.items():
            if fnmatch.fnmatch(filename, pattern.lower()):
                return review_type

        return None

    def scan_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Scan a single file for review eligibility.

        Returns review data if file should be reviewed, None otherwise.
        """
        if not file_path.exists() or file_path.suffix != '.md':
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            frontmatter, body = self.parse_frontmatter(content)

            # Method 1: Explicit frontmatter marking
            if frontmatter.get('review_type') or frontmatter.get('action'):
                return {
                    "file_path": str(file_path.relative_to(self.project_root)),
                    "file_type": "markdown",
                    "detection_method": "explicit",
                    "review_type": frontmatter.get('review_type', 'general'),
                    "action": frontmatter.get('action', 'start_implementation'),
                    "action_params": frontmatter.get('action_params', {}),
                    "content_preview": body[:500] if body else None,
                    "agent_name": frontmatter.get('agent_name', frontmatter.get('author', 'System')),
                }

            # Method 2: Auto-detection by file name
            review_type = self.detect_file_type(file_path)
            if review_type:
                # Try to get agent name from frontmatter, otherwise use descriptive name
                agent_name = frontmatter.get('agent_name', frontmatter.get('author'))
                if not agent_name:
                    # Generate descriptive name based on review type
                    type_agents = {
                        'requirements': 'Executive Director',
                        'architecture': 'System Architect',
                        'milestone': 'Development Manager',
                        'plan': 'Development Manager',
                        'tasks': 'Coordinator',
                        'test_plan': 'Test Coordinator',
                    }
                    agent_name = type_agents.get(review_type, 'File Scanner')
                return {
                    "file_path": str(file_path.relative_to(self.project_root)),
                    "file_type": "markdown",
                    "detection_method": "auto",
                    "review_type": review_type,
                    "action": DEFAULT_ACTIONS.get(review_type, "start_implementation"),
                    "action_params": {"budget_tier": "balanced"},
                    "content_preview": body[:500] if body else content[:500],
                    "agent_name": agent_name,
                }

            return None

        except FileNotFoundError:
            # File was deleted between glob and read - this is normal during active development
            logger.debug(f"File disappeared during scan (normal): {file_path}")
            return None
        except PermissionError:
            logger.warning(f"Permission denied reading file: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            return None

    def scan_output_directory(self, yolo_mode: bool = False) -> List[Dict[str, Any]]:
        """
        Scan output directory for new reviewable files.

        Args:
            yolo_mode: If True, skip creating pending reviews (YOLO mode runs autonomously)

        Returns list of review items to be added to pending_reviews table.
        """
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()

        new_reviews = []

        # In YOLO mode, skip creating pending reviews - let agents run fully autonomous
        if yolo_mode:
            logger.info("YOLO mode enabled - skipping pending review creation")
            return new_reviews

        if not self.output_dir.exists():
            logger.warning(f"Output directory does not exist: {self.output_dir}")
            return new_reviews

        for file_path in self.output_dir.glob("**/*.md"):
            # Check if already tracked
            relative_path = str(file_path.relative_to(self.project_root))
            if swarm.is_file_tracked_for_review(relative_path):
                continue

            review_data = self.scan_file(file_path)
            if review_data:
                # Add to database
                review_id = swarm.add_pending_review(**review_data)
                review_data["id"] = review_id
                new_reviews.append(review_data)

                # If auto-detected, create improvement report for agent
                if review_data["detection_method"] == "auto":
                    self._create_improvement_report(file_path, review_data)

        logger.info(f"Scanned output directory, found {len(new_reviews)} new reviewable files")
        return new_reviews

    def _create_improvement_report(
        self,
        file_path: Path,
        review_data: Dict[str, Any]
    ):
        """Create improvement report when file is auto-detected."""
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()

        # Try to identify the agent that created this file
        from src.runtime.agents.runtime import AgentRuntime
        tracker = AgentRuntime.get_activity_tracker()

        relative_path = str(file_path.relative_to(self.project_root))

        # Find the agent that generated this file by checking recent activities
        for activity in tracker.activities:
            if hasattr(activity, 'activity_type') and hasattr(activity.activity_type, 'value'):
                if activity.activity_type.value == "file_generated":
                    activity_file_path = activity.data.get("file_path", "")
                    # Check if the path matches (could be relative or absolute)
                    if relative_path in activity_file_path or activity_file_path in relative_path:
                        swarm.add_improvement_report(
                            agent_id=activity.agent_id,
                            agent_name=activity.agent_name,
                            request_id=activity.request_id,
                            issue_type="missing_explicit_marking",
                            file_path=relative_path,
                            detection_method=review_data["detection_method"],
                            severity="warning",
                            recommendation=(
                                f"Agent '{activity.agent_name}' generated a reviewable file "
                                f"({review_data['review_type']}) without explicit frontmatter. "
                                "Consider adding YAML frontmatter with review_type and action fields."
                            )
                        )
                        logger.info(f"Created improvement report for agent {activity.agent_name}")
                        return

        # If we couldn't find the agent, log it but don't fail
        logger.warning(f"Could not identify agent for auto-detected file: {relative_path}")


def get_scanner(project_root: Path = None) -> PendingReviewScanner:
    """Get a scanner instance with the default or specified project root."""
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent.parent
    return PendingReviewScanner(project_root)
