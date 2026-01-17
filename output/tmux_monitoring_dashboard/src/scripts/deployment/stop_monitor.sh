#!/bin/bash

# Tmux Monitoring Dashboard - Stop Script
# Milestone 1: Basic 2x2 Layout Implementation

SESSION_NAME="ensemble_monitor"

# Kill the tmux session if it exists
tmux has-session -t $SESSION_NAME 2>/dev/null
if [ $? == 0 ]; then
    tmux kill-session -t $SESSION_NAME
    echo "Ensemble monitoring dashboard stopped successfully."
else
    echo "No active monitoring dashboard found."
fi