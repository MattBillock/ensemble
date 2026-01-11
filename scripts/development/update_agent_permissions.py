#!/usr/bin/env python3
"""Add permission fields to all agent definitions."""
from pathlib import Path

# Define permissions for each agent type
PERMISSIONS = {
    # Leadership (all supervisors - no code writing)
    "leadership/executive_director.md": {"can_write_code": "false", "can_write_tests": "false"},
    "leadership/development_manager.md": {"can_write_code": "false", "can_write_tests": "false"},
    "leadership/system_architect.md": {"can_write_code": "false", "can_write_tests": "false"},
    "leadership/tdd_coordinator.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Coordinators (task breakdown - no code writing)
    "coordinators/backend_coordinator.md": {"can_write_code": "false", "can_write_tests": "false"},
    "coordinators/frontend_coordinator.md": {"can_write_code": "false", "can_write_tests": "false"},
    "coordinators/test_coordinator.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Developer Leads (supervisors - no code writing)
    "developers/frontend_lead.md": {"can_write_code": "false", "can_write_tests": "false"},
    "developers/backend_lead.md": {"can_write_code": "false", "can_write_tests": "false"},
    "developers/api_lead.md": {"can_write_code": "false", "can_write_tests": "false"},
    "developers/component_lead.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Developers (code writers only)
    "developers/frontend_developer.md": {"can_write_code": "true", "can_write_tests": "false"},
    "developers/backend_developer.md": {"can_write_code": "true", "can_write_tests": "false"},
    "developers/api_developer.md": {"can_write_code": "true", "can_write_tests": "false"},
    "developers/component_developer.md": {"can_write_code": "true", "can_write_tests": "false"},

    # Test Leads (supervisors - no writing)
    "testers/unit_test_lead.md": {"can_write_code": "false", "can_write_tests": "false"},
    "testers/test_validator.md": {"can_write_code": "false", "can_write_tests": "false"},
    "testers/integration_test_lead.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Test Writers (test writers only)
    "testers/unit_test_writer.md": {"can_write_code": "false", "can_write_tests": "true"},
    "testers/test_fixture_writer.md": {"can_write_code": "false", "can_write_tests": "true"},
    "testers/integration_test_writer.md": {"can_write_code": "false", "can_write_tests": "true"},

    # Style Lead (supervisor)
    "designers/style_lead.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Style Developer (styling - counts as code)
    "designers/style_developer.md": {"can_write_code": "true", "can_write_tests": "false"},
}

def add_permissions_to_agent(file_path: Path, permissions: dict):
    """Add Can Write Code and Can Write Tests fields to agent file."""
    content = file_path.read_text()

    # Check if permissions already exist
    if "## Can Write Code" in content:
        print(f"  ⏭️  Already has permissions: {file_path}")
        return False

    # Find where to insert (after "## Max Iterations" or before EOF)
    lines = content.split('\n')
    insert_index = None

    for i, line in enumerate(lines):
        if line.startswith("## Max Iterations"):
            # Find the end of this section (next blank line or section)
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "" or lines[j].startswith("#"):
                    insert_index = j
                    break
            break

    if insert_index is None:
        # No Max Iterations section, add at end
        insert_index = len(lines)

    # Create permission lines
    permission_lines = [
        "",
        "## Can Write Code",
        permissions["can_write_code"],
        "",
        "## Can Write Tests",
        permissions["can_write_tests"],
    ]

    # Insert permissions
    lines[insert_index:insert_index] = permission_lines

    # Write back
    file_path.write_text('\n'.join(lines))
    print(f"  ✅ Added permissions: {file_path}")
    return True

def main():
    """Update all agent files with permissions."""
    print("=" * 70)
    print("🔒 UPDATING AGENT PERMISSIONS")
    print("=" * 70)
    print()

    updated_count = 0
    skipped_count = 0

    for agent_path, perms in PERMISSIONS.items():
        file_path = Path(agent_path)
        if not file_path.exists():
            print(f"  ⚠️  Not found: {file_path}")
            continue

        if add_permissions_to_agent(file_path, perms):
            updated_count += 1
        else:
            skipped_count += 1

    print()
    print("=" * 70)
    print(f"✅ Updated: {updated_count} agents")
    print(f"⏭️  Skipped: {skipped_count} agents (already had permissions)")
    print("=" * 70)

if __name__ == "__main__":
    main()
