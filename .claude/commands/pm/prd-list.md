---
allowed-tools: Read, LS
---

List all PRDs by reading filesystem directly:

1. List `.claude/prds/*.md`
2. For each, read frontmatter: name, status, created
3. Group by status: backlog, in-progress, complete
