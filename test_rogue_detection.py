#!/usr/bin/env python3
"""Test rogue agent detection - verify supervisors cannot write code."""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry

load_dotenv()


def test_supervisor_blocked_from_code():
    """Test that a supervisor agent (Program Coordinator) is blocked from writing code."""
    print("=" * 70)
    print("🛡️  TEST 1: Supervisor Blocked From Writing Code")
    print("=" * 70)
    print()

    # Load Program Coordinator (supervisor with can_write_code=false)
    prog_coord_path = Path("leadership/program_coordinator.md")
    prog_coord_def = AgentDefinition.from_file(prog_coord_path)

    print(f"Agent: {prog_coord_def.name}")
    print(f"can_write_code: {prog_coord_def.can_write_code}")
    print(f"can_write_tests: {prog_coord_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(prog_coord_def)

    # Try to write a code file
    write_tool = tools.get_tool("write_file")
    result = write_tool.execute({
        "file_path": "test_rogue.py",
        "content": "print('This should be blocked')"
    })

    print("Attempting to write test_rogue.py...")
    print(f"Result: {result}")
    print()

    # Check if blocked
    if not result["success"] and "ROGUE AGENT DETECTED" in result["error"]:
        print("✅ SUCCESS: Supervisor was blocked from writing code!")
        print(f"Error message: {result['error']}")
        return True
    else:
        print("❌ FAILURE: Supervisor was NOT blocked!")
        return False


def test_supervisor_blocked_from_tests():
    """Test that a supervisor agent is blocked from writing test files."""
    print()
    print("=" * 70)
    print("🛡️  TEST 2: Supervisor Blocked From Writing Tests")
    print("=" * 70)
    print()

    # Load Drum Major (supervisor with can_write_tests=false)
    drum_major_path = Path("leadership/drum_major.md")
    drum_major_def = AgentDefinition.from_file(drum_major_path)

    print(f"Agent: {drum_major_def.name}")
    print(f"can_write_code: {drum_major_def.can_write_code}")
    print(f"can_write_tests: {drum_major_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(drum_major_def)

    # Try to write a test file
    write_tool = tools.get_tool("write_file")
    result = write_tool.execute({
        "file_path": "tests/test_rogue.py",
        "content": "def test_something(): assert True"
    })

    print("Attempting to write tests/test_rogue.py...")
    print(f"Result: {result}")
    print()

    # Check if blocked
    if not result["success"] and "ROGUE AGENT DETECTED" in result["error"]:
        print("✅ SUCCESS: Supervisor was blocked from writing tests!")
        print(f"Error message: {result['error']}")
        return True
    else:
        print("❌ FAILURE: Supervisor was NOT blocked!")
        return False


def test_code_writer_allowed():
    """Test that a code writer (Trumpet) CAN write code."""
    print()
    print("=" * 70)
    print("🎺 TEST 3: Code Writer Allowed To Write Code")
    print("=" * 70)
    print()

    # Load Trumpet (code writer with can_write_code=true)
    trumpet_path = Path("brass/trumpet.md")
    trumpet_def = AgentDefinition.from_file(trumpet_path)

    print(f"Agent: {trumpet_def.name}")
    print(f"can_write_code: {trumpet_def.can_write_code}")
    print(f"can_write_tests: {trumpet_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(trumpet_def)

    # Try to write a code file (NOT starting with "test_")
    write_tool = tools.get_tool("write_file")
    result = write_tool.execute({
        "file_path": "AllowedComponent.jsx",
        "content": "export default function TestComponent() { return <div>Test</div>; }"
    })

    print("Attempting to write AllowedComponent.jsx...")
    print(f"Result: {result}")
    print()

    # Check if allowed
    if result["success"]:
        print("✅ SUCCESS: Code writer was allowed to write code!")
        # Clean up
        Path("AllowedComponent.jsx").unlink(missing_ok=True)
        return True
    else:
        print("❌ FAILURE: Code writer was BLOCKED!")
        return False


def test_test_writer_allowed():
    """Test that a test writer (Snare) CAN write tests."""
    print()
    print("=" * 70)
    print("🥁 TEST 4: Test Writer Allowed To Write Tests")
    print("=" * 70)
    print()

    # Load Snare (test writer with can_write_tests=true)
    snare_path = Path("percussion/snare.md")
    snare_def = AgentDefinition.from_file(snare_path)

    print(f"Agent: {snare_def.name}")
    print(f"can_write_code: {snare_def.can_write_code}")
    print(f"can_write_tests: {snare_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(snare_def)

    # Try to write a test file
    write_tool = tools.get_tool("write_file")
    result = write_tool.execute({
        "file_path": "tests/test_allowed_test.py",
        "content": "def test_example(): assert True"
    })

    print("Attempting to write tests/test_allowed_test.py...")
    print(f"Result: {result}")
    print()

    # Check if allowed
    if result["success"]:
        print("✅ SUCCESS: Test writer was allowed to write tests!")
        # Clean up
        Path("tests/test_allowed_test.py").unlink(missing_ok=True)
        return True
    else:
        print("❌ FAILURE: Test writer was BLOCKED!")
        return False


def test_test_writer_blocked_from_code():
    """Test that a test writer (Snare) CANNOT write production code."""
    print()
    print("=" * 70)
    print("🚫 TEST 5: Test Writer Blocked From Writing Production Code")
    print("=" * 70)
    print()

    # Load Snare (test writer with can_write_code=false)
    snare_path = Path("percussion/snare.md")
    snare_def = AgentDefinition.from_file(snare_path)

    print(f"Agent: {snare_def.name}")
    print(f"can_write_code: {snare_def.can_write_code}")
    print(f"can_write_tests: {snare_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(snare_def)

    # Try to write a production code file
    write_tool = tools.get_tool("write_file")
    result = write_tool.execute({
        "file_path": "src/production_code.py",
        "content": "def production_function(): pass"
    })

    print("Attempting to write src/production_code.py...")
    print(f"Result: {result}")
    print()

    # Check if blocked
    if not result["success"] and "ROGUE AGENT DETECTED" in result["error"]:
        print("✅ SUCCESS: Test writer was blocked from writing production code!")
        print(f"Error message: {result['error']}")
        return True
    else:
        print("❌ FAILURE: Test writer was NOT blocked!")
        return False


def main():
    """Run all rogue detection tests."""
    print("\n" + "=" * 70)
    print("🛡️  ROGUE AGENT DETECTION TEST SUITE")
    print("=" * 70)
    print()

    results = []

    # Run all tests
    results.append(("Supervisor blocked from code", test_supervisor_blocked_from_code()))
    results.append(("Supervisor blocked from tests", test_supervisor_blocked_from_tests()))
    results.append(("Code writer allowed code", test_code_writer_allowed()))
    results.append(("Test writer allowed tests", test_test_writer_allowed()))
    results.append(("Test writer blocked from code", test_test_writer_blocked_from_code()))

    # Summary
    print()
    print("=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    print()

    if passed == total:
        print("🎉 ALL TESTS PASSED! Rogue agent detection is working perfectly.")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED! Review the output above.")
        return 1


if __name__ == "__main__":
    exit(main())
