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
| `timer_abandoned` | `TIMER_ABANDONED` | `timerAbandoned` | User cancels before countdown finishes | `target_duration`, `remaining_duration`, `status` |
| `timer_countdown_finished` | `TIMER_COUNTDOWN_FINISHED` | `timerCountdownFinished` | Countdown reaches zero (before alarm phase) | `target_duration` |
| `settings_changed` | `SETTINGS_CHANGED` | `settingsChanged` | User modifies timer config | `min_duration`, `max_duration`, `sound_type`, `repeat_enabled` |
| `review_prompt_requested` | `REVIEW_PROMPT_REQUESTED` | `reviewPromptRequested` | In-app review dialog shown | — |
| `write_review_tapped` | `WRITE_REVIEW_TAPPED` | `writeReviewTapped` | User taps "Write Review" | — |

## Paywall & monetization

| Event Name | Android Constant | iOS Constant | Trigger | Properties |
|-----------|-----------------|-------------|---------|-----------|
| `paywall_view` | `PAYWALL_VIEW` | `paywallView` | Paywall becomes visible (compatibility; paired with `paywall_viewed`) | `entry_point`, `paywall_experiment_variant` (`monthly_default` \| `annual_default`) |
| `paywall_viewed` | `PAYWALL_VIEWED` | `paywallViewed` | Same as `paywall_view` | `entry_point`, `paywall_experiment_variant` |
| `paywall_offer_select` | `PAYWALL_OFFER_SELECT` | `paywallOfferSelect` | User selects a plan (including default on open) | `entry_point`, `product_id`, `plan` |
| `paywall_dismissed` | `PAYWALL_DISMISSED` | `paywallDismissed` | User leaves paywall | `entry_point` |
| `paywall_purchase_attempt` | `PAYWALL_PURCHASE_ATTEMPT` | `paywallPurchaseAttempt` | User taps purchase CTA | `entry_point`, product / result fields per implementation |
| `paywall_purchase_result` | `PAYWALL_PURCHASE_RESULT` | `paywallPurchaseResult` | Purchase flow completes | `entry_point`, `result` / `success` (platform-specific) |
| `paywall_purchase_success` | `PAYWALL_PURCHASE_SUCCESS` | `paywallPurchaseSuccess` | Successful purchase | per `ProManager` / billing layer |
| `paywall_purchase_fail_reason` | `PAYWALL_PURCHASE_FAIL_REASON` | `paywallPurchaseFailReason` | Failed purchase (not user-cancel on iOS where omitted) | `reason`, `product_id`, `entry_point` |
| `paywall_restore_result` | `PAYWALL_RESTORE_RESULT` | `paywallRestoreResult` | Restore tapped | `entry_point`, `result` |
| `feature_gate_hit` | `FEATURE_GATE_HIT` | `featureGateHit` | Free user taps a Pro upgrade affordance | `feature` |

**PostHog feature flag (default plan):** Boolean flag key **`paywall_default_plan_annual`** (same string on iOS and Android). When enabled, the paywall opens with annual selected; `paywall_experiment_variant` on view events is `annual_default` vs `monthly_default`. See `docs/OBSERVABILITY.md`.

## Onboarding Funnel Events (PostHog queries only)

These events are emitted from app code (`AnalyticsService`); PostHog lifecycle auto-capture is disabled so payloads always include app context.

| Event | Description |
|-------|-------------|
| `first_open` | First app launch (one-shot flag in local storage + `track`) |
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
| Lifecycle Events | `false` (emitted manually from app code) |
| Deep Links | `true` (Android) |
| Screen Views | `false` (manual tracking) |
| Distinct ID | `SharedPreferences` (Android) / `UserDefaults` (iOS) |

## Source Files

- **Android Service:** `native-android/.../analytics/AnalyticsService.kt`, `PostHogExperimentKeys.kt`
- **Android ViewModel:** `native-android/.../ui/viewmodel/TimerViewModel.kt`
- **Android Navigation / Paywall:** `native-android/.../ui/navigation/Navigation.kt`, `PaywallSheet.kt`
- **Android Reviews:** `native-android/.../review/StoreReviewManager.kt`
- **iOS Service:** `native-ios/.../Services/AnalyticsService.swift`
- **iOS Timer Manager:** `native-ios/.../Services/TimerManager.swift`
- **iOS Screens:** `native-ios/.../UI/Screens/TimerSetupScreen.swift`, `PaywallSheet.swift`, `ActiveTimerScreen.swift`
- **iOS Reviews:** `native-ios/.../Services/StoreReviewManager.swift`
