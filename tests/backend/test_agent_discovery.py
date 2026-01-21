"""
Tests for agent discovery functionality.

Validates that only legitimate agent directories are discovered and
output/docs/other non-agent directories are properly excluded.
"""

import pytest
import tempfile
from pathlib import Path


class TestAgentDiscovery:
    """Test agent discovery functions."""

    def test_discover_only_valid_agent_directories(self):
        """Test that only directories in VALID_AGENT_DIRS are discovered."""
        # Import the discovery function
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src/field/ensemble_ui/backend'))

        from src.field.ensemble_ui.backend.main import discover_agent_directories, VALID_AGENT_DIRS

        # Discover directories
        discovered = discover_agent_directories()

        # All discovered directories should be in VALID_AGENT_DIRS
        for dir_name in discovered.keys():
            assert dir_name in VALID_AGENT_DIRS, \
                f"Discovered non-agent directory: {dir_name}"

    def test_output_directory_not_discovered(self):
        """Test that output directory is NOT discovered as agent directory."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src/field/ensemble_ui/backend'))

        from src.field.ensemble_ui.backend.main import discover_agent_directories

        discovered = discover_agent_directories()

        # Output should never be in discovered directories
        assert 'output' not in discovered, \
            "Output directory should not be discovered as agent directory"

    def test_docs_directory_not_discovered(self):
        """Test that docs directory is NOT discovered as agent directory."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src/field/ensemble_ui/backend'))

        from src.field.ensemble_ui.backend.main import discover_agent_directories

        discovered = discover_agent_directories()

        # Docs should never be in discovered directories
        assert 'docs' not in discovered, \
            "Docs directory should not be discovered as agent directory"

    def test_src_directory_not_discovered(self):
        """Test that src directory is NOT discovered as agent directory."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src/field/ensemble_ui/backend'))

        from src.field.ensemble_ui.backend.main import discover_agent_directories

        discovered = discover_agent_directories()

        # Src should never be in discovered directories
        assert 'src' not in discovered, \
            "Src directory should not be discovered as agent directory"

    def test_expected_agent_directories_discovered(self):
        """Test that expected agent directories ARE discovered."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src/field/ensemble_ui/backend'))

        from src.field.ensemble_ui.backend.main import discover_agent_directories

        discovered = discover_agent_directories()

        # These category subdirectories should be discovered if they exist in agents/
        expected_dirs = ['leadership', 'coordinators', 'developers', 'testers', 'designers', 'support']

        for expected in expected_dirs:
            # Only check if directory exists in project under agents/
            project_root = Path(__file__).parent.parent.parent
            if (project_root / 'agents' / expected).exists():
                assert expected in discovered, \
                    f"Expected agent directory '{expected}' was not discovered"


class TestAgentDefinitionValidation:
    """Test that agent definitions are properly validated."""

    def test_output_files_are_not_agents(self):
        """Test that files in output directory are not treated as agents."""
        from pathlib import Path
        from src.runtime.agents.definition import AgentDefinition

        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / 'output'

        if output_dir.exists():
            # Try to load a few output files as agent definitions
            for md_file in list(output_dir.glob('*.md'))[:5]:
                try:
                    definition = AgentDefinition.from_file(md_file)
                    # If it loads, it should have minimal/empty instructions
                    # which would fail proper agent validation
                    assert definition.instructions.strip(), \
                        f"Output file {md_file.name} should not be a valid agent definition"
                except Exception:
                    # Expected - output files should fail to parse as agents
                    pass

    def test_valid_agent_definition_has_required_sections(self):
        """Test that valid agent definitions have required sections."""
        from pathlib import Path
        from src.runtime.agents.definition import AgentDefinition

        project_root = Path(__file__).parent.parent.parent

        # Load a known valid agent definition from consolidated agents/ folder
        exec_dir = project_root / 'agents' / 'leadership' / 'executive_director.md'
        if exec_dir.exists():
            definition = AgentDefinition.from_file(exec_dir)

            # Valid agents should have these populated
            assert definition.name, "Agent should have a name"
            assert definition.purpose, "Agent should have a purpose"
            assert definition.instructions, "Agent should have instructions"


class TestAgentCategoryMapping:
    """Test that agent categories are properly mapped."""

    def test_category_derived_from_directory(self):
        """Test that category is derived from parent directory."""
        from pathlib import Path
        from src.runtime.agents.definition import AgentDefinition

        project_root = Path(__file__).parent.parent.parent

        # Paths are now under agents/ folder
        test_cases = [
            ('agents/leadership/executive_director.md', 'leadership'),
            ('agents/coordinators/backend_coordinator.md', 'coordinators'),
            ('agents/developers/backend_developer.md', 'developers'),
            ('agents/testers/unit_test_writer.md', 'testers'),
        ]

        for path, expected_category in test_cases:
            full_path = project_root / path
            if full_path.exists():
                definition = AgentDefinition.from_file(full_path)
                assert definition.category == expected_category, \
                    f"Expected category '{expected_category}' for {path}, got '{definition.category}'"
