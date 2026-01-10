"""Test the Executive Director agent."""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, WriteFileTool, ReadFileTool

load_dotenv()


def main():
    """Test Executive Director on a sample project vision."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    print("=" * 70)
    print("TEST: Executive Director")
    print("=" * 70)

    # Sample project vision (the UI project we'll eventually build)
    user_vision = """
I want to build a web-based user interface for our Ensemble agent system.

Right now, our agents are command-line tools that developers use by writing
Python scripts. This works, but it's not very accessible.

I want a web UI where users can:
- Input a problem description
- See the agent system work on it in real-time
- View generated code files and test results
- Track which agents are running and what they're doing

The goal is to make the Ensemble system more accessible and easier to use,
while also demonstrating its capabilities. It should be a clean, professional
interface that shows off the agent system working.

This is version 1.0 - keep it simple and focused. We can add features later.
"""

    # Load the Executive Director agent
    agent_def = AgentDefinition.from_file(Path("leadership/executive_director.md"))

    # Set up tools
    tools = ToolRegistry()
    tools.register(ReadFileTool())
    tools.register(WriteFileTool())

    runtime = AgentRuntime(agent_def, api_key=api_key, tools=tools)

    input_data = {
        "user_vision": user_vision,
        "output_file": "charts/ensemble_ui_project_definition.md",
        "stakeholders": "Developers and technical users who want to use Ensemble"
    }

    print(f"\nUser Vision:\n{user_vision[:200]}...")
    print(f"\nOutput will be written to: {input_data['output_file']}")
    print("\n" + "-" * 70)

    result = runtime.execute(input_data)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Status: {result['status']}")
    print(f"Project Name: {result.get('project_name', 'N/A')}")

    print(f"\nStrategic Summary:")
    print(result.get('strategic_summary', 'N/A'))

    if result.get('key_objectives'):
        print(f"\nKey Objectives:")
        for i, obj in enumerate(result['key_objectives'], 1):
            print(f"  {i}. {obj}")

    if result.get('out_of_scope'):
        print(f"\nOut of Scope:")
        for item in result['out_of_scope']:
            print(f"  - {item}")

    if result.get('success_definition'):
        print(f"\nSuccess Definition:")
        print(f"  {result['success_definition']}")

    if result.get('project_definition_file'):
        print(f"\n✓ Project definition written to: {result['project_definition_file']}")

        # Show first part of document
        if os.path.exists(result['project_definition_file']):
            with open(result['project_definition_file'], 'r') as f:
                content = f.read()
                print(f"\n--- Document Preview (first 1000 chars) ---")
                print(content[:1000])
                if len(content) > 1000:
                    print("... (truncated)")

    if result.get('clarification_needed'):
        print(f"\n⚠ Clarification Needed:")
        print(result['clarification_needed'])

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
