# Attribution & UTM Pipeline

How marketing spend flows from content/ads through UTM parameters to install attribution and back into optimization loops.

## Data Flow

```
Blog/Ad/Reddit Post
   ↓ UTM-tagged links (utm_source, utm_medium, utm_campaign, utm_content)
App Store / Play Store listing
   ↓ Install referrer captured by PostHog SDK (captureDeepLinks=true)
PostHog events table (deep_link_opened)
   ↓ Weekly HogQL queries via attribution_feedback.py
marketing/keywords/posthog_feedback.json  →  ASO keyword rotation
marketing/data/content_feedback.json      →  Content topic selection
marketing/data/attribution-report.md      →  This dashboard
```

## UTM Tagging Convention

All outbound links in blog posts are tagged by `growth_content_pipeline.py → add_utm()`:

| Parameter | Value | Example |
|-----------|-------|---------|
| `utm_source` | Platform name | `github_pages`, `devto`, `linkedin`, `twitter` |
| `utm_medium` | Channel type | `organic`, `paid`, `referral` |
| `utm_campaign` | Date-stamped | `daily_blog_20260220` |
| `utm_content` | Keyword slug | `daily_blog`, `reaction_training_app` |

## PostHog Queries (run weekly)

### 1. UTM Attribution
```sql
SELECT properties.utm_source, properties.utm_medium,
       properties.utm_campaign, properties.utm_content,
       count() AS installs, count(DISTINCT person_id) AS unique_users
FROM events
WHERE event = 'deep_link_opened'
  AND timestamp > now() - interval 30 day
GROUP BY source, medium, campaign, content
ORDER BY installs DESC
```

### 2. Onboarding Funnel
Queries `first_open`, `first_timer_configured`, `first_timer_completed` events to compute:
- **Open → Configured rate**: % of new users who set up a timer
- **Configured → Completed rate**: % who run a timer to completion
- **Open → Completed rate**: Full funnel conversion

### 3. Campaign Performance with Activation
```sql
SELECT properties.utm_campaign, properties.utm_source,
       count(DISTINCT person_id) AS attributed_users,
       countIf(person_id IN (
           SELECT DISTINCT person_id FROM events
           WHERE event = 'first_timer_completed'
       )) AS activated_users
FROM events WHERE event = 'deep_link_opened' ...
```

## Feedback Loops

### → ASO Keyword Rotation
`posthog_feedback.json` maps `utm_content` values to install counts. The weekly `aso_keyword_rotation.py` uses these as real performance signals instead of simulated rankings.

### → Content Pipeline
`content_feedback.json` ranks campaigns by activation rate. The daily `growth_content_pipeline.py` uses this to prioritize topics that drive actual installs.

### → Campaign Budget
`attribution-report.md` shows campaign ROI. Manual review informs budget reallocation between Apple Search Ads and Google UAC.

## Automation Schedule

| Workflow | Schedule | What it does |
|----------|----------|-------------|
| `weekly-attribution-feedback.yml` | Sunday 08:00 UTC | Runs PostHog queries, writes feedback JSON, commits to repo |
| `weekly-aso-rotation.yml` | Monday 10:00 UTC | Consumes feedback, rotates iOS keywords |
| `daily-growth-publishing.yml` | Daily 13:15 UTC | Publishes content with UTM tags |

## Required Secrets

| Secret | Purpose |
|--------|---------|
| `POSTHOG_PERSONAL_API_KEY` | Bearer token for PostHog HogQL API |
| `POSTHOG_PROJECT_ID` | PostHog project to query |

Without these secrets, the pipeline generates empty feedback files so downstream scripts don't break.

## Source Files

- `scripts/attribution_feedback.py` — Main pipeline
- `scripts/growth_content_pipeline.py` → `add_utm()` — UTM tag builder
- `.github/workflows/weekly-attribution-feedback.yml` — Automation
