#!/usr/bin/env bash
#
# stop_monitor.sh - Stop the Ensemble Agent Swarm Monitoring Dashboard
#
# Cleanly terminates the tmux monitoring session.
#

set -e

# Default configuration
SESSION_NAME="${ENSEMBLE_MONITOR_SESSION:-ensemble-monitor}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Show usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Stop the Ensemble Agent Swarm Monitoring Dashboard.

Cleanly terminates the tmux monitoring session.

Options:
    -n, --name NAME    Session name to kill (default: ensemble-monitor)
    -h, --help         Show this help message

Environment Variables:
    ENSEMBLE_MONITOR_SESSION   Default session name

Examples:
    $(basename "$0")
    $(basename "$0") -n my-session

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

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                SESSION_NAME="$2"
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

# Main function
main() {
    parse_args "$@"
    
    # Check if tmux is available
    if ! command -v tmux &> /dev/null; then
        log_error "tmux is not installed."
        exit 1
    fi
    
    # Check if session exists
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        log_info "Stopping monitoring session: $SESSION_NAME"
        tmux kill-session -t "$SESSION_NAME"
        log_info "Session '$SESSION_NAME' stopped successfully."
    else
        log_warn "Session '$SESSION_NAME' does not exist or is not running."
        exit 0
    fi
}

main "$@"
