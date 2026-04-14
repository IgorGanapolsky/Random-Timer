package com.iganapolsky.randomtimer.analytics

import org.junit.Assert.assertEquals
import org.junit.Test

class AndroidInstallChannelTest {
    @Test
    fun playStoreInstallerMapsToPlayStore() {
        assertEquals(AndroidInstallChannel.PLAY_STORE, AndroidInstallChannel.fromInstallerPackageName("com.android.vending"))
    }

    @Test
    fun nullInstallerMapsToUnknown() {
        assertEquals(AndroidInstallChannel.UNKNOWN_INSTALLER, AndroidInstallChannel.fromInstallerPackageName(null))
    }

    @Test
    fun firebaseOrSideloadMapsToNonPlay() {
        assertEquals(
            AndroidInstallChannel.NON_PLAY_INSTALL,
            AndroidInstallChannel.fromInstallerPackageName("com.google.android.packageinstaller"),
        )
    }
}
