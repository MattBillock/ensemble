"""Agent definition parser for loading agent type definitions from markdown files."""
import re
from pathlib import Path
from typing import List, Optional


class AgentDefinition:
    """Represents an agent type definition loaded from a markdown file."""

    def __init__(
        self,
        name: str,
        purpose: str,
        instantiation_conditions: List[str],
        termination_conditions: List[str],
        input_format: str,
        output_format: str,
        instructions: str,
        clarification_conditions: List[str],
        model_preference: str = "haiku",
        max_iterations: int = 10,
    ):
        self.name = name
        self.purpose = purpose
        self.instantiation_conditions = instantiation_conditions
        self.termination_conditions = termination_conditions
        self.input_format = input_format
        self.output_format = output_format
        self.instructions = instructions
        self.clarification_conditions = clarification_conditions
        self.model_preference = model_preference
        self.max_iterations = max_iterations

    @classmethod
    def from_file(cls, file_path: Path) -> "AgentDefinition":
        """
        Load an agent definition from a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            AgentDefinition instance

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Agent definition file not found: {file_path}")

        content = file_path.read_text()

        # Extract the name from the first H1 heading
        name = cls._extract_heading(content, 1)

        # Extract sections
        purpose = cls._extract_section_text(content, "Purpose")
        instantiation_conditions = cls._extract_list_items(content, "Instantiation Conditions")
        termination_conditions = cls._extract_list_items(content, "Termination Conditions")
        input_format = cls._extract_json_block(content, "Input Format")
        output_format = cls._extract_json_block(content, "Output Format")
        instructions = cls._extract_section_text(content, "Instructions")
        clarification_conditions = cls._extract_list_items(content, "Request Clarification When")

        # Extract metadata
        model_preference = cls._extract_metadata(content, "Model Preference", "haiku")
        max_iterations_str = cls._extract_metadata(content, "Max Iterations", "10")
        max_iterations = int(max_iterations_str)

        return cls(
            name=name,
            purpose=purpose,
            instantiation_conditions=instantiation_conditions,
            termination_conditions=termination_conditions,
            input_format=input_format,
            output_format=output_format,
            instructions=instructions,
            clarification_conditions=clarification_conditions,
            model_preference=model_preference,
            max_iterations=max_iterations,
        )

    @staticmethod
    def _extract_heading(content: str, level: int) -> str:
        """Extract the first heading of the specified level."""
        pattern = f"^{'#' * level} (.+)$"
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_section_text(content: str, section_name: str) -> str:
        """Extract text content from a section until the next heading."""
        # Find the section heading
        pattern = f"## {re.escape(section_name)}\\n(.+?)(?=\\n## |\\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Remove code blocks and list items for plain text sections
            text = re.sub(r"```[^`]+```", "", text, flags=re.DOTALL)
            text = re.sub(r"^\s*-\s*", "", text, flags=re.MULTILINE)
            return text.strip()
        return ""

    @staticmethod
    def _extract_list_items(content: str, section_name: str) -> List[str]:
        """Extract list items from a section."""
        # Find the section
        pattern = f"## {re.escape(section_name)}\\n(.+?)(?=\\n## |\\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)

        # Extract list items (lines starting with -)
        items = []
        for line in section_content.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                # Remove the dash and any leading whitespace
                item = line[1:].strip()
                if item:
                    items.append(item)

        return items

    @staticmethod
    def _extract_json_block(content: str, section_name: str) -> str:
        """Extract JSON content from a code block in a section."""
        # Find the section
        pattern = f"## {re.escape(section_name)}\\n(.+?)(?=\\n## |\\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return "{}"

        section_content = match.group(1)

        # Extract JSON from code block
        json_pattern = r"```json\n(.+?)\n```"
        json_match = re.search(json_pattern, section_content, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        return "{}"

    @staticmethod
    def _extract_metadata(content: str, field_name: str, default: str) -> str:
        """Extract a metadata field value."""
        pattern = f"## {re.escape(field_name)}\\n(.+?)(?=\\n## |\\n\\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return default
