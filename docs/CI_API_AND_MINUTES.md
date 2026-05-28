# CI: API rate limits vs Actions minutes

## Two different budgets

| Budget | Symptom | Typical cause here |
|--------|---------|-------------------|
| **GraphQL API** (`gh pr view`, `gh pr checks`) | `API rate limit exceeded` on GraphQL | Tight `gh` polling; `check_suite` fan-out (fixed 2026-05-28) |
| **Actions minutes** | Slow PRs, high bill | Duplicate Android build (CI + device-tests), macOS Maestro, 33 cron workflows |

Verify GraphQL: `gh api rate_limit --jq .resources.graphql`

## Agent / automation rules

1. Prefer **REST**: `gh api repos/{owner}/{repo}/commits/{sha}/check-runs` — not `gh pr checks` in loops.
2. Poll interval **≥ 3 minutes**; stop when `pending == 0`.
3. Never poll GraphQL in parallel across multiple agents.

## Repo guardrails (2026-05-28)

- `pr-state-machine.yml`: reconciles on `workflow_run` (CI + Device Tests completed), not per `check_suite`.
- `claude-review.yml`: `push` limited to `develop`, `main`, `release/**`, `hotfix/**`.
- `device-tests.yml`: `cancel-in-progress: true`; PR branches include `release/**`, `hotfix/**`.
