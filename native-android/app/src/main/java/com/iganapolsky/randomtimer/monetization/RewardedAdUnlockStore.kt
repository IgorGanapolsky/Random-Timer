package com.iganapolsky.randomtimer.monetization

import android.content.Context

/** Persists a single-session Pro sound trial unlocked via rewarded ad. */
class RewardedAdUnlockStore(
    context: Context,
) {
    private val prefs =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun hasActiveUnlock(): Boolean = prefs.getBoolean(KEY_ACTIVE, false)

    fun grantUnlock() {
        prefs.edit().putBoolean(KEY_ACTIVE, true).apply()
    }

    fun consumeUnlock() {
        prefs.edit().putBoolean(KEY_ACTIVE, false).apply()
    }

    companion object {
        private const val PREFS_NAME = "rewarded_ad_unlock"
        private const val KEY_ACTIVE = "pro_sound_trial_active"
    }
}
