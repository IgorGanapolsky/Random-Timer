---
allowed-tools: Bash, Read, LS
---

Find next available tasks by reading filesystem directly:

1. Find open tasks: `grep -rl "^status: open" .claude/epics/ 2>/dev/null`
2. For each, check `depends_on:` — skip if dependencies aren't closed
3. Show ready tasks with epic name and parallel flag
4. Summary: "{count} tasks ready to start"
