package com.iganapolsky.randomtimer.domain.model

data class EliteConfig(
    val aiCalloutsEnabled: Boolean = false,
    val calloutFrequency: Double = 5.0, // Seconds between callouts
    val calloutIntensity: Double = 0.5  // 0.0 to 1.0
)
