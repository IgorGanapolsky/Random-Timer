package com.iganapolsky.randomtimer.monetization

import android.content.Context

class QualifiedTrainingPaywallStore(
    context: Context,
) {
    private val prefs =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun hasPresented(): Boolean = prefs.getBoolean(KEY_PRESENTED, false)

    fun markPresented() {
        prefs.edit().putBoolean(KEY_PRESENTED, true).apply()
    }

    companion object {
        private const val PREFS_NAME = "qualified_training_paywall"
        private const val KEY_PRESENTED = "presented"
    }
}
