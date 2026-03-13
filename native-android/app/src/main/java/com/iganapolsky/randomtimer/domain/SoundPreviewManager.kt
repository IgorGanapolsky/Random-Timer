package com.iganapolsky.randomtimer.domain

import com.iganapolsky.randomtimer.domain.model.SoundType

interface SoundPreviewManager {
    fun previewSound(soundType: SoundType, volume: Float)
    fun previewVolume(soundType: SoundType, volume: Float)
    fun previewCommandCue(volume: Float = 1.0f)
    fun stop()
}
