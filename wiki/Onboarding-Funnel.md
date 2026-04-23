# Onboarding Funnel

Tracks new user activation from first app open through first timer completion.

## Funnel Steps

```
First Open  →  First Timer Configured  →  First Timer Completed
  100%            ??% conversion             ??% conversion
```

> **Note:** Real data populates once `POSTHOG_PERSONAL_API_KEY` and `POSTHOG_PROJECT_ID` secrets are configured. Until then, the attribution pipeline writes zero-value placeholders.

## How It Works

1. **PostHog lifecycle tracking** fires `first_open` on first launch
2. **`settings_changed`** event (first occurrence per user) = `first_timer_configured`
3. **`timer_completed`** event (first occurrence per user) = `first_timer_completed`
4. `attribution_feedback.py` queries these via HogQL `count(DISTINCT person_id)` over a 30-day window
5. Conversion rates computed:
   - **Open → Configured**: `first_timer_configured / first_open`
   - **Configured → Completed**: `first_timer_completed / first_timer_configured`
   - **Open → Completed**: Full funnel `first_timer_completed / first_open`

## Where Data Lives

- **Live query**: `scripts/attribution_feedback.py` → `fetch_onboarding_funnel()`
- **Output**: `marketing/data/content_feedback.json` → `onboarding_funnel` key
- **Report**: `marketing/data/attribution-report.md`

## What Drives Improvement

| Lever | Measured By | Optimized By |
|-------|-----------|-------------|
| Store listing clarity | Install → Open rate | CRO screenshot/title experiments |
| First-use simplicity | Open → Configured rate | Timer setup UX (single screen) |
| Value delivery | Configured → Completed rate | Alarm quality, loop mode |
| Review prompts | Completed → Review rate | `StoreReviewManager` (earned milestone gate: 3, 10, 25, then every 25, plus cooldown) |

<!-- LIVE_DATA_START -->
## Latest Funnel Data

_This section is auto-updated by the wiki-sync workflow._

| Metric | Value |
|--------|-------|
| First Open | — |
| First Timer Configured | — |
| First Timer Completed | — |
| Open → Configured | — |
| Open → Completed | — |
<!-- LIVE_DATA_END -->
