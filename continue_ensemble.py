"""Continue the Ensemble build - spawn Program Coordinator to drive lifecycle."""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, SpawnAgentTool

load_dotenv()


def main():
    """User approved requirements - spawn Program Coordinator to drive the build."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    print("=" * 70)
    print("🎺 USER APPROVED - PROCEEDING WITH BUILD 🥁")
    print("=" * 70)
    print("\nSpawning Program Coordinator to drive lifecycle:")
    print("  1. Break into milestones")
    print("  2. Spawn Designer for architecture")
    print("  3. Spawn Caption Heads for task breakdown")
    print("  4. Coordinate with Drum Major for implementation")
    print("\n" + "=" * 70)

    # Load Program Coordinator
    print("\n📋 Loading Program Coordinator...")
    prog_coord_def = AgentDefinition.from_file(Path("leadership/program_coordinator.md"))

    # Set up tools
    tools = ToolRegistry.default()

    # Add spawn_agent tool so Program Coordinator can spawn other agents
    spawn_tool = SpawnAgentTool(
        agent_types_dir=Path("."),  # Project root - agents can use paths like "leadership/designer"
        api_key=api_key,
        tools=tools  # Spawned agents get same tools
    )
    tools.register(spawn_tool)

    runtime = AgentRuntime(prog_coord_def, api_key=api_key, tools=tools)

    # Execute Program Coordinator
    print("\n🚀 Launching Program Coordinator...")
    print("=" * 70)

    input_data = {
        "requirements_file": "src/field/ensemble_ui/requirements.md",
        "output_directory": "src/field/ensemble_ui",
        "project_name": "Ensemble Web UI"
    }

    result = runtime.execute(input_data)

    # Report Results
    print("\n" + "=" * 70)
    print("📊 PROGRAM COORDINATOR REPORT")
    print("=" * 70)

    print(f"\nStatus: {result['status']}")
    print(f"Phase: {result.get('phase', 'N/A')}")

    if result.get('milestones'):
        print(f"\n🎯 Milestones ({len(result['milestones'])}):")
        for i, milestone in enumerate(result['milestones'], 1):
            print(f"  {i}. {milestone}")

    if result.get('deliverables'):
        print(f"\n📦 Deliverables ({len(result['deliverables'])}):")
        for deliverable in result['deliverables']:
            print(f"  ✓ {deliverable}")

    if result.get('clarification_needed'):
        print(f"\n❓ Clarification Needed:")
        print(result['clarification_needed'])

    print(f"\n💬 Message:")
    print(result.get('message', 'No message'))

    print("\n" + "=" * 70)

    return result


if __name__ == "__main__":
    main()
