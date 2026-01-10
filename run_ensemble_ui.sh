#!/bin/bash
# Run the complete Ensemble UI stack (backend + frontend)

echo "========================================"
echo "🎺 ENSEMBLE UI - MILESTONE 2 DEMO"
echo "========================================"
echo ""
echo "Starting services..."
echo ""

# Kill any existing processes on the ports
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Activate virtual environment
source venv/bin/activate

# Start backend in background
echo "🚀 Starting FastAPI backend on http://localhost:8000..."
cd src/field/ensemble_ui/backend
python main.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ../../..

sleep 2

# Check if backend started
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "❌ Backend failed to start. Check backend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend running (PID: $BACKEND_PID)"

# Start frontend
echo "🎨 Starting React frontend on http://localhost:5173..."
cd src/field/ensemble_ui/frontend
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../../..

echo ""
echo "========================================"
echo "✨ ENSEMBLE UI IS RUNNING"
echo "========================================"
echo ""
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "========================================"
echo ""

# Trap Ctrl+C to cleanup
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Services stopped.'; exit" INT

# Wait for processes
wait
