#!/usr/bin/env python3
"""Complete Milestone 2: Connect React frontend to FastAPI backend."""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, SpawnAgentTool

load_dotenv()


def main():
    """Execute Development Manager to complete frontend integration."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    print("="*70)
    print("🔌 COMPLETING MILESTONE 2: FRONTEND-BACKEND CONNECTION")
    print("="*70)
    print()
    print("Tasks:")
    print("  1. Add WebSocket connection to React app")
    print("  2. Implement API calls to backend")
    print("  3. Display real-time agent status")
    print("  4. Show generated solutions")
    print()
    print("="*70)
    print()

    # Load Development Manager
    dev_mgr_path = Path("leadership/development_manager.md")
    dev_mgr_def = AgentDefinition.from_file(dev_mgr_path)

    # Set up tools with agent definition
    tools = ToolRegistry.default(dev_mgr_def)

    # Add spawn_agent tool
    spawn_tool = SpawnAgentTool(
        agent_types_dir=Path("."),
        api_key=api_key,
        tools=tools
    )
    tools.register(spawn_tool)

    # Create runtime
    runtime = AgentRuntime(
        dev_mgr_def,
        api_key=api_key,
        tools=tools
    )

    input_data = {
        "requirements_file": "src/field/ensemble_ui/frontend_integration_requirements.md",
        "output_directory": "src/field/ensemble_ui/frontend/src",
        "project_name": "Ensemble UI Frontend Integration"
    }

    print("🚀 Launching Development Manager...")
    print("="*70)
    print()

    result = runtime.execute(input_data)

    # Print results
    print()
    print("="*70)
    print("📊 PROGRAM COORDINATOR REPORT")
    print("="*70)
    print()
    print(f"Status: {result.get('status')}")
    print()

    deliverables = result.get("deliverables", [])
    if deliverables:
        print(f"📦 Deliverables ({len(deliverables)}):")
        for item in deliverables:
            print(f"  ✓ {item}")
        print()

    message = result.get("message")
    if message:
        print(f"💬 Message:")
        print(f"{message}")
        print()

    print("="*70)
    print()


if __name__ == "__main__":
    main()
