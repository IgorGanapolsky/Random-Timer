package com.iganapolsky.randomtimer.data

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import com.iganapolsky.randomtimer.R
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.domain.model.SoundType
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SoundPreviewManagerImpl
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
        private val scope: CoroutineScope,
    ) : SoundPreviewManager {
        private var player: MediaPlayer? = null
        private var stopJob: Job? = null
        private var currentlyPreviewing: SoundType? = null
        private val maxDurationMs = 5000L
        private val volumeStopDelayMs = 1500L

        override fun previewSound(
            soundType: SoundType,
            volume: Float,
        ) {
            if (currentlyPreviewing == soundType && player?.isPlaying == true) {
                stop()
                return
            }
            startPreview(soundType, volume)
            scheduleStop(maxDurationMs)
        }

        override fun previewVolume(
            soundType: SoundType,
            volume: Float,
        ) {
            if (currentlyPreviewing != soundType || player?.isPlaying != true) {
                startPreview(soundType, volume)
            } else {
                player?.setVolume(volume, volume)
            }
            scheduleStop(volumeStopDelayMs)
        }

        override fun stop() {
            stopJob?.cancel()
            stopJob = null
            player?.stop()
            player?.release()
            player = null
            currentlyPreviewing = null
        }

        private fun startPreview(
            soundType: SoundType,
            volume: Float,
        ) {
            stop()

            val resourceId =
                when (soundType) {
                    SoundType.INTENSE -> R.raw.alarm
                    SoundType.GENTLE -> R.raw.gentle_chime
                    SoundType.KLAXON -> R.raw.klaxon
                    SoundType.WHISTLE -> R.raw.whistle
                    SoundType.BUZZER -> R.raw.buzzer
                    SoundType.GONG -> R.raw.gong
                    SoundType.AIRHORN -> R.raw.airhorn
                    SoundType.DRUM_ROLL -> R.raw.drum_roll
                    SoundType.SIREN -> R.raw.siren
                    SoundType.BELL -> R.raw.bell
                }

            player =
                MediaPlayer().apply {
                    setAudioAttributes(
                        AudioAttributes
                            .Builder()
                            .setUsage(AudioAttributes.USAGE_ALARM)
                            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                            .build(),
                    )
                    val afd = context.resources.openRawResourceFd(resourceId) ?: return
                    setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
                    afd.close()
                    isLooping = true
                    setVolume(volume, volume)
                    prepare()
                    start()
                }
            currentlyPreviewing = soundType
        }

        private fun scheduleStop(delayMs: Long) {
            stopJob?.cancel()
            stopJob =
                scope.launch {
                    delay(delayMs)
                    stop()
                }
        }
    }
