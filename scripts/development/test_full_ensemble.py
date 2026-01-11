"""Test the complete Ensemble agent system on the UI project."""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry

load_dotenv()


def main():
    """Run the full ensemble on the UI project."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    print("=" * 70)
    print("🎺 ENSEMBLE - FULL SYSTEM TEST 🥁")
    print("=" * 70)
    print("\nProject: Ensemble Web UI")
    print("Agents: 17 agents in hierarchical coordination")
    print("\n" + "=" * 70)

    # UI Project Vision
    user_vision = """
I want to build a web-based user interface for our Ensemble agent system.

Currently, our agents are command-line tools that developers use by writing
Python scripts. This works for us developers, but it's not accessible to
non-technical users who want to see the system in action.

I want a simple, clean web UI where users can:
1. Input a problem description in a text box
2. Click "Generate Solution" to start the agent system
3. See real-time updates as agents work (which agents are running, what phase)
4. View the generated code files and test results
5. See a summary of what was accomplished

Technical requirements:
- Frontend: React with JavaScript (I'm open to TypeScript if recommended)
- Backend: Python (prefer lightweight - Flask or FastAPI)
- Keep it simple - this is v1.0, a proof of concept
- Should work locally first (deployment can come later)
- Must show the agent system actually working

This should demonstrate the Ensemble system's capabilities while making it
more accessible. Focus on making it work well, not on fancy features.
"""

    print("\n📋 USER VISION:")
    print("-" * 70)
    print(user_vision)
    print("-" * 70)

    # Load Executive Director
    print("\n🎯 Loading Executive Director...")
    exec_director_def = AgentDefinition.from_file(Path("leadership/executive_director.md"))

    # Set up tools for Executive Director
    tools = ToolRegistry.default()

    runtime = AgentRuntime(exec_director_def, api_key=api_key, tools=tools)

    # Execute!
    print("\n🚀 Launching Executive Director...")
    print("=" * 70)

    input_data = {
        "user_vision": user_vision,
        "output_directory": "src/field/ensemble_ui"
    }

    result = runtime.execute(input_data)

    # Report Results
    print("\n" + "=" * 70)
    print("🎭 ENSEMBLE PERFORMANCE COMPLETE")
    print("=" * 70)

    print(f"\nStatus: {result['status']}")
    print(f"Project: {result.get('project_name', 'N/A')}")
    print(f"Phase: {result.get('phase', 'N/A')}")

    print(f"\n📝 Summary:")
    print(result.get('summary', 'No summary provided'))

    if result.get('deliverables'):
        print(f"\n📦 Deliverables ({len(result['deliverables'])}):")
        for deliverable in result['deliverables']:
            print(f"  ✓ {deliverable}")

    if result.get('user_question'):
        print(f"\n❓ User Input Needed:")
        print(result['user_question'])

    print(f"\n💬 Message:")
    print(result.get('message', 'No message'))

    print("\n" + "=" * 70)

    return result


if __name__ == "__main__":
    main()
