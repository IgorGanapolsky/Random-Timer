package com.iganapolsky.randomtimer.ui.viewmodel

import android.app.Application
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.media.MediaPlayer
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.R
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.domain.usecase.StartTimerUseCase
import com.iganapolsky.randomtimer.service.TimerForegroundService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TimerViewModel @Inject constructor(
    private val application: Application,
    private val repository: TimerRepository,
    private val startTimerUseCase: StartTimerUseCase
) : AndroidViewModel(application) {

    val config: StateFlow<TimerConfig> = repository.getTimerConfig()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = TimerConfig.DEFAULT
        )

    private val _timerState = MutableStateFlow<TimerState?>(null)
    val timerState: StateFlow<TimerState?> = _timerState

    private var service: TimerForegroundService? = null
    private var bound = false

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
            val localBinder = binder as TimerForegroundService.LocalBinder
            service = localBinder.getService()
            bound = true
            // Collect service state
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
        // Bind to service to get state updates
        bindToService()
    }

    private fun bindToService() {
        val intent = Intent(application, TimerForegroundService::class.java)
        application.bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
    }

    override fun onCleared() {
        super.onCleared()
        if (bound) {
            application.unbindService(serviceConnection)
            bound = false
        }
    }

    fun updateConfig(newConfig: TimerConfig) {
        viewModelScope.launch {
            repository.saveTimerConfig(newConfig)
        }
    }

    fun startTimer() {
        // Stop any preview sound
        stopSoundPreview()

        viewModelScope.launch {
            val state = startTimerUseCase(config.value)
            _timerState.value = state

            // Start foreground service with primitive extras
            val intent = Intent(application, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_START
                putExtra(TimerForegroundService.EXTRA_TARGET_DURATION_MS, state.targetDuration.inWholeMilliseconds)
                putExtra(TimerForegroundService.EXTRA_REMAINING_DURATION_MS, state.remainingDuration.inWholeMilliseconds)
                putExtra(TimerForegroundService.EXTRA_MIN_SECONDS, state.config.minSeconds)
                putExtra(TimerForegroundService.EXTRA_MAX_SECONDS, state.config.maxSeconds)
                putExtra(TimerForegroundService.EXTRA_ALARM_DURATION, state.config.alarmDuration)
                putExtra(TimerForegroundService.EXTRA_HIDDEN_MODE, state.config.hiddenMode)
                putExtra(TimerForegroundService.EXTRA_REPEAT_ENABLED, state.config.repeatEnabled)
                putExtra(TimerForegroundService.EXTRA_SOUND_TYPE, state.config.soundType.name)
                putExtra(TimerForegroundService.EXTRA_VOLUME, state.config.volume)
                putExtra(TimerForegroundService.EXTRA_VIBRATION_ENABLED, state.config.vibrationEnabled)
            }
            application.startForegroundService(intent)
        }
    }

    fun cancelTimer() {
        viewModelScope.launch {
            repository.clearActiveTimer()
            _timerState.value = null

            val intent = Intent(application, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_STOP
            }
            application.startService(intent)
        }
    }

    fun dismissAlarm() {
        viewModelScope.launch {
            repository.clearActiveTimer()
            _timerState.value = null

            val intent = Intent(application, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_DISMISS_ALARM
            }
            application.startService(intent)
        }
    }

    fun pauseTimer() {
        val intent = Intent(application, TimerForegroundService::class.java).apply {
            action = TimerForegroundService.ACTION_PAUSE
        }
        application.startService(intent)
    }

    fun resumeTimer() {
        val intent = Intent(application, TimerForegroundService::class.java).apply {
            action = TimerForegroundService.ACTION_RESUME
        }
        application.startService(intent)
    }

    fun restartTimer() {
        // Restart with a NEW random duration (used after alarm completes with loop)
        dismissAlarm()
        startTimer()
    }

    fun resetTimer() {
        // Reset to the SAME duration (restart from beginning)
        val intent = Intent(application, TimerForegroundService::class.java).apply {
            action = TimerForegroundService.ACTION_RESET
        }
        application.startService(intent)
    }

    fun updateLoopSetting(enabled: Boolean) {
        viewModelScope.launch {
            repository.saveTimerConfig(config.value.copy(repeatEnabled = enabled))

            // Send update to running service
            val intent = Intent(application, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_UPDATE_LOOP
                putExtra(TimerForegroundService.EXTRA_REPEAT_ENABLED, enabled)
            }
            application.startService(intent)
        }
    }

    private var previewPlayer: MediaPlayer? = null
    private val previewHandler = Handler(Looper.getMainLooper())
    private var currentlyPreviewingSound: SoundType? = null

    fun previewSound(soundType: SoundType) {
        // If same sound is already playing, stop it (toggle behavior)
        if (currentlyPreviewingSound == soundType && previewPlayer?.isPlaying == true) {
            stopSoundPreview()
            return
        }

        // Stop any currently playing preview
        stopSoundPreview()

        // Get the resource for the sound type
        val resourceId = when (soundType) {
            SoundType.INTENSE -> R.raw.alarm
            SoundType.GENTLE -> R.raw.gentle_chime
        }

        // Play the actual sound file
        previewPlayer = MediaPlayer.create(application, resourceId)?.apply {
            isLooping = true
            setVolume(config.value.volume, config.value.volume)
            start()
        }
        currentlyPreviewingSound = soundType

        // Stop after 5 seconds
        previewHandler.postDelayed({
            stopSoundPreview()
        }, 5000)
    }

    fun stopSoundPreview() {
        previewHandler.removeCallbacksAndMessages(null)
        previewPlayer?.stop()
        previewPlayer?.release()
        previewPlayer = null
        currentlyPreviewingSound = null
    }
}
