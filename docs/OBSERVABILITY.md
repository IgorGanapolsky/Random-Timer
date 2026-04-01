# Observability (Random Timer)

Last updated: 2026-04-01.

## Stack (what we use)

| Pillar | Tool | Purpose |
|--------|------|---------|
| Product analytics & funnels | PostHog | Events, persons, feature flags, **session replay** (sampled) |
| Crashes & ANRs | Firebase Crashlytics | Native stack traces, release health |
| App performance | Firebase Performance | Startup, screen rendering, HTTP (when applicable) |
| Remote config | Firebase Remote Config | Feature toggles coexisting with PostHog flags |
| Push (if enabled) | Firebase Messaging | Delivery; correlate with opens via analytics |

Stores (App Store Connect, Play Console) remain the **source of truth** for installs, revenue, and subscription state at the platform level.

## PostHog

- **Host:** `https://us.i.posthog.com` (US project).
- **Session replay:** Enabled in SDK when not an internal/debug build. Uses **screenshot mode** (SwiftUI / Compose). **Sampling:** Android `posthog` 3.8.2 has no client replay `sampleRate` on `PostHogConfig`; iOS `PostHogSessionReplayConfig` in the pinned SDK likewise has no `sampleRate` yet. Use **PostHog project session-replay settings** (and throttling: Android `debouncerDelayMs` 1000 ms, iOS `throttleDelay` 1 s) to control volume and cost.
- **Privacy:** Text and images masked in replay config; internal users excluded from replay.
- **Project setting:** In PostHog → Project settings, **Record user sessions** must be on for replays to appear.

### Key custom events (non-exhaustive)

Funnel and product metrics use events such as `timer_started`, `timer_completed`, `paywall_*`, onboarding steps, etc. North-star query (WQTU) uses `timer_completed` in HogQL.

## Firebase

- **Crashlytics:** Enabled when `google-services.json` / `GoogleService-Info.plist` are present (CI uses placeholders).
- **Performance:** Auto-instrumentation after dependency + plugin (Android) / SPM product (iOS). Custom traces can be added around cold start or paywall if needed.

## What we intentionally do not duplicate in-app

- Full **subscription ledger** (refunds, grace, family sharing) — use StoreKit 2 / Play Billing + server notifications if you need billing-grade truth.
- **Ad network attribution** — only if running ads; wire SKAdNetwork / Play Install Referrer as needed.
- **Synthetic monitoring** — optional (e.g. mobile RUM vendors); PostHog + Firebase cover most indie app needs.

## March 2026 practice checklist

- [x] Product analytics with identifiable persons and funnels (PostHog)
- [x] Session replay with masking and sampling (PostHog)
- [x] Crash + ANR reporting (Crashlytics)
- [x] Performance monitoring baseline (Firebase Performance)
- [x] Privacy: exclude internal users from replay; mask sensitive UI
- [ ] Periodically review PostHog **data retention** and **session replay** costs vs project sampling / throttle settings
