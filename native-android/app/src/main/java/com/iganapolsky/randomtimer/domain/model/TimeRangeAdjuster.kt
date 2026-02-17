package com.iganapolsky.randomtimer.domain.model

/**
 * Shared business rules for the "Goes off in this range" sliders.
 *
 * UX requirement:
 * - Min/max must keep at least [DEFAULT_MIN_GAP_SECONDS] between them.
 * - Dragging one thumb should "push/pull" the other thumb as needed, rather than blocking.
 */
object TimeRangeAdjuster {
    const val DEFAULT_MIN_SECONDS = 0
    const val DEFAULT_MAX_SECONDS = 300
    const val DEFAULT_MIN_GAP_SECONDS = 30

    fun adjustForMinChange(
        currentMinSeconds: Int,
        currentMaxSeconds: Int,
        newMinSeconds: Int,
        minSecondsLimit: Int = DEFAULT_MIN_SECONDS,
        maxSecondsLimit: Int = DEFAULT_MAX_SECONDS,
        minGapSeconds: Int = DEFAULT_MIN_GAP_SECONDS,
    ): Pair<Int, Int> {
        require(minGapSeconds >= 0) { "minGapSeconds must be >= 0" }
        require(maxSecondsLimit >= minSecondsLimit) { "maxSecondsLimit must be >= minSecondsLimit" }

        var min = newMinSeconds.coerceIn(minSecondsLimit, maxSecondsLimit - minGapSeconds)
        var max = currentMaxSeconds.coerceIn(minSecondsLimit + minGapSeconds, maxSecondsLimit)

        if (min > max - minGapSeconds) {
            max = (min + minGapSeconds).coerceAtMost(maxSecondsLimit)
            min = (max - minGapSeconds).coerceAtLeast(minSecondsLimit)
        }

        return min to max
    }

    fun adjustForMaxChange(
        currentMinSeconds: Int,
        currentMaxSeconds: Int,
        newMaxSeconds: Int,
        minSecondsLimit: Int = DEFAULT_MIN_SECONDS,
        maxSecondsLimit: Int = DEFAULT_MAX_SECONDS,
        minGapSeconds: Int = DEFAULT_MIN_GAP_SECONDS,
    ): Pair<Int, Int> {
        require(minGapSeconds >= 0) { "minGapSeconds must be >= 0" }
        require(maxSecondsLimit >= minSecondsLimit) { "maxSecondsLimit must be >= minSecondsLimit" }

        var max = newMaxSeconds.coerceIn(minSecondsLimit + minGapSeconds, maxSecondsLimit)
        var min = currentMinSeconds.coerceIn(minSecondsLimit, maxSecondsLimit - minGapSeconds)

        if (max < min + minGapSeconds) {
            min = (max - minGapSeconds).coerceAtLeast(minSecondsLimit)
            max = (min + minGapSeconds).coerceAtMost(maxSecondsLimit)
        }

        return min to max
    }
}

