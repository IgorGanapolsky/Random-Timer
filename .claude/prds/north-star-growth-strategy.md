---
title: "North Star Growth Strategy"
status: active
created: 2026-02-23
author: CTO (Claude)
---

# North Star Growth Strategy

## Executive Summary

Random Timer is a niche utility app with **5 downloads/month**, **4 DAU**, and a **24.6% open-to-completion rate**. This PRD defines our North Star metric, sets quarterly targets grounded in industry benchmarks, and lays out the execution plan to reach product-market fit within 2 quarters.

---

## 1. Current State (Baseline — Feb 2026)

| Metric | Value | Benchmark (Utility Apps) | Gap |
|--------|-------|--------------------------|-----|
| Downloads/month | 5 (iOS), 0 (Android) | — | Critical |
| DAU | 4 | — | Critical |
| WAU | 5 | — | Critical |
| MAU | 129 | — | Low |
| DAU/MAU ratio | 3.1% | 10-20% | Very poor |
| Day-1 retention | Unknown | 18.3% | Not measured |
| Day-7 retention | Unknown | 6.8% | Not measured |
| Day-30 retention | Unknown | 2.4-3.4% | Not measured |
| Open → Configured | 46.9% | — | Acceptable |
| Configured → Completed | 52.5% | — | Needs improvement |
| Open → Completed | 24.6% | — | Poor |
| UTM attribution | Empty | — | Fixed (PR #450) |
| Store listing conversion | Unknown | 25-27% avg | Not measured |

### Key Insight
The 129 MAU vs 4 DAU means users install, try once, and don't return. This is a **retention problem first**, distribution problem second. Fixing the leaky bucket before pouring more water in.

---

## 2. North Star Metric

### **Weekly Completed Timer Sessions (WCTS)**

**Definition:** Number of timer sessions that reach the COMPLETE state (alarm finishes naturally) per calendar week, across all users and platforms.

**Why this metric:**
- Measures actual value delivery (user got the random timing they wanted)
- Upstream of retention (users who complete timers come back)
- Upstream of reviews (review prompt triggers after 3 completions)
- Upstream of word-of-mouth (satisfied users share)
- Not vanity (downloads, installs, opens are vanity without completions)

**Current baseline:** ~32 total first completions in 30 days = ~8 WCTS (estimated)

**How to measure:** PostHog query — `COUNT(timer_completed)` grouped by `toStartOfWeek(timestamp)`.

### Supporting Metrics (Input Metrics)

| Input Metric | Drives WCTS Via | Current | Target |
|--------------|-----------------|---------|--------|
| Weekly Active Completers (WAC) | More unique users completing | ~5 | 50 by Q3 |
| Completions Per Active User | Deeper engagement per user | ~1.3/week | 3/week |
| Day-1 Retention | Users returning after install | Unknown | >25% |
| Day-7 Retention | Habit formation | Unknown | >10% |
| Open → Completed Rate | Activation efficiency | 24.6% | >40% |
| Store Page → Install Rate | Top-of-funnel conversion | Unknown | >30% |

---

## 3. Quarterly Targets

### Q1 2026 (Mar-May): "Fix the Foundation"

**WCTS Target: 8 → 50** (6x growth)

Focus: Retention, onboarding, and analytics instrumentation.

| Initiative | Expected Impact | Effort |
|-----------|----------------|--------|
| First-run tutorial (3-screen intro) | +30% open→configured | 1 week |
| Smart defaults (10-30s for new users) | +15% configured→completed | 2 days |
| Retention analytics (D1/D7/D30 cohorts) | Visibility into churn | 3 days |
| Session depth tracking (dwell time, adjustments) | Understand setup friction | 2 days |
| Lower review prompt to 1st completion | +5x review prompt impressions | 1 day |
| Loop mode discovery (setup screen toggle + tooltip) | +20% repeat sessions | 2 days |
| ASO: screenshots (MVP 3 per platform) | +25-40% store conversion | 3 days |
| ASO: optimize iOS keywords | +10% search discovery | 1 day |
| ASO: create Android keywords | +15% Android discovery | 1 day |
| Daily reminder notification (opt-in) | +15% D7 retention | 3 days |

**Success criteria:**
- WCTS ≥ 50
- D1 retention ≥ 25%
- D7 retention ≥ 10%
- Open → Completed ≥ 35%
- Downloads/month ≥ 30

### Q2 2026 (Jun-Aug): "Find the Segment"

**WCTS Target: 50 → 200** (4x growth)

Focus: Identify winning user segment, double down on acquisition for that segment.

| Initiative | Expected Impact | Effort |
|-----------|----------------|--------|
| User segment tracking (fitness/classroom/meditation/productivity) | Identify best segment | 1 week |
| Segment-specific onboarding (preset configs per use case) | +20% activation per segment | 1 week |
| Content marketing with working UTM attribution | +50% organic installs | Ongoing |
| Micro-influencer outreach (fitness YouTubers, teachers) | +100 installs/month | 2 weeks |
| Streak/habit tracking ("X-day streak" badge) | +25% D30 retention | 1 week |
| Share results ("Just survived a 47s random timer!") | Viral loop | 3 days |
| A/B test store listing screenshots | +15% conversion lift | 1 week |
| Localize listings (top 5 markets) | +20% non-US installs | 1 week |

**Success criteria:**
- WCTS ≥ 200
- D30 retention ≥ 5%
- Downloads/month ≥ 150
- Identified primary user segment with >40% D7 retention
- Android downloads > 0

### Q3 2026 (Sep-Nov): "Scale What Works"

**WCTS Target: 200 → 1,000** (5x growth)

Focus: Scale the winning channel and segment. Consider monetization.

| Initiative | Expected Impact | Effort |
|-----------|----------------|--------|
| Paid acquisition experiment ($500 budget) | Validate CPI < $3 | 2 weeks |
| Pro tier (custom sounds, longer timers, history) | Revenue baseline | 2 weeks |
| Cross-promotion with complementary fitness apps | +200 installs/month | Ongoing |
| Widget (iOS/Android) for quick-start | +30% DAU from returners | 1 week |
| Apple Watch / Wear OS companion | New surface area | 2 weeks |

**Success criteria:**
- WCTS ≥ 1,000
- WAC ≥ 200
- MRR > $0 (if Pro tier shipped)
- CPI validated below $3

---

## 4. Competitive Landscape

### Niche Position

The "random timer" niche is **small but underserved**:
- Closest competitor ("Random Timer Generator"): ~42K total downloads, ~870/month
- Timer+ (general timer): 9M+ downloads
- Seconds (interval timer): 3M+ downloads

**Our differentiation:** "Train for chaos, not rhythm" — combat/tactical positioning is unique. No other timer app targets the stress inoculation / reaction training angle.

### Target Segments (Priority Order)

| Segment | Use Case | Engagement Potential | Acquisition Channel |
|---------|----------|---------------------|-------------------|
| **Fitness Trainers** | HIIT, boxing drills, reaction training | High (daily use) | YouTube, Instagram, fitness forums |
| **Teachers/Educators** | Classroom games, musical chairs, quiz timers | High (weekly use) | Teacher blogs, Pinterest, EdTech forums |
| **Meditators** | Random mindfulness bells | Medium (daily use) | Meditation subreddits, wellness blogs |
| **Party Game Players** | Hot potato, drinking games | Medium (sporadic) | TikTok, party game lists |
| **Productivity** | Random focus sprints | Low-Medium | Productivity subreddits |

**Initial focus: Fitness Trainers + Teachers** — highest engagement, clearest acquisition channels, willing to recommend tools.

---

## 5. Immediate Action Plan (Next 2 Weeks)

### Week 1: Instrumentation + ASO

| Day | Action | Owner |
|-----|--------|-------|
| Mon | Add D1/D7/D30 retention tracking (PostHog cohorts) | Dev |
| Mon | Add session depth analytics (dwell time, settings changes) | Dev |
| Tue | Optimize iOS keywords.txt (reaction timer, interval training focus) | Dev |
| Tue | Create Android keywords.txt | Dev |
| Wed | Create 3 MVP screenshots per platform (Figma/code screenshots) | Dev |
| Thu | Update store descriptions with CTAs and formatting | Dev |
| Fri | Deploy updated metadata via Fastlane | Dev |

### Week 2: Onboarding + First Retention Hook

| Day | Action | Owner |
|-----|--------|-------|
| Mon | Design 3-screen first-run tutorial (what, why, how) | Dev |
| Tue | Implement first-run tutorial (iOS + Android) | Dev |
| Wed | Smart defaults for new users (10-30s range) | Dev |
| Wed | Lower review prompt threshold (3 → 1 completion) | Dev |
| Thu | Add loop mode toggle to setup screen with tooltip | Dev |
| Fri | Ship both platforms, monitor analytics | Dev |

---

## 6. Measurement Dashboard

### Weekly Review (Every Monday)

```
NORTH STAR: Weekly Completed Timer Sessions (WCTS)
├── WAC (Weekly Active Completers)
│   ├── New Users Completing (activation)
│   └── Returning Users Completing (retention)
├── Completions Per User
│   ├── Loop usage rate
│   └── Sessions per visit
├── Funnel
│   ├── Store impressions → Install rate
│   ├── Install → First open
│   ├── First open → First configured
│   ├── First configured → First completed
│   └── First completed → Second session
└── Retention Cohorts
    ├── D1 retention
    ├── D7 retention
    └── D30 retention
```

### Monthly Deep-Dive (First Monday of Month)

- Segment breakdown (which user type has highest WCTS?)
- Channel attribution (which source drives best-retaining users?)
- Feature usage (loop, vibration, sound type, alarm duration)
- Abandonment analysis (where do timer_abandoned events cluster?)

### Quarterly Strategy Review

- Is the North Star still the right metric?
- Which segment is winning?
- Should we pivot positioning?
- Revenue readiness assessment

---

## 7. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Niche too small (random timer demand ceiling) | Medium | High | Expand to adjacent use cases (interval, Pomodoro) |
| Screenshots don't improve conversion | Low | Medium | A/B test variants; iterate monthly |
| Onboarding adds friction instead of removing it | Medium | Medium | Add skip option; measure open→configured before/after |
| Android remains at 0 downloads | High | Medium | Investigate Play Store indexing; manual ASO audit |
| No clear winning segment after Q2 | Medium | High | Broaden targeting; survey existing users |

---

## 8. Anti-Goals

- **Not optimizing for downloads.** Downloads without retention is vanity.
- **Not adding features for feature's sake.** Every feature must drive WCTS.
- **Not chasing paid acquisition yet.** Fix retention first (Q1), then scale (Q3).
- **Not building a subscription paywall yet.** Need PMF signals first (D7 > 10%, WCTS > 200).
- **Not expanding to new platforms (web, Watch).** Focus on iOS + Android mobile until Q3.

---

## 9. Definition of Product-Market Fit

We will declare initial product-market fit when:

1. **D7 retention > 15%** (above utility app average of 6.8%)
2. **WCTS > 500** sustained for 4 consecutive weeks
3. **At least one segment** shows D7 retention > 25%
4. **Organic growth rate > 10%** month-over-month (without paid)
5. **App Store rating ≥ 4.5** with > 50 reviews

At that point, we unlock paid acquisition and monetization experiments.

---

## Appendix A: Industry Benchmarks (Sources)

| Metric | Utility Apps | All Apps | Source |
|--------|-------------|----------|--------|
| D1 Retention | 18.3% | 25-26% | Adjust Global App Trends 2025 |
| D7 Retention | 6.8% | 10.7-12% | Adjust Global App Trends 2025 |
| D30 Retention | 2.4-3.4% | 5-6% | Adjust/AppsFlyer 2025 |
| DAU/MAU | 10-20% | 20% | Industry standard |
| Store → Install | 25-27% | 25-27% | Apple/Google benchmarks |
| CPI (Utility, iOS US) | $2.90 | $1.74 | Apple Search Ads benchmarks |
| Install → Active | ~4% | ~4% | Industry average |

## Appendix B: Keyword Strategy

### iOS keywords.txt (Recommended)

```
reaction timer,interval training,boxing timer,hiit timer,mma drills,tabata,combat training,random
```
(99 chars — within 100 limit)

### Android Target Keywords

```
reaction timer, interval training, boxing drills, hiit timer, mma workout timer
```

### Long-Tail Blog/SEO Keywords

- "random countdown timer for workouts"
- "musical chairs timer app"
- "boxing round timer random intervals"
- "stress inoculation training timer"
- "classroom random timer for teachers"
- "meditation bell random intervals"
