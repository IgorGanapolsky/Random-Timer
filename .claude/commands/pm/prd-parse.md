---
allowed-tools: Bash, Read, Write, LS
---

# PRD Parse

Convert PRD to technical epic for: **$ARGUMENTS**

## Steps

1. Verify `$ARGUMENTS` provided, `.claude/prds/$ARGUMENTS.md` exists. If epic already exists, ask before overwriting.
2. Read the PRD. Analyze requirements, constraints, success criteria.
3. Create `.claude/epics/$ARGUMENTS/epic.md` with frontmatter:

```yaml
---
name: $ARGUMENTS
status: backlog
created: <run date -u +"%Y-%m-%dT%H:%M:%SZ">
progress: 0%
prd: .claude/prds/$ARGUMENTS.md
---
```

4. Write the epic body: Overview, Architecture Decisions, Technical Approach, Task Breakdown Preview (max 10 tasks), Dependencies, Success Criteria.
5. Output: "Epic created. Next: `/pm:epic-decompose $ARGUMENTS`"

Keep tasks under 10. Leverage existing code over new code.
