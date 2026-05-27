# GitHub Actions budget policy

Org-wide Actions spend is capped. **ThumbGate** and **openclaw-console** are the
primary burn sources; this repo still must not waste minutes on schedules that do not
directly earn revenue.

## Tiers

| Tier | Purpose | Trigger |
|------|---------|---------|
| **0** | Ship path | PR `ci.yml`, path-aware `device-tests.yml`, security scan |
| **1** | Revenue ops | `daily-growth-publishing`, `native-release` (dispatch), store verify (dispatch) |
| **2** | Dashboards / hygiene | Throttled `schedule` (6h or daily); `workflow_dispatch` always available |

## Random-Timer schedule caps (2026-05-26)

- `wiki-sync`: `*/15` → `0 */6 * * *` (push to `develop` on `marketing/data/**` still runs)
- `store-release-watcher`: `*/30` → `0 */6 * * *`
- `resolve-bot-comments`: schedule removed (PR `pull_request_target` only)
- `stackoverflow-hourly-digest`: hourly → daily
- `ios-internal-retry`: `*/3` → `*/6`
- PR iOS device job: `CI_IOS_DEVICE_TIER=smoke` (Maestro smoke only; paywall regressions via dispatch)

## Do not

- Raise org Actions budget broadly before capping high-burn repos.
- Add new `*/15` or `*/30` schedules without CEO approval and minute estimate.

## Off-Actions alternatives

Recurring agent loops → local cron, Railway, or a cheap self-hosted runner.
Keep secrets and deploy gates on GitHub.
