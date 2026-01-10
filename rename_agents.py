#!/usr/bin/env python3
"""Migrate from drum corps naming to standard developer naming."""
import shutil
from pathlib import Path
import re

# Complete mapping of old → new paths
DIRECTORY_RENAMES = {
    "caption_heads": "coordinators",
    "brass": "developers",
    "percussion": "testers",
    "guard": "designers",
}

FILE_RENAMES = {
    # Leadership (most stay same, some rename)
    "leadership/program_coordinator.md": "leadership/development_manager.md",
    "leadership/designer.md": "leadership/system_architect.md",
    "leadership/drum_major.md": "leadership/tdd_coordinator.md",

    # Caption Heads → Coordinators
    "caption_heads/backend_captain.md": "coordinators/backend_coordinator.md",
    "caption_heads/frontend_captain.md": "coordinators/frontend_coordinator.md",
    "caption_heads/test_captain.md": "coordinators/test_coordinator.md",

    # Brass → Developers
    "brass/trumpet_tech.md": "developers/frontend_lead.md",
    "brass/trumpet.md": "developers/frontend_developer.md",
    "brass/baritone_tech.md": "developers/backend_lead.md",
    "brass/baritone.md": "developers/backend_developer.md",
    "brass/tuba_tech.md": "developers/api_lead.md",
    "brass/tuba.md": "developers/api_developer.md",
    "brass/horn_tech.md": "developers/component_lead.md",
    "brass/horn.md": "developers/component_developer.md",

    # Percussion → Testers
    "percussion/snare_tech.md": "testers/unit_test_lead.md",
    "percussion/snare.md": "testers/unit_test_writer.md",
    "percussion/cymbal_tech.md": "testers/test_validator.md",
    "percussion/bass.md": "testers/test_fixture_writer.md",
    "percussion/tenor_tech.md": "testers/integration_test_lead.md",
    "percussion/tenor.md": "testers/integration_test_writer.md",

    # Guard → Designers
    "guard/flag_tech.md": "designers/style_lead.md",
    "guard/flag.md": "designers/style_developer.md",
}

# Path replacements for agent instructions
PATH_REPLACEMENTS = {
    # Leadership spawns
    "leadership/program_coordinator": "leadership/development_manager",
    "leadership/designer": "leadership/system_architect",
    "leadership/drum_major": "leadership/tdd_coordinator",

    # Caption heads spawns
    "caption_heads/backend_captain": "coordinators/backend_coordinator",
    "caption_heads/frontend_captain": "coordinators/frontend_coordinator",
    "caption_heads/test_captain": "coordinators/test_coordinator",

    # Brass spawns → Developers
    "brass/trumpet_tech": "developers/frontend_lead",
    "brass/trumpet": "developers/frontend_developer",
    "brass/baritone_tech": "developers/backend_lead",
    "brass/baritone": "developers/backend_developer",
    "brass/tuba_tech": "developers/api_lead",
    "brass/tuba": "developers/api_developer",
    "brass/horn_tech": "developers/component_lead",
    "brass/horn": "developers/component_developer",

    # Percussion spawns → Testers
    "percussion/snare_tech": "testers/unit_test_lead",
    "percussion/snare": "testers/unit_test_writer",
    "percussion/cymbal_tech": "testers/test_validator",
    "percussion/bass": "testers/test_fixture_writer",
    "percussion/tenor_tech": "testers/integration_test_lead",
    "percussion/tenor": "testers/integration_test_writer",

    # Guard spawns → Designers
    "guard/flag_tech": "designers/style_lead",
    "guard/flag": "designers/style_developer",
}


def rename_directories():
    """Rename drum corps directories to standard names."""
    print("=" * 70)
    print("📁 STEP 1: Renaming Directories")
    print("=" * 70)
    print()

    for old_dir, new_dir in DIRECTORY_RENAMES.items():
        old_path = Path(old_dir)
        new_path = Path(new_dir)

        if old_path.exists():
            print(f"  {old_dir}/ → {new_dir}/")
            shutil.move(str(old_path), str(new_path))
        else:
            print(f"  ⚠️  {old_dir}/ not found (may already be renamed)")

    print()


def rename_files():
    """Rename individual agent files."""
    print("=" * 70)
    print("📄 STEP 2: Renaming Files")
    print("=" * 70)
    print()

    for old_file, new_file in FILE_RENAMES.items():
        old_path = Path(old_file)
        new_path = Path(new_file)

        if old_path.exists():
            print(f"  {old_file} → {new_file}")
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_path), str(new_path))
        else:
            print(f"  ⚠️  {old_file} not found")

    print()


def update_file_content(file_path: Path, replacements: dict):
    """Update spawn_agent paths in a file."""
    content = file_path.read_text()
    updated = content
    changes_made = []

    for old_path, new_path in replacements.items():
        # Match spawn_agent("old_path", ...) patterns
        pattern = f'spawn_agent\\("{re.escape(old_path)}"'
        replacement = f'spawn_agent("{new_path}"'

        if pattern in updated:
            updated = updated.replace(f'"{old_path}"', f'"{new_path}"')
            changes_made.append(f'"{old_path}" → "{new_path}"')

    if changes_made:
        file_path.write_text(updated)
        return changes_made

    return None


def update_agent_instructions():
    """Update spawn paths in all agent .md files."""
    print("=" * 70)
    print("✏️  STEP 3: Updating Agent Instructions")
    print("=" * 70)
    print()

    # Find all .md files in agent directories
    agent_files = []
    for directory in ["leadership", "coordinators", "developers", "testers", "designers"]:
        dir_path = Path(directory)
        if dir_path.exists():
            agent_files.extend(dir_path.glob("*.md"))

    updated_count = 0
    for file_path in agent_files:
        changes = update_file_content(file_path, PATH_REPLACEMENTS)
        if changes:
            print(f"  ✅ {file_path}")
            for change in changes:
                print(f"     {change}")
            updated_count += 1
        else:
            print(f"  ⏭️  {file_path} (no spawn paths)")

    print()
    print(f"Updated {updated_count} agent files")
    print()


def update_python_scripts():
    """Update paths in Python scripts."""
    print("=" * 70)
    print("🐍 STEP 4: Updating Python Scripts")
    print("=" * 70)
    print()

    python_files = [
        "build_milestone2.py",
        "complete_milestone2_frontend.py",
        "test_rogue_detection.py",
        "update_agent_permissions.py",
        "add_fail_fast_rules.py",
    ]

    for script in python_files:
        script_path = Path(script)
        if script_path.exists():
            changes = update_file_content(script_path, PATH_REPLACEMENTS)
            if changes:
                print(f"  ✅ {script}")
                for change in changes:
                    print(f"     {change}")
            else:
                print(f"  ⏭️  {script} (no agent paths)")
        else:
            print(f"  ⚠️  {script} not found")

    print()


def cleanup_old_state_files():
    """Remove old state files with old agent paths."""
    print("=" * 70)
    print("🗑️  STEP 5: Cleaning Up Old State Files")
    print("=" * 70)
    print()

    state_files = [
        "src/field/ensemble_ui/milestone2_exec_state.json",
    ]

    for state_file in state_files:
        state_path = Path(state_file)
        if state_path.exists():
            print(f"  🗑️  Deleting {state_file} (contains old paths)")
            state_path.unlink()
        else:
            print(f"  ⏭️  {state_file} (not found)")

    print()


def verify_no_old_references():
    """Check for any remaining old path references."""
    print("=" * 70)
    print("🔍 STEP 6: Verifying No Old References")
    print("=" * 70)
    print()

    # Old names that should NOT appear
    old_names = [
        "brass/trumpet",
        "brass/tuba",
        "brass/baritone",
        "brass/horn",
        "percussion/snare",
        "percussion/tenor",
        "percussion/bass",
        "percussion/cymbal",
        "guard/flag",
        "caption_heads/",
        "drum_major",
    ]

    issues_found = []

    # Check all .md and .py files
    for file_path in Path(".").rglob("*.md"):
        if ".git" in str(file_path) or "node_modules" in str(file_path):
            continue

        content = file_path.read_text()
        for old_name in old_names:
            if old_name in content:
                issues_found.append(f"{file_path}: contains '{old_name}'")

    for file_path in Path(".").rglob("*.py"):
        if ".git" in str(file_path) or "venv" in str(file_path):
            continue

        content = file_path.read_text()
        for old_name in old_names:
            if old_name in content:
                issues_found.append(f"{file_path}: contains '{old_name}'")

    if issues_found:
        print("  ⚠️  Found old references:")
        for issue in issues_found[:10]:  # Show first 10
            print(f"     {issue}")
        if len(issues_found) > 10:
            print(f"     ... and {len(issues_found) - 10} more")
    else:
        print("  ✅ No old references found!")

    print()


def main():
    """Execute the complete renaming migration."""
    print()
    print("=" * 70)
    print("🎭 → 💼 AGENT NAMING MIGRATION")
    print("Drum Corps Metaphor → Standard Developer Names")
    print("=" * 70)
    print()

    input("Press Enter to begin migration (Ctrl+C to cancel)...")
    print()

    rename_directories()
    rename_files()
    update_agent_instructions()
    update_python_scripts()
    cleanup_old_state_files()
    verify_no_old_references()

    print("=" * 70)
    print("✅ MIGRATION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Update AGENT_REGISTRY.md")
    print("2. Run: python test_rogue_detection.py")
    print("3. Test agent spawning with new paths")
    print("4. Commit all changes")
    print()


if __name__ == "__main__":
    main()
