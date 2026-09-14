---
name: dagster-fleet-assets
description: >
  Steal Dagster asset/lineage/check/automation patterns for Random Timer fleet
  evidence under marketing/data. Auto-invoke for NSM claims, store LIVE claims,
  freshness, or pipeline health. Uses scripts/fleet_assets.py — no Dagster+.
version: 1.0.0
---

# Skill: dagster-fleet-assets

Patterns from [Dagster docs](https://docs.dagster.io/): assets, deps, asset checks,
freshness, schedules/sensors — mapped onto our JSON GSD artifacts.

## Core rule

Treat `marketing/data/*.json` as **assets**. Agents **observe** and **check** them;
only materialize via the documented script/workflow. Never claim LIVE / on-track
without a passing check.

## Commands

```bash
python3 scripts/fleet_assets.py catalog --json
python3 scripts/fleet_assets.py status --json
python3 scripts/fleet_assets.py lineage --json
python3 scripts/fleet_assets.py check --json   # exit 1 if any check fails
```

Catalog: `marketing/data/fleet_asset_catalog.json`

## Lineage (declared)

`wqtu_health` → `north_star` → `executive_metrics` ← `paywall_conversion`  
`executive_metrics` → `post_publish_gate`

## Automation map (existing)

| Dagster idea | Ours |
|---|---|
| Schedules | GitHub Actions cron (north-star, store snapshots) |
| Sensors | store-release-watcher, internal-signoff statuses |
| Asset sensors | Rematerialize executive after north_star; then post_publish_gate |
| Asset checks | `fleet_assets.py check` (keys, freshness, proxy labels) |
| Observations vs materializations | `status` observes; snapshot scripts materialize |

## Do not

- Install Dagster+ or burn credits for this
- Equate Play review-list counts with public totals (proxy labels)
- Skip freshness when citing WQTU / paywall / store readiness
