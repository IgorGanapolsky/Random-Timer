---
allowed-tools: Bash, Read, LS
---

Generate standup summary by reading filesystem directly:

1. Read recent git log: `git log --oneline --since="yesterday" 2>/dev/null`
2. Find in-progress tasks: `grep -rl "^status: in.progress" .claude/epics/ 2>/dev/null`
3. Find blocked tasks with unresolved dependencies
4. Format as: Done / Doing / Blocked
