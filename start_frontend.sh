#!/bin/bash
# Quick start script for Ensemble frontend with HOT-RELOAD

cd "$(dirname "$0")/src/field/ensemble_ui/frontend"

echo "🚀 Starting frontend with HOT-RELOAD on http://localhost:5173..."
echo "   📁 Watching:"
echo "      - React components (*.jsx)"
echo "      - Styles (*.css)"
echo "      - All frontend source files"
echo ""
echo "   🔄 Browser will auto-refresh when files change!"
echo ""
npm run dev
