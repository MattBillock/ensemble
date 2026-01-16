"""
Configuration for output file organization.

This module defines categorization rules for organizing output files into
standard categories based on filename patterns.
"""

import re
from pathlib import Path

# Standard categories for organizing output files
STANDARD_CATEGORIES = [
    "requirements",
    "architecture",
    "milestones",
    "tasks",
    "reports",
    "planning",
    "guides",
    "status",
]

# Category rules: list of (compiled_regex_pattern, category_name) tuples
# Patterns match markdown filenames to their appropriate category
CATEGORY_RULES = [
    # Requirements files
    (re.compile(r".*requirements.*\.md$", re.IGNORECASE), "requirements"),
    # Architecture files
    (re.compile(r".*architecture.*\.md$", re.IGNORECASE), "architecture"),
    # Milestone files
    (re.compile(r".*milestone.*\.md$", re.IGNORECASE), "milestones"),
    # Task files (backend, frontend, test, api, dev tasks)
    (re.compile(r".*(tasks?|backend|frontend|test_tasks|api_tasks|dev_tasks)\.md$", re.IGNORECASE), "tasks"),
    # Reports and analysis files
    (re.compile(r".*(report|analysis|audit|assessment).*\.md$", re.IGNORECASE), "reports"),
    # Planning files
    (re.compile(r".*(plan|feasibility).*\.md$", re.IGNORECASE), "planning"),
    # Guide and reference files
    (re.compile(r".*(guide|dictionary|reference|inventory).*\.md$", re.IGNORECASE), "guides"),
    # Status files
    (re.compile(r".*status.*\.md$", re.IGNORECASE), "status"),
]

# Output root directory
OUTPUT_ROOT = Path("/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/output/")
