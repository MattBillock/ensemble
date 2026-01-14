#!/bin/bash
# Ensemble Dashboard - tmux-based development environment
# Creates a 2x2 pane layout:
#   ┌─────────────────┬─────────────────┐
#   │    Backend      │    Frontend     │
#   │   (port 8001)   │   (port 5173)   │
#   ├─────────────────┼─────────────────┤
#   │      Logs       │      Shell      │
#   │                 │                 │
#   └─────────────────┴─────────────────┘

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

# Create new session (this creates the first pane - top left)
tmux new-session -d -s "$SESSION_NAME" -c "$ENSEMBLE_DIR"

# Split horizontally to create top-right pane
tmux split-window -h -t "$SESSION_NAME" -c "$ENSEMBLE_DIR/src/field/ensemble_ui/frontend"

# Split the left pane vertically to create bottom-left
tmux split-window -v -t "$SESSION_NAME:0.0" -c "$ENSEMBLE_DIR"

# Split the right pane vertically to create bottom-right
tmux split-window -v -t "$SESSION_NAME:0.1" -c "$ENSEMBLE_DIR"

# Now we have 4 panes:
# 0.0 = top-left (backend)
# 0.1 = top-right (frontend)
# 0.2 = bottom-left (logs)
# 0.3 = bottom-right (shell)

# Start backend in top-left (pane 0)
tmux send-keys -t "$SESSION_NAME:0.0" "source venv/bin/activate && python -m uvicorn src.field.ensemble_ui.backend.main:app --host 0.0.0.0 --port 8001 --reload" Enter

# Start frontend in top-right (pane 1)
tmux send-keys -t "$SESSION_NAME:0.1" "npm run dev" Enter

# Start log tail in bottom-left (pane 2)
tmux send-keys -t "$SESSION_NAME:0.2" "mkdir -p logs && sleep 3 && tail -f logs/*.log 2>/dev/null || echo 'No log files yet. Services log to stdout in their panes.'" Enter

# Setup shell in bottom-right (pane 3)
tmux send-keys -t "$SESSION_NAME:0.3" "source venv/bin/activate && clear" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo '🎺 ENSEMBLE DASHBOARD'" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo ''" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo 'Panes: Ctrl-b + arrow keys to navigate'" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo 'Detach: Ctrl-b + d'" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo 'Reattach: ens-dash-attach'" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo ''" Enter

# Select the shell pane (bottom-right) as active
tmux select-pane -t "$SESSION_NAME:0.3"

# Attach to the session
tmux attach-session -t "$SESSION_NAME"
