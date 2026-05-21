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
 * Voice gender preference for AI voice callouts.
 * MALE = marine drill sergeant persona.
 * FEMALE = female HIIT instructor persona.
 */
enum class VoiceGender {
    MALE,
    FEMALE,
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
    /** Whether to use the extended 60-minute range (Pro only) */
    val useExtendedRange: Boolean = false,
    /** Whether AI voice callouts are enabled (Pro only, off by default) */
    val voiceEnabled: Boolean = false,
    /** Voice gender preference: MALE (drill sergeant) or FEMALE (HIIT instructor) */
    val voiceGender: VoiceGender = VoiceGender.MALE,
    /** How many rounds to loop for (0 = infinite). Pro only feature. */
    val repeatRounds: Int = 0,
) {
    init {
        require(minSeconds >= 0) { "Minimum seconds cannot be negative" }
        require(maxSeconds >= minSeconds) { "Maximum seconds must be >= minimum seconds" }
        val maxAllowed = if (useExtendedRange) MAX_SECONDS_PRO else MAX_SECONDS_FREE
        require(maxSeconds <= maxAllowed) { "Maximum seconds cannot exceed $maxAllowed" }
        require(alarmDuration > 0) { "Alarm duration must be positive" }
        require(volume in 0f..1f) { "Volume must be between 0 and 1" }
        require(repeatRounds >= 0) { "Repeat rounds cannot be negative" }
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
                minSeconds = TimeRangeAdjuster.DEFAULT_MIN_SECONDS,
                maxSeconds = 30,
                alarmDuration = 10,
                hiddenMode = false,
                repeatEnabled = false,
                soundType = SoundType.INTENSE,
                volume = 0.5f,
                vibrationEnabled = false,
                useExtendedRange = false,
                voiceEnabled = false,
                voiceGender = VoiceGender.MALE,
                repeatRounds = 0,
            )

        val ALARM_DURATION_OPTIONS = listOf(5, 10, 15, 30, 60)

        /** Min seconds for first-session activation preset (mirrors iOS TimerModels). */
        const val ACTIVATION_FIRST_RUN_MIN_SECONDS = TimeRangeAdjuster.DEFAULT_MIN_SECONDS

        /** Max seconds for first-session activation preset (mirrors iOS TimerModels). */
        const val ACTIVATION_FIRST_RUN_MAX_SECONDS = 30
    }
}

data class RangeToggleProfiles(
    val freeMinSeconds: Int,
    val freeMaxSeconds: Int,
    val extendedMinSeconds: Int,
    val extendedMaxSeconds: Int,
)

data class RangeToggleResult(
    val config: TimerConfig,
    val profiles: RangeToggleProfiles,
)

fun sanitizedStoredRange(
    minSeconds: Int,
    maxSeconds: Int,
    maxSecondsLimit: Int,
): Pair<Int, Int> {
    val clampedMax = maxSeconds.coerceIn(TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS, maxSecondsLimit)
    val clampedMin =
        minSeconds.coerceIn(
            TimeRangeAdjuster.DEFAULT_MIN_SECONDS,
            clampedMax - TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS,
        )
    return TimeRangeAdjuster.adjustForMaxChange(
        currentMinSeconds = clampedMin,
        currentMaxSeconds = clampedMax,
        newMaxSeconds = clampedMax,
        maxSecondsLimit = maxSecondsLimit,
    )
}

fun toggleExtendedRange(
    current: TimerConfig,
    profiles: RangeToggleProfiles,
): RangeToggleResult =
    if (current.useExtendedRange) {
        val nextProfiles =
            profiles.copy(
                extendedMinSeconds = current.minSeconds,
                extendedMaxSeconds = current.maxSeconds,
            )
        val restoredFree =
            sanitizedStoredRange(
                minSeconds = profiles.freeMinSeconds,
                maxSeconds = profiles.freeMaxSeconds,
                maxSecondsLimit = TimerConfig.MAX_SECONDS_FREE,
            )
        RangeToggleResult(
            config =
                current.copy(
                    minSeconds = restoredFree.first,
                    maxSeconds = restoredFree.second,
                    useExtendedRange = false,
                ),
            profiles = nextProfiles,
        )
    } else {
        val nextProfiles =
            profiles.copy(
                freeMinSeconds = current.minSeconds,
                freeMaxSeconds = current.maxSeconds,
            )
        val restoredExtended =
            sanitizedStoredRange(
                minSeconds = profiles.extendedMinSeconds,
                maxSeconds = profiles.extendedMaxSeconds,
                maxSecondsLimit = TimerConfig.MAX_SECONDS_PRO,
            )
        RangeToggleResult(
            config =
                current.copy(
                    minSeconds = restoredExtended.first,
                    maxSeconds = restoredExtended.second,
                    useExtendedRange = true,
                ),
            profiles = nextProfiles,
        )
    }

/**
 * Migrates legacy canonical defaults (30–120s) to activation-first 5–30s on the free range.
 * New installs already use [TimerConfig.DEFAULT]. Returns null when no migration applies.
 * One-shot application is enforced by the caller (e.g. `activation_first_run_range_nudge_applied`).
 */
fun activationLegacyRangePresetIfEligible(current: TimerConfig): TimerConfig? {
    if (current.useExtendedRange) return null
    if (current.minSeconds != 30 || current.maxSeconds != 120) {
        return null
    }
    return current.copy(
        minSeconds = TimerConfig.ACTIVATION_FIRST_RUN_MIN_SECONDS,
        maxSeconds = TimerConfig.ACTIVATION_FIRST_RUN_MAX_SECONDS,
    )
}

data class TrainingPreset(
    val id: String,
    val title: String,
    val subtitle: String,
    val minSeconds: Int,
    val maxSeconds: Int,
    val alarmDuration: Int,
    val repeatEnabled: Boolean,
    val soundType: SoundType,
    val vibrationEnabled: Boolean,
) {
    fun applyTo(config: TimerConfig): TimerConfig =
        config.copy(
            minSeconds = minSeconds,
            maxSeconds = maxSeconds,
            alarmDuration = alarmDuration,
            hiddenMode = false,
            repeatEnabled = repeatEnabled,
            soundType = soundType,
            vibrationEnabled = vibrationEnabled,
            useExtendedRange = false,
        )

    companion object {
        val CompetitionWarmup =
            TrainingPreset(
                id = "competition_warmup",
                title = "Competition Warmup",
                subtitle = "Reactive mat-ready cues for the 30 minutes before first call.",
                minSeconds = 20,
                maxSeconds = 90,
                alarmDuration = 5,
                repeatEnabled = true,
                soundType = SoundType.INTENSE,
                vibrationEnabled = true,
            )

        val ALL = listOf(CompetitionWarmup)
    }
}

data class RangeToggleProfiles(
    val freeMinSeconds: Int,
    val freeMaxSeconds: Int,
    val extendedMinSeconds: Int,
    val extendedMaxSeconds: Int,
)

data class RangeToggleResult(
    val config: TimerConfig,
    val profiles: RangeToggleProfiles,
)

fun sanitizedStoredRange(
    minSeconds: Int,
    maxSeconds: Int,
    maxSecondsLimit: Int,
): Pair<Int, Int> {
    val clampedMax = maxSeconds.coerceIn(TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS, maxSecondsLimit)
    val clampedMin =
        minSeconds.coerceIn(
            TimeRangeAdjuster.DEFAULT_MIN_SECONDS,
            clampedMax - TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS,
        )
    return TimeRangeAdjuster.adjustForMaxChange(
        currentMinSeconds = clampedMin,
        currentMaxSeconds = clampedMax,
        newMaxSeconds = clampedMax,
        maxSecondsLimit = maxSecondsLimit,
    )
}

fun toggleExtendedRange(
    current: TimerConfig,
    profiles: RangeToggleProfiles,
): RangeToggleResult =
    if (current.useExtendedRange) {
        val nextProfiles =
            profiles.copy(
                extendedMinSeconds = current.minSeconds,
                extendedMaxSeconds = current.maxSeconds,
            )
        val restoredFree =
            sanitizedStoredRange(
                minSeconds = profiles.freeMinSeconds,
                maxSeconds = profiles.freeMaxSeconds,
                maxSecondsLimit = TimerConfig.MAX_SECONDS_FREE,
            )
        RangeToggleResult(
            config =
                current.copy(
                    minSeconds = restoredFree.first,
                    maxSeconds = restoredFree.second,
                    useExtendedRange = false,
                ),
            profiles = nextProfiles,
        )
    } else {
        val nextProfiles =
            profiles.copy(
                freeMinSeconds = current.minSeconds,
                freeMaxSeconds = current.maxSeconds,
            )
        val restoredExtended =
            sanitizedStoredRange(
                minSeconds = profiles.extendedMinSeconds,
                maxSeconds = profiles.extendedMaxSeconds,
                maxSecondsLimit = TimerConfig.MAX_SECONDS_PRO,
            )
        RangeToggleResult(
            config =
                current.copy(
                    minSeconds = restoredExtended.first,
                    maxSeconds = restoredExtended.second,
                    useExtendedRange = true,
                ),
            profiles = nextProfiles,
        )
    }

/**
 * Migrates legacy canonical defaults (30–120s) to activation-first 5–30s for users who have
 * not completed their first timer. New installs already use [TimerConfig.DEFAULT]; returns null
 * when no migration applies.
 */
fun activationPresetForFirstCompletionIfEligible(
    hasCompletedFirstTimer: Boolean,
    current: TimerConfig,
): TimerConfig? {
    if (hasCompletedFirstTimer) return null
    if (current.useExtendedRange) return null
    if (current.minSeconds != 30 || current.maxSeconds != 120) {
        return null
    }
    return current.copy(
        minSeconds = TimerConfig.ACTIVATION_FIRST_RUN_MIN_SECONDS,
        maxSeconds = TimerConfig.ACTIVATION_FIRST_RUN_MAX_SECONDS,
    )
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
    val roundCount: Int = 1,
) {
    /**
     * Unpredictable progress based on maxSeconds (not targetDuration).
     * This prevents the user from deducing the random target by watching the arc.
     * Capped at 0.98 so the arc never visually "completes" before the alarm fires.
     * Matches iOS `unpredictableProgress` in TimerModels.swift.
     */
    val progress: Float
        get() {
            val maxDuration = config.maxDuration
            if (maxDuration == Duration.ZERO) return 0f
            val elapsed = targetDuration - remainingDuration
            return (elapsed / maxDuration).toFloat().coerceIn(0f, 0.98f)
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

enum class EntitlementLevel {
    NONE,
    BASE,
    ELITE,
    ;

    val isPro: Boolean get() = this != NONE
}
