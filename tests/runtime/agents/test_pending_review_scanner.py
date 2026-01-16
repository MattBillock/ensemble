"""
Tests for pending_review_scanner.py
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.runtime.agents.pending_review_scanner import (
    PendingReviewScanner,
    REVIEWABLE_FILE_PATTERNS,
    DEFAULT_ACTIONS
)


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create output directory
        output_dir = project_root / "src" / "field" / "ensemble_ui" / "output"
        output_dir.mkdir(parents=True)

        yield project_root, output_dir


class TestParseFrontmatter:
    """Test YAML frontmatter parsing."""

    def test_parse_valid_frontmatter(self, temp_project):
        """Test parsing valid YAML frontmatter."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        content = """---
review_type: requirements
action: start_implementation
action_params:
  budget_tier: balanced
---

# Requirements

This is the content.
"""
        frontmatter, body = scanner.parse_frontmatter(content)

        assert frontmatter["review_type"] == "requirements"
        assert frontmatter["action"] == "start_implementation"
        assert frontmatter["action_params"]["budget_tier"] == "balanced"
        assert "# Requirements" in body

    def test_parse_no_frontmatter(self, temp_project):
        """Test parsing content without frontmatter."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        content = """# Requirements

No frontmatter here.
"""
        frontmatter, body = scanner.parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_parse_invalid_yaml(self, temp_project):
        """Test handling invalid YAML in frontmatter."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        content = """---
invalid: yaml: content: here
  - broken
---

# Content
"""
        frontmatter, body = scanner.parse_frontmatter(content)

        # Should handle gracefully
        assert isinstance(frontmatter, dict)

    def test_parse_incomplete_frontmatter(self, temp_project):
        """Test handling incomplete frontmatter (missing closing ---)."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        content = """---
review_type: test
# No closing ---

Content here.
"""
        frontmatter, body = scanner.parse_frontmatter(content)

        # With only one ---, parts will be ['', 'review_type: test...', ''],
        # which means len(parts) < 3, so we return original content
        # OR if YAML parses successfully with `# No closing ---` being a comment
        # Either way the function handles it gracefully
        assert isinstance(frontmatter, dict)
        assert isinstance(body, str)


class TestDetectFileType:
    """Test file type detection by pattern matching."""

    def test_detect_requirements_patterns(self, temp_project):
        """Test detection of requirements files."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        assert scanner.detect_file_type(Path("feature_requirements.md")) == "requirements"
        assert scanner.detect_file_type(Path("requirements.md")) == "requirements"
        assert scanner.detect_file_type(Path("requirements_v2.md")) == "requirements"

    def test_detect_architecture_patterns(self, temp_project):
        """Test detection of architecture files."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        assert scanner.detect_file_type(Path("system_architecture.md")) == "architecture"
        assert scanner.detect_file_type(Path("architecture.md")) == "architecture"
        assert scanner.detect_file_type(Path("architecture_v1.md")) == "architecture"

    def test_detect_milestone_patterns(self, temp_project):
        """Test detection of milestone files."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        assert scanner.detect_file_type(Path("project_milestone_1.md")) == "milestone"
        assert scanner.detect_file_type(Path("milestone_plan.md")) == "milestone"
        assert scanner.detect_file_type(Path("milestones.md")) == "milestone"

    def test_tasks_and_plans_not_matched(self, temp_project):
        """Test that task and plan files are NOT matched (deliverables only)."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        # Task files should NOT be matched - they're not deliverables
        assert scanner.detect_file_type(Path("backend_tasks_m1.md")) is None
        assert scanner.detect_file_type(Path("frontend_tasks.md")) is None

        # Plan files should NOT be matched - they're not deliverables
        assert scanner.detect_file_type(Path("implementation_plan.md")) is None
        assert scanner.detect_file_type(Path("project_plan.md")) is None

    def test_no_match_returns_none(self, temp_project):
        """Test that non-matching files return None."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        assert scanner.detect_file_type(Path("readme.md")) is None
        assert scanner.detect_file_type(Path("notes.md")) is None
        assert scanner.detect_file_type(Path("random_file.md")) is None
        assert scanner.detect_file_type(Path("test_plan.md")) is None  # test_plan not a deliverable


class TestScanFile:
    """Test scanning individual files."""

    def test_scan_file_with_explicit_frontmatter(self, temp_project):
        """Test scanning file with explicit frontmatter marking."""
        project_root, output_dir = temp_project
        scanner = PendingReviewScanner(project_root)

        # Create file with frontmatter
        file_path = output_dir / "explicit_review.md"
        file_path.write_text("""---
review_type: requirements
action: start_implementation
action_params:
  budget_tier: full_firepower
---

# Explicit Review

Content here.
""")

        result = scanner.scan_file(file_path)

        assert result is not None
        assert result["detection_method"] == "explicit"
        assert result["review_type"] == "requirements"
        assert result["action"] == "start_implementation"
        assert result["action_params"]["budget_tier"] == "full_firepower"

    def test_scan_file_auto_detected(self, temp_project):
        """Test scanning file detected by filename pattern."""
        project_root, output_dir = temp_project
        scanner = PendingReviewScanner(project_root)

        # Create file without frontmatter but matching pattern
        file_path = output_dir / "feature_requirements.md"
        file_path.write_text("""# Feature Requirements

This document describes requirements.
""")

        result = scanner.scan_file(file_path)

        assert result is not None
        assert result["detection_method"] == "auto"
        assert result["review_type"] == "requirements"
        assert result["action"] == "start_implementation"

    def test_scan_file_non_reviewable(self, temp_project):
        """Test scanning file that shouldn't be reviewed."""
        project_root, output_dir = temp_project
        scanner = PendingReviewScanner(project_root)

        # Create file that doesn't match patterns and has no frontmatter
        file_path = output_dir / "notes.md"
        file_path.write_text("""# Notes

Just some notes.
""")

        result = scanner.scan_file(file_path)

        assert result is None

    def test_scan_nonexistent_file(self, temp_project):
        """Test scanning file that doesn't exist."""
        project_root, _ = temp_project
        scanner = PendingReviewScanner(project_root)

        result = scanner.scan_file(Path("/nonexistent/file.md"))

        assert result is None

    def test_scan_non_markdown_file(self, temp_project):
        """Test scanning non-markdown file."""
        project_root, output_dir = temp_project
        scanner = PendingReviewScanner(project_root)

        file_path = output_dir / "file.txt"
        file_path.write_text("Not markdown")

        result = scanner.scan_file(file_path)

        assert result is None


class TestScanOutputDirectory:
    """Test scanning entire output directory."""

    def test_scan_output_directory_finds_files(self, temp_project):
        """Test that scanning finds reviewable files."""
        project_root, output_dir = temp_project
        scanner = PendingReviewScanner(project_root, output_dir=output_dir)

        # Create some reviewable files
        (output_dir / "requirements.md").write_text("# Requirements")
        (output_dir / "architecture.md").write_text("# Architecture")
        (output_dir / "notes.md").write_text("# Notes")  # Not reviewable

        # Mock the swarm_state to avoid database operations
        with patch('src.runtime.agents.swarm_state.get_swarm_state') as mock_swarm:
            mock_state = MagicMock()
            mock_state.is_file_tracked_for_review.return_value = False
            mock_state.add_pending_review.return_value = 1
            mock_swarm.return_value = mock_state

            with patch('src.runtime.agents.runtime.AgentRuntime') as mock_runtime:
                mock_tracker = MagicMock()
                mock_tracker.activities = []
                mock_runtime.get_activity_tracker.return_value = mock_tracker

                new_reviews = scanner.scan_output_directory()

        # Should find requirements and architecture but not notes
        assert len(new_reviews) == 2

    def test_scan_skips_already_tracked(self, temp_project):
        """Test that already tracked files are skipped."""
        project_root, output_dir = temp_project
        scanner = PendingReviewScanner(project_root, output_dir=output_dir)

        # Create file
        (output_dir / "requirements.md").write_text("# Requirements")

        with patch('src.runtime.agents.swarm_state.get_swarm_state') as mock_swarm:
            mock_state = MagicMock()
            # File is already tracked
            mock_state.is_file_tracked_for_review.return_value = True
            mock_swarm.return_value = mock_state

            new_reviews = scanner.scan_output_directory()

        assert len(new_reviews) == 0

    def test_scan_empty_directory(self, temp_project):
        """Test scanning empty directory."""
        project_root, output_dir = temp_project
        scanner = PendingReviewScanner(project_root, output_dir=output_dir)

        with patch('src.runtime.agents.swarm_state.get_swarm_state') as mock_swarm:
            mock_state = MagicMock()
            mock_swarm.return_value = mock_state

            new_reviews = scanner.scan_output_directory()

        assert len(new_reviews) == 0

    def test_scan_nonexistent_directory(self, temp_project):
        """Test scanning when output directory doesn't exist."""
        project_root, _ = temp_project
        # Use a different output dir that doesn't exist
        scanner = PendingReviewScanner(project_root, output_dir=Path("/nonexistent"))

        new_reviews = scanner.scan_output_directory()

        assert len(new_reviews) == 0


class TestDefaultActions:
    """Test default actions for review types."""

    def test_default_actions_defined(self):
        """Test that all review types have default actions."""
        for pattern, review_type in REVIEWABLE_FILE_PATTERNS.items():
            assert review_type in DEFAULT_ACTIONS, f"Missing default action for {review_type}"

    def test_default_action_values(self):
        """Test specific default action values for deliverables only."""
        assert DEFAULT_ACTIONS["requirements"] == "start_implementation"
        assert DEFAULT_ACTIONS["architecture"] == "start_implementation"
        assert DEFAULT_ACTIONS["milestone"] == "start_implementation"
        # test_plan is no longer a deliverable
        assert "test_plan" not in DEFAULT_ACTIONS
