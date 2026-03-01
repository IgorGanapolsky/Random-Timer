package com.iganapolsky.randomtimer.domain.model

/**
 * Represents the current subscription or purchase tier of the user.
 */
enum class EntitlementLevel {
    NONE,   // Free user
    BASE,   // One-time purchase (Pro)
    ELITE;  // Subscription (Elite Tactical)

    companion object {
        fun fromValue(value: Int): EntitlementLevel = entries.getOrElse(value) { NONE }
    }
}
