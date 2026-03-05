package com.iganapolsky.randomtimer.domain.model

import java.util.UUID

data class WorkoutSession(
    val id: String = UUID.randomUUID().toString(),
    val timestamp: Long = System.currentTimeMillis(),
    val targetDurationSeconds: Int,
    val soundType: SoundType,
    val completed: Boolean,
)
