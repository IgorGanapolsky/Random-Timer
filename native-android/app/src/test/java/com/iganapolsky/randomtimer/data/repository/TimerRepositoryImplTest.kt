package com.iganapolsky.randomtimer.data.repository

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.PreferenceDataStoreFactory
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Test
import java.nio.file.Files
import kotlin.time.Duration.Companion.seconds

class TimerRepositoryImplTest {
    @Test
    fun `getTimerConfig returns defaults when preferences are empty`() =
        runTest {
            val (repository, _) = createRepository(backgroundScope)

            val config = repository.getTimerConfig().first()

            assertThat(config).isEqualTo(TimerConfig.DEFAULT)
        }

    @Test
    fun `saveTimerConfig persists and emits stored config`() =
        runTest {
            val (repository, _) = createRepository(backgroundScope)
            val expected =
                TimerConfig(
                    minSeconds = 5,
                    maxSeconds = 120,
                    alarmDuration = 15,
                    hiddenMode = true,
                    repeatEnabled = true,
                    soundType = SoundType.GENTLE,
                    volume = 0.8f,
                    vibrationEnabled = true,
                )

            repository.saveTimerConfig(expected)

            val restored = repository.getTimerConfig().first()
            assertThat(restored).isEqualTo(expected)
        }

    @Test
    fun `getTimerConfig falls back to INTENSE for invalid stored sound type`() =
        runTest {
            val (repository, dataStore) = createRepository(backgroundScope)

            dataStore.edit { preferences ->
                preferences[stringPreferencesKey("sound_type")] = "INVALID_SOUND"
            }

            val config = repository.getTimerConfig().first()
            assertThat(config.soundType).isEqualTo(SoundType.INTENSE)
        }

    @Test
    fun `getActiveTimer returns null when active timer is not stored`() =
        runTest {
            val (repository, _) = createRepository(backgroundScope)

            val activeTimer = repository.getActiveTimer().first()

            assertThat(activeTimer).isNull()
        }

    @Test
    fun `getActiveTimer returns null when active timer keys are incomplete`() =
        runTest {
            val (repository, dataStore) = createRepository(backgroundScope)

            dataStore.edit { preferences ->
                preferences[longPreferencesKey("active_target_ms")] = 5_000L
            }

            val activeTimer = repository.getActiveTimer().first()
            assertThat(activeTimer).isNull()
        }

    @Test
    fun `saveActiveTimer persists and restores active timer state`() =
        runTest {
            val (repository, _) = createRepository(backgroundScope)
            val config =
                TimerConfig(
                    minSeconds = 10,
                    maxSeconds = 90,
                    alarmDuration = 30,
                    hiddenMode = false,
                    repeatEnabled = true,
                    soundType = SoundType.GENTLE,
                    volume = 0.6f,
                    vibrationEnabled = true,
                )
            val expected =
                TimerState(
                    config = config,
                    targetDuration = 90.seconds,
                    remainingDuration = 45.seconds,
                    status = TimerStatus.PAUSED,
                    startedAt = 123456789L,
                )

            repository.saveTimerConfig(config)
            repository.saveActiveTimer(expected)

            val restored = repository.getActiveTimer().first()
            assertThat(restored).isEqualTo(expected)
        }

    @Test
    fun `getActiveTimer uses default config when config keys are absent`() =
        runTest {
            val (repository, _) = createRepository(backgroundScope)
            val state =
                TimerState(
                    config =
                        TimerConfig.DEFAULT.copy(
                            minSeconds = 10,
                            maxSeconds = 20,
                            alarmDuration = 15,
                            hiddenMode = true,
                            repeatEnabled = true,
                            soundType = SoundType.GENTLE,
                            volume = 0.9f,
                            vibrationEnabled = true,
                        ),
                    targetDuration = 20.seconds,
                    remainingDuration = 5.seconds,
                    status = TimerStatus.RUNNING,
                    startedAt = 999L,
                )

            repository.saveActiveTimer(state)

            val restored = repository.getActiveTimer().first()
            assertThat(restored?.config).isEqualTo(TimerConfig.DEFAULT)
        }

    @Test
    fun `getActiveTimer falls back to INTENSE for invalid stored sound type`() =
        runTest {
            val (repository, dataStore) = createRepository(backgroundScope)
            val state =
                TimerState(
                    config = TimerConfig.DEFAULT,
                    targetDuration = 25.seconds,
                    remainingDuration = 7.seconds,
                    status = TimerStatus.PAUSED,
                    startedAt = 123L,
                )
            repository.saveActiveTimer(state)
            dataStore.edit { preferences ->
                preferences[stringPreferencesKey("sound_type")] = "NOT_A_REAL_SOUND"
            }

            val restored = repository.getActiveTimer().first()

            assertThat(restored?.config?.soundType).isEqualTo(SoundType.INTENSE)
        }

    @Test
    fun `clearActiveTimer removes persisted active timer`() =
        runTest {
            val (repository, _) = createRepository(backgroundScope)
            val state =
                TimerState(
                    config = TimerConfig.DEFAULT,
                    targetDuration = 30.seconds,
                    remainingDuration = 10.seconds,
                    status = TimerStatus.RUNNING,
                    startedAt = 777L,
                )

            repository.saveActiveTimer(state)
            repository.clearActiveTimer()

            val restored = repository.getActiveTimer().first()
            assertThat(restored).isNull()
        }

    @Test
    fun `clearActiveTimer does not remove saved timer config`() =
        runTest {
            val (repository, _) = createRepository(backgroundScope)
            val config =
                TimerConfig(
                    minSeconds = 3,
                    maxSeconds = 100,
                    alarmDuration = 30,
                    hiddenMode = true,
                    repeatEnabled = true,
                    soundType = SoundType.GENTLE,
                    volume = 0.75f,
                    vibrationEnabled = true,
                )
            val state =
                TimerState(
                    config = config,
                    targetDuration = 40.seconds,
                    remainingDuration = 11.seconds,
                    status = TimerStatus.WARNING,
                    startedAt = 456L,
                )

            repository.saveTimerConfig(config)
            repository.saveActiveTimer(state)
            repository.clearActiveTimer()

            val restoredConfig = repository.getTimerConfig().first()
            val restoredActiveTimer = repository.getActiveTimer().first()
            assertThat(restoredConfig).isEqualTo(config)
            assertThat(restoredActiveTimer).isNull()
        }

    private fun createRepository(scope: CoroutineScope): Pair<TimerRepositoryImpl, DataStore<Preferences>> {
        val dataStore =
            PreferenceDataStoreFactory.create(
                scope = scope,
                produceFile = {
                    Files.createTempFile("timer-repo-test", ".preferences_pb").toFile()
                },
            )
        return TimerRepositoryImpl(dataStore) to dataStore
    }
}
