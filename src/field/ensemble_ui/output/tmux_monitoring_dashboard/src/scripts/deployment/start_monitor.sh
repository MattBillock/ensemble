#!/bin/bash

# Tmux Monitoring Dashboard - Start Script
# Milestone 1: Basic 2x2 Layout Implementation

SESSION_NAME="ensemble_monitor"
OUTPUT_DIR="/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/output/tmux_monitoring_dashboard"

# Check if session already exists
tmux has-session -t $SESSION_NAME 2>/dev/null
if [ $? == 0 ]; then
    echo "Monitoring session already running. Use stop_monitor.sh to terminate."
    exit 1
fi

# Create new tmux session
tmux new-session -d -s $SESSION_NAME

# Split window into 2x2 grid
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v

# Pane Configuration
# Pane 0 (top-left): Interactive Shell
tmux send-keys -t 0 'echo "Ensemble Agent Monitoring Dashboard - CLI Ready"' C-m

# Pane 1 (top-right): Tail Backend Log
tmux send-keys -t 1 "tail -f $OUTPUT_DIR/backend.log" C-m

# Pane 2 (bottom-left): Vim Output Directory Browser
tmux send-keys -t 2 "vim $OUTPUT_DIR" C-m

# Pane 3 (bottom-right): Watch Project Files
tmux send-keys -t 3 "watch -n 5 'ls -l $OUTPUT_DIR/project_files'" C-m

# Select first pane
tmux select-pane -t 0

# Attach to session
tmux attach-session -t $SESSION_NAME