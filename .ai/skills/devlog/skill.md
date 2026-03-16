# Devlog Workflow — AI-Optimized Changelog

Record a change with enough context for future AI agents to understand the **what**, **why**, and **impact**.

## When to Use

- After completing a feature, bug fix, or refactoring
- After a significant configuration or dependency change
- When something non-obvious was done that future developers should know about

## Workflow Steps

### Step 1: Gather Change Information

If the user provided a description, use it as the starting point. Otherwise, analyze the current conversation context to identify:

1. What was changed (files, components, features)
2. Why it was changed
3. What else might be affected

If the context is insufficient, ask the user briefly. Prefer extracting from conversation over asking.

Also run `git diff --stat` and `git log --oneline -5` to understand recent changes if the conversation doesn't make it clear.

### Step 2: Determine the File

The changelog file is `.ai/changelog/YYYY-MM.md` based on the current month. If the file doesn't exist, create it with the month header:

```markdown
# YYYY-MM Changelog
```

### Step 3: Append the Entry

Add a new entry at the **end** of the file:

```markdown
## [YYYY-MM-DD] <type>: <short description>

- **What**: What was changed (files, components, features)
- **Why**: The motivation or problem being solved
- **Impact**: What other parts of the system are affected
- **Gotchas**: Any non-obvious side effects or things to watch out for
- **Related**: Links to ADRs, commits, issues, or PRs
```

**Type values**: `feat`, `fix`, `refactor`, `perf`, `config`, `deps`

### Step 4: Confirm

Output:
- The entry that was added (formatted)
- File path updated

## Style Guidelines

- Write **What** as a factual list of changes (files/components)
- Write **Why** as the problem or motivation (one sentence)
- Write **Impact** as what other parts of the system are affected
- Write **Gotchas** only if there are actual non-obvious side effects; omit if none
- Keep each field to 1-2 lines
- Use present tense ("Updates X", "Fixes Y")
- Include commit hashes or PR numbers in **Related** when available
