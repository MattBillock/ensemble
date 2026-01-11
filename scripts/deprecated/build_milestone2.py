#!/usr/bin/env python3
"""Build Milestone 2: Backend Integration for Ensemble UI."""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, SpawnAgentTool

load_dotenv()


def main():
    """Execute Executive Director to build Milestone 2."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    print("="*70)
    print("🎺 BUILDING MILESTONE 2: BACKEND INTEGRATION 🥁")
    print("="*70)
    print()
    print("Spawning Executive Director to coordinate:")
    print("  1. FastAPI backend server")
    print("  2. WebSocket real-time updates")
    print("  3. Agent execution endpoint")
    print("  4. Connect frontend to backend")
    print()
    print("="*70)
    print()

    # Load Executive Director
    exec_dir_path = Path("leadership/executive_director.md")
    exec_dir_def = AgentDefinition.from_file(exec_dir_path)

    # Set up tools with agent definition for permission checking
    tools = ToolRegistry.default(exec_dir_def)

    # Add spawn_agent tool
    spawn_tool = SpawnAgentTool(
        agent_types_dir=Path("."),
        api_key=api_key,
        tools=tools
    )
    tools.register(spawn_tool)

    # Create runtime with state persistence
    state_file = Path("src/field/ensemble_ui/milestone2_exec_state.json")
    runtime = AgentRuntime(
        exec_dir_def,
        api_key=api_key,
        tools=tools,
        state_file=state_file
    )

    # Execute with Milestone 2 vision
    user_vision = """
I want to complete Milestone 2 for the Ensemble UI project: Backend Integration.

Current Status:
- ✅ Milestone 1 Complete: React frontend with ProblemInputForm component
- ❌ Milestone 2 Needed: FastAPI backend + WebSocket integration

Requirements for Milestone 2:
1. FastAPI Backend Server
   - Create backend/ directory structure
   - Implement FastAPI application (main.py)
   - WebSocket endpoint for real-time agent updates (/ws/agent-status)
   - HTTP endpoint for triggering agent execution (POST /api/generate-solution)
   - Agent execution integration (spawn Ensemble agents)

2. WebSocket Real-Time Updates
   - Stream agent progress to frontend
   - Send status updates (which agents are running, current phase)
   - Send final results when complete

3. Frontend Integration
   - Update React app to connect to WebSocket
   - Display real-time agent status
   - Show generated code/results
   - Error handling for backend connection

Please break this into tasks, spawn the Program Coordinator to execute, and build a working FastAPI backend that integrates with our existing React frontend.
"""

    input_data = {
        "user_vision": user_vision,
        "output_directory": "src/field/ensemble_ui",
        "context": "Milestone 1 (React frontend) is complete. Tests are passing. Now we need the backend."
    }

    print("📋 Loading Executive Director...")
    print()
    print("🚀 Launching Executive Director...")
    print("="*70)
    print()

    result = runtime.execute(input_data)

    # Print results
    print()
    print("="*70)
    print("📊 EXECUTIVE DIRECTOR REPORT")
    print("="*70)
    print()
    print(f"Status: {result.get('status')}")
    print(f"Phase: {result.get('phase')}")
    print(f"Project: {result.get('project_name')}")
    print()

    deliverables = result.get("deliverables", [])
    if deliverables:
        print(f"📦 Deliverables ({len(deliverables)}):")
        for item in deliverables:
            print(f"  ✓ {item}")
        print()

    summary = result.get("summary")
    if summary:
        print(f"📝 Summary:")
        print(f"{summary}")
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
