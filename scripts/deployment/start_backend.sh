#!/bin/bash
# Quick start script for Ensemble backend with HOT-RELOAD

cd "$(dirname "$0")"

# Kill any existing backend on port 8001 (NOT 8000 - that's for Firestorm!)
echo "🔍 Checking for existing backend..."
lsof -ti:8001 | xargs kill -9 2>/dev/null && echo "✅ Killed existing backend" || echo "✅ No existing backend found"

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Start backend with auto-reload
echo "🚀 Starting backend with HOT-RELOAD on http://localhost:8001..."
echo "   (Port 8000 reserved for Firestorm)"
echo "   📁 Watching:"
echo "      - Backend Python files (*.py)"
echo "      - Agent definitions (*.md)"
echo "      - Runtime code changes"
echo ""
echo "   🔄 Server will auto-restart when files change!"
echo ""
cd src/field/ensemble_ui/backend
python main.py
