package com.iganapolsky.randomtimer.domain.model

import kotlin.random.Random

/**
 * Inclusive random duration in milliseconds. When [maxMillis] is at least one full second,
 * the result is never below 1000 ms so a running timer does not complete on the first tick.
 */
fun pickRandomDurationMillisInclusive(
    minMillis: Long,
    maxMillis: Long,
    random: Random,
): Long {
    require(maxMillis >= minMillis)
    val lower =
        if (maxMillis >= 1000L) {
            maxOf(minMillis, 1000L)
        } else {
            minMillis
        }
    val from = minOf(lower, maxMillis)
    return random.nextLong(from, maxMillis + 1)
}
