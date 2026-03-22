package com.iganapolsky.randomtimer.data.repository

import androidx.datastore.preferences.core.PreferenceDataStoreFactory
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runTest
import org.junit.Test
import java.nio.file.Files
import kotlin.time.Duration.Companion.milliseconds

class TimerRepositoryImplTest {
    @Test
    fun getTimerConfig_returns_defaults_when_preferences_are_empty() =
        runTest {
            val repo = createRepository(this)
            val config = repo.getTimerConfig().first()
            assertThat(config).isEqualTo(TimerConfig.DEFAULT)
        }

    @Test
    fun saveTimerConfig_persists_and_emits_stored_config() =
        runTest {
            val repo = createRepository(this)
            val newConfig =
                TimerConfig.DEFAULT.copy(
                    minSeconds = 15,
                    maxSeconds = 45,
                    alarmDuration = 20,
                    repeatEnabled = true,
                    soundType = SoundType.GENTLE,
                    volume = 0.8f,
                    vibrationEnabled = true,
                    voiceEnabled = true,
                )

            repo.saveTimerConfig(newConfig)
            val stored = repo.getTimerConfig().first()
            assertThat(stored).isEqualTo(newConfig)
        }

    @Test
    fun getTimerConfig_reemits_raw_pro_values_when_entitlement_changes() =
        runTest {
            val entitlementLevelFlow = MutableStateFlow(EntitlementLevel.NONE)
            val isProFlow = MutableStateFlow(false)
            val repo = createRepository(this, entitlementLevelFlow = entitlementLevelFlow, isProFlow = isProFlow)
            val storedRawConfig =
                TimerConfig.DEFAULT.copy(
                    maxSeconds = 900,
                    soundType = SoundType.BELL,
                    useExtendedRange = true,
                )

            repo.saveTimerConfig(storedRawConfig)

            val freeTierView = repo.getTimerConfig().first()
            assertThat(freeTierView.maxSeconds).isEqualTo(TimerConfig.MAX_SECONDS_FREE)
            assertThat(freeTierView.soundType).isEqualTo(SoundType.INTENSE)
            assertThat(freeTierView.useExtendedRange).isFalse()

            entitlementLevelFlow.value = EntitlementLevel.ELITE
            isProFlow.value = true

            val proView = repo.getTimerConfig().first { it.useExtendedRange }
            assertThat(proView.maxSeconds).isEqualTo(900)
            assertThat(proView.soundType).isEqualTo(SoundType.BELL)
            assertThat(proView.useExtendedRange).isTrue()
        }

    @Test
    fun getActiveTimer_returns_null_when_active_timer_is_not_stored() =
        runTest {
            val repo = createRepository(this)
            val active = repo.getActiveTimer().first()
            assertThat(active).isNull()
        }

    @Test
    fun saveActiveTimer_persists_and_restores_active_timer_state() =
        runTest {
            val repo = createRepository(this)
            val state =
                TimerState(
                    config = TimerConfig.DEFAULT,
                    targetDuration = 5000.milliseconds,
                    remainingDuration = 3000.milliseconds,
                    status = TimerStatus.RUNNING,
                    startedAt = 123456789L,
                )

            repo.saveActiveTimer(state)
            val restored = repo.getActiveTimer().first()
            assertThat(restored).isEqualTo(state)
        }

    private fun createRepository(
        testScope: TestScope,
        entitlementLevelFlow: MutableStateFlow<EntitlementLevel> = MutableStateFlow(EntitlementLevel.NONE),
        isProFlow: MutableStateFlow<Boolean> = MutableStateFlow(false),
    ): TimerRepositoryImpl {
        val dataStore =
            PreferenceDataStoreFactory.create(
                scope = testScope.backgroundScope,
                produceFile = {
                    Files.createTempFile("timer-repo-test", ".preferences_pb").toFile()
                },
            )

        val proManager = mockk<ProManager>(relaxed = true)

        every { proManager.entitlementLevel } returns entitlementLevelFlow.asStateFlow()
        every { proManager.isPro } returns isProFlow.asStateFlow()
        every { proManager.maxSecondsLimit(any()) } answers {
            val level = firstArg<EntitlementLevel>()
            if (level.isPro) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE
        }
        every { proManager.availableSounds(any()) } answers {
            val level = firstArg<EntitlementLevel>()
            if (level.isPro) SoundType.entries.toList() else SoundType.FREE
        }

        return TimerRepositoryImpl(dataStore, proManager)
    }
}
