# Marketing Leads & Acquisition

> Consolidated view of all lead generation channels, acquisition funnels, and conversion metrics.

## Lead Sources

| Channel | Type | Status | Tracking |
|---------|------|--------|----------|
| **Google Play organic** | Store search | Active | PostHog `first_open` + `utm_source=google_play` |
| **App Store organic** | Store search | Active | PostHog `first_open` + `utm_source=app_store` |
| **Apple Search Ads** | Paid search | Draft ($6/day) | PostHog `deep_link_opened` + `utm_source=apple_search_ads` |
| **Google UAC** | Paid search | Draft ($4/day) | PostHog `deep_link_opened` + `utm_source=google_uac` |
| **Reddit** | Social / referral | 7 posts drafted | UTM links: `utm_source=reddit&utm_medium=social` |
| **Product Hunt** | Launch / referral | Draft | UTM links: `utm_source=producthunt&utm_medium=launch` |
| **Blog (GitHub Pages)** | SEO / content | 1 post live | UTM links: `utm_source=blog&utm_medium=content` |
| **DEV.to** | Content syndication | Active (API key set) | UTM links: `utm_source=devto&utm_medium=content` |
| **X (Twitter)** | Social | Active (API keys set) | UTM links: `utm_source=twitter&utm_medium=social` |

## Acquisition Funnel

```
Impression (store listing view)
    → Install (download)
        → First Open (PostHog: first_open)
            → First Timer Configured (PostHog: first_timer_configured)
                → First Timer Completed (PostHog: first_timer_completed)
                    → Retained (DAU/WAU/MAU via PostHog)
                        → Review prompted (after 3 completions)
```

## Measurement Infrastructure

### What's tracked automatically:

| Metric | Source | Pipeline | Dashboard Section |
|--------|--------|----------|-------------------|
| **Downloads (30d)** | App Store Connect + Google Play | `store_downloads_tracker.py` (weekly) | Downloads & Active Users |
| **Active Installs** | Google Play Console | `store_downloads_tracker.py` (weekly) | Downloads & Active Users |
| **DAU / WAU / MAU** | PostHog HogQL | `store_downloads_tracker.py` (weekly) | Downloads & Active Users |
| **UTM Attribution** | PostHog `deep_link_opened` | `attribution_feedback.py` (weekly) | Attribution Summary |
| **Onboarding Funnel** | PostHog event sequence | `attribution_feedback.py` (weekly) | Onboarding Funnel |
| **Review Velocity** | App Store Connect cache | `review_velocity_tracker.py` (weekly) | Review Velocity |
| **Keyword Performance** | PostHog installs per keyword | `aso_keyword_rotation.py` (weekly) | ASO Keywords |
| **Content Engagement** | DEV.to / X APIs | `growth_content_pipeline.py` (daily) | Content Pipeline |

### GitHub Secrets powering this pipeline:

| Secret | Set? | Powers |
|--------|:----:|--------|
| `POSTHOG_API_KEY` | Yes | Attribution, funnel, DAU/WAU/MAU |
| `POSTHOG_PROJECT_ID` | **No** | Required for PostHog HogQL queries |
| `GOOGLE_PLAY_JSON_KEY` | Yes | Android download counts |
| `APPSTORE_KEY_ID` | Yes | iOS download counts, review velocity |
| `APPSTORE_ISSUER_ID` | Yes | iOS download counts, review velocity |
| `APPSTORE_PRIVATE_KEY` | Yes | iOS download counts, review velocity |
| `DEVTO_API_KEY` | Yes | Blog syndication to DEV.to |
| `X_API_KEY` + tokens | Yes | X/Twitter publishing |
| `BLOG_BASE_URL` | Yes | GitHub Pages blog |

### Remaining gap:

`POSTHOG_PROJECT_ID` is the only critical secret still missing. Find it at: PostHog → Project Settings → Project ID. Once set, all attribution + funnel + active user data flows automatically.

## Weekly Pipeline Schedule

```
Sunday  07:00  →  Downloads Tracker (stores + PostHog active users)
Sunday  08:00  →  Attribution Feedback (UTM + funnel from PostHog)
Monday  10:00  →  ASO Keyword Rotation (swap underperformers)
Tuesday 11:00  →  CRO Optimization (A/B test proposals)
Wed     09:00  →  Review Velocity (review rates + prompt tuning)
Thursday 12:00 →  Paid Acquisition (campaign config refresh)
Friday  14:00  →  Referral Content (Reddit/PH/blog outreach)
Daily   13:15  →  Content Publishing (blog + DEV.to + X)
Daily   14:30  →  Wiki Sync (inject all data → Daily Metrics Dashboard)
```
