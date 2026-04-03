package com.iganapolsky.randomtimer.appfunctions

import androidx.appfunctions.AppFunctionInvalidArgumentException
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.VoiceGender
import java.util.Locale
import javax.inject.Inject

class RandomTimerAppFunctionConfigFactory
    @Inject
    constructor() {
        fun create(
            minSeconds: Int,
            maxSeconds: Int,
            alarmDuration: Int,
            soundType: String,
            voiceEnabled: Boolean,
            voiceGender: String,
            hiddenMode: Boolean,
            repeatEnabled: Boolean,
            vibrationEnabled: Boolean,
            entitlementLevel: EntitlementLevel,
        ): TimerConfig {
            if (alarmDuration !in TimerConfig.ALARM_DURATION_OPTIONS) {
                invalidArgument(
                    "alarmDuration must be one of ${TimerConfig.ALARM_DURATION_OPTIONS.joinToString(", ")} seconds.",
                )
            }

            val parsedSoundType = parseSoundType(soundType)
            val parsedVoiceGender = parseVoiceGender(voiceGender)
            val usesExtendedRange =
                minSeconds > TimerConfig.MAX_SECONDS_FREE || maxSeconds > TimerConfig.MAX_SECONDS_FREE

            if (usesExtendedRange && !entitlementLevel.isPro) {
                invalidArgument("Extended timer ranges above ${TimerConfig.MAX_SECONDS_FREE} seconds require Pro.")
            }

            if (parsedSoundType.isPro && !entitlementLevel.isPro) {
                invalidArgument("Sound type ${parsedSoundType.name} requires Pro.")
            }

            if (voiceEnabled && !entitlementLevel.isPro) {
                invalidArgument("Voice callouts require Pro.")
            }

            return try {
                TimerConfig(
                    minSeconds = minSeconds,
                    maxSeconds = maxSeconds,
                    alarmDuration = alarmDuration,
                    hiddenMode = hiddenMode,
                    repeatEnabled = repeatEnabled,
                    soundType = parsedSoundType,
                    volume = TimerConfig.DEFAULT.volume,
                    vibrationEnabled = vibrationEnabled,
                    useExtendedRange = usesExtendedRange,
                    voiceEnabled = voiceEnabled,
                    voiceGender = parsedVoiceGender,
                )
            } catch (error: IllegalArgumentException) {
                invalidArgument(error.message ?: "Invalid timer configuration.")
            }
        }

        private fun parseSoundType(rawValue: String): SoundType = parseEnum(rawValue, "soundType")

        private fun parseVoiceGender(rawValue: String): VoiceGender = parseEnum(rawValue, "voiceGender")

        private inline fun <reified T : Enum<T>> parseEnum(
            rawValue: String,
            fieldName: String,
        ): T {
            val normalized = rawValue.trim().uppercase(Locale.US)
            return enumValues<T>().firstOrNull { value -> value.name == normalized }
                ?: invalidArgument(
                    "$fieldName must be one of ${enumValues<T>().joinToString(", ") { value -> value.name }}.",
                )
        }

        private fun invalidArgument(message: String): Nothing = throw AppFunctionInvalidArgumentException(message)
    }
