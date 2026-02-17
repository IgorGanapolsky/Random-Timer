---
allowed-tools: Bash, Read, LS
---

List all epics by reading filesystem directly:

1. For each dir in `.claude/epics/*/epic.md`: read frontmatter (name, status, progress)
2. Count tasks per epic: `ls .claude/epics/{name}/[0-9]*.md 2>/dev/null | wc -l`
3. Group by status: planning, in-progress, completed
4. Show summary count at end
