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
- common context on all events: `platform`, `app_version`, `environment`, `build_audience`, `build_type`, `runtime_target`

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
