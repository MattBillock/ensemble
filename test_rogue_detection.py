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

    # Load Development Manager (supervisor with can_write_code=false)
    dev_mgr_path = Path("leadership/development_manager.md")
    dev_mgr_def = AgentDefinition.from_file(dev_mgr_path)

    print(f"Agent: {dev_mgr_def.name}")
    print(f"can_write_code: {dev_mgr_def.can_write_code}")
    print(f"can_write_tests: {dev_mgr_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(dev_mgr_def)

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

    # Load TDD Coordinator (supervisor with can_write_tests=false)
    tdd_coord_path = Path("leadership/tdd_coordinator.md")
    tdd_coord_def = AgentDefinition.from_file(tdd_coord_path)

    print(f"Agent: {tdd_coord_def.name}")
    print(f"can_write_code: {tdd_coord_def.can_write_code}")
    print(f"can_write_tests: {tdd_coord_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(tdd_coord_def)

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
    """Test that a code writer (Frontend Developer) CAN write code."""
    print()
    print("=" * 70)
    print("🎺 TEST 3: Code Writer Allowed To Write Code")
    print("=" * 70)
    print()

    # Load Frontend Developer (code writer with can_write_code=true)
    frontend_dev_path = Path("developers/frontend_developer.md")
    frontend_dev_def = AgentDefinition.from_file(frontend_dev_path)

    print(f"Agent: {frontend_dev_def.name}")
    print(f"can_write_code: {frontend_dev_def.can_write_code}")
    print(f"can_write_tests: {frontend_dev_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(frontend_dev_def)

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
    """Test that a test writer (Unit Test Writer) CAN write tests."""
    print()
    print("=" * 70)
    print("🥁 TEST 4: Test Writer Allowed To Write Tests")
    print("=" * 70)
    print()

    # Load Unit Test Writer (test writer with can_write_tests=true)
    unit_test_writer_path = Path("testers/unit_test_writer.md")
    unit_test_writer_def = AgentDefinition.from_file(unit_test_writer_path)

    print(f"Agent: {unit_test_writer_def.name}")
    print(f"can_write_code: {unit_test_writer_def.can_write_code}")
    print(f"can_write_tests: {unit_test_writer_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(unit_test_writer_def)

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
    """Test that a test writer (Unit Test Writer) CANNOT write production code."""
    print()
    print("=" * 70)
    print("🚫 TEST 5: Test Writer Blocked From Writing Production Code")
    print("=" * 70)
    print()

    # Load Unit Test Writer (test writer with can_write_code=false)
    unit_test_writer_path2 = Path("testers/unit_test_writer.md")
    unit_test_writer_def = AgentDefinition.from_file(unit_test_writer_path2)

    print(f"Agent: {unit_test_writer_def.name}")
    print(f"can_write_code: {unit_test_writer_def.can_write_code}")
    print(f"can_write_tests: {unit_test_writer_def.can_write_tests}")
    print()

    # Create tools with permission checking
    tools = ToolRegistry.default(unit_test_writer_def)

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
