#!/bin/bash
# Quick start script for Ensemble backend

cd "$(dirname "$0")"

# Kill any existing backend on port 8000
echo "🔍 Checking for existing backend..."
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "✅ Killed existing backend" || echo "✅ No existing backend found"

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Start backend
echo "🚀 Starting backend on http://localhost:8000..."
cd src/field/ensemble_ui/backend
python main.py
