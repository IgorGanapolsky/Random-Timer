---
allowed-tools: Bash, Read, LS
---

Find blocked tasks by reading filesystem directly:

1. Find open tasks with non-empty `depends_on:` that reference open tasks
2. Show each blocked task, what it's waiting on, and which epic it belongs to
3. Summary: "{count} tasks blocked"
