---
allowed-tools: Bash, Read, LS
---

Show in-progress work by reading filesystem directly:

1. Find in-progress tasks: `grep -rl "^status: in.progress" .claude/epics/ 2>/dev/null`
2. Find in-progress epics: `grep -rl "^status: in.progress" .claude/epics/*/epic.md 2>/dev/null`
3. Show each with its epic context and progress
