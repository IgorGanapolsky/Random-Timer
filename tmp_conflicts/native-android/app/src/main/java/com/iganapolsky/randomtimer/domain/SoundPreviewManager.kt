package com.iganapolsky.randomtimer.domain

import com.iganapolsky.randomtimer.domain.model.SoundType

interface SoundPreviewManager {
<<<<<<< HEAD
    fun previewSound(
        soundType: SoundType,
        volume: Float,
    )

    fun previewVolume(
        soundType: SoundType,
        volume: Float,
    )

    fun previewCountdownCue()

    fun previewDrillCommand()

||||||| 0ed85a75
    fun previewSound(soundType: SoundType, volume: Float)
    fun previewVolume(soundType: SoundType, volume: Float)
=======
    fun previewSound(soundType: SoundType, volume: Float)
    fun previewVolume(soundType: SoundType, volume: Float)
    fun previewVoiceCallout()
>>>>>>> feat/tactical-gsd-sprint-20260306
    fun stop()
}
