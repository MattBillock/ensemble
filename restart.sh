#!/bin/bash
# Restart script for ensemble backend and frontend

cd /Users/mattbillock/Development/ai_exploration/ensemble

echo "🛑 Stopping existing processes..."
pkill -f "uvicorn.*ensemble"
pkill -f "vite"
sleep 2

echo "🧹 Creating logs directory..."
mkdir -p logs

echo "🔄 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Starting backend on port 8001..."
python -m uvicorn src.field.ensemble_ui.backend.main:app --host 0.0.0.0 --port 8001 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!

sleep 2

echo "🎨 Starting frontend on port 5173..."
cd src/field/ensemble_ui/frontend
npm run dev > ../../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

cd /Users/mattbillock/Development/ai_exploration/ensemble

echo ""
echo "✅ Services started!"
echo "   Backend PID:  $BACKEND_PID (http://localhost:8001)"
echo "   Frontend PID: $FRONTEND_PID (http://localhost:5173)"
echo ""
echo "📋 Tail logs with:"
echo "   tail -f logs/backend.log logs/frontend.log"
echo ""
echo "🛑 Stop services with:"
echo "   pkill -f 'uvicorn.*ensemble' && pkill -f vite"
