package com.iganapolsky.randomtimer.ui.screens

internal object TimerSetupLayoutPolicy {
    // Compact-height policy for modern tall phones where dense controls can exceed the viewport.
    const val COMPACT_HEIGHT_THRESHOLD_DP = 780

    fun isCompactHeightViewport(heightDp: Int): Boolean = heightDp in 1 until COMPACT_HEIGHT_THRESHOLD_DP
}
