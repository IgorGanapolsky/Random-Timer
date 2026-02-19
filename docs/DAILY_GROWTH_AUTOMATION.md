# Daily Growth Publishing Automation

## Overview

`Daily Growth Publishing` runs every day on GitHub Actions and does the following:

1. Generates one short engineering post (SEO-friendly, AI/LLM-focused)
2. Creates a PaperBanana-style technology flow diagram (`SVG` + `Mermaid`)
3. Builds and deploys static blog pages to GitHub Pages
4. Publishes post distribution updates to DEV.to, LinkedIn, and X
5. Collects engagement metrics and stores historical snapshots

Workflow file: `.github/workflows/daily-growth-publishing.yml`
Script entrypoint: `scripts/growth_content_pipeline.py`

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

This generates content and metrics locally without posting to external APIs.

## Output evidence

- `marketing/data/posts.jsonl`
- `marketing/data/publications.jsonl`
- `marketing/data/engagement.jsonl`
- `marketing/data/engagement-latest.md`
- `marketing/site/` (deployed pages artifact)

## Notes

- The script never commits secrets.
- Missing channel credentials cause channel-level `skipped` results, not hard crashes.
- UTM parameters are injected automatically to measure CTR to app download/review links.
