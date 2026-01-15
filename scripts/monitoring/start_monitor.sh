#!/bin/bash
#
# Ensemble Agent Swarm Monitoring Dashboard
# Creates a 2x2 tmux layout for monitoring agent activity
#
# Layout:
#   +------------------+------------------+
#   | Pane 1: CLI      | Pane 2: Logs    |
#   | (shell/commands) | (backend.log)   |
#   +------------------+------------------+
#   | Pane 3: Files    | Pane 4: Status  |
#   | (output dir)     | (agent status)  |
#   +------------------+------------------+
#

set -e

# Configuration (can be overridden by environment variables)
SESSION_NAME="${ENSEMBLE_SESSION:-ensemble-monitor}"
PROJECT_ROOT="${ENSEMBLE_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
OUTPUT_DIR="${ENSEMBLE_OUTPUT:-$PROJECT_ROOT/src/field/ensemble_ui/output}"
LOG_FILE="${ENSEMBLE_LOG:-$PROJECT_ROOT/src/field/ensemble_ui/backend/backend.log}"
BACKEND_DIR="$PROJECT_ROOT/src/field/ensemble_ui/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    local missing=0

    if ! command -v tmux &> /dev/null; then
        echo_error "tmux is not installed. Please install it first."
        missing=1
    fi

    if ! command -v vim &> /dev/null; then
        echo_warn "vim is not installed. File browser pane will use ls instead."
    fi

    return $missing
}

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo_warn "Session '$SESSION_NAME' already exists."
    echo_info "Attaching to existing session..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

# Check dependencies
if ! check_dependencies; then
    exit 1
fi

# Create output and log directories if they don't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

echo_info "Starting Ensemble Monitor Dashboard"
echo_info "Session: $SESSION_NAME"
echo_info "Project Root: $PROJECT_ROOT"
echo_info "Output Dir: $OUTPUT_DIR"
echo_info "Log File: $LOG_FILE"

# Create new tmux session in detached mode
# First pane (0) will be the CLI
tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_ROOT"

# Set default window title
tmux rename-window -t "$SESSION_NAME:0" "monitor"

# Split window horizontally (creates pane 1 on the right)
tmux split-window -h -t "$SESSION_NAME:0" -c "$PROJECT_ROOT"

# Split left pane vertically (creates pane 2 at bottom-left)
tmux split-window -v -t "$SESSION_NAME:0.0" -c "$PROJECT_ROOT"

# Split right pane vertically (creates pane 3 at bottom-right)
tmux split-window -v -t "$SESSION_NAME:0.1" -c "$PROJECT_ROOT"

# Configure Pane 0 (top-left): CLI
# Just a shell prompt ready for commands
tmux send-keys -t "$SESSION_NAME:0.0" "cd '$PROJECT_ROOT' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo '=== Ensemble CLI ===' && echo 'Project: $PROJECT_ROOT' && echo 'Commands: python src/field/ensemble_ui/backend/main.py'" C-m

# Configure Pane 1 (top-right): Log viewer
tmux send-keys -t "$SESSION_NAME:0.1" "tail -f '$LOG_FILE' 2>/dev/null || (echo 'Waiting for log file...' && touch '$LOG_FILE' && tail -f '$LOG_FILE')" C-m

# Configure Pane 2 (bottom-left): File browser
if command -v vim &> /dev/null; then
    tmux send-keys -t "$SESSION_NAME:0.2" "vim -c 'cd $OUTPUT_DIR' -c 'Explore'" C-m
else
    tmux send-keys -t "$SESSION_NAME:0.2" "watch -n 2 'ls -la $OUTPUT_DIR | head -30'" C-m
fi

# Configure Pane 3 (bottom-right): Agent status with task watcher
TASK_WATCHER="$PROJECT_ROOT/scripts/monitoring/task_watcher.py"
if [ -f "$TASK_WATCHER" ]; then
    tmux send-keys -t "$SESSION_NAME:0.3" "python3 '$TASK_WATCHER' --refresh 2" C-m
else
    # Fallback to simple status check if task_watcher.py doesn't exist
    tmux send-keys -t "$SESSION_NAME:0.3" "watch -n 2 'echo \"=== Agent Status ===\"; curl -s http://localhost:8001/api/status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo \"Backend not running\"'" C-m
fi

# Select the CLI pane by default
tmux select-pane -t "$SESSION_NAME:0.0"

# Attach to the session
echo_info "Dashboard ready! Attaching..."
echo_info "Tmux shortcuts: Ctrl-b + arrow keys to navigate panes"
echo_info "To detach: Ctrl-b + d"
echo_info "To stop: scripts/monitoring/stop_monitor.sh"

tmux attach-session -t "$SESSION_NAME"
