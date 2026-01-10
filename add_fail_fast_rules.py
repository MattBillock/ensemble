#!/usr/bin/env python3
"""Add Fail Fast rules to all Tech (supervisor) agents."""
from pathlib import Path

# Tech agents that supervise writers
TECH_AGENTS = {
    "brass/trumpet_tech.md": "brass/trumpet",
    "brass/baritone_tech.md": "brass/baritone",
    "brass/tuba_tech.md": "brass/tuba",  # Already done
    "brass/horn_tech.md": "brass/horn",
    "percussion/snare_tech.md": "percussion/snare",
    "percussion/cymbal_tech.md": None,  # Validator, doesn't spawn writers
    "percussion/tenor_tech.md": "percussion/tenor",
    "guard/flag_tech.md": "guard/flag",
}

def add_fail_fast_rules(file_path: Path, spawns_path: str):
    """Add Fail Fast rules to a Tech agent."""
    content = file_path.read_text()

    # Check if rules already exist
    if "CRITICAL RULES:" in content:
        print(f"  ⏭️  Already has rules: {file_path}")
        return False

    # Find where to insert (right after "## Instructions" line)
    lines = content.split('\n')
    insert_index = None

    for i, line in enumerate(lines):
        if line == "## Instructions":
            # Find the next non-empty line after Instructions
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].startswith('#'):
                    insert_index = j + 1  # Insert after the intro line
                    break
            break

    if insert_index is None:
        print(f"  ⚠️  Could not find insertion point: {file_path}")
        return False

    # Create rules
    if spawns_path:
        rules = [
            "",
            "**CRITICAL RULES:**",
            "1. **NEVER write code yourself** - you lack can_write_code permission",
            "2. **NEVER write tests yourself** - you lack can_write_tests permission",
            f"3. **If spawn_agent fails, STOP and return error** - DO NOT write code as fallback",
            f'4. **ALWAYS spawn {spawns_path}** - use EXACT path "{spawns_path}"',
        ]
    else:
        # Cymbal Tech doesn't spawn writers, just validates
        rules = [
            "",
            "**CRITICAL RULES:**",
            "1. **NEVER write code yourself** - you lack can_write_code permission",
            "2. **NEVER write tests yourself** - you lack can_write_tests permission",
            "3. **Only validate tests, never modify them** - read-only analysis",
        ]

    # Insert rules
    lines[insert_index:insert_index] = rules

    # Write back
    file_path.write_text('\n'.join(lines))
    print(f"  ✅ Added rules: {file_path}")
    return True

def main():
    """Update all Tech agents with Fail Fast rules."""
    print("=" * 70)
    print("🛑 ADDING FAIL FAST RULES TO TECH AGENTS")
    print("=" * 70)
    print()

    updated_count = 0
    skipped_count = 0

    for agent_path, spawns in TECH_AGENTS.items():
        file_path = Path(agent_path)
        if not file_path.exists():
            print(f"  ⚠️  Not found: {file_path}")
            continue

        if add_fail_fast_rules(file_path, spawns):
            updated_count += 1
        else:
            skipped_count += 1

    print()
    print("=" * 70)
    print(f"✅ Updated: {updated_count} agents")
    print(f"⏭️  Skipped: {skipped_count} agents (already had rules)")
    print("=" * 70)

if __name__ == "__main__":
    main()
