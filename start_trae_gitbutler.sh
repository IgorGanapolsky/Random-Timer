#!/bin/bash

# TRAE IDE + GitButler Integration Launcher
# This script starts TRAE IDE with GitButler automation

PROJECT_PATH="${1:-$(pwd)}"

echo "🚀 Starting TRAE IDE + GitButler Integration"
echo "📁 Project: $PROJECT_PATH"

# Start the file watcher in background
echo "🔍 Starting file watcher..."
nohup "$HOME/bin/trae_simple_watcher.sh" "$PROJECT_PATH" > ~/trae_gitbutler.log 2>&1 &
WATCHER_PID=$!

echo "✅ TRAE GitButler integration started!"
echo "📋 Watcher PID: $WATCHER_PID"
echo "📄 Log file: ~/trae_gitbutler.log"
echo ""
echo "Now you can:"
echo "1. Open TRAE IDE in this project"
echo "2. Make changes with AI"
echo "3. Watch automatic GitButler commits!"
echo ""
echo "To stop the watcher: kill $WATCHER_PID"

# Save PID for easy stopping
echo $WATCHER_PID > ~/.trae_gitbutler_pid
