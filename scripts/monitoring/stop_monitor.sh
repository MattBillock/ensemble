#!/bin/bash
#
# Stop the Ensemble Monitoring Dashboard
# Cleanly terminates the tmux session
#

set -e

SESSION_NAME="${ENSEMBLE_SESSION:-ensemble-monitor}"

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

# Check if session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo_warn "Session '$SESSION_NAME' does not exist."
    exit 0
fi

echo_info "Stopping Ensemble Monitor Dashboard..."

# Kill the session
tmux kill-session -t "$SESSION_NAME"

echo_info "Dashboard stopped successfully."
