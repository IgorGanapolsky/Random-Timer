package com.iganapolsky.randomtimer.domain

import com.iganapolsky.randomtimer.domain.model.SoundType

interface SoundPreviewManager {
    fun previewSound(soundType: SoundType, volume: Float)
    fun previewVolume(soundType: SoundType, volume: Float)
    fun stop()
}
