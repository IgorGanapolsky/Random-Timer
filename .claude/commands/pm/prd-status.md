---
allowed-tools: Read, LS
---

Show PRD status by reading filesystem directly:

1. List all `.claude/prds/*.md`
2. For each, extract `status:` from frontmatter
3. Count by status category and show summary
