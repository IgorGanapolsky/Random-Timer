package com.iganapolsky.randomtimer.analytics

import android.content.pm.PackageManager
import android.os.Build

/**
 * Maps Play installer package to executive-metrics distribution_channel (must stay in sync with iOS
 * values used in PostHog and scripts/executive_metrics_snapshot.py).
 */
object AndroidInstallChannel {
    const val DEV = "dev"
    const val EMULATOR = "emulator"
    const val UI_TEST = "ui_test"
    const val PLAY_STORE = "play_store"
    const val UNKNOWN_INSTALLER = "unknown_installer"
    const val NON_PLAY_INSTALL = "non_play_install"

    fun fromInstallerPackageName(installer: String?): String =
        when (installer) {
            "com.android.vending" -> PLAY_STORE
            null -> UNKNOWN_INSTALLER
            else -> NON_PLAY_INSTALL
        }

    fun installingPackageName(
        pm: PackageManager,
        packageName: String,
    ): String? =
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                pm.getInstallSourceInfo(packageName).installingPackageName
            } else {
                @Suppress("DEPRECATION")
                pm.getInstallerPackageName(packageName)
            }
        } catch (_: Exception) {
            null
        }
}
