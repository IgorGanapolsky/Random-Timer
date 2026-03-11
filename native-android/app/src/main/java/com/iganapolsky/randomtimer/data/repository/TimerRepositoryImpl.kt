package com.iganapolsky.randomtimer.data.repository

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.time.Duration.Companion.milliseconds

@Singleton
class TimerRepositoryImpl
    @Inject
    constructor(
        private val dataStore: DataStore<Preferences>,
        private val proManager: ProManager,
    ) : TimerRepository {
        /**
         * Clamps a deserialized config to the current Pro entitlement.
         * Applied on load only — save paths are unchanged so the original values remain persisted
         * and can be restored if the user re-subscribes.
         */
        private fun TimerConfig.clampedForPro(): TimerConfig {
            val level = proManager.entitlementLevel.value
            val maxAllowed = proManager.maxSecondsLimit(level)
            val allowedSounds = proManager.availableSounds(level)
            val clampedMax = maxSeconds.coerceAtMost(maxAllowed)
            val clampedMin = minSeconds.coerceAtMost(clampedMax)
            val clampedSound = if (soundType in allowedSounds) soundType else SoundType.INTENSE
            return copy(
                minSeconds = clampedMin,
                maxSeconds = clampedMax,
                soundType = clampedSound,
            )
        }

        private fun Preferences.toTimerConfig(): TimerConfig =
            TimerConfig(
                minSeconds = this[KEY_MIN_SECONDS] ?: TimerConfig.DEFAULT.minSeconds,
                maxSeconds = this[KEY_MAX_SECONDS] ?: TimerConfig.DEFAULT.maxSeconds,
                alarmDuration = this[KEY_ALARM_DURATION] ?: TimerConfig.DEFAULT.alarmDuration,
                hiddenMode = this[KEY_HIDDEN_MODE] ?: TimerConfig.DEFAULT.hiddenMode,
                repeatEnabled = this[KEY_REPEAT_ENABLED] ?: TimerConfig.DEFAULT.repeatEnabled,
                soundType =
                    this[KEY_SOUND_TYPE]?.let {
                        try {
                            SoundType.valueOf(it)
                        } catch (_: Exception) {
                            TimerConfig.DEFAULT.soundType
                        }
                    } ?: TimerConfig.DEFAULT.soundType,
                volume = this[KEY_VOLUME] ?: TimerConfig.DEFAULT.volume,
                vibrationEnabled = this[KEY_VIBRATION_ENABLED] ?: TimerConfig.DEFAULT.vibrationEnabled,
            ).clampedForPro()

        override fun getTimerConfig(): Flow<TimerConfig> =
            dataStore.data.map { preferences -> preferences.toTimerConfig() }

        override suspend fun saveTimerConfig(config: TimerConfig) {
            dataStore.edit { preferences ->
                preferences[KEY_MIN_SECONDS] = config.minSeconds
                preferences[KEY_MAX_SECONDS] = config.maxSeconds
                preferences[KEY_ALARM_DURATION] = config.alarmDuration
                preferences[KEY_HIDDEN_MODE] = config.hiddenMode
                preferences[KEY_REPEAT_ENABLED] = config.repeatEnabled
                preferences[KEY_SOUND_TYPE] = config.soundType.name
                preferences[KEY_VOLUME] = config.volume
                preferences[KEY_VIBRATION_ENABLED] = config.vibrationEnabled
            }
        }

        override fun getActiveTimer(): Flow<TimerState?> {
            return dataStore.data.map { preferences ->
                val targetMs = preferences[KEY_ACTIVE_TARGET] ?: return@map null
                val remainingMs = preferences[KEY_ACTIVE_REMAINING] ?: return@map null
                val statusStr = preferences[KEY_ACTIVE_STATUS] ?: return@map null
                val startedAt = preferences[KEY_ACTIVE_STARTED_AT] ?: return@map null

                val config = preferences.toTimerConfig()

                TimerState(
                    config = config,
                    targetDuration = targetMs.milliseconds,
                    remainingDuration = remainingMs.milliseconds,
                    status = TimerStatus.valueOf(statusStr),
                    startedAt = startedAt,
                )
            }
        }

        override suspend fun saveActiveTimer(state: TimerState) {
            dataStore.edit { preferences ->
                preferences[KEY_ACTIVE_TARGET] = state.targetDuration.inWholeMilliseconds
                preferences[KEY_ACTIVE_REMAINING] = state.remainingDuration.inWholeMilliseconds
                preferences[KEY_ACTIVE_STATUS] = state.status.name
                preferences[KEY_ACTIVE_STARTED_AT] = state.startedAt
            }
        }

        override suspend fun clearActiveTimer() {
            dataStore.edit { preferences ->
                preferences.remove(KEY_ACTIVE_TARGET)
                preferences.remove(KEY_ACTIVE_REMAINING)
                preferences.remove(KEY_ACTIVE_STATUS)
                preferences.remove(KEY_ACTIVE_STARTED_AT)
            }
        }

        companion object {
            // Config keys
            private val KEY_MIN_SECONDS = intPreferencesKey("min_seconds")
            private val KEY_MAX_SECONDS = intPreferencesKey("max_seconds")
            private val KEY_ALARM_DURATION = intPreferencesKey("alarm_duration")
            private val KEY_HIDDEN_MODE = booleanPreferencesKey("hidden_mode")
            private val KEY_REPEAT_ENABLED = booleanPreferencesKey("repeat_enabled")
            private val KEY_SOUND_TYPE = stringPreferencesKey("sound_type")
            private val KEY_VOLUME = floatPreferencesKey("volume")
            private val KEY_VIBRATION_ENABLED = booleanPreferencesKey("vibration_enabled")

            // Active timer keys
            private val KEY_ACTIVE_TARGET = longPreferencesKey("active_target_ms")
            private val KEY_ACTIVE_REMAINING = longPreferencesKey("active_remaining_ms")
            private val KEY_ACTIVE_STATUS = stringPreferencesKey("active_status")
            private val KEY_ACTIVE_STARTED_AT = longPreferencesKey("active_started_at")
        }
    }
