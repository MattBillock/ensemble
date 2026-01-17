#!/bin/bash

# Core Tmux Session Management Script
# Creates and manages the ensemble-monitor tmux session with 2x2 grid layout
# Compatible with macOS and Linux, tmux 3.0+

set -euo pipefail

# Configuration
SESSION_NAME="ensemble-monitor"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/tmux_session.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

info() { log "INFO" "$@"; }
warn() { log "WARN" "$@"; }
error() { log "ERROR" "$@"; }

# Check if tmux is installed and version is compatible
check_tmux_version() {
    if ! command -v tmux >/dev/null 2>&1; then
        error "tmux is not installed. Please install tmux first."
        exit 1
    fi
    
    local version
    version=$(tmux -V | grep -o '[0-9]\+\.[0-9]\+')
    local major minor
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)
    
    if [[ $major -lt 3 ]]; then
        error "tmux version $version is not supported. Minimum required: 3.0"
        exit 1
    fi
    
    info "tmux version $version detected - compatible"
}

# Check if session exists
session_exists() {
    tmux has-session -t "$SESSION_NAME" 2>/dev/null
}

# Kill existing session
kill_existing_session() {
    if session_exists; then
        warn "Session '$SESSION_NAME' already exists. Killing existing session..."
        tmux kill-session -t "$SESSION_NAME"
        sleep 1
        info "Existing session killed"
    fi
}

# Create new session with 2x2 grid layout
create_session() {
    info "Creating new tmux session: $SESSION_NAME"
    
    # Create new session with first window
    tmux new-session -d -s "$SESSION_NAME" -x 120 -y 30
    
    # Split window into 2x2 grid
    # First split vertically (creates left and right halves)
    tmux split-window -h
    
    # Split left pane horizontally (creates top-left and bottom-left)
    tmux select-pane -t 0
    tmux split-window -v
    
    # Split right pane horizontally (creates top-right and bottom-right)
    tmux select-pane -t 2
    tmux split-window -v
    
    # Set pane titles
    tmux select-pane -t 0 -T "Top-Left"
    tmux select-pane -t 1 -T "Bottom-Left"
    tmux select-pane -t 2 -T "Top-Right"
    tmux select-pane -t 3 -T "Bottom-Right"
    
    # Start in the top-left pane
    tmux select-pane -t 0
    
    # Set status line to show pane titles
    tmux set-option -g pane-border-status top
    tmux set-option -g pane-border-format "#{pane_title}"
    
    info "Session created successfully with 2x2 grid layout"
}

# Attach to session
attach_session() {
    info "Attaching to session: $SESSION_NAME"
    
    # Check if we're already inside a tmux session
    if [[ -n "${TMUX:-}" ]]; then
        # If inside tmux, switch to the session
        tmux switch-client -t "$SESSION_NAME"
    else
        # If not inside tmux, attach normally
        tmux attach-session -t "$SESSION_NAME"
    fi
}

# Display session info
show_session_info() {
    if session_exists; then
        echo -e "${GREEN}Session Information:${NC}"
        tmux list-sessions | grep "$SESSION_NAME" || true
        echo -e "${BLUE}Panes:${NC}"
        tmux list-panes -t "$SESSION_NAME" -F "#{pane_index}: #{pane_title} (#{pane_width}x#{pane_height})" | while read -r line; do
            echo "  $line"
        done
    else
        error "Session '$SESSION_NAME' does not exist"
        exit 1
    fi
}

# Print help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Core Tmux Session Management for ensemble-monitor

OPTIONS:
    -h, --help      Show this help message
    -k, --kill      Kill existing session before creating new one
    -i, --info      Show session information and exit
    -n, --new       Force create new session (implies --kill)
    -a, --attach    Only attach to existing session (don't create)

EXAMPLES:
    $0              Create session if not exists, then attach
    $0 --kill       Kill existing session and create new one
    $0 --info       Show current session information
    $0 --attach     Attach to existing session only

EOF
}

# Main function
main() {
    local kill_existing=false
    local show_info=false
    local force_new=false
    local attach_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -k|--kill)
                kill_existing=true
                shift
                ;;
            -i|--info)
                show_info=true
                shift
                ;;
            -n|--new)
                force_new=true
                kill_existing=true
                shift
                ;;
            -a|--attach)
                attach_only=true
                shift
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Initialize log file
    mkdir -p "$(dirname "$LOG_FILE")"
    info "Starting tmux session management for $SESSION_NAME"
    
    # Check tmux version compatibility
    check_tmux_version
    
    # Show session info and exit if requested
    if [[ "$show_info" == true ]]; then
        show_session_info
        exit 0
    fi
    
    # Handle attach only mode
    if [[ "$attach_only" == true ]]; then
        if session_exists; then
            attach_session
        else
            error "Session '$SESSION_NAME' does not exist. Use without --attach to create it."
            exit 1
        fi
        exit 0
    fi
    
    # Kill existing session if requested
    if [[ "$kill_existing" == true ]]; then
        kill_existing_session
    fi
    
    # Create session if it doesn't exist
    if ! session_exists; then
        create_session
        info "Session '$SESSION_NAME' created successfully"
    else
        info "Session '$SESSION_NAME' already exists"
    fi
    
    # Show final session information
    show_session_info
    
    # Attach to session
    attach_session
}

# Trap errors
trap 'error "Script failed at line $LINENO"' ERR

# Run main function with all arguments
main "$@"