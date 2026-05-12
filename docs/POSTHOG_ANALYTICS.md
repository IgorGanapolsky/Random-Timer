# PostHog Analytics Contract

This project uses PostHog as the single source of truth for product analytics on iOS and Android.

## Runtime contract

**SDK and event definitions in this repository do not prove delivery to PostHog in production.** Treat “fully wired” as verified only after a live check (PostHog Live, HogQL, or an authenticated API query) shows recent events from production builds.

- iOS and Android emit the same event names and screen names.
- Both platforms identify users with a persistent anonymous `distinct_id`.
- Firebase Analytics collection is disabled on Android to avoid duplicated event streams.

## Event schema

Events emitted on both platforms:

- `timer_started`
- `timer_completed`
- `timer_paused`
- `timer_resumed`
- `timer_reset`
- `timer_stopped`
- `alarm_triggered`
- `alarm_dismissed`
- `settings_changed`
- `review_prompt_requested`
- `write_review_tapped`
- `paywall_view` (compatibility; same session as `paywall_viewed`)
- `paywall_viewed`
- `paywall_offer_select`
- `paywall_dismissed`
- `paywall_purchase_attempt`
- `paywall_purchase_result`
- `paywall_purchase_success`
- `paywall_purchase_fail_reason`
- `paywall_restore_result`
- `subscription_funnel_step` — canonical paywall → plan → purchase → trial funnel; use property **`funnel_step`** (`paywall_viewed` \| `paywall_plan_selected` \| `purchase_flow_launched` \| `purchase_succeeded` \| `trial_started`) with the same `entry_point` / `paywall_experiment_variant` / `paywall_value_framing_variant` context as other paywall events.

### Paywall funnel semantics (single definition of “attempt”)

Dashboards (`scripts/wqtu_dashboard.py`, `scripts/engagement_dashboard.py`, `scripts/paywall_conversion_report.py`) use **`paywall_purchase_attempt`** as **“attempt.”** That event has **one** meaning in this codebase:

| Step | Event | Meaning |
| --- | --- | --- |
| **Impression** | `paywall_viewed` (and legacy `paywall_view`) | User saw the paywall surface. |
| **Plan selection** | `paywall_offer_select` | User selected a plan card or tapped the primary paywall CTA. It includes `paywall_selection_source` (`plan_card` \| `primary_cta`). Automatic default-plan impressions must not emit this event. |
| **Attempt** | **`paywall_purchase_attempt`** | The app **started the platform purchase path** for a selected product: **iOS** — tracked at the beginning of `PaywallSheet`’s `purchase(productID:)` **immediately before** `proManager.purchase` (StoreKit). **Android** — tracked in `ProManager` **immediately before** `billingClient.launchBillingFlow` (Play Billing). |

So **“attempt” is not a generic CTA tap** elsewhere in the app; it is **“we are invoking / about to invoke native purchase for this product from the paywall.”** It is also **not** proof the Google / Apple sheet was seen (e.g. `launchBillingFlow` can return non-OK right after; StoreKit can fail early)—only that the **instrumented** start of that path ran.

**Ratios:**

- **view → attempt** = distinct users with `paywall_purchase_attempt` ÷ distinct users with `paywall_viewed` (same time window and live predicate as each script).
- **attempt → success** = distinct users with success signals (`paywall_purchase_success` or successful `paywall_purchase_result`) ÷ distinct users with `paywall_purchase_attempt`.

Do not equate **attempt** with **`subscription_funnel_step` / `purchase_flow_launched`** for reporting unless you explicitly align queries; both are emitted in the same user action on current code, but **HogQL funnels should anchor on `paywall_purchase_attempt`** for “attempt” to match this contract.

Screens emitted on both platforms:

- `Timer Setup`
- `Active Timer`

## Properties (current)

- `timer_started`: `min_duration` (seconds), `max_duration` (seconds), `target_duration` (seconds)
- `settings_changed`: `min_duration` (seconds), `max_duration` (seconds), `sound_type`, `repeat_enabled`
- `alarm_triggered`: `target_duration` (seconds)
- `timer_completed`: see [timer_completed emission paths](#timer_completed-emission-paths) below (iOS and Android differ in **number of code paths** and optional `source` / `entitlement_level`)
- `paywall_view` / `paywall_viewed`: `entry_point`, **`paywall_experiment_variant`** (`monthly_default` \| `annual_default`) — reflects the in-app default plan arm driven by PostHog flag **`paywall_default_plan_annual`** (see `docs/OBSERVABILITY.md`). Also **`paywall_value_framing_variant`** (`control` \| `outcomes_first`) from multivariate flag **`paywall_value_framing`** (copy experiment; default `control` until you add the flag in PostHog).
- `subscription_funnel_step`: `funnel_step`, plus `entry_point`, `paywall_experiment_variant`, `paywall_value_framing_variant`, and step-specific keys (e.g. `product_id`, `plan`, `paywall_selection_source`).
- `paywall_offer_select`: `entry_point`, `product_id`, `plan`, `paywall_selection_source`
- `paywall_*` (other): `entry_point` where applicable; purchase/result events also include `result` (iOS) or `success` / `response_code` (Android) as implemented per platform
- common context on all events: `platform`, `app_version`, `environment`, `build_audience`, `build_type`, `runtime_target`

## `timer_completed` emission paths

All `timer_completed` events include the [common context](#properties-current) above. Platform-specific payloads are listed per call site.

### iOS (`TimerManager.swift`)

There are **six** `AnalyticsService.shared.track(AnalyticsEvents.timerCompleted, …)` call sites:

| # | Trigger (plain language) | Properties (in addition to common context) |
|---|---------------------------|--------------------------------------------|
| 1 | User dismisses alarm (normal completion) | `target_duration`, `source` = `alarm_dismissed`, `entitlement_level` |
| 2 | App returns to foreground; alarm phase already ended; not repeating | `target_duration`, `source` = `foreground_return_alarm_expired`, `entitlement_level` |
| 3 | App returns to foreground; timer and full alarm window already elapsed while backgrounded; not repeating | `target_duration`, `source` = `foreground_return_timer_and_alarm_expired`, `entitlement_level` |
| 4 | Restored saved state was already `alarm` or `complete` (e.g. kill during alarm) — counted as completed | `target_duration`, `source` = `restore_alarm_or_complete`, `entitlement_level` |
| 5 | Timer ran to zero while app was not running; counted as completion | `target_duration`, `source` = `background_completion`, `entitlement_level` |
| 6 | Alarm countdown reaches zero in-app (`alarmTick`) | `target_duration`, `entitlement_level` (no `source` on this path) |

### Android

There are **two** production `analyticsService.track(AnalyticsEvents.TIMER_COMPLETED, …)` call sites:

| # | Location | Trigger (plain language) | Properties (in addition to common context) |
|---|----------|---------------------------|--------------------------------------------|
| 1 | `TimerForegroundService.dismissAlarm()` | User dismisses alarm from the service path | `target_duration`, `source` = `alarm_dismissed` (**no** `entitlement_level` here) |
| 2 | `TimerViewModel.onTimerStateObservedForAnalytics()` | Observed state transition **ALARM → COMPLETE** (e.g. alarm ring duration finished and UI shows complete) | `target_duration`, `entitlement_level` (**no** `source`) |

**Parity note:** iOS encodes more distinct `source` values for edge cases (foreground restore, persisted alarm/complete, background completion). Android does not emit `timer_completed` from those separate code paths today; product analytics comparing `source` across platforms should treat Android as sparse or filter to shared keys only.

**Maintenance:** `scripts/tests/test_mobile_analytics_parity.py` asserts the **count** of `timer_completed` emission sites in `TimerManager.swift` (6) and in the two Android files (2). If you add or remove a path, bump the test and this section together.

## Monetization surface parity (Android vs iOS)

Both apps ship the same **subscription paywall** (monthly + annual subscriptions, same product IDs / Play base plans) opened from **feature gates** on the timer setup surface. Current entry points are `range_gate`, `voice_gate`, `repeat_gate`, and `sound_arsenal_gate`, with `unknown` reserved as a fallback when a surface is unmapped. **Lifetime / one-time SKUs** may appear on iOS only where the sheet exposes a third plan; Android’s primary sheet is subscription-first. For revenue truth, use store ledgers; for funnel health, use `subscription_funnel_step` + `paywall_*` events with `platform` breakdown.

## Store review API counts (Play / App Store Connect)

Executive snapshots that read Play `reviews.list` or ASC `customerReviews` measure **narrow API slices** (e.g. 7-day commented reviews on Play, first page on ASC), **not** public lifetime totals — treat those fields as labeled proxies per `docs/OPERATIONAL_RELIABILITY.md`.

For a **labeled average star rating** over vendor API samples (read-only JSON + CI artifact), run **`python scripts/store_ratings_snapshot.py`** (see `.github/workflows/store-ratings-snapshot.yml`); each platform block includes `review_count_metric_id` and `semantics` text — not PostHog.

## Verification

Run parity and analytics-related tests.

**Important:** Run the Python command from the **repository root** (the directory that contains the `scripts/` folder). If you run it from `native-android/` or `native-ios/`, you will get `ModuleNotFoundError: No module named 'scripts'`.

```bash
# From repo root (directory that contains ./scripts/ — not native-android/)
python3 -m unittest scripts.tests.test_mobile_analytics_parity -v
cd native-android && ./gradlew testDebugUnitTest --tests "*TimerViewModelAnalyticsTest"
```

Run wider mobile verification before release:

```bash
cd native-android && ./gradlew testDebugUnitTest
cd native-ios && xcodebuild -scheme RandomTimer build
```
