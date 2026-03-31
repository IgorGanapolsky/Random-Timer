package com.iganapolsky.randomtimer.domain

import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.VoiceGender

interface SoundPreviewManager {
    fun previewSound(soundType: SoundType, volume: Float)
    fun previewVolume(soundType: SoundType, volume: Float)
    fun previewCommandCue(gender: VoiceGender)
    fun stop()
}
