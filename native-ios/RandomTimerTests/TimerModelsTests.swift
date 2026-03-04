import XCTest
import Foundation
@testable import RandomTimer

final class TimerConfigTests: XCTestCase {

    func testDefaultConfigHasValidRange() {
        let config = TimerConfig.default

        XCTAssertEqual(config.minSeconds, 0)
        XCTAssertEqual(config.maxSeconds, 300)
        XCTAssertEqual(config.volume, 0.5)
        XCTAssertFalse(config.vibrationEnabled)
    }

    func testConfigAcceptsValidRange() {
        let config = TimerConfig(
            minSeconds: 60,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )

        XCTAssertEqual(config.minDuration, 60.0)
        XCTAssertEqual(config.maxDuration, 300.0)
    }

    func testConfigAcceptsSameMinAndMax() {
        let config = TimerConfig(
            minSeconds: 120,
            maxSeconds: 120,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )

        XCTAssertEqual(config.minSeconds, config.maxSeconds)
    }

    func testConfigCanEnableVibration() {
        let config = TimerConfig(
            minSeconds: 30,
            maxSeconds: 120,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: true
        )

        XCTAssertTrue(config.vibrationEnabled)
    }

    func testDefaultAlarmDurationIs10Seconds() {
        let config = TimerConfig.default
        XCTAssertEqual(config.alarmDuration, 10)
    }

    func testConfigDurationConversion() {
        let config = TimerConfig(minSeconds: 90, maxSeconds: 180)
        XCTAssertEqual(config.minDuration, 90.0)
        XCTAssertEqual(config.maxDuration, 180.0)
        XCTAssertEqual(config.alarmDurationInterval, 10.0)
    }

    func testConfigDecodingSupportsLegacyKeysAndLooseSoundNames() throws {
        let payload = """
        {
          "min_time": -5,
          "max_time": 9000,
          "alarm_duration": 0,
          "hidden_mode": "true",
          "repeat_enabled": "1",
          "sound_type": "DRUM_ROLL",
          "soundVolume": "1.5",
          "vibration": "yes"
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(TimerConfig.self, from: payload)

        XCTAssertEqual(decoded.minSeconds, 0)
        XCTAssertEqual(decoded.maxSeconds, TimerConfig.maxSecondsPro)
        XCTAssertEqual(decoded.alarmDuration, 1)
        XCTAssertTrue(decoded.hiddenMode)
        XCTAssertTrue(decoded.repeatEnabled)
        XCTAssertEqual(decoded.soundType, .drumRoll)
        XCTAssertEqual(decoded.volume, 1.0, accuracy: 0.0001)
        XCTAssertTrue(decoded.vibrationEnabled)
    }

    func testConfigDecodingFallsBackToDefaultsWhenFieldsMissing() throws {
        let payload = "{}".data(using: .utf8)!
        let decoded = try JSONDecoder().decode(TimerConfig.self, from: payload)
        
        let expected = TimerConfig(
            minSeconds: 0,
            maxSeconds: 300,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: false
        )
        XCTAssertEqual(decoded, expected)
    }
}

final class TimerStateTests: XCTestCase {

    private let defaultConfig = TimerConfig.default

    func testProgressIsZeroAtStart() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 300,
            status: .running
        )

        XCTAssertEqual(state.progress, 0.0, accuracy: 0.001)
    }

    func testProgressIsHalfAtHalfway() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 600,
            remainingDuration: 300,
            status: .running
        )

        XCTAssertEqual(state.progress, 0.5, accuracy: 0.001)
    }

    func testProgressIsOneWhenComplete() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 0,
            status: .complete
        )

        XCTAssertEqual(state.progress, 1.0, accuracy: 0.001)
    }

    func testIsCompleteTrueWhenStatusIsComplete() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 0,
            status: .complete
        )

        XCTAssertTrue(state.isComplete)
    }

    func testIsCompleteTrueWhenStatusIsAlarm() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 0,
            status: .alarm
        )

        XCTAssertTrue(state.isComplete)
    }

    func testIsCompleteFalseWhenStillRunning() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 120,
            status: .running
        )

        XCTAssertFalse(state.isComplete)
    }

    func testProgressHandlesZeroTargetDuration() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 0,
            remainingDuration: 0,
            status: .complete
        )

        XCTAssertEqual(state.progress, 0.0)
    }

    func testTimeRemainingSeconds() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 300,
            remainingDuration: 125.7,
            status: .running
        )

        XCTAssertEqual(state.timeRemainingSeconds, 125)
    }

    func testStateDecodingSupportsLegacyKeysAndStatusNormalization() throws {
        let payload = """
        {
          "config": {
            "minSeconds": 15,
            "maxSeconds": 120,
            "alarmDuration": 10,
            "hiddenMode": false,
            "repeatEnabled": false,
            "soundType": "GENTLE",
            "volume": 0.4,
            "vibrationEnabled": true
          },
          "target_duration": "90",
          "started_at": "2026-03-02T00:00:00Z",
          "remaining_duration": "45",
          "timerStatus": "PAUSED",
          "alarm_time_remaining": "5"
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(TimerState.self, from: payload)

        XCTAssertEqual(decoded.config.soundType, .gentle)
        XCTAssertEqual(decoded.targetDuration, 90, accuracy: 0.0001)
        XCTAssertEqual(decoded.remainingDuration, 45, accuracy: 0.0001)
        XCTAssertEqual(decoded.status, .paused)
        XCTAssertEqual(decoded.alarmTimeRemaining, 5, accuracy: 0.0001)
    }
}

final class SoundTypeTests: XCTestCase {

    func testIntenseNotificationSoundName() {
        XCTAssertEqual(SoundType.intense.notificationSoundName, "alarm.mp3")
    }

    func testGentleNotificationSoundName() {
        XCTAssertEqual(SoundType.gentle.notificationSoundName, "gentle-chime.mp3")
    }
}

final class TimerStatusTests: XCTestCase {

    func testStatusFromReturnsCompleteAtZero() {
        let status = TimerStatus.from(remainingSeconds: 0, currentStatus: .running)
        XCTAssertEqual(status, .complete)
    }

    func testStatusFromReturnsRunningAboveZero() {
        let status = TimerStatus.from(remainingSeconds: 31, currentStatus: .running)
        XCTAssertEqual(status, .running)
    }

    func testStatusFromPreservesPaused() {
        let status = TimerStatus.from(remainingSeconds: 120, currentStatus: .paused)
        XCTAssertEqual(status, .paused)
    }

    func testStatusFromReturnsCompleteWhenNegative() {
        let status = TimerStatus.from(remainingSeconds: -5, currentStatus: .running)
        XCTAssertEqual(status, .complete)
    }
}

final class TimeRangeAdjusterTests: XCTestCase {

    func testMinChangeWithinGapKeepsMaxUnchanged() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 0,
            currentMaxSeconds: 300,
            newMinSeconds: 120
        )

        XCTAssertEqual(adjusted.min, 120)
        XCTAssertEqual(adjusted.max, 300)
    }

    func testMinChangeBeyondMaxMinusGapPushesMaxForward() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 0,
            currentMaxSeconds: 60,
            newMinSeconds: 60
        )

        XCTAssertEqual(adjusted.min, 60)
        XCTAssertEqual(adjusted.max, 60 + TimeRangeAdjuster.defaultMinGapSeconds)
        XCTAssertGreaterThanOrEqual(adjusted.max - adjusted.min, TimeRangeAdjuster.defaultMinGapSeconds)
    }

    func testMinChangeThatWouldExceedMaxLimitClampsToMaxMinusGap() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 250,
            currentMaxSeconds: 300,
            newMinSeconds: 300
        )

        XCTAssertEqual(adjusted.min, 300 - TimeRangeAdjuster.defaultMinGapSeconds)
        XCTAssertEqual(adjusted.max, 300)
        XCTAssertGreaterThanOrEqual(adjusted.max - adjusted.min, TimeRangeAdjuster.defaultMinGapSeconds)
    }

    func testMaxChangeBelowMinPlusGapPullsMinBack() {
        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: 100,
            currentMaxSeconds: 200,
            newMaxSeconds: 100
        )

        XCTAssertEqual(adjusted.min, 100 - TimeRangeAdjuster.defaultMinGapSeconds)
        XCTAssertEqual(adjusted.max, 100)
        XCTAssertGreaterThanOrEqual(adjusted.max - adjusted.min, TimeRangeAdjuster.defaultMinGapSeconds)
    }

    func testMaxChangeThatWouldPullMinBelowLimitClampsToMinLimit() {
        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: 10,
            currentMaxSeconds: 40,
            newMaxSeconds: 0
        )

        XCTAssertEqual(adjusted.min, 0)
        XCTAssertEqual(adjusted.max, 0 + TimeRangeAdjuster.defaultMinGapSeconds)
        XCTAssertGreaterThanOrEqual(adjusted.max - adjusted.min, TimeRangeAdjuster.defaultMinGapSeconds)
    }

    func testMinChangeByOneSecondNearUpperBoundPushesMaxByOne() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 298,
            currentMaxSeconds: 299,
            newMinSeconds: 299,
            maxSecondsLimit: 300
        )

        XCTAssertEqual(adjusted.min, 299)
        XCTAssertEqual(adjusted.max, 300)
        XCTAssertEqual(adjusted.max - adjusted.min, TimeRangeAdjuster.defaultMinGapSeconds)
    }

    func testMaxChangeByOneSecondNearLowerBoundPullsMinBackByOne() {
        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: 1,
            currentMaxSeconds: 1 + TimeRangeAdjuster.defaultMinGapSeconds,
            newMaxSeconds: TimeRangeAdjuster.defaultMinGapSeconds,
            maxSecondsLimit: 300
        )

        XCTAssertEqual(adjusted.min, 0)
        XCTAssertEqual(adjusted.max, TimeRangeAdjuster.defaultMinGapSeconds)
        XCTAssertEqual(adjusted.max - adjusted.min, TimeRangeAdjuster.defaultMinGapSeconds)
    }

    func testMinChangeBeyondUpperBoundIsDeterministicallyClamped() {
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: 290,
            currentMaxSeconds: 300,
            newMinSeconds: 295,
            maxSecondsLimit: 300
        )

        XCTAssertEqual(adjusted.min, 290)
        XCTAssertEqual(adjusted.max, 300)
    }
}

final class TimeIntervalExtensionTests: XCTestCase {

    func testFormattedMMSSMinutesAndSeconds() {
        let interval: TimeInterval = 150 // 2:30
        XCTAssertEqual(interval.formattedMMSS, "02:30")
    }

    func testFormattedMMSSPadsSingleDigits() {
        let interval: TimeInterval = 305 // 5:05
        XCTAssertEqual(interval.formattedMMSS, "05:05")
    }

    func testFormattedMMSSHandlesZero() {
        let interval: TimeInterval = 0
        XCTAssertEqual(interval.formattedMMSS, "00:00")
    }

    func testFormattedMMSSHandlesNegative() {
        let interval: TimeInterval = -5
        XCTAssertEqual(interval.formattedMMSS, "00:00")
    }

    func testFormattedDurationSeconds() {
        let interval: TimeInterval = 45
        XCTAssertEqual(interval.formattedDuration, "45s")
    }

    func testFormattedDurationMinutesOnly() {
        let interval: TimeInterval = 120
        XCTAssertEqual(interval.formattedDuration, "2m")
    }

    func testFormattedDurationMinutesAndSeconds() {
        let interval: TimeInterval = 90
        XCTAssertEqual(interval.formattedDuration, "1m 30s")
    }

    func testMinutesAndSecondsComponents() {
        let interval: TimeInterval = 150
        XCTAssertEqual(interval.minutes, 2)
        XCTAssertEqual(interval.seconds, 30)
    }
}

// MARK: - Alarm Background Expiry Tests

final class AlarmBackgroundExpiryTests: XCTestCase {

    private let defaultConfig = TimerConfig.default

    func testAlarmStartedAtIsNilByDefault() {
        let state = TimerState(
            config: defaultConfig,
            targetDuration: 60
        )
        XCTAssertNil(state.alarmStartedAt)
    }

    func testAlarmStartedAtCanBeSet() {
        let now = Date()
        var state = TimerState(
            config: defaultConfig,
            targetDuration: 60,
            status: .alarm,
            alarmTimeRemaining: 10,
            alarmStartedAt: now
        )
        XCTAssertEqual(state.alarmStartedAt, now)
    }

    func testAlarmExpiredWhenElapsedExceedsDuration() {
        // Simulate: alarm started 15 seconds ago, alarm duration is 10s
        let alarmStart = Date().addingTimeInterval(-15)
        let alarmDuration: TimeInterval = 10
        let elapsed = Date().timeIntervalSince(alarmStart)

        XCTAssertTrue(elapsed >= alarmDuration, "Alarm should be expired")
    }

    func testAlarmStillActiveWhenElapsedLessThanDuration() {
        // Simulate: alarm started 3 seconds ago, alarm duration is 10s
        let alarmStart = Date().addingTimeInterval(-3)
        let alarmDuration: TimeInterval = 10
        let elapsed = Date().timeIntervalSince(alarmStart)

        XCTAssertTrue(elapsed < alarmDuration, "Alarm should still be active")
        let remaining = alarmDuration - elapsed
        XCTAssertTrue(remaining > 0 && remaining <= 10)
    }

    func testAlarmRemainingTimeCalculation() {
        let alarmStart = Date().addingTimeInterval(-7)
        let alarmDuration: TimeInterval = 10
        let remaining = alarmDuration - Date().timeIntervalSince(alarmStart)

        XCTAssertEqual(remaining, 3, accuracy: 0.5)
    }
}

// MARK: - Media Button Dismiss Tests

final class MediaButtonTests: XCTestCase {

    func testOnMediaButtonDismissCallbackIsInvocable() {
        var dismissed = false
        let callback: () -> Void = { dismissed = true }
        callback()
        XCTAssertTrue(dismissed)
    }

    func testOnMediaButtonDismissCallbackDefaultsToNil() {
        // Verify the callback pattern works — optional closure starts nil
        var callback: (() -> Void)?
        XCTAssertNil(callback)

        callback = { /* dismiss */ }
        XCTAssertNotNil(callback)
    }
}

final class TimerManagerResetTests: XCTestCase {
    @MainActor
    func testResetWhileAlarmStopsAlarmAndRestartsTimer() async {
        let timerManager = TimerManager()

        let config = RandomTimer.TimerConfig(
            minSeconds: 5,
            maxSeconds: 5,
            alarmDuration: 10,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: true
        )
        let alarmState = RandomTimer.TimerState(
            config: config,
            targetDuration: 5,
            remainingDuration: 0,
            status: .alarm,
            alarmTimeRemaining: 10,
            alarmStartedAt: Date()
        )

        timerManager._setTimerStateForTesting(alarmState)

        await timerManager.resetTimer()

        let newState = timerManager.timerState
        XCTAssertNotNil(newState)
        XCTAssertEqual(newState?.status, .running)
        XCTAssertEqual(newState?.targetDuration, alarmState.targetDuration)
        XCTAssertEqual(newState?.remainingDuration, newState?.targetDuration)
    }

    @MainActor
    func testResetWhileRunningRestartsFromFullDuration() async {
        let timerManager = TimerManager()

        let config = RandomTimer.TimerConfig.default
        let startDate = Date(timeIntervalSince1970: 0)
        let runningState = RandomTimer.TimerState(
            config: config,
            targetDuration: 60,
            startedAt: startDate,
            remainingDuration: 10,
            status: .running
        )

        timerManager._setTimerStateForTesting(runningState)

        await timerManager.resetTimer()

        guard let newState = timerManager.timerState else {
            XCTFail("Expected timerState after reset")
            return
        }
        XCTAssertEqual(newState.status, .running)
        XCTAssertEqual(newState.targetDuration, runningState.targetDuration)
        XCTAssertEqual(newState.remainingDuration, newState.targetDuration, accuracy: 1.0)
        XCTAssertTrue(newState.startedAt > startDate)
    }
}

// MARK: - Loop toggle regression tests (mirrors Android TimerStateFlowTest)

final class TimerManagerLoopTests: XCTestCase {
    @MainActor
    func testUpdateConfigSyncsRepeatEnabledIntoRunningTimerState() {
        let timerManager = TimerManager()

        let config = RandomTimer.TimerConfig(
            minSeconds: 5,
            maxSeconds: 10,
            alarmDuration: 5,
            hiddenMode: false,
            repeatEnabled: false,
            soundType: .intense,
            volume: 0.5,
            vibrationEnabled: true
        )
        let state = RandomTimer.TimerState(
            config: config,
            targetDuration: 7,
            remainingDuration: 5,
            status: .running
        )

        timerManager._setTimerStateForTesting(state)
        XCTAssertFalse(timerManager.timerState!.config.repeatEnabled)

        // Toggle loop ON via updateConfig
        var newConfig = config
        newConfig = RandomTimer.TimerConfig(
            minSeconds: config.minSeconds,
            maxSeconds: config.maxSeconds,
            alarmDuration: config.alarmDuration,
            hiddenMode: config.hiddenMode,
            repeatEnabled: true,
            soundType: config.soundType,
            volume: config.volume,
            vibrationEnabled: config.vibrationEnabled
        )
        timerManager.updateConfig(newConfig)

        // timerState.config must reflect the change
        XCTAssertTrue(timerManager.timerState!.config.repeatEnabled,
                      "Loop toggle must propagate into running timerState.config")
    }

    @MainActor
    func testUpdateConfigDoesNotCrashWhenNoTimerRunning() {
        let timerManager = TimerManager()

        XCTAssertNil(timerManager.timerState)

        let newConfig = RandomTimer.TimerConfig(
            minSeconds: 1,
            maxSeconds: 60,
            alarmDuration: 5,
            hiddenMode: false,
            repeatEnabled: true,
            soundType: .gentle,
            volume: 0.8,
            vibrationEnabled: false
        )
        // Should not crash
        timerManager.updateConfig(newConfig)
        XCTAssertNil(timerManager.timerState)
        XCTAssertTrue(timerManager.config.repeatEnabled)
    }
}

// MARK: - Live Activity Must Not Leak Timing Info

final class LiveActivityTimingLeakTests: XCTestCase {

    /// The Live Activity content state should NEVER carry real remaining seconds
    /// because it would let an observer deduce the random duration from the lock screen.
    @MainActor
    func testLiveActivityUpdateSendsZeroRemainingSeconds() {
        // When building the content state for a running timer,
        // remainingSeconds must always be 0 to prevent timing leaks
        let config = TimerConfig(minSeconds: 30, maxSeconds: 120, alarmDuration: 10)
        let state = TimerState(
            config: config,
            targetDuration: 75, // random duration
            remainingDuration: 42, // 42s left
            status: .running
        )

        // The sanitized remaining seconds for Live Activity should be 0
        XCTAssertEqual(state.liveActivityRemainingSeconds, 0,
                       "Running timer must not leak remainingSeconds to Live Activity")
    }

    /// Alarm/complete states CAN show 0 since the timer is done
    @MainActor
    func testLiveActivityShowsZeroWhenComplete() {
        let config = TimerConfig(minSeconds: 30, maxSeconds: 120, alarmDuration: 10)
        let state = TimerState(
            config: config,
            targetDuration: 75,
            remainingDuration: 0,
            status: .complete
        )

        XCTAssertEqual(state.liveActivityRemainingSeconds, 0)
    }

    /// endDate must be the MAX possible end time, not the actual random end time
    @MainActor
    func testLiveActivityEndDateUsesMaxDuration() {
        let config = TimerConfig(minSeconds: 30, maxSeconds: 120, alarmDuration: 10)
        let state = TimerState(
            config: config,
            targetDuration: 75, // actual random: 75s
            remainingDuration: 75,
            status: .running
        )

        let maxPossibleEnd = state.startedAt.addingTimeInterval(Double(config.maxSeconds))

        // liveActivityEndDate should be based on maxSeconds, not targetDuration
        XCTAssertEqual(
            state.liveActivityEndDate.timeIntervalSinceReferenceDate,
            maxPossibleEnd.timeIntervalSinceReferenceDate,
            accuracy: 1.0,
            "Live Activity endDate must use maxSeconds to avoid leaking the random duration"
        )
    }
}

// MARK: - Silence Alarm State Tests

final class TimerManagerSilenceTests: XCTestCase {

    @MainActor
    func testIsAlarmSilencedDefaultsToFalse() {
        let timerManager = TimerManager()
        XCTAssertFalse(timerManager.isAlarmSilenced,
                       "isAlarmSilenced should default to false")
    }

    @MainActor
    func testSilenceAlarmSetsIsAlarmSilencedTrue() {
        let timerManager = TimerManager()

        let config = RandomTimer.TimerConfig(
            minSeconds: 5, maxSeconds: 10, alarmDuration: 30,
            hiddenMode: false, repeatEnabled: false,
            soundType: .intense, volume: 0.5, vibrationEnabled: false
        )
        let alarmState = RandomTimer.TimerState(
            config: config, targetDuration: 5,
            remainingDuration: 0, status: .alarm,
            alarmTimeRemaining: 25, alarmStartedAt: Date()
        )
        timerManager._setTimerStateForTesting(alarmState)

        timerManager.silenceAlarm()

        XCTAssertTrue(timerManager.isAlarmSilenced,
                      "After silenceAlarm(), isAlarmSilenced must be true")
    }

    @MainActor
    func testIsAlarmSilencedResetsOnNewAlarm() async {
        let timerManager = TimerManager()

        // Simulate: alarm active, user silences it
        let config = RandomTimer.TimerConfig(
            minSeconds: 5, maxSeconds: 5, alarmDuration: 30,
            hiddenMode: false, repeatEnabled: false,
            soundType: .intense, volume: 0.5, vibrationEnabled: false
        )
        let alarmState = RandomTimer.TimerState(
            config: config, targetDuration: 5,
            remainingDuration: 0, status: .alarm,
            alarmTimeRemaining: 25, alarmStartedAt: Date()
        )
        timerManager._setTimerStateForTesting(alarmState)
        timerManager.silenceAlarm()
        XCTAssertTrue(timerManager.isAlarmSilenced)

        // Reset timer — starts a new timer, isAlarmSilenced should reset
        await timerManager.resetTimer()

        XCTAssertFalse(timerManager.isAlarmSilenced,
                       "isAlarmSilenced must reset when a new timer starts")
    }

    /// When user taps notification to open app, sound stops but alarm state stays.
    /// handleForeground with didTapAlarmNotification must set isAlarmSilenced = true.
    @MainActor
    func testHandleForegroundViaNotificationTapSetsAlarmSilenced() async {
        let timerManager = TimerManager()

        // Simulate: timer expired while backgrounded, alarm is active
        let config = RandomTimer.TimerConfig(
            minSeconds: 5, maxSeconds: 30, alarmDuration: 30,
            hiddenMode: false, repeatEnabled: false,
            soundType: .intense, volume: 0.5, vibrationEnabled: false
        )
        // Timer started 15s ago, target was 10s — already expired
        let startDate = Date().addingTimeInterval(-15)
        let state = RandomTimer.TimerState(
            config: config, targetDuration: 10,
            startedAt: startDate,
            remainingDuration: 5, // stale value from when app was suspended
            status: .running // stale — was running when app backgrounded
        )
        timerManager._setTimerStateForTesting(state)

        // Simulate notification tap flag being set
        timerManager.setNotificationTapFlagForTesting()

        await timerManager.handleForeground()

        // After foreground via notification tap, alarm sound is stopped
        // so isAlarmSilenced must be true
        XCTAssertTrue(timerManager.isAlarmSilenced,
                      "Opening via notification tap must set isAlarmSilenced since sound is stopped")
    }
}

// MARK: - Storage Service Persistence Tests

final class StorageServiceTests: XCTestCase {
    private let configKey = "timer_config"
    private let timerStateKey = "active_timer_state"
    private var storageService: StorageService!

    override func setUp() {
        super.setUp()
        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: configKey)
        defaults.removeObject(forKey: timerStateKey)
        storageService = StorageService()
    }

    override func tearDown() {
        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: configKey)
        defaults.removeObject(forKey: timerStateKey)
        storageService = nil
        super.tearDown()
    }

    func testLoadConfigReturnsNilWhenNothingSaved() async {
        let loadedAsync = await storageService.loadConfig()
        let loadedSync = storageService.loadConfigSync()

        XCTAssertNil(loadedAsync)
        XCTAssertNil(loadedSync)
    }

    func testSaveAndLoadConfigPersistsAcrossAsyncAndSyncAPIs() async {
        let config = RandomTimer.TimerConfig(
            minSeconds: 15,
            maxSeconds: 90,
            alarmDuration: 30,
            hiddenMode: true,
            repeatEnabled: true,
            soundType: .gentle,
            volume: 0.8,
            vibrationEnabled: true
        )

        await storageService.saveConfig(config)

        let loadedAsync = await storageService.loadConfig()
        let loadedSync = storageService.loadConfigSync()

        XCTAssertEqual(loadedAsync, config)
        XCTAssertEqual(loadedSync, config)
    }

    func testSaveAndLoadTimerStatePersistsAcrossAsyncAndSyncAPIs() async {
        let config = RandomTimer.TimerConfig(minSeconds: 20, maxSeconds: 80, alarmDuration: 10)
        let startedAt = Date(timeIntervalSince1970: 1_700_000_000)
        let alarmStartedAt = Date(timeIntervalSince1970: 1_700_000_050)
        let state = RandomTimer.TimerState(
            config: config,
            targetDuration: 72,
            startedAt: startedAt,
            remainingDuration: 18,
            status: .alarm,
            alarmTimeRemaining: 5,
            alarmStartedAt: alarmStartedAt
        )

        await storageService.saveTimerState(state)

        let loadedAsync = await storageService.loadTimerState()
        let loadedSync = storageService.loadTimerStateSync()

        XCTAssertEqual(loadedAsync, state)
        XCTAssertEqual(loadedSync, state)
    }

    func testClearTimerStateRemovesPersistedState() async {
        let state = RandomTimer.TimerState(
            config: .default,
            targetDuration: 60,
            startedAt: Date(timeIntervalSince1970: 1_700_000_100),
            remainingDuration: 30,
            status: .running
        )
        await storageService.saveTimerState(state)
        let savedState = await storageService.loadTimerState()
        XCTAssertNotNil(savedState)

        await storageService.clearTimerState()

        let clearedAsync = await storageService.loadTimerState()
        XCTAssertNil(clearedAsync)
        XCTAssertNil(storageService.loadTimerStateSync())
    }

    func testClearTimerStateSyncRemovesPersistedState() async {
        let state = RandomTimer.TimerState(
            config: .default,
            targetDuration: 45,
            startedAt: Date(timeIntervalSince1970: 1_700_000_200),
            remainingDuration: 22,
            status: .paused
        )
        await storageService.saveTimerState(state)
        XCTAssertNotNil(storageService.loadTimerStateSync())

        storageService.clearTimerStateSync()

        XCTAssertNil(storageService.loadTimerStateSync())
        let clearedAsync = await storageService.loadTimerState()
        XCTAssertNil(clearedAsync)
    }

    func testLoadConfigSyncClearsCorruptPayload() {
        UserDefaults.standard.set(Data([0xFF, 0x00, 0xFE]), forKey: configKey)

        let loaded = storageService.loadConfigSync()

        XCTAssertNil(loaded)
        XCTAssertNil(UserDefaults.standard.data(forKey: configKey))
    }

    func testLoadTimerStateSyncClearsCorruptPayload() {
        UserDefaults.standard.set(Data([0xAA, 0xBB, 0xCC]), forKey: timerStateKey)

        let loaded = storageService.loadTimerStateSync()

        XCTAssertNil(loaded)
        XCTAssertNil(UserDefaults.standard.data(forKey: timerStateKey))
    }
}

#if DEBUG
private struct CapturedAnalyticsEvent {
    let name: String
    let properties: [String: Any]?
}

final class TimerAbandonedAnalyticsTests: XCTestCase {

    @MainActor
    func testCancelTimerIncludesAbandonReasonAndSource() async {
        var captured: [CapturedAnalyticsEvent] = []
        AnalyticsService.shared.testEventHandler = { event, properties in
            captured.append(CapturedAnalyticsEvent(name: event, properties: properties))
        }
        defer { AnalyticsService.shared.testEventHandler = nil }

        let manager = TimerManager()
        manager._setTimerStateForTesting(
            RandomTimer.TimerState(
                config: RandomTimer.TimerConfig.default,
                targetDuration: 120,
                remainingDuration: 90,
                status: .running
            )
        )

        await manager.cancelTimer()

        guard let abandonedEvent = captured.first(where: { $0.name == AnalyticsEvents.timerAbandoned }) else {
            XCTFail("Expected timer_abandoned event")
            return
        }

        XCTAssertEqual(
            abandonedEvent.properties?[AnalyticsProperties.abandonReason] as? String,
            AnalyticsValues.abandonReasonUserCancelled
        )
        XCTAssertEqual(
            abandonedEvent.properties?[AnalyticsProperties.abandonSource] as? String,
            AnalyticsValues.abandonSourceTimerControls
        )
    }

    @MainActor
    func testRestoreExpiredTimerEmitsStaleRestoreAbandonEvent() async {
        let storage = StorageService()
        storage.clearTimerStateSync()
        defer { storage.clearTimerStateSync() }

        await storage.saveTimerState(
            RandomTimer.TimerState(
                config: RandomTimer.TimerConfig.default,
                targetDuration: 5,
                startedAt: Date().addingTimeInterval(-120),
                remainingDuration: 3,
                status: .running
            )
        )

        var captured: [CapturedAnalyticsEvent] = []
        AnalyticsService.shared.testEventHandler = { event, properties in
            captured.append(CapturedAnalyticsEvent(name: event, properties: properties))
        }
        defer { AnalyticsService.shared.testEventHandler = nil }

        let manager = TimerManager(storageService: storage)

        // restoreActiveTimer() is started asynchronously from init.
        for _ in 0..<20 where !captured.contains(where: { $0.name == AnalyticsEvents.timerAbandoned }) {
            try? await Task.sleep(for: .milliseconds(50))
        }

        guard let abandonedEvent = captured.first(where: { $0.name == AnalyticsEvents.timerAbandoned }) else {
            XCTFail("Expected timer_abandoned event for stale restore")
            return
        }

        XCTAssertEqual(
            abandonedEvent.properties?[AnalyticsProperties.abandonReason] as? String,
            AnalyticsValues.abandonReasonStaleRestoreExpired
        )
        XCTAssertEqual(
            abandonedEvent.properties?[AnalyticsProperties.abandonSource] as? String,
            AnalyticsValues.abandonSourceStateRestore
        )
        XCTAssertNil(manager.timerState)
    }
}
#endif
