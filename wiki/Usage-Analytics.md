# Usage Analytics

> How we measure what users do inside the app. All events tracked via PostHog on both Android and iOS.

## Active User Metrics

| Metric | Definition | Source |
|--------|-----------|--------|
| **DAU** | Unique users with any non-system event in last 24h | PostHog HogQL |
| **WAU** | Unique users with any non-system event in last 7d | PostHog HogQL |
| **MAU** | Unique users with any non-system event in last 30d | PostHog HogQL |

Tracked by `store_downloads_tracker.py` → `marketing/data/store_downloads.json` → wiki dashboard.

## Core User Events

### Timer Lifecycle

| Event | Fired when | Properties |
|-------|-----------|------------|
| `timer_started` | User taps Start | `min_seconds`, `max_seconds`, `sound_enabled` |
| `timer_paused` | User taps Pause | `elapsed_seconds` |
| `timer_resumed` | User taps Resume | `elapsed_seconds` |
| `timer_completed` | Timer reaches end | `total_seconds`, `was_random` |
| `timer_reset` | User taps Reset | — |
| `timer_stopped` | User force-stops | `elapsed_seconds` |

### Alarm

| Event | Fired when | Properties |
|-------|-----------|------------|
| `alarm_triggered` | Alarm sound starts | `sound_name` |
| `alarm_dismissed` | User dismisses alarm | `time_to_dismiss_ms` |

### Settings & Config

| Event | Fired when | Properties |
|-------|-----------|------------|
| `settings_changed` | Any setting modified | `setting_name`, `old_value`, `new_value` |
| `first_timer_configured` | First time user sets timer params | `min_seconds`, `max_seconds` |

### Engagement & Retention

| Event | Fired when | Properties |
|-------|-----------|------------|
| `first_open` | App opened for the first time | `platform`, `app_version` |
| `review_prompt_requested` | In-app review prompt shown | `completions_count` |
| `write_review_tapped` | User taps "Write Review" | — |
| `deep_link_opened` | UTM deep link opened | `utm_source`, `utm_medium`, `utm_campaign`, `utm_content` |

### Screen Tracking

| Screen | Tracked as |
|--------|-----------|
| Timer Setup | `$screen` / `screen_view` with `screen_name=Timer Setup` |
| Active Timer | `$screen` / `screen_view` with `screen_name=Active Timer` |

## Key Funnels

### Onboarding Funnel (automated weekly)

```
first_open → first_timer_configured → first_timer_completed
```

Conversion rates computed by `attribution_feedback.py` and injected into the Daily Metrics Dashboard.

### Retention Funnel

```
first_open → timer_started (same session)
           → timer_completed (D0)
           → timer_started (D1)  ← Day 1 retention
           → timer_started (D7)  ← Week 1 retention
```

Available via PostHog Retention chart (manual query).

### Review Prompt Funnel

```
timer_completed (×3) → review_prompt_requested → write_review_tapped
```

Prompt config in `marketing/data/review_velocity.json`:
- Show after **3 completions**
- Minimum **30 days** between prompts
- Only after positive experience (completion, not force-stop)

## PostHog Configuration

- **Host:** `https://us.i.posthog.com`
- **Secrets:** `POSTHOG_API_KEY` (set), `POSTHOG_PROJECT_ID` (needs to be added)
- **SDK:** Android PostHog SDK + iOS PostHog SDK
- **Identified users:** Yes, with `platform` and `app_version` properties

## Data Flow

```
App (Android/iOS)
    │ PostHog SDK
    ▼
PostHog Cloud (us.i.posthog.com)
    │ HogQL API (weekly)
    ├──→ attribution_feedback.py → posthog_feedback.json + content_feedback.json
    ├──→ store_downloads_tracker.py → store_downloads.json (DAU/WAU/MAU)
    │
    ▼
wiki_sync.py (daily 14:30 UTC)
    │
    ▼
Daily Metrics Dashboard (wiki)
```
