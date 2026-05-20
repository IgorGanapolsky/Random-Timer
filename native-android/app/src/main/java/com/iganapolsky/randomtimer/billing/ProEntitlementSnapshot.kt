package com.iganapolsky.randomtimer.billing

import android.content.Context

/**
 * Lightweight persisted Pro flag so background workers can gate monthly content alerts
 * without initializing BillingClient.
 */
object ProEntitlementSnapshot {
    private const val PREFS_NAME = "pro_prefs"
    private const val KEY_IS_PRO = "is_pro_entitled"

    fun persistIsPro(
        context: Context,
        isPro: Boolean,
    ) {
        context
            .getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(KEY_IS_PRO, isPro)
            .apply()
    }

    fun readIsPro(context: Context): Boolean =
        context
            .getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(KEY_IS_PRO, false)
}
