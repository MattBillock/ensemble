#!/usr/bin/env python3
"""Add permission fields to all agent definitions."""
from pathlib import Path

# Define permissions for each agent type
PERMISSIONS = {
    # Leadership (all supervisors - no code writing)
    "leadership/executive_director.md": {"can_write_code": "false", "can_write_tests": "false"},
    "leadership/program_coordinator.md": {"can_write_code": "false", "can_write_tests": "false"},
    "leadership/designer.md": {"can_write_code": "false", "can_write_tests": "false"},
    "leadership/drum_major.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Brass Tech (supervisors - no code writing)
    "brass/trumpet_tech.md": {"can_write_code": "false", "can_write_tests": "false"},
    "brass/baritone_tech.md": {"can_write_code": "false", "can_write_tests": "false"},
    "brass/tuba_tech.md": {"can_write_code": "false", "can_write_tests": "false"},
    "brass/horn_tech.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Brass Writers (code writers only)
    "brass/trumpet.md": {"can_write_code": "true", "can_write_tests": "false"},
    "brass/baritone.md": {"can_write_code": "true", "can_write_tests": "false"},
    "brass/tuba.md": {"can_write_code": "true", "can_write_tests": "false"},
    "brass/horn.md": {"can_write_code": "true", "can_write_tests": "false"},

    # Percussion Tech (supervisors - no writing)
    "percussion/snare_tech.md": {"can_write_code": "false", "can_write_tests": "false"},
    "percussion/cymbal_tech.md": {"can_write_code": "false", "can_write_tests": "false"},
    "percussion/tenor_tech.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Percussion Writers (test writers only)
    "percussion/snare.md": {"can_write_code": "false", "can_write_tests": "true"},
    "percussion/bass.md": {"can_write_code": "false", "can_write_tests": "true"},
    "percussion/tenor.md": {"can_write_code": "false", "can_write_tests": "true"},

    # Guard Tech (supervisor)
    "guard/flag_tech.md": {"can_write_code": "false", "can_write_tests": "false"},

    # Guard Writer (styling - counts as code)
    "guard/flag.md": {"can_write_code": "true", "can_write_tests": "false"},
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
