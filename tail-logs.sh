#!/bin/bash
# Tail logs for ensemble services

cd /Users/mattbillock/Development/ai_exploration/ensemble

if [ ! -f logs/backend.log ] && [ ! -f logs/frontend.log ]; then
    echo "❌ No log files found. Make sure services are running."
    echo "   Start with: ./restart.sh"
    exit 1
fi

echo "📋 Tailing logs (Ctrl+C to stop)..."
echo ""
tail -f logs/backend.log logs/frontend.log
