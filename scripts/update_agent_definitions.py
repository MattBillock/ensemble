#!/usr/bin/env python3
"""Update all agent definition files to reference common_instructions.md instead of duplicating content."""

import re
from pathlib import Path

# Define the replacements to make
REPLACEMENTS = [
    # Self-Improvement Directive
    {
        "pattern": re.compile(
            r'## Self-Improvement Directive\s*\n\s*\n'
            r'\*\*CRITICAL\*\*: Analyze your performance in EVERY execution\. This is MANDATORY\.\s*\n\s*\n'
            r'### Your Self-Analysis \(self_analysis field\):\s*\n'
            r'1\. \*\*Quality\*\*: Was my output high quality\?\s*\n'
            r'2\. \*\*Efficiency\*\*: Iterations used vs needed\?\s*\n'
            r'3\. \*\*Decisiveness\*\*: Good assumptions or unnecessary questions\?\s*\n'
            r'4\. \*\*Errors\*\*: What went wrong\?\s*\n'
            r'5\. \*\*Improvement\*\*: What would I do differently\?\s*\n\s*\n'
            r'Format: 2-4 honest sentences\. Example: "Task breakdown clear with proper dependencies\. '
            r'Used 2 iterations efficiently\. Over-specified edge cases not in requirements\. '
            r'Next time: stick closer to requirements\."\s*\n\s*\n'
            r'\*\*Why\*\*: Your analysis feeds the metrics system\. Honest self-assessment = system improvement\.',
            re.MULTILINE
        ),
        "replacement": (
            "## Self-Improvement Directive\n\n"
            "See [Common Instructions - Self-Improvement Directive]"
            "(/Users/mattbillock/Development/ai_exploration/ensemble/docs/common_instructions.md"
            "#self-improvement-directive) for guidelines on continuous improvement and self-analysis."
        )
    },
    # Git Workflow (generic version for all agents except TDD Coordinator)
    {
        "pattern": re.compile(
            r'### Git Workflow:?\s*\n'
            r'After completing your [^,]+, commit changes to version control:\s*\n\s*\n'
            r'```json\s*\n'
            r'git_commit\(\{\s*\n'
            r'\s*"message": "Descriptive commit message \(min 10 chars\)"\s*\n'
            r'\}\)\s*\n'
            r'```\s*\n\s*\n'
            r'\*\*When to commit\*\*:\s*\n'
            r'(?:- .+\n)+\s*\n'
            r'\*\*Commit message examples\*\*:\s*\n'
            r'(?:- ".+"\n)+',
            re.MULTILINE
        ),
        "replacement": (
            "### Git Workflow\n"
            "See [Common Instructions - Git Workflow]"
            "(/Users/mattbillock/Development/ai_exploration/ensemble/docs/common_instructions.md"
            "#git-workflow-instructions) for commit guidelines and best practices.\n\n"
            "**Agent-Specific**: Commit after completing your assigned work."
        )
    }
]

def update_file(file_path: Path):
    """Update a single agent definition file."""
    print(f"Processing {file_path}...")

    content = file_path.read_text()
    original_content = content
    changes_made = []

    for i, replacement_spec in enumerate(REPLACEMENTS):
        pattern = replacement_spec["pattern"]
        replacement = replacement_spec["replacement"]

        if pattern.search(content):
            content = pattern.sub(replacement, content)
            changes_made.append(i)

    if content != original_content:
        file_path.write_text(content)
        print(f"  ✓ Updated with {len(changes_made)} replacement(s)")
        return True
    else:
        print(f"  - No changes needed")
        return False

def main():
    """Update all agent definition files."""
    base_dir = Path("/Users/mattbillock/Development/ai_exploration/ensemble")

    # Find all .md files in agent directories
    patterns = [
        "coordinators/*.md",
        "developers/*.md",
        "testers/*.md",
        "leadership/*.md",
        "designers/*.md"
    ]

    files_updated = 0
    total_files = 0

    for pattern in patterns:
        for file_path in base_dir.glob(pattern):
            total_files += 1
            if update_file(file_path):
                files_updated += 1

    print(f"\nSummary: Updated {files_updated}/{total_files} files")

if __name__ == "__main__":
    main()
