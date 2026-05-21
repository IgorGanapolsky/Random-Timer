# GSD — Get Shit Done

**Mode:** Ship concrete artifacts every cycle. No status without evidence.

## Each cycle must produce one of

- Merged PR (merge SHA)
- Green workflow run URL
- Updated `marketing/data/*.json` on `develop`
- Published wiki / GitHub Release / store read-back log

## Priority order

1. Revenue blockers (IAP console, paywall catalog, publish)
2. Distribution (internal signoff → Firebase / TestFlight)
3. Store parity (release branch, read-back)
4. Analytics freshness (wiki-sync, executive-metrics)
5. Hygiene (green PRs, dependabot)

## Automation vs CEO

See **`docs/AUTONOMOUS_OPERATIONS.md`** and **`.claude/scheduled_tasks.json`**.

## Code discipline

- Worktree + PR off `develop` (`docs/workflow.md`)
- Ralph Loop for multi-step fixes: `.claude/skills/ralph-mode.md`
- TDD for product code: `AGENTS.md`
