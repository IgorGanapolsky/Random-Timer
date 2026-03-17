# PR Management & System Hygiene Process

## When to Run

- At session start (per Session Start Protocol)
- When user asks to review/merge PRs
- When user asks about branch cleanup
- Invoke via `/pr-management` skill

## Process (in order)

1. **Audit** all open PRs — table with #, title, branch, CI status
2. **Identify** orphan branches (no associated PR)
3. **Merge** green PRs (all checks pass, no REQUEST_CHANGES)
4. **Delete** stale/orphan branches (confirm with user first)
5. **Verify** CI passes on `develop` and `main`
6. **Provide APK link** from latest CI run

## API Pattern

All GitHub operations use `requests` library with PAT:
```python
headers = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github+json'}
```

Key endpoints:
- PRs: `GET /repos/{REPO}/pulls?state=open`
- Branches: `GET /repos/{REPO}/branches?per_page=100`
- Check runs: `GET /repos/{REPO}/commits/{sha}/check-runs`
- Merge: `PUT /repos/{REPO}/pulls/{number}/merge`
- Delete branch: `DELETE /repos/{REPO}/git/refs/heads/{branch}`
- Workflow runs: `GET /repos/{REPO}/actions/runs?branch={branch}`
- Artifacts: `GET /repos/{REPO}/actions/runs/{id}/artifacts`

## Completion Format

> **"Done merging PRs. CI passing. System hygiene complete. Ready for next session."**

With evidence: branch count before/after, merged PR list, CI status, APK link.

## Mistakes to Avoid

- Never tell user to run `gh` commands themselves — execute via API
- Never claim a PR was merged without verifying via API
- Always poll for APK artifact and provide the direct download link
- Always check for merge conflicts before attempting merge

## 2026-03-02 Lessons

- If `strict_required_status_checks_policy` is enabled on branch rulesets, auto-merge PRs can flip to `BEHIND` after any merge to base. Immediately run `gh pr update-branch <pr>` to unblock.
- Keep required checks deterministic: `Android Tests`, `iOS Build Check`, `Security`, `Seer Code Review`. Keep advisory bot checks non-required to prevent deadlocks.
- GitHub Rulesets API accepted strict-check updates but rejected `merge_queue` rule for this repository configuration with HTTP 422. Record the exact response and continue with strict-check enforcement instead of blocking the whole rollout.
- When release PR branch naming policy requires `release/vX.Y.Z`, close superseded non-compliant release PRs and open a compliant replacement branch/PR to avoid persistent policy failures.

## 2026-03-17 Lessons

- **develop divergence**: Local `develop` was ahead 16 / behind 7 vs `origin/develop`. Push rejected (non-fast-forward). Rebase hit conflicts. Do not force-push; resolve divergence via PR or manual conflict resolution first.
- **No merge-ready PRs**: 20 open PRs; none have `mergeStateStatus: CLEAN`. Merge only when CI green + mergeable + no conflicts.
