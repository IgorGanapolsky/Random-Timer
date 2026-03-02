package com.iganapolsky.randomtimer.domain.model

import kotlin.time.Duration
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

/**
 * Sound type for the alarm.
 * Free tier: INTENSE, GENTLE
 * Pro tier: all 10 sounds
 */
enum class SoundType(
    val isPro: Boolean = false,
) {
    INTENSE,
    GENTLE,
    KLAXON(isPro = true),
    WHISTLE(isPro = true),
    BUZZER(isPro = true),
    GONG(isPro = true),
    AIRHORN(isPro = true),
    DRUM_ROLL(isPro = true),
    SIREN(isPro = true),
    BELL(isPro = true),
    ;

    companion object {
        val FREE = entries.filter { !it.isPro }
        val PRO = entries.filter { it.isPro }
    }
}

/**
 * Configuration for a random timer with all settings.
 */
data class TimerConfig(
    /** Minimum time in seconds */
    val minSeconds: Int,
    /** Maximum time in seconds */
    val maxSeconds: Int,
    /** How long the alarm should sound (seconds) */
    val alarmDuration: Int,
    /** Hide remaining time (random mode) */
    val hiddenMode: Boolean,
    /** Auto-repeat timer after completion */
    val repeatEnabled: Boolean,
    /** Alarm sound type */
    val soundType: SoundType,
    /** Volume level 0.0 - 1.0 */
    val volume: Float,
    /** Whether vibration is enabled */
    val vibrationEnabled: Boolean = false,
) {
    init {
        require(minSeconds >= 0) { "Minimum seconds cannot be negative" }
        require(maxSeconds >= minSeconds) { "Maximum seconds must be >= minimum seconds" }
        require(maxSeconds <= MAX_SECONDS_PRO) { "Maximum seconds cannot exceed $MAX_SECONDS_PRO" }
        require(alarmDuration > 0) { "Alarm duration must be positive" }
        require(volume in 0f..1f) { "Volume must be between 0 and 1" }
    }

    /** Minimum as Duration */
    val minDuration: Duration get() = minSeconds.seconds

    /** Maximum as Duration */
    val maxDuration: Duration get() = maxSeconds.seconds

    /** Alarm duration as Duration */
    val alarmDurationDuration: Duration get() = alarmDuration.seconds

    companion object {
        const val MAX_SECONDS_FREE = 300
        const val MAX_SECONDS_PRO = 3600

        val DEFAULT =
            TimerConfig(
                minSeconds = 0,
                maxSeconds = 60,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = false,
            )

        val ALARM_DURATION_OPTIONS = listOf(5, 10, 15, 30, 60)
    }
}

/**
 * Represents the current state of an active timer.
 */
data class TimerState(
    val config: TimerConfig,
    val targetDuration: Duration,
    val remainingDuration: Duration,
    val status: TimerStatus,
    val alarmTimeRemaining: Duration = Duration.ZERO,
    val startedAt: Long = System.currentTimeMillis(),
    val isAlarmSilenced: Boolean = false,
) {
    val progress: Float
        get() =
            if (targetDuration == Duration.ZERO) {
                0f
            } else {
                1f - (remainingDuration / targetDuration).toFloat()
            }

    val isComplete: Boolean
        get() = status == TimerStatus.COMPLETE

    val isAlarmActive: Boolean
        get() = status == TimerStatus.ALARM && alarmTimeRemaining > Duration.ZERO

    /** True when the alarm notification (with fullScreenIntent) should be shown.
     *  Returns false once the alarm has been silenced — prevents screen wake-up. */
    val shouldShowAlarmNotification: Boolean
        get() = status == TimerStatus.ALARM && !isAlarmSilenced

    /** Time remaining in seconds (for display) */
    val timeRemainingSeconds: Int
        get() = remainingDuration.inWholeSeconds.toInt()

    /** Total time in seconds */
    val totalTimeSeconds: Int
        get() = targetDuration.inWholeSeconds.toInt()
}

enum class TimerStatus {
    IDLE,
    RUNNING,
    PAUSED,
    WARNING, // < 30 seconds remaining
    DANGER, // < 10 seconds remaining
    COMPLETE, // Timer finished, transitioning to alarm
    ALARM, // Alarm is playing
}
