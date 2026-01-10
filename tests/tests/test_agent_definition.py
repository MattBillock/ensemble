"""Tests for agent definition parser."""
import json
from pathlib import Path

import pytest

from agents.definition import AgentDefinition


class TestAgentDefinition:
    """Test agent definition parsing."""

    @pytest.fixture
    def code_writer_path(self):
        """Path to code_writer agent definition."""
        return Path(__file__).parent.parent / "agent_types" / "code_writer.md"

    def test_load_agent_definition(self, code_writer_path):
        """Test loading an agent definition from markdown file."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.name == "Code Writer"
        assert agent_def.purpose is not None
        assert "Python code" in agent_def.purpose

    def test_parse_purpose(self, code_writer_path):
        """Test parsing the Purpose section."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert "computational" in agent_def.purpose.lower()
        assert "algorithmic" in agent_def.purpose.lower()

    def test_parse_instantiation_conditions(self, code_writer_path):
        """Test parsing instantiation conditions."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.instantiation_conditions is not None
        assert len(agent_def.instantiation_conditions) > 0
        assert any("problem" in cond.lower() for cond in agent_def.instantiation_conditions)

    def test_parse_termination_conditions(self, code_writer_path):
        """Test parsing termination conditions."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.termination_conditions is not None
        assert len(agent_def.termination_conditions) > 0
        assert any("written" in cond.lower() for cond in agent_def.termination_conditions)

    def test_parse_input_format(self, code_writer_path):
        """Test parsing input format with JSON schema."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.input_format is not None
        # Should be able to parse as JSON
        input_schema = json.loads(agent_def.input_format)
        assert "problem_description" in input_schema
        assert "output_file" in input_schema

    def test_parse_output_format(self, code_writer_path):
        """Test parsing output format with JSON schema."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.output_format is not None
        # Should be able to parse as JSON
        output_schema = json.loads(agent_def.output_format)
        assert "status" in output_schema
        assert "output_file" in output_schema

    def test_parse_instructions(self, code_writer_path):
        """Test parsing instructions section."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.instructions is not None
        assert len(agent_def.instructions) > 0

    def test_parse_clarification_conditions(self, code_writer_path):
        """Test parsing when to request clarification."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.clarification_conditions is not None
        assert len(agent_def.clarification_conditions) > 0

    def test_parse_model_preference(self, code_writer_path):
        """Test parsing model preference metadata."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.model_preference == "haiku"

    def test_parse_max_iterations(self, code_writer_path):
        """Test parsing max iterations metadata."""
        agent_def = AgentDefinition.from_file(code_writer_path)

        assert agent_def.max_iterations == 5

    def test_missing_file_raises_error(self):
        """Test that missing file raises appropriate error."""
        with pytest.raises(FileNotFoundError):
            AgentDefinition.from_file(Path("nonexistent.md"))
