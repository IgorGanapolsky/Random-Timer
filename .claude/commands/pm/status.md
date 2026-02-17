---
allowed-tools: Bash, Read, LS
---

Show project status by reading the filesystem directly:

1. List PRDs: `ls .claude/prds/*.md 2>/dev/null`
2. List epics: `ls -d .claude/epics/*/ 2>/dev/null`
3. Count open tasks: `grep -rl "^status: open" .claude/epics/ 2>/dev/null | wc -l`
4. Count closed tasks: `grep -rl "^status: closed" .claude/epics/ 2>/dev/null | wc -l`

Output a concise summary table.
