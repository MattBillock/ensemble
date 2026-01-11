#!/usr/bin/env python3
"""Execute Milestone 0: Foundation Fixes via agent pipeline."""
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
    print("🎯 MILESTONE 0: FOUNDATION FIXES")
    print("=" * 70)
    print()
    print("Objectives:")
    print("  1. Complete drum corps cleanup (339 → 0 refs)")
    print("  2. Consolidate agents (23 → 14)")
    print("  3. Fix Executive Director coordination bug")
    print("  4. Implement budget tier system")
    print("  5. Initial DDD refactoring")
    print("  6. Set up local CI/CD")
    print()
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

    # Execute with Milestone 0 requirements
    input_data = {
        "user_vision": Path("MILESTONE_0_REQUIREMENTS.md").read_text(),
        "output_directory": ".",  # Root directory for this work
        "context": """Foundation fixes to clean technical debt and prepare for UI development.

        CRITICAL: This is REFACTORING and CLEANUP work, NOT new feature development.

        Key tasks:
        1. Delete and merge agent files (consolidation)
        2. Update existing agent .md files (cleanup text, fix bugs)
        3. Create new Python modules (ModelSelector, domain layer)
        4. Set up CI/CD config files
        5. Run tests to verify nothing broke

        DO NOT try to implement the UI yet - that's Milestone 1.
        Focus only on cleaning up the agent system itself.
        """,
        "project_name": "milestone-0-foundation"
    }

    print("🚀 Spawning Executive Director for Milestone 0...")
    print("=" * 70)
    print()

    try:
        result = runtime.execute(input_data)

        print()
        print("=" * 70)
        print("📊 MILESTONE 0 COMPLETION REPORT")
        print("=" * 70)
        print()
        print(f"Status: {result.get('status', 'UNKNOWN')}")

        if result.get('phase'):
            print(f"Phase: {result.get('phase')}")
        if result.get('project_name'):
            print(f"Project: {result.get('project_name')}")
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

        if result.get('user_question'):
            print(f"❓ Question:")
            print(result['user_question'])
            print()

        print("=" * 70)

        # Return appropriate exit code
        status = result.get('status', 'unknown').lower()
        if status == 'success':
            print()
            print("✅ MILESTONE 0 COMPLETED SUCCESSFULLY")
            print()
            print("Next steps:")
            print("  1. Review deliverables")
            print("  2. Run comprehensive analysis: python analyze_milestone.py milestone-0")
            print("  3. Review MILESTONE_0_ANALYSIS.md")
            print("  4. Implement recommendations")
            print("  5. Commit changes")
            print("  6. Start Milestone 1")
            return 0
        elif status == 'needs_user_input':
            print("⏸️  Milestone 0 needs user input")
            return 2
        else:
            print("⚠️  Milestone 0 completed with issues")
            return 1

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ MILESTONE 0 EXECUTION ERROR")
        print("=" * 70)
        print(f"Error: {type(e).__name__}: {e}")
        print()

        import traceback
        print("Traceback:")
        traceback.print_exc()
        print("=" * 70)
        return 3

if __name__ == "__main__":
    exit(main())
