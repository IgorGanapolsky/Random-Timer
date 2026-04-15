# PostHog Analytics Contract

This project uses PostHog as the single source of truth for product analytics on iOS and Android.

## Runtime contract

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

Screens emitted on both platforms:

- `Timer Setup`
- `Active Timer`

## Properties (current)

- `timer_started`: `min_duration` (seconds), `max_duration` (seconds), `target_duration` (seconds)
- `settings_changed`: `min_duration` (seconds), `max_duration` (seconds), `sound_type`, `repeat_enabled`
- `alarm_triggered`: `target_duration` (seconds)
- `timer_completed`: see [timer_completed emission paths](#timer_completed-emission-paths) below (iOS and Android differ in **number of code paths** and optional `source` / `entitlement_level`)
- `paywall_view` / `paywall_viewed`: `entry_point`, **`paywall_experiment_variant`** (`monthly_default` \| `annual_default`) — reflects the in-app default plan arm driven by PostHog flag **`paywall_default_plan_annual`** (see `docs/OBSERVABILITY.md`).
- `paywall_offer_select`: `entry_point`, `product_id`, `plan`
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
