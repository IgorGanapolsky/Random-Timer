---
name: browser-automate
description: Automate web UI tasks using agent-browser CLI. Use when a task requires interacting with a web console (Google Play, App Store Connect, GitHub settings, etc.) that has no API.
user_invocable: true
---

# Browser Automation Skill

Automate web UI interactions using `agent-browser` CLI.

## Prerequisites

```bash
npm install -g agent-browser
agent-browser install
```

## Usage Pattern

```bash
# 1. Open URL
agent-browser open "<URL>"

# 2. Take snapshot to see interactive elements (returns @e1, @e2, etc.)
agent-browser snapshot --json

# 3. Click elements by reference
agent-browser click @e5

# 4. Fill form fields
agent-browser fill @e3 "value"

# 5. Upload files
agent-browser fill @e7 "/path/to/file"

# 6. Screenshot for verification
agent-browser screenshot /tmp/result.png

# 7. Close
agent-browser close
```

## Key Rules

- Always `snapshot --json` before interacting to get element refs
- Use `@eN` refs, not CSS selectors
- Screenshot after critical actions for verification
- Close session when done
