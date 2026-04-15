# Observability (Random Timer)

Last updated: 2026-04-15T13:52:51Z.

This document is the **source of truth** for what is **implemented in code** versus **optional / not built yet**. It replaces earlier wording that overstated Firebase Performance (iOS) and Remote Config.

---

## Implementation status (verified in repo)

| Capability | iOS | Android | Notes |
|------------|-----|---------|--------|
| **PostHog** (events, identify, funnels) | Yes | Yes | Initializes only when `POSTHOG_API_KEY` is non-empty at build/runtime wiring. |
| **Session replay** | Yes (SDK config) | Yes (SDK config) | Masking + throttling in code. **Internal** builds / simulators excluded on iOS; Android excludes emulators / debug similarly. **PostHog project** must have session recording enabled if you want replays in the UI. |
| **Firebase Crashlytics** | Yes | Yes | Release pipelines require real `GoogleService-Info.plist` / `google-services.json` (not committed). iOS debug/test builds can run without a local `GoogleService-Info.plist`; Firebase init is skipped when the plist is not bundled or when CI/test skip flags are set. |
| **Firebase Performance** | **No** (SPM product not linked) | **Yes** (Gradle plugin + `firebase-perf` dependency) | iOS auto-instrumentation was removed to stabilize CI; can be re-added later with the same CI skip pattern if validated. |
| **Firebase Remote Config** | **No** | **No** | Not referenced in app sources; use PostHog feature flags until/unless RC is added. |
| **PostHog feature flags (in-app)** | Yes | Yes | SDK `isFeatureEnabled` / `reloadFeatureFlags` (see `AnalyticsService` on each platform). Flags load at init with `preloadFeatureFlags` on Android; iOS reloads before paywall when needed. |
| **Firebase Cloud Messaging** | Not wired for product analytics | Not wired for product analytics | Listed only as a future option if you add push. |

**Firebase Analytics (Google Analytics)** in-app collection is **disabled on Android** (`setAnalyticsCollectionEnabled(false)`) so telemetry is not duplicated with PostHog.

---

## Stack intent (target architecture)

| Pillar | Tool | Purpose |
|--------|------|---------|
| Product analytics & funnels | PostHog | Events, persons, feature flags, session replay (controlled in PostHog + code) |
| Crashes | Firebase Crashlytics | Native crashes, release health |
| Performance (partial) | Firebase Performance | **Android** auto-instrumentation; **iOS** not currently in the binary |
| Remote toggles (today) | PostHog | Feature flags in SDK; Remote Config is **not** implemented |

App Store Connect and Google Play Console remain the **source of truth** for installs, revenue, and subscription state at the platform level.

---

## What you need to provide (CEO / operator checklist)

Nothing below should be pasted into chat or committed to git. Use Xcode, Gradle local files, GitHub Actions secrets, and consoles.

### 1. PostHog

- [ ] **Project API key** (PostHog → Project → API keys).
- [ ] **iOS:** Set `POSTHOG_API_KEY` for the Xcode configuration you ship (e.g. `.xcconfig` referenced by the project, or build settings). `Info.plist` uses `$(POSTHOG_API_KEY)`.
- [ ] **Android:** Set `POSTHOG_API_KEY` for release builds (environment variable when invoking Gradle, or `gradle.properties` on the **machine that builds releases**, never committed).
- [ ] In PostHog → **Project settings**, turn on **Record user sessions** if you want session replay; configure **sampling / volume** there (client-side sample rates are limited on pinned SDK versions—see comments in `AnalyticsService` on each platform).
- [ ] **Feature flags:** For each in-app experiment, create the matching flag in PostHog (see **In-app experiments** below). Example: boolean **`paywall_default_plan_annual`** controls default plan on the paywall; start at 0% rollout until QA sign-off.

### 2. Firebase (Crashlytics + Android Performance)

- [ ] **iOS release / local Firebase validation:** Download **`GoogleService-Info.plist`** from Firebase Console for `com.iganapolsky.randomtimer`, place at `native-ios/RandomTimer/GoogleService-Info.plist` (file is **gitignored**). Debug/test builds can compile without it, but Firebase/Crashlytics will stay disabled until the real plist is present.
- [ ] **Android:** **`google-services.json`** in `native-android/app/` for real builds (gitignored in normal dev; CI generates a dummy for builds/tests).
- [ ] Firebase Console: ensure **Crashlytics** is enabled for the app; **Performance Monitoring** enabled for Android (already depends on Gradle setup).

### 3. CI / automation (optional but recommended)

- [ ] If you want PostHog in **CI-built artifacts** (usually you do **not** for debug CI), add secrets to GitHub Actions and wire them the same way as local builds. **Default CI** is designed to run **without** real secrets, using placeholders where needed.

### 4. Nothing else required from you for “baseline” analytics

Once keys and plist/json are in place on **your** build machines and Firebase is configured, the **existing app code** initializes PostHog and Crashlytics. No further code changes are strictly required for that baseline.

---

## PostHog (reference)

- **Host:** `https://us.i.posthog.com` (US), as configured in code.
- **Privacy:** Text/images masked in replay; internal-like users excluded from replay where implemented.
- **North star:** WQTU uses `timer_completed` in PostHog (see `CLAUDE.md` / analytics docs).
- **Executive metrics (`marketing/data/executive_metrics.json`):** Generated by `scripts/executive_metrics_snapshot.py`. The PostHog section uses **pragmatic_live** HogQL: excludes debug/simulator/emulator, `is_internal`, and non–store-production `distribution_channel` values (TestFlight, Firebase/sideload Android installs, etc.). Legacy events without `distribution_channel` still count as `legacy`. To drop specific PostHog **person** rows (e.g. your own devices), set env **`POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS`** (comma-separated UUIDs) where the snapshot runs. There is no automatic “LLM bot” filter—use person exclusions if you identify automation IDs.

### In-app experiments (feature flags)

Create and manage flags in the PostHog project UI. Code uses the **same string** on iOS and Android.

| Flag key (PostHog) | Type | Behavior when **enabled** | Analytics |
|--------------------|------|-----------------------------|-----------|
| `paywall_default_plan_annual` | Boolean | Paywall opens with **annual** plan selected by default (treatment). When disabled / unavailable, default remains **monthly** (control). | `paywall_view` and `paywall_viewed` include property **`paywall_experiment_variant`**: `annual_default` or `monthly_default`. |

**Code references:** `PostHogExperimentKeys` + `PaywallExperimentVariants` (`native-android/.../analytics/PostHogExperimentKeys.kt`); `PostHogExperimentKeys` + `PaywallExperimentVariants` (`native-ios/.../Services/AnalyticsService.swift`). Paywall UI: `PaywallSheet` on each platform; Android resolves the flag in `Navigation.kt` before showing the sheet; iOS resolves in `TimerSetupScreen.presentPaywall`.

---

## Practice checklist (honest)

- [x] PostHog integrated (iOS + Android); events flow when API key is set.
- [x] Session replay configured in SDK (subject to PostHog project + non-internal users).
- [x] Crashlytics integrated (subject to real Firebase config files).
- [x] Android Firebase Performance dependency + plugin present.
- [ ] iOS Firebase Performance (optional follow-up).
- [ ] Firebase Remote Config (optional; PostHog flags cover many cases).
- [x] In-app PostHog feature flags used for paywall default-plan experiment (`paywall_default_plan_annual`); document new flags here when added.
- [ ] Periodically review PostHog **retention** and **replay** cost vs sampling.

---

## If something still looks “off”

1. Confirm **keys** and **plist/json** on the machine that produced the build.  
2. Confirm **PostHog** project has recording/sampling as you expect.  
3. Confirm **Firebase** Crashlytics is enabled and the app matches the Firebase app’s bundle id / package name.

This closes the documentation vs implementation gap; further “full” parity (iOS Performance, Remote Config) is incremental engineering, not a missing secret.
