package com.iganapolsky.randomtimer.monetization

/**
 * Action-triggered paywall aligned with WQTU (>=3 timer_completed in 7d).
 * Presents once after the user completes their third training session.
 */
object QualifiedTrainingPaywallPolicy {
    const val SESSION_THRESHOLD = 3
    const val ENTRY_POINT = "qualified_training_gate"
    const val FEATURE_GATE = "qualified_training_gate"

    fun shouldPresent(
        completedSessionCount: Int,
        isPro: Boolean,
        alreadyPresented: Boolean,
    ): Boolean =
        !isPro &&
            !alreadyPresented &&
            completedSessionCount == SESSION_THRESHOLD
}
