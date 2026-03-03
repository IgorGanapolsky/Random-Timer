package com.iganapolsky.randomtimer.domain.model

data class TimerPreset(
    val id: String,
    val name: String,
    val emoji: String,
    val minSeconds: Int,
    val maxSeconds: Int,
    val soundType: SoundType = SoundType.INTENSE,
    val alarmDuration: Int = 10,
    val isPro: Boolean = false,
)
