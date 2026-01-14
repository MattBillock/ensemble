#!/bin/bash
# Ensemble Dashboard - tmux-based development environment
# Usage: ens-dashboard

SESSION_NAME="ensemble-dash"
ENSEMBLE_DIR="/Users/mattbillock/Development/ai_exploration/ensemble"

# Check if session already exists
tmux has-session -t "$SESSION_NAME" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Session '$SESSION_NAME' already exists. Attaching..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

# Kill any existing processes on ports first
echo "Cleaning up existing processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
pkill -f "uvicorn.*ensemble" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null
sleep 1

# Create new session with first window for backend
tmux new-session -d -s "$SESSION_NAME" -c "$ENSEMBLE_DIR" -n "backend"

# Setup backend pane (first pane)
tmux send-keys -t "$SESSION_NAME:backend" "source venv/bin/activate && python -m uvicorn src.field.ensemble_ui.backend.main:app --host 0.0.0.0 --port 8001 --reload" Enter

# Create second window for frontend
tmux new-window -t "$SESSION_NAME" -n "frontend" -c "$ENSEMBLE_DIR/src/field/ensemble_ui/frontend"
tmux send-keys -t "$SESSION_NAME:frontend" "npm run dev" Enter

# Create third window for logs
tmux new-window -t "$SESSION_NAME" -n "logs" -c "$ENSEMBLE_DIR"
tmux send-keys -t "$SESSION_NAME:logs" "mkdir -p logs && tail -f logs/*.log 2>/dev/null || echo 'Waiting for log files...'" Enter

# Create fourth window for shell
tmux new-window -t "$SESSION_NAME" -n "shell" -c "$ENSEMBLE_DIR"
tmux send-keys -t "$SESSION_NAME:shell" "source venv/bin/activate && clear" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo ''" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo '🎺 ENSEMBLE DASHBOARD'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo ''" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo 'Windows:'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo '  [1] backend  - Backend server (port 8001)'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo '  [2] frontend - Frontend server (port 5173)'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo '  [3] logs     - Log viewer'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo '  [4] shell    - Command shell (this window)'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo ''" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo 'Navigation: Ctrl-b + [1-4] to switch windows'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo 'Detach: Ctrl-b + d'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo 'Reattach: tmux attach -t ensemble-dash'" Enter
tmux send-keys -t "$SESSION_NAME:shell" "echo ''" Enter

# Go to shell window by default
tmux select-window -t "$SESSION_NAME:shell"

# Attach to the session
tmux attach-session -t "$SESSION_NAME"
