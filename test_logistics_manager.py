"""Test the Logistics Manager agent."""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, WriteFileTool, ReadFileTool, RunCommandTool

load_dotenv()


def main():
    """Test Logistics Manager on our own codebase."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    print("=" * 70)
    print("TEST: Logistics Manager")
    print("=" * 70)
    print("\nTesting on our own Ensemble codebase...")

    # Load the Logistics Manager agent
    agent_def = AgentDefinition.from_file(Path("support/logistics_manager.md"))

    # Set up tools
    tools = ToolRegistry()
    tools.register(ReadFileTool())
    tools.register(WriteFileTool())
    tools.register(RunCommandTool())

    runtime = AgentRuntime(agent_def, api_key=api_key, tools=tools)

    # Test case: Explore the ensemble codebase
    input_data = {
        "codebase_path": ".",
        "objective": "Map the agent system structure - identify all agent definitions, the runtime system, and how agents are organized",
        "output_file": "charts/codebase_survey.md"
    }

    print(f"\nObjective: {input_data['objective']}")
    print(f"Exploring: {input_data['codebase_path']}")
    print(f"Report will be written to: {input_data['output_file']}")
    print("\n" + "-" * 70)

    result = runtime.execute(input_data)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Status: {result['status']}")
    print(f"\nSummary:\n{result.get('summary', 'N/A')}")

    if result.get('key_files'):
        print(f"\nKey Files ({len(result['key_files'])}):")
        for file_info in result['key_files'][:5]:  # Show first 5
            importance = file_info.get('importance', 'medium')
            print(f"  [{importance.upper()}] {file_info['path']}")
            print(f"      → {file_info.get('purpose', 'No description')}")

    if result.get('tech_stack'):
        print(f"\nTech Stack: {', '.join(result['tech_stack'])}")

    if result.get('directory_structure'):
        print(f"\nDirectory Structure:\n{result['directory_structure']}")

    if result.get('report_file'):
        print(f"\n✓ Detailed report written to: {result['report_file']}")

        # Show first part of report
        if os.path.exists(result['report_file']):
            with open(result['report_file'], 'r') as f:
                content = f.read()
                print(f"\n--- Report Preview (first 800 chars) ---")
                print(content[:800])
                if len(content) > 800:
                    print("... (truncated)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
