---
description: "Run codebase hygiene audit — checks root folder cleanliness, absolute paths, secrets, stale docs, build artifacts. Same checks enforced by pre-push hook."
user-invocable: true
---

# Codebase Hygiene Audit

Run the hygiene check script and report results. This is the same audit enforced by the pre-push git hook.

## Steps

1. Run the hygiene check script:
```bash
bash scripts/hygiene-check.sh
```

2. If any errors are found, fix them:
   - **Unexpected .md in root**: Move to `docs/` or `.claude/` or delete if stale
   - **Absolute paths**: Replace with relative paths
   - **Secrets/temp paths**: Remove or move to `.env` (gitignored)
   - **Stale publishing docs**: Delete
   - **Build artifacts tracked**: Add to `.gitignore` and `git rm --cached`

3. Re-run the check to confirm all issues resolved.

4. Report summary: errors fixed, warnings remaining.

## When to Run

- Before creating a PR
- After adding new files to the repo
- During periodic tech debt audits
- Automatically on every `git push` (pre-push hook)

## Adding New Checks

Edit `scripts/hygiene-check.sh` to add new checks. Use `error()` for blocking issues and `warn()` for non-blocking advisories.
