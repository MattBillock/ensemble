"""
Documentation Bot

Generates intelligent documentation for commit messages.
"""

from typing import Any, Optional
import re

from ..core.base_bot import BaseBot


class DocumentationBot(BaseBot):
    """
    Documentation Bot implementation.
    
    Features:
    - Analyze staged changes
    - Generate Conventional Commits format messages
    - Detect change types (feat, fix, refactor, etc.)
    - Auto-detect scope from file paths
    - Extract issue references from branch names
    """
    
    name = "documentation_bot"
    
    @property
    def bot_config(self) -> Any:
        """Get Documentation Bot configuration."""
        return self.config.documentation_bot
    
    def detect_change_type(self, files: list) -> str:
        """Detect the type of changes based on modified files."""
        # Check for test files
        if any("test" in f.lower() for f in files):
            return "test"
        
        # Check for documentation
        if any(f.endswith((".md", ".rst", ".txt")) for f in files):
            return "docs"
        
        # Check for config files
        config_patterns = [".yml", ".yaml", ".json", ".toml", ".ini", ".cfg"]
        if any(f.endswith(tuple(config_patterns)) for f in files):
            return "chore"
        
        # Default to feat for new functionality
        return "feat"
    
    def detect_scope(self, files: list) -> Optional[str]:
        """Detect scope from file paths."""
        if not files:
            return None
        
        # Extract common directory prefix
        if len(files) == 1:
            parts = files[0].split("/")
            if len(parts) > 1:
                return parts[0]
        
        # Find common parent directory
        common_parts = None
        for f in files:
            parts = f.split("/")[:-1]  # Exclude filename
            if common_parts is None:
                common_parts = parts
            else:
                # Find common prefix
                new_common = []
                for a, b in zip(common_parts, parts):
                    if a == b:
                        new_common.append(a)
                    else:
                        break
                common_parts = new_common
        
        if common_parts:
            return common_parts[-1] if common_parts else None
        
        return None
    
    def extract_issue_reference(self) -> Optional[str]:
        """Extract issue reference from branch name."""
        branch = self.git.get_current_branch()
        if not branch:
            return None
        
        # Common patterns: feature/ABC-123-description, fix/123, issue-456
        patterns = [
            r"([A-Z]+-\d+)",  # JIRA-style: ABC-123
            r"#(\d+)",  # GitHub-style: #123
            r"issue[/-]?(\d+)",  # issue-123 or issue/123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, branch, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def generate_message(self) -> Optional[str]:
        """
        Generate a commit message based on staged changes.
        
        Returns:
            Generated commit message or None if no staged changes
        """
        staged_files = self.git.get_staged_files()
        if not staged_files:
            self.log_error("generate", "No staged files")
            return None
        
        # Detect change type and scope
        change_type = self.detect_change_type(staged_files)
        scope = self.detect_scope(staged_files) if self.bot_config.include_scope else None
        issue_ref = self.extract_issue_reference()
        
        # Generate subject line
        file_count = len(staged_files)
        if file_count == 1:
            subject = f"update {staged_files[0].split('/')[-1]}"
        else:
            subject = f"update {file_count} files"
        
        # Truncate subject if needed
        max_len = self.bot_config.max_subject_length
        if len(subject) > max_len - 10:  # Leave room for type/scope
            subject = subject[:max_len - 13] + "..."
        
        # Build message
        if scope:
            header = f"{change_type}({scope}): {subject}"
        else:
            header = f"{change_type}: {subject}"
        
        # Build body
        body_lines = [
            "",
            "Changes:",
        ]
        for f in staged_files[:10]:  # Limit to first 10 files
            body_lines.append(f"- {f}")
        if len(staged_files) > 10:
            body_lines.append(f"- ... and {len(staged_files) - 10} more files")
        
        # Add footer with issue reference
        footer_lines = []
        if issue_ref:
            footer_lines.append("")
            footer_lines.append(f"Refs: {issue_ref}")
        
        message = header + "\n".join(body_lines) + "\n".join(footer_lines)
        return message
    
    def run(self) -> bool:
        """
        Generate commit message for staged changes.
        
        Returns:
            True if message was generated successfully
        """
        message = self.generate_message()
        if message:
            self.log_operation("generate", {"message_length": len(message)})
            # Store message for Commit Bot to use
            self._generated_message = message
            return True
        return False
    
    def get_message(self) -> Optional[str]:
        """Get the last generated message."""
        return getattr(self, "_generated_message", None)
