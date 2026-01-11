#!/usr/bin/env python3
"""Use agent pipeline to create ModelSelector implementation."""
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
    print("🎯 CREATING MODEL SELECTOR VIA AGENT PIPELINE")
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

    # Execute with ModelSelector requirements
    input_data = {
        "user_vision": Path("MODEL_SELECTOR_REQUIREMENTS.md").read_text(),
        "output_directory": "src/runtime/agents",
        "context": """Create the ModelSelector class for budget-aware model selection.

This is NEW CODE CREATION (not refactoring), which the agent pipeline handles well.

Key deliverables:
1. model_selector.py with ModelSelector class
2. Unit tests (test_model_selector.py)
3. Integration tests (test_budget_tier_integration.py)
4. Update AgentDefinition with task_complexity field
5. Update AgentRuntime to use ModelSelector

Focus on clean, well-tested code following DDD principles where applicable.""",
        "project_name": "model-selector"
    }

    print("🚀 Spawning Executive Director to create ModelSelector...")
    print("=" * 70)
    print()

    try:
        result = runtime.execute(input_data)

        print()
        print("=" * 70)
        print("📊 MODEL SELECTOR CREATION REPORT")
        print("=" * 70)
        print()
        print(f"Status: {result.get('status', 'UNKNOWN')}")

        if result.get('phase'):
            print(f"Phase: {result.get('phase')}")
        print()

        if result.get('summary'):
            print(f"📝 Summary:")
            print(result['summary'])
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

        status = result.get('status', 'unknown').lower()
        if status == 'success':
            print("✅ ModelSelector creation completed successfully")
            return 0
        elif status == 'needs_user_input':
            print("⏸️  Pipeline needs user input")
            return 2
        else:
            print("⚠️  Pipeline completed with issues")
            return 1

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ PIPELINE EXECUTION ERROR")
        print("=" * 70)
        print(f"Error: {type(e).__name__}: {e}")
        print()

        import traceback
        traceback.print_exc()
        print("=" * 70)
        return 3

if __name__ == "__main__":
    exit(main())
