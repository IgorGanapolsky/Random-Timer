# Referral & Content

Community marketing through Reddit posts, Product Hunt launch, and blog outreach.

## Reddit Campaign (7 Posts)

| Subreddit | Audience | Status |
|-----------|----------|--------|
| r/HIIT | HIIT practitioners | Draft |
| r/CrossFit | CrossFit athletes | Draft |
| r/boxing | Boxers, trainers | Draft |
| r/bodyweightfitness | Calisthenics community | Draft |
| r/tacticaltraining | Tactical/LEO trainers | Draft |
| r/androidapps | Android users | Draft |
| r/iOSProgramming | iOS developers | Draft |

Each post is platform-tailored with authentic use cases, not promotional spam.

## Product Hunt Launch

- **Tagline:** Set by `generate_product_hunt_launch()`
- **Topics:** Productivity, Health & Fitness, Developer Tools
- **Pre-launch checklist:** 5 items (1 completed)
- **Status:** Draft, date TBD

## Blog Outreach (3 Targets)

| Target Niche | Angle | Status |
|-------------|-------|--------|
| Fitness blogs | Reaction training for athletes | Draft |
| Coaching blogs | Unpredictable drill timer for coaches | Draft |
| Productivity blogs | Focus training with random intervals | Draft |

## Content Pipeline (Daily)

The `growth_content_pipeline.py` runs daily at 13:15 UTC:

1. **Keyword selection** — Picks daily keyword from BID-score backlog
2. **Post generation** — Builds markdown from git commits + keyword + topic rotation
3. **Site build** — Generates GitHub Pages (HTML, sitemap, `llms.txt`, `agents.md`)
4. **Publish** — Posts to DEV.to, LinkedIn, X/Twitter
5. **Engagement** — Collects metrics from DEV.to API and X

### Published Content

Tracked in `marketing/data/posts.jsonl` (one JSON object per line).

## Source Files

- `scripts/backlinks_referral.py` — Reddit, PH, blog outreach generation
- `scripts/growth_content_pipeline.py` — Daily blog pipeline
- `marketing/data/referral_campaigns.json` — Campaign data
- `marketing/referral_content/` — Generated markdown files
- `.github/workflows/weekly-referral-content.yml` — Friday 14:00 UTC
- `.github/workflows/daily-growth-publishing.yml` — Daily 13:15 UTC
