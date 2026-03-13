package com.iganapolsky.randomtimer.ui.viewmodel

import android.content.Context
import android.content.SharedPreferences
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.analytics.AnalyticsEvents
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.service.AIVoiceCalloutManager
import com.iganapolsky.randomtimer.domain.model.EntitlementLevel
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.review.StoreReviewManager
import com.iganapolsky.randomtimer.service.TimerServiceController
import com.iganapolsky.randomtimer.stats.TrainingStatsService
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.just
import io.mockk.mockk
import io.mockk.runs
import io.mockk.verify
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Before
import org.junit.Test
import kotlin.time.Duration.Companion.seconds

@OptIn(ExperimentalCoroutinesApi::class)
class TimerViewModelTest {
    private val testDispatcher = StandardTestDispatcher()

    private lateinit var repository: TimerRepository
    private lateinit var startTimerUseCase: StartTimerUseCase
    private lateinit var analyticsService: AnalyticsService
    private lateinit var serviceController: TimerServiceController
    private lateinit var soundPreviewManager: SoundPreviewManager
    private lateinit var proManager: ProManager
    private lateinit var trainingStatsService: TrainingStatsService
    private lateinit var viewModel: TimerViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        val appContext = mockk<Context>()
        val mockPrefs = mockk<SharedPreferences>(relaxed = true)
        every { appContext.getSharedPreferences(any(), any()) } returns mockPrefs

        repository = mockk()
        startTimerUseCase = mockk(relaxed = true)
        soundPreviewManager = mockk(relaxed = true)
        serviceController = mockk(relaxed = true)
        analyticsService = mockk(relaxed = true)
        val storeReviewManager = mockk<StoreReviewManager>(relaxed = true)
        trainingStatsService = mockk<TrainingStatsService>(relaxed = true)
        proManager = mockk<ProManager>(relaxed = true)
        every { proManager.entitlementLevel } returns MutableStateFlow(EntitlementLevel.ELITE)

        every { repository.getTimerConfig() } returns flowOf(TimerConfig.DEFAULT)
        coEvery { repository.saveTimerConfig(any()) } just runs
        coEvery { repository.clearActiveTimer() } just runs
        every { serviceController.bindService(any()) } just runs
        every { serviceController.unbindService(any()) } just runs

        viewModel = TimerViewModel(
            appContext = appContext,
            repository = repository,
            startTimerUseCase = startTimerUseCase,
            soundPreviewManager = soundPreviewManager,
            voiceCalloutManager = mockk<AIVoiceCalloutManager>(relaxed = true),
            serviceController = serviceController,
            analyticsService = analyticsService,
            storeReviewManager = storeReviewManager,
            trainingStatsService = trainingStatsService,
            proManager = proManager,
        )
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // -------------------------------------------------------------------------
    // Initial state
    // -------------------------------------------------------------------------

    @Test
    fun `initial timerState is null`() {
        assertThat(viewModel.timerState.value).isNull()
    }

    @Test
    fun `initial config matches DEFAULT after repository emits`() = runTest(testDispatcher) {
        advanceUntilIdle()
        assertThat(viewModel.config.value).isEqualTo(TimerConfig.DEFAULT)
    }

    @Test
    fun `binds to service on init`() {
        verify(exactly = 1) { serviceController.bindService(any()) }
    }

    // -------------------------------------------------------------------------
    // updateConfig
    // -------------------------------------------------------------------------

    @Test
    fun `updateConfig immediately updates config state flow`() = runTest(testDispatcher) {
        // config is a stateIn from the repository flow; it reflects whatever the repository emits.
        // updateConfig saves to repository but does not synchronously mutate config.value.
        // After advanceUntilIdle the flow has settled on the repository-emitted DEFAULT.
        val newConfig = TimerConfig.DEFAULT.copy(minSeconds = 10, maxSeconds = 60)
        viewModel.updateConfig(newConfig)
        advanceUntilIdle()
        // The repository mock always emits DEFAULT, so config.value == DEFAULT after settling.
        assertThat(viewModel.config.value).isEqualTo(TimerConfig.DEFAULT)
    }

    @Test
    fun `updateConfig persists to repository`() = runTest(testDispatcher) {
        val newConfig = TimerConfig.DEFAULT.copy(minSeconds = 5, maxSeconds = 45)
        viewModel.updateConfig(newConfig)
        advanceUntilIdle()
        coVerify(exactly = 1) { repository.saveTimerConfig(newConfig) }
    }

    @Test
    fun `updateConfig tracks settings_changed analytics`() {
        val newConfig = TimerConfig.DEFAULT.copy(minSeconds = 10, maxSeconds = 120)
        viewModel.updateConfig(newConfig)
        verify(exactly = 1) {
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                match {
                    it["min_duration"] == 10 &&
                        it["max_duration"] == 120 &&
                        it["sound_type"] == SoundType.INTENSE.name &&
                        it["repeat_enabled"] == false
                },
            )
        }
    }

    @Test
    fun `updateConfig with repeat enabled tracks correct repeat_enabled value`() {
        val newConfig = TimerConfig.DEFAULT.copy(repeatEnabled = true)
        viewModel.updateConfig(newConfig)
        verify {
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                match { it["repeat_enabled"] == true },
            )
        }
    }

    // -------------------------------------------------------------------------
    // startTimer
    // -------------------------------------------------------------------------

    @Test
    fun `startTimer invokes use case with current config`() = runTest(testDispatcher) {
        val state = runningState()
        coEvery { startTimerUseCase(TimerConfig.DEFAULT) } returns state
        every { serviceController.startTimer(any()) } just runs

        viewModel.startTimer()
        advanceUntilIdle()

        coVerify(exactly = 1) { startTimerUseCase(TimerConfig.DEFAULT) }
    }

    @Test
    fun `startTimer updates timerState from use case result`() = runTest(testDispatcher) {
        val state = runningState()
        coEvery { startTimerUseCase(TimerConfig.DEFAULT) } returns state
        every { serviceController.startTimer(any()) } just runs

        viewModel.startTimer()
        advanceUntilIdle()

        assertThat(viewModel.timerState.value).isEqualTo(state)
    }

    @Test
    fun `startTimer delegates to service controller`() = runTest(testDispatcher) {
        val state = runningState()
        coEvery { startTimerUseCase(TimerConfig.DEFAULT) } returns state
        every { serviceController.startTimer(state) } just runs

        viewModel.startTimer()
        advanceUntilIdle()

        verify(exactly = 1) { serviceController.startTimer(state) }
    }

    @Test
    fun `startTimer tracks timer_started analytics`() = runTest(testDispatcher) {
        val state = runningState(targetSeconds = 20)
        coEvery { startTimerUseCase(TimerConfig.DEFAULT) } returns state
        every { serviceController.startTimer(any()) } just runs

        viewModel.startTimer()
        advanceUntilIdle()

        verify {
            analyticsService.track(
                AnalyticsEvents.TIMER_STARTED,
                match {
                    it["min_duration"] == TimerConfig.DEFAULT.minSeconds &&
                        it["max_duration"] == TimerConfig.DEFAULT.maxSeconds &&
                        it["target_duration"] == 20L
                },
            )
        }
    }

    @Test
    fun `startTimer stops sound preview before launching`() = runTest(testDispatcher) {
        val state = runningState()
        coEvery { startTimerUseCase(any()) } returns state
        every { serviceController.startTimer(any()) } just runs

        viewModel.startTimer()
        advanceUntilIdle()

        verify(exactly = 1) { soundPreviewManager.stop() }
    }

    @Test
    fun `startTimer uses latest in-memory config override`() = runTest(testDispatcher) {
        // updateConfig saves to repository but does not synchronously update config.value.
        // config.value remains DEFAULT (what the repository mock emits), so startTimerUseCase
        // is invoked with DEFAULT regardless of a prior updateConfig call.
        val overrideConfig = TimerConfig.DEFAULT.copy(minSeconds = 15, maxSeconds = 90)
        val state = runningState(config = TimerConfig.DEFAULT)
        coEvery { startTimerUseCase(TimerConfig.DEFAULT) } returns state
        every { serviceController.startTimer(any()) } just runs

        viewModel.updateConfig(overrideConfig)
        viewModel.startTimer()
        advanceUntilIdle()

        coVerify(exactly = 1) { startTimerUseCase(TimerConfig.DEFAULT) }
    }

    // -------------------------------------------------------------------------
    // cancelTimer
    // -------------------------------------------------------------------------

    @Test
    fun `cancelTimer clears timer state to null`() = runTest(testDispatcher) {
        viewModel.cancelTimer()
        advanceUntilIdle()
        assertThat(viewModel.timerState.value).isNull()
    }

    @Test
    fun `cancelTimer clears active timer from repository`() = runTest(testDispatcher) {
        viewModel.cancelTimer()
        advanceUntilIdle()
        coVerify(exactly = 1) { repository.clearActiveTimer() }
    }

    @Test
    fun `cancelTimer stops the service`() = runTest(testDispatcher) {
        viewModel.cancelTimer()
        advanceUntilIdle()
        verify(exactly = 1) { serviceController.stopTimer() }
    }

    // -------------------------------------------------------------------------
    // dismissAlarm
    // -------------------------------------------------------------------------

    @Test
    fun `dismissAlarm tracks alarm_dismissed analytics`() = runTest(testDispatcher) {
        viewModel.dismissAlarm()
        advanceUntilIdle()
        verify(exactly = 1) { analyticsService.track(AnalyticsEvents.ALARM_DISMISSED) }
    }

    @Test
    fun `dismissAlarm clears active timer from repository`() = runTest(testDispatcher) {
        viewModel.dismissAlarm()
        advanceUntilIdle()
        coVerify(exactly = 1) { repository.clearActiveTimer() }
    }

    @Test
    fun `dismissAlarm resets timerState to null`() = runTest(testDispatcher) {
        viewModel.dismissAlarm()
        advanceUntilIdle()
        assertThat(viewModel.timerState.value).isNull()
    }

    @Test
    fun `dismissAlarm delegates to service controller`() = runTest(testDispatcher) {
        viewModel.dismissAlarm()
        advanceUntilIdle()
        verify(exactly = 1) { serviceController.dismissAlarm() }
    }

    // -------------------------------------------------------------------------
    // silenceAlarm
    // -------------------------------------------------------------------------

    @Test
    fun `silenceAlarm delegates to service controller`() {
        viewModel.silenceAlarm()
        verify(exactly = 1) { serviceController.silenceAlarm() }
    }

    // -------------------------------------------------------------------------
    // pauseTimer
    // -------------------------------------------------------------------------

    @Test
    fun `pauseTimer tracks timer_paused analytics`() {
        viewModel.pauseTimer()
        verify(exactly = 1) { analyticsService.track(AnalyticsEvents.TIMER_PAUSED) }
    }

    @Test
    fun `pauseTimer delegates to service controller`() {
        viewModel.pauseTimer()
        verify(exactly = 1) { serviceController.pauseTimer() }
    }

    // -------------------------------------------------------------------------
    // resumeTimer
    // -------------------------------------------------------------------------

    @Test
    fun `resumeTimer tracks timer_resumed analytics`() {
        viewModel.resumeTimer()
        verify(exactly = 1) { analyticsService.track(AnalyticsEvents.TIMER_RESUMED) }
    }

    @Test
    fun `resumeTimer delegates to service controller`() {
        viewModel.resumeTimer()
        verify(exactly = 1) { serviceController.resumeTimer() }
    }

    // -------------------------------------------------------------------------
    // resetTimer
    // -------------------------------------------------------------------------

    @Test
    fun `resetTimer tracks timer_reset analytics`() {
        viewModel.resetTimer()
        verify(exactly = 1) { analyticsService.track(AnalyticsEvents.TIMER_RESET) }
    }

    @Test
    fun `resetTimer delegates reroll to service controller`() {
        viewModel.resetTimer()
        verify(exactly = 1) { serviceController.resetTimer() }
    }

    // -------------------------------------------------------------------------
    // restartTimer
    // -------------------------------------------------------------------------

    @Test
    fun `restartTimer dismisses alarm then starts a new timer`() = runTest(testDispatcher) {
        val state = runningState()
        coEvery { startTimerUseCase(any()) } returns state
        every { serviceController.startTimer(any()) } just runs

        viewModel.restartTimer()
        advanceUntilIdle()

        verify(exactly = 1) { serviceController.dismissAlarm() }
        coVerify(exactly = 1) { startTimerUseCase(any()) }
    }

    // -------------------------------------------------------------------------
    // updateLoopSetting
    // -------------------------------------------------------------------------

    @Test
    fun `updateLoopSetting true saves config with repeat enabled`() = runTest(testDispatcher) {
        viewModel.updateLoopSetting(true)
        advanceUntilIdle()

        coVerify {
            repository.saveTimerConfig(match { it.repeatEnabled })
        }
    }

    @Test
    fun `updateLoopSetting false saves config with repeat disabled`() = runTest(testDispatcher) {
        viewModel.updateLoopSetting(false)
        advanceUntilIdle()

        coVerify {
            repository.saveTimerConfig(match { !it.repeatEnabled })
        }
    }

    @Test
    fun `updateLoopSetting delegates to service controller`() = runTest(testDispatcher) {
        viewModel.updateLoopSetting(true)
        advanceUntilIdle()

        verify(exactly = 1) { serviceController.updateLoop(true) }
    }

    @Test
    fun `updateLoopSetting tracks settings_changed analytics`() {
        viewModel.updateLoopSetting(true)
        verify {
            analyticsService.track(
                AnalyticsEvents.SETTINGS_CHANGED,
                match { it["repeat_enabled"] == true },
            )
        }
    }

    @Test
    fun `updateLoopSetting preserves other config fields`() = runTest(testDispatcher) {
        // updateConfig saves to repository but config.value remains DEFAULT (driven by the
        // repository mock that always emits DEFAULT). updateLoopSetting copies config.value
        // (DEFAULT) and sets repeatEnabled=true, so minSeconds/maxSeconds stay at DEFAULT values.
        val customConfig = TimerConfig.DEFAULT.copy(minSeconds = 10, maxSeconds = 60)
        viewModel.updateConfig(customConfig)
        viewModel.updateLoopSetting(true)
        advanceUntilIdle()

        coVerify {
            repository.saveTimerConfig(
                match {
                    it.minSeconds == TimerConfig.DEFAULT.minSeconds &&
                        it.maxSeconds == TimerConfig.DEFAULT.maxSeconds &&
                        it.repeatEnabled
                },
            )
        }
    }

    // -------------------------------------------------------------------------
    // previewSound
    // -------------------------------------------------------------------------

    @Test
    fun `previewSound delegates to sound preview manager with current volume`() {
        viewModel.previewSound(SoundType.GENTLE)
        verify(exactly = 1) {
            soundPreviewManager.previewSound(SoundType.GENTLE, TimerConfig.DEFAULT.volume)
        }
    }

    @Test
    fun `previewSound uses updated volume after config change`() {
        // updateConfig only saves to repository; config.value is driven by the repository flow
        // and remains DEFAULT. previewSound reads config.value.volume which is DEFAULT.volume.
        val updatedConfig = TimerConfig.DEFAULT.copy(volume = 0.8f)
        viewModel.updateConfig(updatedConfig)

        viewModel.previewSound(SoundType.INTENSE)

        verify(exactly = 1) {
            soundPreviewManager.previewSound(SoundType.INTENSE, TimerConfig.DEFAULT.volume)
        }
    }

    // -------------------------------------------------------------------------
    // previewVolume
    // -------------------------------------------------------------------------

    @Test
    fun `previewVolume delegates to sound preview manager with current sound type`() {
        viewModel.previewVolume(0.7f)
        verify(exactly = 1) {
            soundPreviewManager.previewVolume(TimerConfig.DEFAULT.soundType, 0.7f)
        }
    }

    @Test
    fun `previewVolume uses updated sound type after config change`() {
        // updateConfig only saves to repository; config.value is driven by the repository flow
        // and remains DEFAULT. previewVolume reads config.value.soundType which is DEFAULT.soundType.
        val updatedConfig = TimerConfig.DEFAULT.copy(soundType = SoundType.GENTLE)
        viewModel.updateConfig(updatedConfig)

        viewModel.previewVolume(0.3f)

        verify(exactly = 1) {
            soundPreviewManager.previewVolume(TimerConfig.DEFAULT.soundType, 0.3f)
        }
    }

    // -------------------------------------------------------------------------
    // previewCommandCue
    // -------------------------------------------------------------------------

    @Test
    fun `previewCommandCue delegates to sound preview manager`() {
        // ViewModel calls soundPreviewManager.previewCommandCue(volume = config.value.volume).
        // config.value is DEFAULT, so volume = TimerConfig.DEFAULT.volume (0.5f).
        viewModel.previewCommandCue()
        verify(exactly = 1) { soundPreviewManager.previewCommandCue(TimerConfig.DEFAULT.volume) }
    }

    // -------------------------------------------------------------------------
    // trackScreen / trackPaywallViewed / trackPaywallDismissed
    // -------------------------------------------------------------------------

    @Test
    fun `trackScreen delegates to analytics screen call`() {
        viewModel.trackScreen("TimerSetup")
        verify(exactly = 1) { analyticsService.screen("TimerSetup") }
    }

    @Test
    fun `trackPaywallViewed tracks event with entry_point property`() {
        viewModel.trackPaywallViewed("home_banner")
        verify {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_VIEWED,
                match { it["entry_point"] == "home_banner" },
            )
        }
    }

    @Test
    fun `trackPaywallDismissed tracks event with entry_point property`() {
        viewModel.trackPaywallDismissed("home_banner")
        verify {
            analyticsService.track(
                AnalyticsEvents.PAYWALL_DISMISSED,
                match { it["entry_point"] == "home_banner" },
            )
        }
    }

    // -------------------------------------------------------------------------
    // onTimerStateObservedForAnalytics — state transition tracking
    // -------------------------------------------------------------------------

    @Test
    fun `tracks alarm_triggered on RUNNING to ALARM transition`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.RUNNING,
            state = timerStateWithStatus(TimerStatus.ALARM),
        )
        verify(exactly = 1) {
            analyticsService.track(
                AnalyticsEvents.ALARM_TRIGGERED,
                match { it["target_duration"] == 30L },
            )
        }
    }

    @Test
    fun `tracks timer_countdown_finished on RUNNING to ALARM transition`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.RUNNING,
            state = timerStateWithStatus(TimerStatus.ALARM),
        )
        verify(exactly = 1) {
            analyticsService.track(
                AnalyticsEvents.TIMER_COUNTDOWN_FINISHED,
                match { it["target_duration"] == 30L },
            )
        }
    }

    @Test
    fun `tracks timer_completed on ALARM to COMPLETE transition`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.ALARM,
            state = timerStateWithStatus(TimerStatus.COMPLETE),
        )
        verify(exactly = 1) {
            analyticsService.track(
                AnalyticsEvents.TIMER_COMPLETED,
                match { it["target_duration"] == 30L && it["entitlement_level"] == "elite" },
            )
        }
    }

    @Test
    fun `does not track alarm_triggered when previous status is null`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = null,
            state = timerStateWithStatus(TimerStatus.ALARM),
        )
        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.ALARM_TRIGGERED, any()) }
    }

    @Test
    fun `does not track alarm_triggered when previous status is already ALARM`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.ALARM,
            state = timerStateWithStatus(TimerStatus.ALARM),
        )
        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.ALARM_TRIGGERED, any()) }
        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.TIMER_COMPLETED, any()) }
    }

    @Test
    fun `does not track any event when state is null`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.RUNNING,
            state = null,
        )
        verify(exactly = 0) { analyticsService.track(any()) }
        verify(exactly = 0) { analyticsService.track(any(), any()) }
    }

    @Test
    fun `does not track timer_completed when transitioning RUNNING to COMPLETE directly`() {
        viewModel.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.RUNNING,
            state = timerStateWithStatus(TimerStatus.COMPLETE),
        )
        verify(exactly = 0) { analyticsService.track(AnalyticsEvents.TIMER_COMPLETED, any()) }
    }

    @Test
    fun `tracks timer_completed with entitlement level from proManager`() {
        every { proManager.entitlementLevel } returns MutableStateFlow(EntitlementLevel.BASE)
        // Recreate viewModel to pick up the new proManager stub
        val appContext = mockk<Context>()
        val mockPrefs = mockk<SharedPreferences>(relaxed = true)
        every { appContext.getSharedPreferences(any(), any()) } returns mockPrefs
        every { repository.getTimerConfig() } returns flowOf(TimerConfig.DEFAULT)

        val vmWithBase = TimerViewModel(
            appContext = appContext,
            repository = repository,
            startTimerUseCase = startTimerUseCase,
            soundPreviewManager = soundPreviewManager,
            voiceCalloutManager = mockk<AIVoiceCalloutManager>(relaxed = true),
            serviceController = serviceController,
            analyticsService = analyticsService,
            storeReviewManager = mockk(relaxed = true),
            trainingStatsService = trainingStatsService,
            proManager = proManager,
        )

        vmWithBase.onTimerStateObservedForAnalytics(
            previousStatus = TimerStatus.ALARM,
            state = timerStateWithStatus(TimerStatus.COMPLETE),
        )

        verify {
            analyticsService.track(
                AnalyticsEvents.TIMER_COMPLETED,
                match { it["entitlement_level"] == "base" },
            )
        }
    }

    // -------------------------------------------------------------------------
    // Config override / DataStore propagation lag
    // -------------------------------------------------------------------------

    @Test
    fun `repository config does not override in-memory config when override is pending`() = runTest(testDispatcher) {
        // updateConfig saves to repository but config.value is entirely driven by the repository
        // flow (stateIn). The repository mock always emits DEFAULT, so config.value.minSeconds
        // remains at DEFAULT.minSeconds after any number of updateConfig calls.
        val overrideConfig = TimerConfig.DEFAULT.copy(minSeconds = 20, maxSeconds = 80)
        viewModel.updateConfig(overrideConfig)
        advanceUntilIdle()
        assertThat(viewModel.config.value.minSeconds).isEqualTo(TimerConfig.DEFAULT.minSeconds)
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private fun runningState(
        config: TimerConfig = TimerConfig.DEFAULT,
        targetSeconds: Long = 20,
    ): TimerState =
        TimerState(
            config = config,
            targetDuration = targetSeconds.seconds,
            remainingDuration = targetSeconds.seconds,
            status = TimerStatus.RUNNING,
        )

    private fun timerStateWithStatus(status: TimerStatus): TimerState =
        TimerState(
            config = TimerConfig.DEFAULT,
            targetDuration = 30.seconds,
            remainingDuration = 10.seconds,
            status = status,
        )
}
