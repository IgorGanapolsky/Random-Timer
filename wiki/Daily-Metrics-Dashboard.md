# Daily Metrics Dashboard

> **Auto-updated** by the `wiki-sync.yml` workflow. Data sourced from `marketing/data/` JSON files and PostHog attribution reports.

## Downloads & Active Users

<!-- DOWNLOADS_START -->
| Metric | iOS | Android | Combined |
|--------|:---:|:-------:|:--------:|
| Distinct install users (30d) | 39 | 36 | 75 |
| Active Installs | — | 41 | — |

| Active Users | Count |
|-------------|:-----:|
| DAU | 2 |
| WAU | 18 |
| MAU | 92 |
<!-- DOWNLOADS_END -->

## North Star (WQTU)

<!-- NORTH_STAR_START -->
| Metric | Value |
|--------|-------|
| WQTU (7d) | 4 |
| Timer Completed (7d) | 125 |
| Completed Users (7d) | 10 |
| Sessions/Completed User (7d) | 12.5 |
| Checkpoint Target (2026-03-31) | 8 |
| Quarter Target (2026-06-30) | 25 |
| Paid Attributed Users (30d) | 0 |
| Active Campaign Count | 0 |
| Guardrail Violated | NO |
<!-- NORTH_STAR_END -->

## Attribution Summary

<!-- ATTRIBUTION_START -->
# Attribution Feedback Report

**Generated:** 2026-07-11T00:49:57+00:00

## Onboarding Funnel
- First Open: **76**
- First Timer Configured: **54** (71.0% of opens)
- First Timer Completed: **35** (46.1% of opens)

## UTM Attribution (Top Sources)
| Source | Medium | Campaign | Installs | Unique Users |
|--------|--------|----------|----------|-------------|

## Campaign Performance
| Campaign | Source | Attributed | Activated | Rate |
|----------|--------|-----------|-----------|------|

<!-- ATTRIBUTION_END -->

## Paywall & Revenue Funnel (30-day)

<!-- PAYWALL_START -->
| Metric | Value |
|--------|-------|
| Paywall Views | 85 |
| Offer Selects | 3 |
| Purchase Attempts | 0 |
| Purchase Successes | 0 |
| Attempt → Success | — |

**Top failure reasons:** failed (1)

**Catalog failures (Android):** pro_base (8), elite_tactical_monthly (7), elite_tactical (6)
<!-- PAYWALL_END -->

## Onboarding Funnel (30-day window)

<!-- FUNNEL_START -->
| Step | Users | Conversion |
|------|:-----:|:----------:|
| First Open | 76 | — |
| First Timer Configured | 54 | 71.0% of opens |
| First Timer Completed | 35 | 46.1% of opens |
<!-- FUNNEL_END -->

## Review Velocity

<!-- REVIEWS_START -->
| Platform | Total Reviews | Avg Rating | 7-day Velocity |
|----------|:------------:|:----------:|:--------------:|
| iOS | 1 | 5.0 | — reviews/day |
| Android | 1 | 5.0 | 1.0 reviews/day |

**Prompt Config:** Show after 3 completions, 30 days between prompts
<!-- REVIEWS_END -->

## Active CRO Experiments

<!-- CRO_START -->
| Experiment | Platform | Status | Duration |
|-----------|----------|--------|----------|
| title_ab_test | android | proposed | 14 days |
| short_description_ab_test | android | proposed | 14 days |
| screenshot_ab_test | both | proposed | 21 days |
| title_ab_test | android | proposed | 14 days |
| short_description_ab_test | android | proposed | 14 days |
| screenshot_ab_test | both | proposed | 21 days |
| title_ab_test | android | proposed | 14 days |
| short_description_ab_test | android | proposed | 14 days |
| screenshot_ab_test | both | proposed | 21 days |
<!-- CRO_END -->

## Paid Campaign Status

<!-- CAMPAIGNS_START -->
| Platform | Daily Budget | Status | Keywords |
|----------|:-----------:|--------|:--------:|
| apple_search_ads | $18.00 | paused | 45 |
| google_uac | $12.00 | ready_to_launch | 10 |
| reddit_ads | $0.00 | ready_to_launch | 0 |
| **Total** | **$30.00** | — | 55 |
<!-- CAMPAIGNS_END -->

## ASO Keywords

<!-- ASO_START -->
**iOS (current):** `bjj,hiit,sparring,wrestling,muaythai,tabata,crossfit,reaction,jiujitsu,wod,kickboxing`

**Last rotation:** —
**Performing:** — | **Replaced:** —
<!-- ASO_END -->

## Content Pipeline

<!-- CONTENT_START -->
| Metric | Value |
|--------|-------|
| Total Posts Published | 1 |
| Latest Post | The inspiration behind Random Tactical Timer |
| Published At | 2026-02-19T19:31:07+00:00 |
<!-- CONTENT_END -->

## Referral Campaigns

<!-- REFERRAL_START -->
| Channel | Items | Status |
|---------|:-----:|--------|
| Reddit Posts | 7 | draft |
| Product Hunt | 1 | draft |
| Blog Outreach | 3 | draft |
<!-- REFERRAL_END -->

## Charts

<!-- CHARTS_START -->
```mermaid
xychart-beta
    title "Downloads (30d rolling)"
    x-axis ["2026-07-07" , "2026-07-08" , "2026-07-08" , "2026-07-08" , "2026-07-08" , "2026-07-09" , "2026-07-09" , "2026-07-09" , "2026-07-09" , "2026-07-10" , "2026-07-10" , "2026-07-10" , "2026-07-10" , "2026-07-11"]
    y-axis "Downloads"
    line [43 , 43 , 43 , 41 , 41 , 40 , 39 , 39 , 39 , 39 , 40 , 40 , 39 , 39]
    line [96 , 96 , 96 , 96 , 96 , 95 , 95 , 92 , 52 , 48 , 48 , 48 , 42 , 36]
```

```mermaid
xychart-beta
    title "WQTU (7d)"
    x-axis ["2026-07-07" , "2026-07-08" , "2026-07-08" , "2026-07-08" , "2026-07-08" , "2026-07-09" , "2026-07-09" , "2026-07-09" , "2026-07-09" , "2026-07-10" , "2026-07-10" , "2026-07-10" , "2026-07-10" , "2026-07-11"]
    y-axis "Users"
    line [6 , 6 , 5 , 5 , 5 , 5 , 5 , 5 , 5 , 3 , 3 , 3 , 3 , 4]
```

```mermaid
pie title Daily Ad Budget Allocation ($)
    "Apple Search Ads" : 18.0
    "Google Uac" : 12.0
```

```mermaid
xychart-beta
    title "Keywords by Ad Group"
    x-axis ["Exact Match - High Intent" , "Search Match - Discovery" , "Competitor - Brand" , "UAC Themes"]
    y-axis "Count" 0 --> 25
    bar [15 , 20 , 10 , 10]
```

```mermaid
xychart-beta
    title "Referral Content Pieces"
    x-axis ["Reddit" , "Product Hunt" , "Blog Outreach"]
    y-axis "Items" 0 --> 9
    bar [7 , 1 , 3]
```
<!-- CHARTS_END -->

---

_Dashboard generated at: `2026-07-11T00:49:58+00:00`. Data refreshed daily by [`wiki-sync.yml`](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/wiki-sync.yml)._
