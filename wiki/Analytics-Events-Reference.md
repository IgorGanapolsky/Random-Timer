# Analytics Events Reference

All events tracked via **PostHog** on both platforms. Firebase Analytics is explicitly disabled (`setAnalyticsCollectionEnabled(false)`).

## Event Catalog

| Event Name | Android Constant | iOS Constant | Trigger | Properties |
|-----------|-----------------|-------------|---------|-----------|
| `timer_started` | `TIMER_STARTED` | `timerStarted` | User starts a timer | `min_duration`, `max_duration`, `target_duration` |
| `timer_completed` | `TIMER_COMPLETED` | `timerCompleted` | Timer finishes naturally (ALARM → COMPLETE) | `target_duration` |
| `timer_paused` | `TIMER_PAUSED` | `timerPaused` | User pauses active timer | — |
| `timer_resumed` | `TIMER_RESUMED` | `timerResumed` | User resumes paused timer | — |
| `timer_reset` | `TIMER_RESET` | `timerReset` | User resets timer to setup | — |
| `timer_stopped` | `TIMER_STOPPED` | `timerStopped` | User cancels running timer | — |
| `alarm_triggered` | `ALARM_TRIGGERED` | `alarmTriggered` | Timer reaches zero, alarm fires | `target_duration` |
| `alarm_dismissed` | `ALARM_DISMISSED` | `alarmDismissed` | User dismisses alarm (tap or power button on iOS) | — |
| `settings_changed` | `SETTINGS_CHANGED` | `settingsChanged` | User modifies timer config | `min_duration`, `max_duration`, `sound_type`, `repeat_enabled` |
| `review_prompt_requested` | `REVIEW_PROMPT_REQUESTED` | `reviewPromptRequested` | In-app review dialog shown | — |
| `write_review_tapped` | `WRITE_REVIEW_TAPPED` | `writeReviewTapped` | User taps "Write Review" | — |

## Onboarding Funnel Events (PostHog queries only)

These events are queried by the attribution feedback script but fired implicitly by PostHog lifecycle tracking:

| Event | Description |
|-------|-------------|
| `first_open` | First app launch (PostHog lifecycle) |
| `first_timer_configured` | First `settings_changed` event for a user |
| `first_timer_completed` | First `timer_completed` event for a user |

## Screen Tracking

| Screen Name | Android Constant | iOS Constant | When |
|------------|-----------------|-------------|------|
| `Timer Setup` | `TIMER_SETUP` | `timerSetup` | User on setup screen |
| `Active Timer` | `ACTIVE_TIMER` | `activeTimer` | Timer running/alarm screen |

## SDK Configuration

| Setting | Value |
|---------|-------|
| Host | `https://us.i.posthog.com` |
| API Key | `BuildConfig.POSTHOG_API_KEY` / `Info.plist POSTHOG_API_KEY` |
| Lifecycle Events | `true` |
| Deep Links | `true` (Android) |
| Screen Views | `false` (manual tracking) |
| Distinct ID | `SharedPreferences` (Android) / `UserDefaults` (iOS) |

## Source Files

- **Android Service:** `native-android/.../analytics/AnalyticsService.kt`
- **Android ViewModel:** `native-android/.../ui/viewmodel/TimerViewModel.kt`
- **Android Navigation:** `native-android/.../ui/navigation/Navigation.kt`
- **Android Reviews:** `native-android/.../review/StoreReviewManager.kt`
- **iOS Service:** `native-ios/.../Services/AnalyticsService.swift`
- **iOS Timer Manager:** `native-ios/.../Services/TimerManager.swift`
- **iOS Screens:** `native-ios/.../UI/Screens/TimerSetupScreen.swift`, `ActiveTimerScreen.swift`
- **iOS Reviews:** `native-ios/.../Services/StoreReviewManager.swift`
