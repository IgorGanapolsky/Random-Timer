package com.iganapolsky.randomtimer.appfunctions

import androidx.appfunctions.AppFunctionContext
import androidx.appfunctions.AppFunctionIntValueConstraint
import androidx.appfunctions.AppFunctionStringValueConstraint
import androidx.appfunctions.service.AppFunction

class RandomTimerAppFunctions(
    private val handler: RandomTimerAppFunctionHandler,
) {
    /**
     * Saves a random tactical timer preset without starting it.
     *
     * @param minSeconds Lowest possible timer duration in seconds.
     * @param maxSeconds Highest possible timer duration in seconds.
     * @param alarmDuration Alarm length in seconds after the random countdown completes.
     * @param soundType Alarm sound to use.
     * @param voiceEnabled Whether AI voice callouts should be enabled.
     * @param voiceGender Which voice persona should be used for callouts.
     * @param hiddenMode Whether the countdown should stay hidden while the timer runs.
     * @param repeatEnabled Whether the timer should automatically loop after each round.
     * @param vibrationEnabled Whether vibration should fire with the alarm.
     * @return The saved timer configuration summary.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun configureRandomTimer(
        appFunctionContext: AppFunctionContext,
        minSeconds: Int,
        maxSeconds: Int,
        @AppFunctionIntValueConstraint(enumValues = [5, 10, 15, 30, 60])
        alarmDuration: Int = TimerDefaults.ALARM_DURATION_SECONDS,
        @AppFunctionStringValueConstraint(
            enumValues = [
                "INTENSE",
                "GENTLE",
                "KLAXON",
                "WHISTLE",
                "BUZZER",
                "GONG",
                "AIRHORN",
                "DRUM_ROLL",
                "SIREN",
                "BELL",
            ],
        )
        soundType: String,
        voiceEnabled: Boolean = false,
        @AppFunctionStringValueConstraint(enumValues = ["MALE", "FEMALE"])
        voiceGender: String,
        hiddenMode: Boolean = false,
        repeatEnabled: Boolean = false,
        vibrationEnabled: Boolean = false,
    ): TimerFunctionResult =
        appFunctionContext.let {
        handler.configureRandomTimer(
            minSeconds = minSeconds,
            maxSeconds = maxSeconds,
            alarmDuration = alarmDuration,
            soundType = soundType,
            voiceEnabled = voiceEnabled,
            voiceGender = voiceGender,
            hiddenMode = hiddenMode,
            repeatEnabled = repeatEnabled,
            vibrationEnabled = vibrationEnabled,
        )
        }

    /**
     * Starts a random tactical timer immediately.
     *
     * @param minSeconds Lowest possible timer duration in seconds.
     * @param maxSeconds Highest possible timer duration in seconds.
     * @param alarmDuration Alarm length in seconds after the random countdown completes.
     * @param soundType Alarm sound to use.
     * @param voiceEnabled Whether AI voice callouts should be enabled.
     * @param voiceGender Which voice persona should be used for callouts.
     * @param hiddenMode Whether the countdown should stay hidden while the timer runs.
     * @param repeatEnabled Whether the timer should automatically loop after each round.
     * @param vibrationEnabled Whether vibration should fire with the alarm.
     * @return The started timer summary, including the chosen target duration.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun startRandomTimer(
        appFunctionContext: AppFunctionContext,
        minSeconds: Int,
        maxSeconds: Int,
        @AppFunctionIntValueConstraint(enumValues = [5, 10, 15, 30, 60])
        alarmDuration: Int = TimerDefaults.ALARM_DURATION_SECONDS,
        @AppFunctionStringValueConstraint(
            enumValues = [
                "INTENSE",
                "GENTLE",
                "KLAXON",
                "WHISTLE",
                "BUZZER",
                "GONG",
                "AIRHORN",
                "DRUM_ROLL",
                "SIREN",
                "BELL",
            ],
        )
        soundType: String,
        voiceEnabled: Boolean = false,
        @AppFunctionStringValueConstraint(enumValues = ["MALE", "FEMALE"])
        voiceGender: String,
        hiddenMode: Boolean = false,
        repeatEnabled: Boolean = false,
        vibrationEnabled: Boolean = false,
    ): TimerFunctionResult =
        appFunctionContext.let {
        handler.startRandomTimer(
            minSeconds = minSeconds,
            maxSeconds = maxSeconds,
            alarmDuration = alarmDuration,
            soundType = soundType,
            voiceEnabled = voiceEnabled,
            voiceGender = voiceGender,
            hiddenMode = hiddenMode,
            repeatEnabled = repeatEnabled,
            vibrationEnabled = vibrationEnabled,
        )
        }

    /**
     * Pauses the currently running timer.
     *
     * @return The active timer state after the pause request.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun pauseTimer(appFunctionContext: AppFunctionContext): TimerFunctionResult =
        appFunctionContext.let { handler.pauseTimer() }

    /**
     * Resumes the currently paused timer.
     *
     * @return The active timer state after the resume request.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun resumeTimer(appFunctionContext: AppFunctionContext): TimerFunctionResult =
        appFunctionContext.let { handler.resumeTimer() }

    /**
     * Stops the current timer and clears its active state.
     *
     * @return The active timer state after the stop request.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun stopTimer(appFunctionContext: AppFunctionContext): TimerFunctionResult =
        appFunctionContext.let { handler.stopTimer() }
}

private object TimerDefaults {
    const val ALARM_DURATION_SECONDS = 10
}
