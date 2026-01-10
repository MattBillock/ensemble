#!/usr/bin/env python3
"""Use Ensemble agents to complete the UI."""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, SpawnAgentTool

load_dotenv()

def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found")

    print("=" * 70)
    print("🎭 COMPLETING ENSEMBLE UI VIA AGENT PIPELINE")
    print("=" * 70)
    print()

    # Load Executive Director
    exec_dir_path = Path("leadership/executive_director.md")
    exec_dir_def = AgentDefinition.from_file(exec_dir_path)

    # Set up tools
    tools = ToolRegistry.default(exec_dir_def)
    spawn_tool = SpawnAgentTool(
        agent_types_dir=Path("."),
        api_key=api_key,
        tools=tools
    )
    tools.register(spawn_tool)

    # Create runtime
    runtime = AgentRuntime(
        exec_dir_def,
        api_key=api_key,
        tools=tools
    )

    # Execute with UI completion requirements
    input_data = {
        "user_vision": Path("src/field/ensemble_ui/UI_COMPLETION_REQUIREMENTS.md").read_text(),
        "output_directory": "src/field/ensemble_ui",
        "context": "Complete the Ensemble UI web application. Backend needs integration with agent runtime, frontend needs status display and hierarchy visualization components."
    }

    print("🚀 Spawning Executive Director to complete UI...")
    print("=" * 70)
    print()

    result = runtime.execute(input_data)

    print()
    print("=" * 70)
    print("📊 EXECUTIVE DIRECTOR REPORT")
    print("=" * 70)
    print()
    print(f"Status: {result.get('status')}")
    print()

    if result.get('deliverables'):
        print(f"📦 Deliverables ({len(result.get('deliverables'))}):")
        for item in result['deliverables']:
            print(f"  ✓ {item}")
        print()

    if result.get('message'):
        print(f"💬 Message:")
        print(result['message'])
        print()

    print("=" * 70)

if __name__ == "__main__":
    main()
