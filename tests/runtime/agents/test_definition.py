"""
Unit tests for definition module.

Tests the AgentDefinition class for loading agent definitions from markdown files.
"""

import pytest
import tempfile
from pathlib import Path


class TestAgentDefinition:
    """Test AgentDefinition class."""

    def test_init(self):
        """Test AgentDefinition initialization."""
        from src.runtime.agents.definition import AgentDefinition

        definition = AgentDefinition(
            name="Test Agent",
            purpose="Test purpose",
            instantiation_conditions=["condition1"],
            termination_conditions=["condition2"],
            input_format="{}",
            output_format="{}",
            instructions="Test instructions",
            clarification_conditions=["clarify1"]
        )

        assert definition.name == "Test Agent"
        assert definition.purpose == "Test purpose"
        assert definition.instantiation_conditions == ["condition1"]
        assert definition.model_preference == "haiku"  # default
        assert definition.max_iterations == 10  # default
        assert definition.can_write_code is False  # default

    def test_init_with_all_params(self):
        """Test AgentDefinition with all parameters."""
        from src.runtime.agents.definition import AgentDefinition

        definition = AgentDefinition(
            name="Test Agent",
            purpose="Test purpose",
            instantiation_conditions=[],
            termination_conditions=[],
            input_format="{}",
            output_format="{}",
            instructions="Test",
            clarification_conditions=[],
            model_preference="sonnet",
            max_iterations=50,
            can_write_code=True,
            can_write_tests=True,
            task_complexity="strategic",
            category="leadership"
        )

        assert definition.model_preference == "sonnet"
        assert definition.max_iterations == 50
        assert definition.can_write_code is True
        assert definition.can_write_tests is True
        assert definition.task_complexity == "strategic"
        assert definition.category == "leadership"

    def test_get_required_input_fields_with_required_list(self):
        """Test extracting required fields from schema with required list."""
        from src.runtime.agents.definition import AgentDefinition

        definition = AgentDefinition(
            name="Test",
            purpose="Test",
            instantiation_conditions=[],
            termination_conditions=[],
            input_format='{"required": ["field1", "field2"], "properties": {}}',
            output_format="{}",
            instructions="Test",
            clarification_conditions=[]
        )

        fields = definition.get_required_input_fields()

        assert fields == {"field1", "field2"}

    def test_get_required_input_fields_by_description(self):
        """Test extracting required fields when no explicit required list."""
        from src.runtime.agents.definition import AgentDefinition

        definition = AgentDefinition(
            name="Test",
            purpose="Test",
            instantiation_conditions=[],
            termination_conditions=[],
            input_format='{"properties": {"required_field": {"description": "A field"}, "optional_field": {"description": "(optional) Another field"}}}',
            output_format="{}",
            instructions="Test",
            clarification_conditions=[]
        )

        fields = definition.get_required_input_fields()

        assert "required_field" in fields
        assert "optional_field" not in fields

    def test_get_required_input_fields_invalid_json(self):
        """Test that invalid JSON returns empty set."""
        from src.runtime.agents.definition import AgentDefinition

        definition = AgentDefinition(
            name="Test",
            purpose="Test",
            instantiation_conditions=[],
            termination_conditions=[],
            input_format='not valid json',
            output_format="{}",
            instructions="Test",
            clarification_conditions=[]
        )

        fields = definition.get_required_input_fields()

        assert fields == set()


class TestAgentDefinitionFromFile:
    """Test loading AgentDefinition from markdown files."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_from_file_not_found(self, temp_dir):
        """Test FileNotFoundError when file doesn't exist."""
        from src.runtime.agents.definition import AgentDefinition

        with pytest.raises(FileNotFoundError):
            AgentDefinition.from_file(temp_dir / "nonexistent.md")

    def test_from_file_basic(self, temp_dir):
        """Test loading a basic definition file."""
        from src.runtime.agents.definition import AgentDefinition

        # Create a test markdown file
        content = """# Test Agent

## Purpose
This is a test agent.

## Instantiation Conditions
- When testing is needed

## Termination Conditions
- When tests complete

## Input Format
```json
{"test": "input"}
```

## Output Format
```json
{"result": "output"}
```

## Instructions
Do the testing.

## Request Clarification When
- When unclear
"""

        test_file = temp_dir / "test_agent.md"
        test_file.write_text(content)

        definition = AgentDefinition.from_file(test_file)

        assert definition.name == "Test Agent"
        assert "test agent" in definition.purpose.lower()
        assert len(definition.instantiation_conditions) == 1
        assert len(definition.termination_conditions) == 1
        assert "Do the testing" in definition.instructions

    def test_from_file_with_metadata(self, temp_dir):
        """Test loading a definition file with metadata fields."""
        from src.runtime.agents.definition import AgentDefinition

        content = """# Advanced Agent

## Purpose
An advanced agent.

## Instantiation Conditions
- Always

## Termination Conditions
- Done

## Input Format
```json
{}
```

## Output Format
```json
{}
```

## Instructions
Work hard.

## Request Clarification When
- Never

## Model Preference
opus

## Max Iterations
100

## Can Write Code
true

## Can Write Tests
yes

## Task Complexity
strategic
"""

        test_file = temp_dir / "advanced_agent.md"
        test_file.write_text(content)

        definition = AgentDefinition.from_file(test_file)

        assert definition.model_preference == "opus"
        assert definition.max_iterations == 100
        assert definition.can_write_code is True
        assert definition.can_write_tests is True
        assert definition.task_complexity == "strategic"

    def test_from_file_missing_heading_uses_filename(self, temp_dir):
        """Test that missing H1 heading falls back to filename."""
        from src.runtime.agents.definition import AgentDefinition

        content = """## Purpose
Test purpose.

## Instantiation Conditions
- Test

## Termination Conditions
- Test

## Input Format
```json
{}
```

## Output Format
```json
{}
```

## Instructions
Test

## Request Clarification When
- Test
"""

        test_file = temp_dir / "my_test_agent.md"
        test_file.write_text(content)

        definition = AgentDefinition.from_file(test_file)

        assert definition.name == "My Test Agent"

    def test_from_file_category_from_parent_dir(self, temp_dir):
        """Test that category is derived from parent directory."""
        from src.runtime.agents.definition import AgentDefinition

        # Create leadership subdirectory
        leadership_dir = temp_dir / "leadership"
        leadership_dir.mkdir()

        content = """# Leader Agent

## Purpose
Lead.

## Instantiation Conditions
- Start

## Termination Conditions
- End

## Input Format
```json
{}
```

## Output Format
```json
{}
```

## Instructions
Lead well.

## Request Clarification When
- Unclear
"""

        test_file = leadership_dir / "leader.md"
        test_file.write_text(content)

        definition = AgentDefinition.from_file(test_file)

        assert definition.category == "leadership"

    def test_from_file_invalid_task_complexity(self, temp_dir):
        """Test that invalid task complexity defaults to routine."""
        from src.runtime.agents.definition import AgentDefinition

        content = """# Agent

## Purpose
Test.

## Instantiation Conditions
- Test

## Termination Conditions
- Test

## Input Format
```json
{}
```

## Output Format
```json
{}
```

## Instructions
Test

## Request Clarification When
- Test

## Task Complexity
invalid_complexity
"""

        test_file = temp_dir / "agent.md"
        test_file.write_text(content)

        definition = AgentDefinition.from_file(test_file)

        assert definition.task_complexity == "routine"


class TestExtractMethods:
    """Test static extraction methods."""

    def test_extract_heading(self):
        """Test heading extraction."""
        from src.runtime.agents.definition import AgentDefinition

        content = "# Main Heading\n\nSome content"
        heading = AgentDefinition._extract_heading(content, 1)

        assert heading == "Main Heading"

    def test_extract_heading_level_2(self):
        """Test H2 heading extraction."""
        from src.runtime.agents.definition import AgentDefinition

        content = "# H1\n## H2 Heading\nContent"
        heading = AgentDefinition._extract_heading(content, 2)

        assert heading == "H2 Heading"

    def test_extract_heading_not_found(self):
        """Test heading extraction when not found."""
        from src.runtime.agents.definition import AgentDefinition

        content = "No headings here"
        heading = AgentDefinition._extract_heading(content, 1)

        assert heading == ""

    def test_extract_section_text(self):
        """Test section text extraction."""
        from src.runtime.agents.definition import AgentDefinition

        content = """## Purpose
This is the purpose text.
It has multiple lines.

## Next Section
"""
        text = AgentDefinition._extract_section_text(content, "Purpose")

        assert "purpose text" in text
        assert "multiple lines" in text

    def test_extract_list_items(self):
        """Test list item extraction."""
        from src.runtime.agents.definition import AgentDefinition

        content = """## Items
- First item
- Second item
- Third item

## Other
"""
        items = AgentDefinition._extract_list_items(content, "Items")

        assert len(items) == 3
        assert "First item" in items
        assert "Second item" in items
        assert "Third item" in items

    def test_extract_list_items_empty(self):
        """Test list item extraction when section not found."""
        from src.runtime.agents.definition import AgentDefinition

        content = "## Other\nNo list here"
        items = AgentDefinition._extract_list_items(content, "Items")

        assert items == []

    def test_extract_json_block(self):
        """Test JSON block extraction."""
        from src.runtime.agents.definition import AgentDefinition

        content = """## Format
```json
{"key": "value"}
```

## Other
"""
        json_str = AgentDefinition._extract_json_block(content, "Format")

        assert json_str == '{"key": "value"}'

    def test_extract_json_block_not_found(self):
        """Test JSON block extraction when not found."""
        from src.runtime.agents.definition import AgentDefinition

        content = "## Format\nNo JSON here"
        json_str = AgentDefinition._extract_json_block(content, "Format")

        assert json_str == "{}"

    def test_extract_metadata(self):
        """Test metadata extraction."""
        from src.runtime.agents.definition import AgentDefinition

        content = """## Model Preference
sonnet

## Other
"""
        value = AgentDefinition._extract_metadata(content, "Model Preference", "default")

        assert value == "sonnet"

    def test_extract_metadata_default(self):
        """Test metadata extraction returns default when not found."""
        from src.runtime.agents.definition import AgentDefinition

        content = "## Other\nStuff"
        value = AgentDefinition._extract_metadata(content, "Model Preference", "haiku")

        assert value == "haiku"
