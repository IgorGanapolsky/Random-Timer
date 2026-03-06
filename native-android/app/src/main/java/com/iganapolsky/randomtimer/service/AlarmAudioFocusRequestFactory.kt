package com.iganapolsky.randomtimer.service

import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager

/**
 * Central place for alarm audio focus configuration so behavior is consistent and unit-testable.
 *
 * Goal: duck other audio (navigation-app style) rather than pausing it, when possible.
 */
object AlarmAudioFocusRequestFactory {
    internal data class Spec(
        val focusGain: Int,
        val willPauseWhenDucked: Boolean,
        val usage: Int,
        val contentType: Int,
    )

    /**
     * Returns the spec used to build the request.
     *
     * Kept as a pure value so local unit tests can validate behavior without needing Robolectric
     * (framework builders return null under `testOptions.unitTests.isReturnDefaultValues = true`).
     */
    internal fun spec(): Spec =
        Spec(
            focusGain = AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK,
            willPauseWhenDucked = false,
            // Keep USAGE_ALARM so volume stream + routing are alarm-like.
            usage = AudioAttributes.USAGE_ALARM,
            contentType = AudioAttributes.CONTENT_TYPE_SONIFICATION,
        )

    fun build(): AudioFocusRequest {
        val spec = spec()

        val attributes =
            AudioAttributes
                .Builder()
                .setUsage(spec.usage)
                .setContentType(spec.contentType)
                .build()

        return AudioFocusRequest
            .Builder(spec.focusGain)
            .setAudioAttributes(attributes)
            // Keep non-pausing behavior explicit for compatibility across API levels.
            .setWillPauseWhenDucked(spec.willPauseWhenDucked)
            .build()
    }
}
