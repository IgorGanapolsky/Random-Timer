#!/bin/bash

# Badge Monitoring Setup Script
# This script sets up automated local badge monitoring via cron

echo "🔧 Setting up automated badge monitoring..."

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/check-badges.sh"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/badge-health.log"

# Create logs directory
mkdir -p "$LOG_DIR"

# Make sure the badge check script is executable
chmod +x "$SCRIPT_PATH"

# Create the cron job script
CRON_SCRIPT="$PROJECT_DIR/scripts/badge-monitor-cron.sh"
cat > "$CRON_SCRIPT" << EOF
#!/bin/bash

# Badge monitoring cron job
# Runs every 10 minutes to check badge health

cd "$PROJECT_DIR"

echo "\$(date): Starting badge health check..." >> "$LOG_FILE"

# Run the badge check and capture output
if ./scripts/check-badges.sh >> "$LOG_FILE" 2>&1; then
    echo "\$(date): ✅ All badges healthy" >> "$LOG_FILE"
else
    echo "\$(date): ❌ Badge issues detected" >> "$LOG_FILE"
    
    # Attempt auto-fix
    echo "\$(date): Attempting auto-fix..." >> "$LOG_FILE"
    
    # Fix common badge issues
    if grep -q "workflows/SuperPassword%20CI%2FCD/badge.svg" README.md; then
        sed -i.bak 's|workflows/SuperPassword%20CI%2FCD/badge.svg|workflows/ci-cd.yml/badge.svg|g' README.md
        echo "\$(date): Fixed GitHub Actions badge URL" >> "$LOG_FILE"
    fi
    
    if grep -q "branch/develop" README.md; then
        sed -i.bak 's|branch/develop|branch/main|g' README.md
        echo "\$(date): Fixed branch references" >> "$LOG_FILE"
    fi
    
    # Commit fixes if any were made
    if git diff --quiet README.md; then
        echo "\$(date): No fixes needed" >> "$LOG_FILE"
    else
        git add README.md
        git commit -m "🔧 Auto-fix badge issues (automated)" >> "$LOG_FILE" 2>&1
        git push >> "$LOG_FILE" 2>&1
        echo "\$(date): Auto-fixes committed and pushed" >> "$LOG_FILE"
    fi
fi

# Keep log file manageable (last 1000 lines)
tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"

echo "\$(date): Badge monitoring completed" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
EOF

chmod +x "$CRON_SCRIPT"

# Create the cron job entry
CRON_ENTRY="*/10 * * * * $CRON_SCRIPT"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
    echo "⚠️  Cron job already exists"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Cron job added: Badge monitoring every 10 minutes"
fi

# Create a LaunchAgent for macOS (more reliable than cron on macOS)
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
LAUNCH_AGENT_PLIST="$LAUNCH_AGENT_DIR/com.superpassword.badge-monitor.plist"

mkdir -p "$LAUNCH_AGENT_DIR"

cat > "$LAUNCH_AGENT_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.superpassword.badge-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>$CRON_SCRIPT</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
</dict>
</plist>
EOF

# Load the LaunchAgent
launchctl unload "$LAUNCH_AGENT_PLIST" 2>/dev/null || true
launchctl load "$LAUNCH_AGENT_PLIST"

echo "✅ LaunchAgent created and loaded"

# Create a status check script
STATUS_SCRIPT="$PROJECT_DIR/scripts/badge-monitor-status.sh"
cat > "$STATUS_SCRIPT" << EOF
#!/bin/bash

# Badge Monitor Status Script
echo "📊 Badge Monitoring Status"
echo "=========================="

# Check if LaunchAgent is loaded
if launchctl list | grep -q "com.superpassword.badge-monitor"; then
    echo "✅ LaunchAgent: Running"
else
    echo "❌ LaunchAgent: Not running"
fi

# Check if cron job exists
if crontab -l 2>/dev/null | grep -q "badge-monitor-cron.sh"; then
    echo "✅ Cron Job: Configured"
else
    echo "❌ Cron Job: Not configured"
fi

# Show recent log entries
echo ""
echo "📋 Recent Activity:"
echo "==================="
if [ -f "$LOG_FILE" ]; then
    tail -n 20 "$LOG_FILE"
else
    echo "No log file found yet"
fi

echo ""
echo "🔗 Useful Commands:"
echo "==================="
echo "View live logs: tail -f $LOG_FILE"
echo "Manual check: $SCRIPT_PATH"
echo "Restart service: launchctl unload $LAUNCH_AGENT_PLIST && launchctl load $LAUNCH_AGENT_PLIST"
EOF

chmod +x "$STATUS_SCRIPT"

echo ""
echo "🎉 Badge monitoring setup complete!"
echo "=================================="
echo ""
echo "📊 Status: Badge health is now monitored every 10 minutes"
echo "📁 Logs: $LOG_FILE"
echo "🔧 Manual status check: $STATUS_SCRIPT"
echo ""
echo "The system will automatically:"
echo "• Check badge health every 10 minutes"
echo "• Fix common badge issues automatically"
echo "• Commit and push fixes to the repository"
echo "• Log all activity for review"
echo ""
echo "No manual intervention required! 🚀"
