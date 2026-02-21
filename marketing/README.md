# Growth Content Artifacts

This folder is managed by `scripts/growth_content_pipeline.py` and `.github/workflows/daily-growth-publishing.yml`.

- `posts/`: source markdown posts
- `diagrams/`: PaperBanana-style diagram assets (`.svg`, `.mmd`)
- `data/`: publication + engagement logs (`.jsonl`)
- `keywords/`: seed/modifier strategy and BID-scored keyword backlog
- `site/`: generated static site deployed to GitHub Pages

## DEV.to A/B Pilot (14-run)

The daily growth workflow now supports a 14-run A/B pilot for DEV.to publishing:

- `control`: direct DEV.to API publish (`control_direct_api`)
- `candidate`: retry-enabled DEV.to API publish (`candidate_retry_api`)

Pilot decision rule (strict):

Candidate is kept only if it beats control on all three metrics:

1. Success rate
2. Mean execution time
3. Cost per successful publish

Cost guardrail:

- Hard cap via `AB_PILOT_MAX_COST_USD` (default in workflow: `10`)
- When projected spend would exceed the cap, the pilot automatically falls back to the cheaper affordable arm.
- If no arm is affordable, DEV.to publish is skipped for that run with `ab_pilot_budget_cap_exhausted`.

Generated pilot artifacts in `marketing/data/`:

- `publish_ab_pilot_runs.jsonl`
- `publish_ab_pilot_summary.json`
- `publish_ab_pilot_report.md`

Do not store secrets here. API keys/tokens are pulled from GitHub Actions secrets.
