# PostHog Analytics Contract

This project uses PostHog as the source of truth for in-app product analytics on iOS and Android.
It is not the source of truth for store installs, published reviews, or subscription ledger state.

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
- `paywall_viewed`
- `paywall_dismissed`
- `paywall_purchase_result`
- `paywall_restore_result`

Screens emitted on both platforms:

- `Timer Setup`
- `Active Timer`

## Properties (current)

- `timer_started`: `min_duration` (seconds), `max_duration` (seconds), `target_duration` (seconds)
- `settings_changed`: `min_duration` (seconds), `max_duration` (seconds), `sound_type`, `repeat_enabled`
- `alarm_triggered`: `target_duration` (seconds)
- `timer_completed`: `target_duration` (seconds) on Android, no properties on iOS
- `paywall_*`: `entry_point`; result events also include `result` (iOS) or `success`/`response_code` (Android)
- common context on all events: `platform`, `app_version`, `environment`, `build_audience`, `build_type`, `runtime_target`, `is_internal`

## Internal-build rule

- Developer-installed release builds must set `ANALYTICS_INTERNAL_BUILD=true` so they emit `is_internal=true`.
- Debug builds, simulators/emulators, and UI test sessions are already marked internal automatically.
- All product insights should filter out `is_internal=true` traffic via the same live predicate used by the metrics scripts.

## Verification

Run parity and analytics-related tests:

```bash
python3 -m unittest scripts.tests.test_mobile_analytics_parity
cd native-android && ./gradlew testDebugUnitTest --tests "*TimerViewModelAnalyticsTest"
```

Run wider mobile verification before release:

```bash
cd native-android && ./gradlew testDebugUnitTest
cd native-ios && xcodebuild -scheme RandomTimer build
```
