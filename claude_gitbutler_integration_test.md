# Claude Code + GitButler Integration Test

This file was created to test the **real** GitButler + Claude Code integration using the official hooks system.

## How it should work:
1. Claude Code creates/modifies files
2. When the session ends, the "Stop" hook triggers
3. The hook script commits changes with the user prompt as the commit message
4. GitButler manages the virtual branches automatically

## Testing the official integration:
- Using Claude Code hooks (not custom scripts)
- Following the GitButler blog post exactly
- Real automation, not manual commands

**Created:** $(date)
**Purpose:** Test the GitButler + Claude Code hooks integration
