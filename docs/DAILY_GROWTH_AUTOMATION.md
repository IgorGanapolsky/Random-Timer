# Daily Growth Publishing Automation

## Overview

`Daily Growth Publishing` runs every day on GitHub Actions and does the following:

1. Generates one short engineering post (SEO-friendly, AI/LLM-focused)
2. Creates a PaperBanana-style technology flow diagram (`SVG` + `Mermaid`)
3. Builds BID-ranked keyword backlog (Business potential, Intent, Difficulty)
4. Flags AI-trap keywords and prioritizes tool keywords (calculator/checker/generator/template)
5. Builds and deploys static blog pages to GitHub Pages
6. Publishes post distribution updates to DEV.to, LinkedIn, and X
7. Collects engagement metrics and stores historical snapshots
8. Classifies AI-bot crawl logs (when available) into training/retrieval/search groups

Workflow file: `.github/workflows/daily-growth-publishing.yml`
Script entrypoint: `scripts/growth_content_pipeline.py`
Keyword engine: `scripts/growth_keyword_engine.py`
Bot analytics: `scripts/growth_bot_analytics.py`

## First post rule

The first generated post is forced to:

- **Title**: `The inspiration behind Random Tactical Timer`
- **Inspiration source**: `Hard Target` URL
  - `https://www.amazon.com/Hard-Target-Become-Person-Predators/dp/B0F78ZL7ML`

This is enforced in code so it cannot be skipped by accident.

## Required secrets

### Publishing channels

- `DEVTO_API_KEY`
- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN` (format: `urn:li:person:...`)
- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`
- `X_BEARER_TOKEN` (metrics reads)

### Blog + tracking links

- `BLOG_BASE_URL` (default: `https://igorganapolsky.github.io/Random-Timer/`)
- `APP_STORE_URL`
- `PLAY_STORE_URL`
- `IOS_REVIEW_URL`
- `ANDROID_REVIEW_URL`

### Optional analytics tags for GitHub Pages

- `GA4_MEASUREMENT_ID`
- `PLAUSIBLE_DOMAIN`
- `PLAUSIBLE_SCRIPT_URL` (optional override)

## Local dry-run

```bash
python3 scripts/growth_content_pipeline.py \
  --repo-root . \
  --output-root marketing \
  run-daily \
  --dry-run
```

## Keyword playbook execution

```bash
python3 scripts/growth_content_pipeline.py \
  --output-root marketing \
  keyword-plan
```

This writes:
- `marketing/keywords/keyword_backlog.json`
- `marketing/keywords/keyword_backlog.csv`
- `marketing/keywords/keyword_backlog.md`

## AI-friendly surfaces for agents

Generated in `marketing/site/`:
- `llms.txt`: index of markdown resources for LLM crawlers/agents
- `agents.md`: intent-rich summary and latest post map
- `md/*.md`: per-post markdown endpoints

## Bot classification and analytics

If you export edge/CDN traffic to NDJSON, set:

- `AI_BOT_LOG_PATH` (secret or env var), default: `marketing/data/access-log.ndjson`

Expected fields per line:
- `user_agent` (or `ua`)
- `path` (or `url`)
- optional: `timestamp`, `status`

The pipeline classifies known crawler families into:
- `ai_training`
- `ai_retrieval`
- `search_crawler`

Outputs:
- `marketing/data/bot_traffic_summary.json`
- `marketing/data/bot_traffic_summary.md`

This generates content and metrics locally without posting to external APIs.

## Output evidence

- `marketing/data/posts.jsonl`
- `marketing/data/publications.jsonl`
- `marketing/data/engagement.jsonl`
- `marketing/data/engagement-latest.md`
- `marketing/data/bot_traffic_summary.json`
- `marketing/data/bot_traffic_summary.md`
- `marketing/site/` (deployed pages artifact)

## Prompt library

Reusable prompt packs for ASO, creative briefs, screenshot copy, incident summaries, and release notes live in `docs/prompt-library/README.md`.

Use them when the workflow needs copy generation but the repo must stay aligned to live product truth and the North Star metric.

## Notes

- The script never commits secrets.
- Missing channel credentials cause channel-level `skipped` results, not hard crashes.
- UTM parameters are injected automatically to measure CTR to app download/review links.
