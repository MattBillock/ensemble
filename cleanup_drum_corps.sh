#!/bin/bash
# Systematic drum corps terminology cleanup

echo "🎯 Cleaning drum corps terminology from agent files..."

# Define replacements
declare -A REPLACEMENTS=(
  ["Percussion Coordinator"]="Test Coordinator"
  ["Percussion"]="Testing"
  ["Snare"]="Unit Test Writer"
  ["Brass Coordinator"]="Developer Coordinator"
  ["Brass"]="Developers"
  ["Guard"]="Designers"
  ["Trumpet"]="Frontend Developer"
  ["Tuba"]="Backend Developer"
  ["Corps"]="Team"
  ["drum corps"]="development team"
  ["Drum Corps"]="Development Team"
)

# Agent directories to process
DIRS="leadership coordinators developers testers designers"

count=0
for dir in $DIRS; do
  if [ -d "$dir" ]; then
    for file in "$dir"/*.md; do
      if [ -f "$file" ]; then
        # Check if file has any drum corps terms
        if grep -qi "percussion\|brass\|guard\|snare\|trumpet\|tuba\|corps" "$file"; then
          echo "  Processing: $file"

          # Apply all replacements
          for key in "${!REPLACEMENTS[@]}"; do
            value="${REPLACEMENTS[$key]}"
            # Use perl for in-place editing (works on macOS)
            perl -pi -e "s/\Q$key\E/$value/g" "$file"
          done

          ((count++))
        fi
      fi
    done
  fi
done

echo "✅ Processed $count files"

# Count remaining references
remaining=$(grep -ri "drum\|corps\|brass\|percussion\|guard\|snare\|trumpet\|tuba" $DIRS 2>/dev/null | wc -l)
echo "📊 Remaining references: $remaining"
