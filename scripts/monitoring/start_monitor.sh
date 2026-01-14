#!/usr/bin/env bash
#
# start_monitor.sh - Launch the Ensemble Agent Swarm Monitoring Dashboard
#
# Creates a tmux session with a 2x2 grid layout:
#   - Pane 0 (top-left): Interactive shell for running CLI commands
#   - Pane 1 (top-right): Live log streaming (tail -f)
#   - Pane 2 (bottom-left): Vim file browser (netrw)
#   - Pane 3 (bottom-right): Task watcher displaying project tasks
#

set -e

# Default configuration
SESSION_NAME="${ENSEMBLE_MONITOR_SESSION:-ensemble-monitor}"
OUTPUT_DIR="${ENSEMBLE_OUTPUT_DIR:-.}"
LOG_FILE="${ENSEMBLE_LOG_FILE:-backend.log}"
PROJECT_ID="${ENSEMBLE_PROJECT_ID:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Show usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Launch the Ensemble Agent Swarm Monitoring Dashboard.

Creates a tmux session with a 2x2 grid layout for monitoring agent activity.

Options:
    -n, --name NAME       Session name (default: ensemble-monitor)
    -o, --output-dir DIR  Output directory for vim file browser (default: current dir)
    -l, --log-file FILE   Log file to tail (default: backend.log)
    -p, --project-id ID   Project ID for task tracking
    -h, --help            Show this help message

Environment Variables:
    ENSEMBLE_MONITOR_SESSION   Default session name
    ENSEMBLE_OUTPUT_DIR        Default output directory
    ENSEMBLE_LOG_FILE          Default log file path
    ENSEMBLE_PROJECT_ID        Default project ID

Examples:
    $(basename "$0")
    $(basename "$0") -n my-session -o ./output -l logs/backend.log
    $(basename "$0") --project-id abc123

EOF
    exit 0
}

# Log message with color
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is required but not installed."
        return 1
    fi
    return 0
}

# Validate dependencies
check_dependencies() {
    local missing=0
    
    if ! check_command tmux; then
        echo "  Install with: brew install tmux (macOS) or apt install tmux (Linux)"
        missing=1
    fi
    
    if ! check_command vim; then
        echo "  Install with: brew install vim (macOS) or apt install vim (Linux)"
        missing=1
    fi
    
    if ! check_command python3; then
        echo "  Install with: brew install python3 (macOS) or apt install python3 (Linux)"
        missing=1
    fi
    
    if [[ $missing -eq 1 ]]; then
        exit 1
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                SESSION_NAME="$2"
                shift 2
                ;;
            -o|--output-dir)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -l|--log-file)
                LOG_FILE="$2"
                shift 2
                ;;
            -p|--project-id)
                PROJECT_ID="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                ;;
        esac
    done
}

# Main function to create and setup the tmux session
main() {
    parse_args "$@"
    check_dependencies
    
    # Check if session already exists
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        log_info "Session '$SESSION_NAME' already exists. Attaching..."
        tmux attach-session -t "$SESSION_NAME"
        exit 0
    fi
    
    log_info "Creating new monitoring session: $SESSION_NAME"
    
    # Validate output directory
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        log_warn "Output directory '$OUTPUT_DIR' does not exist. Using current directory."
        OUTPUT_DIR="."
    fi
    
    # Resolve to absolute path
    OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
    
    # Check log file
    if [[ ! -f "$LOG_FILE" ]]; then
        log_warn "Log file '$LOG_FILE' does not exist. Will watch for creation."
    fi
    
    # Build task watcher command
    TASK_WATCHER_CMD="echo 'Task Watcher - Waiting for project...'; sleep 2"
    if [[ -f "$SCRIPT_DIR/task_watcher.py" ]]; then
        if [[ -n "$PROJECT_ID" ]]; then
            TASK_WATCHER_CMD="python3 '$SCRIPT_DIR/task_watcher.py' -p '$PROJECT_ID'"
        else
            TASK_WATCHER_CMD="python3 '$SCRIPT_DIR/task_watcher.py' --all"
        fi
    else
        log_warn "task_watcher.py not found. Using placeholder in Pane 3."
        TASK_WATCHER_CMD="watch -n 2 'echo \"═══ ENSEMBLE TASKS ═══\"; echo \"\"; echo \"No task watcher script found.\"; echo \"Run: python3 task_watcher.py -p <project_id>\"; echo \"\"; date'"
    fi
    
    # Create tmux session with first pane (top-left: CLI shell)
    tmux new-session -d -s "$SESSION_NAME" -x 200 -y 50
    
    # Split horizontally to create top-right pane (logs)
    tmux split-window -h -t "$SESSION_NAME:0.0"
    
    # Select left pane and split vertically to create bottom-left (vim)
    tmux select-pane -t "$SESSION_NAME:0.0"
    tmux split-window -v -t "$SESSION_NAME:0.0"
    
    # Select right pane and split vertically to create bottom-right (tasks)
    tmux select-pane -t "$SESSION_NAME:0.1"
    tmux split-window -v -t "$SESSION_NAME:0.1"
    
    # Now we have:
    # Pane 0: top-left (CLI shell) - already a shell
    # Pane 1: bottom-left (vim)
    # Pane 2: top-right (logs)
    # Pane 3: bottom-right (tasks)
    
    # Configure Pane 1 (bottom-left): Vim file browser
    tmux send-keys -t "$SESSION_NAME:0.1" "cd '$OUTPUT_DIR' && vim -c 'Explore'" Enter
    
    # Configure Pane 2 (top-right): Log streaming
    if [[ -f "$LOG_FILE" ]]; then
        tmux send-keys -t "$SESSION_NAME:0.2" "tail -f '$LOG_FILE'" Enter
    else
        tmux send-keys -t "$SESSION_NAME:0.2" "tail -f '$LOG_FILE' 2>/dev/null || (echo 'Waiting for log file: $LOG_FILE'; while [ ! -f '$LOG_FILE' ]; do sleep 1; done; tail -f '$LOG_FILE')" Enter
    fi
    
    # Configure Pane 3 (bottom-right): Task watcher
    tmux send-keys -t "$SESSION_NAME:0.3" "$TASK_WATCHER_CMD" Enter
    
    # Set pane titles (if supported)
    tmux select-pane -t "$SESSION_NAME:0.0" -T "CLI"
    tmux select-pane -t "$SESSION_NAME:0.1" -T "Files"
    tmux select-pane -t "$SESSION_NAME:0.2" -T "Logs"
    tmux select-pane -t "$SESSION_NAME:0.3" -T "Tasks"
    
    # Select the CLI pane for user interaction
    tmux select-pane -t "$SESSION_NAME:0.0"
    
    log_info "Dashboard created successfully!"
    log_info "Pane layout:"
    echo "  ┌─────────────┬─────────────┐"
    echo "  │ CLI (0)     │ Logs (2)    │"
    echo "  ├─────────────┼─────────────┤"
    echo "  │ Files (1)   │ Tasks (3)   │"
    echo "  └─────────────┴─────────────┘"
    echo ""
    log_info "Navigation: Ctrl+b then arrow keys to switch panes"
    log_info "Zoom pane: Ctrl+b then z"
    echo ""
    
    # Attach to the session
    tmux attach-session -t "$SESSION_NAME"
}

main "$@"
