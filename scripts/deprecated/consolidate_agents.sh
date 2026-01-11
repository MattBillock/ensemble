#!/bin/bash
# Agent consolidation: 23 → 14 agents

echo "🔄 Consolidating agents (23 → 14)..."

# Frontend Tier: 4 → 2 agents
echo "  Frontend consolidation..."
# Keep frontend_lead.md and frontend_developer.md
# Delete component_lead.md and component_developer.md
rm -f developers/component_lead.md
rm -f developers/component_developer.md

# Backend Tier: 4 → 2 agents
echo "  Backend consolidation..."
# Keep backend_lead.md and backend_developer.md
# Delete api_lead.md and api_developer.md
rm -f developers/api_lead.md
rm -f developers/api_developer.md

# Test Tier: 5 → 4 agents
echo "  Test consolidation..."
# Delete test_validator.md (merge functionality into leads)
rm -f testers/test_validator.md

# Style Tier: 2 → 1 agent
echo "  Style consolidation..."
# Delete style_lead.md (keep style_developer.md as single agent)
rm -f designers/style_lead.md

# Count remaining agents
count=$(find leadership coordinators developers testers designers -name "*.md" | wc -l)
echo "✅ Consolidation complete. Agent count: $count"
