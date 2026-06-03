# GitHub Actions budget policy

Org-wide Actions spend is capped. **ThumbGate** and **openclaw-console** are the
primary burn sources; this repo still must not waste minutes on schedules that do not
directly earn revenue.

## This repository (public)

`Random-Timer` is a **public** repo: **standard GitHub-hosted runner minutes are free**
for public repositories ([billing docs](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions)).

You may still hit:

- **Org-wide** minute caps from **private** repos on the same account
- **Concurrency** queues (many workflows starting at once)
- **`ANTHROPIC_API_KEY`** cost from `claude-review.yml` (not GitHub minutes)

**GitHub Pro** adds only **+1,000 minutes/month on private repos** — it does not change public-repo pricing.

## Tiers

| Tier | Purpose | Trigger |
|------|---------|---------|
| **0** | Ship path (three contracts only) | PR: `ci.yml` + `app-debug` artifact, path-aware `device-tests.yml`, `security.yml`; push `develop`/`main`: `internal-distribution.yml`; production: `native-release.yml` (`workflow_dispatch` only). See [`CI_CD_GAP_VS_AGENTLEASH.md`](CI_CD_GAP_VS_AGENTLEASH.md). |
| **1** | Revenue ops | `daily-growth-publishing`, store verify (dispatch), growth orchestration |
| **2** | Dashboards / hygiene | Throttled `schedule` (6h or daily); everything else defaults to `workflow_dispatch` unless path-triggered on Tier 0 |

## Random-Timer schedule caps (2026-05-26)

- `wiki-sync`: `*/15` → `0 */6 * * *` (push to `develop` on `marketing/data/**` still runs)
- `store-release-watcher`: `*/30` → `0 */6 * * *`
- `resolve-bot-comments`: schedule removed (PR `pull_request_target` only)
- `stackoverflow-hourly-digest`: hourly → daily
- `ios-internal-retry`: `*/3` → `*/6`
- PR iOS device job: `CI_IOS_DEVICE_TIER=smoke` (Maestro smoke only; paywall regressions via dispatch)

### Six-hour stagger (2026-05-31)

Avoid stacking every `*/6` job at **:00** UTC (queue spikes). Current offsets:

| Minute (UTC) | Workflow |
|--------------|----------|
| :05 | `wiki-sync` |
| :10 | `store-release-watcher` |
| :15 | `operational-verification-bundle` |
| :17 | `ios-reviews-ops` |
| :20 | `main` (metrics) |
| :23 | `ios-release-context` |
| :25 | `zernio-growth-orchestration` |
| :35 | `ios-internal-retry` |

## Claude review (Anthropic tokens)

- `claude-review.yml` runs on **`pull_request` only** (no `push` to `develop`/`main`).
- Required check **Claude Review** still applies on PRs per `.github/ci-config.yml`.

## Do not

- Raise org Actions budget broadly before capping high-burn repos.
- Add new `*/15` or `*/30` schedules without CEO approval and minute estimate.

## Off-Actions alternatives

Recurring agent loops → local cron, Railway, or a cheap self-hosted runner.
Keep secrets and deploy gates on GitHub.
