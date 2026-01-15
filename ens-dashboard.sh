#!/bin/bash
# Ensemble Dashboard - tmux-based development environment
# Creates a 2x2 pane layout:
#   ┌─────────────────┬─────────────────┐
#   │    Backend      │    Frontend     │
#   │   (port 8001)   │   (port 5173)   │
#   ├─────────────────┼─────────────────┤
#   │      Logs       │     Claude      │
#   │                 │  (ensemble root)│
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

# Source aliases and start backend in top-left (pane 0)
tmux send-keys -t "$SESSION_NAME:0.0" "source $ENSEMBLE_DIR/.ensemble_aliases && ens-backend" Enter

# Source aliases and start frontend in top-right (pane 1)
tmux send-keys -t "$SESSION_NAME:0.1" "source $ENSEMBLE_DIR/.ensemble_aliases && ens-frontend" Enter

# Start log tail in bottom-left (pane 2)
tmux send-keys -t "$SESSION_NAME:0.2" "source $ENSEMBLE_DIR/.ensemble_aliases && ens-logs" Enter

# Setup claude pane in bottom-right (pane 3) - in ensemble root
tmux send-keys -t "$SESSION_NAME:0.3" "cd $ENSEMBLE_DIR && source .ensemble_aliases && clear" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo '🤖 CLAUDE PANE - Ensemble Root'" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo 'Ready for: claude'" Enter
tmux send-keys -t "$SESSION_NAME:0.3" "echo ''" Enter

# Select the shell pane (bottom-right) as active
tmux select-pane -t "$SESSION_NAME:0.3"

# Attach to the session
tmux attach-session -t "$SESSION_NAME"
