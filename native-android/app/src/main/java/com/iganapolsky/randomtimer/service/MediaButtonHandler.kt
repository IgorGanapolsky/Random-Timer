package com.iganapolsky.randomtimer.service

import android.view.KeyEvent

/**
 * Pure mapping from media button events to app actions.
 *
 * Keep this logic outside of TimerForegroundService so it's unit-testable without
 * needing to spin up a Service / MediaSession.
 */
object MediaButtonHandler {

    /**
     * Returns true when the given key event should silence the alarm.
     *
     * We only handle ACTION_DOWN to avoid double-triggering on key up.
     */
    fun shouldSilenceAlarm(keyCode: Int, action: Int): Boolean {
        if (action != KeyEvent.ACTION_DOWN) return false

        return when (keyCode) {
            KeyEvent.KEYCODE_MEDIA_PLAY,
            KeyEvent.KEYCODE_MEDIA_PAUSE,
            KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,
            KeyEvent.KEYCODE_HEADSETHOOK,
            KeyEvent.KEYCODE_MEDIA_STOP,
            KeyEvent.KEYCODE_VOLUME_UP,
            KeyEvent.KEYCODE_VOLUME_DOWN,
            -> true

            else -> false
        }
    }

    /** Volume keys should silence the alarm but still adjust system volume. */
    fun isVolumeKey(keyCode: Int): Boolean =
        keyCode == KeyEvent.KEYCODE_VOLUME_UP || keyCode == KeyEvent.KEYCODE_VOLUME_DOWN
}
