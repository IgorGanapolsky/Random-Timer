---
allowed-tools: Bash, Read, LS
---

Validate PM artifacts by reading filesystem directly:

1. Check all `.claude/prds/*.md` have valid frontmatter (name, status, created)
2. Check all `.claude/epics/*/epic.md` have valid frontmatter (name, status, progress)
3. Check all task files have frontmatter (name, status)
4. Report: valid count, invalid count, specific issues
