package com.iganapolsky.randomtimer.ui.viewmodel

import android.content.ComponentName
import android.content.ServiceConnection
import android.os.IBinder
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.review.StoreReviewManager
import com.iganapolsky.randomtimer.service.TimerForegroundService
import com.iganapolsky.randomtimer.service.TimerServiceController
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TimerViewModel
    @Inject
    constructor(
        private val repository: TimerRepository,
        private val startTimerUseCase: StartTimerUseCase,
        private val soundPreviewManager: SoundPreviewManager,
        private val serviceController: TimerServiceController,
        val storeReviewManager: StoreReviewManager,
    ) : ViewModel() {
        val config: StateFlow<TimerConfig> =
            repository
                .getTimerConfig()
                .stateIn(
                    scope = viewModelScope,
                    started = SharingStarted.WhileSubscribed(5000),
                    initialValue = TimerConfig.DEFAULT,
                )

        private val _timerState = MutableStateFlow<TimerState?>(null)
        val timerState: StateFlow<TimerState?> = _timerState

        private var service: TimerForegroundService? = null
        private var bound = false

        private val serviceConnection =
            object : ServiceConnection {
                override fun onServiceConnected(
                    name: ComponentName?,
                    binder: IBinder?,
                ) {
                    val localBinder = binder as TimerForegroundService.LocalBinder
                    service = localBinder.getService()
                    bound = true
                    viewModelScope.launch {
                        service?.timerState?.collect { state ->
                            _timerState.value = state
                        }
                    }
                }

                override fun onServiceDisconnected(name: ComponentName?) {
                    service = null
                    bound = false
                }
            }

        init {
            serviceController.bindService(serviceConnection)
        }

        override fun onCleared() {
            super.onCleared()
            if (bound) {
                serviceController.unbindService(serviceConnection)
                bound = false
            }
        }

        fun updateConfig(newConfig: TimerConfig) {
            viewModelScope.launch {
                repository.saveTimerConfig(newConfig)
            }
        }

        fun startTimer() {
            stopSoundPreview()

            viewModelScope.launch {
                val state = startTimerUseCase(config.value)
                _timerState.value = state
                serviceController.startTimer(state)
            }
        }

        fun cancelTimer() {
            viewModelScope.launch {
                repository.clearActiveTimer()
                _timerState.value = null
                serviceController.stopTimer()
            }
        }

        fun dismissAlarm() {
            viewModelScope.launch {
                repository.clearActiveTimer()
                _timerState.value = null
                serviceController.dismissAlarm()
            }
        }

        fun pauseTimer() {
            serviceController.pauseTimer()
        }

        fun resumeTimer() {
            serviceController.resumeTimer()
        }

        fun restartTimer() {
            dismissAlarm()
            startTimer()
        }

        fun resetTimer() {
            _timerState.value?.let { current ->
                _timerState.value =
                    current.copy(
                        remainingDuration = current.targetDuration,
                        status = TimerStatus.RUNNING,
                        alarmTimeRemaining = kotlin.time.Duration.ZERO,
                        startedAt = System.currentTimeMillis(),
                    )
            }
            serviceController.resetTimer()
        }

        fun updateLoopSetting(enabled: Boolean) {
            viewModelScope.launch {
                repository.saveTimerConfig(config.value.copy(repeatEnabled = enabled))
                serviceController.updateLoop(enabled)
            }
        }

        fun previewSound(soundType: SoundType) {
            soundPreviewManager.previewSound(soundType, config.value.volume)
        }

        fun previewVolume(volume: Float) {
            soundPreviewManager.previewVolume(config.value.soundType, volume)
        }

        private fun stopSoundPreview() {
            soundPreviewManager.stop()
        }
    }
