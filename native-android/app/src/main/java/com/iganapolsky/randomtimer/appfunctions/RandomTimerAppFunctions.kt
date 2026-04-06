package com.iganapolsky.randomtimer.appfunctions

import androidx.appfunctions.AppFunctionContext
import androidx.appfunctions.service.AppFunction

class RandomTimerAppFunctions(
    private val handler: RandomTimerAppFunctionHandler,
) {
    /**
     * Saves a random tactical timer preset without starting it.
     *
     * @param request Timer options to save.
     * @return The saved timer configuration summary.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun configureRandomTimer(
        appFunctionContext: AppFunctionContext,
        request: TimerFunctionRequest,
    ): TimerFunctionResult = appFunctionContext.let { handler.configureRandomTimer(request) }

    /**
     * Starts a random tactical timer immediately.
     *
     * @param request Timer options to start with immediately.
     * @return The started timer summary, including the chosen target duration.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun startRandomTimer(
        appFunctionContext: AppFunctionContext,
        request: TimerFunctionRequest,
    ): TimerFunctionResult = appFunctionContext.let { handler.startRandomTimer(request) }

    /**
     * Pauses the currently running timer.
     *
     * @return The active timer state after the pause request.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun pauseTimer(appFunctionContext: AppFunctionContext): TimerFunctionResult = appFunctionContext.let { handler.pauseTimer() }

    /**
     * Resumes the currently paused timer.
     *
     * @return The active timer state after the resume request.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun resumeTimer(appFunctionContext: AppFunctionContext): TimerFunctionResult = appFunctionContext.let { handler.resumeTimer() }

    /**
     * Stops the current timer and clears its active state.
     *
     * @return The active timer state after the stop request.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun stopTimer(appFunctionContext: AppFunctionContext): TimerFunctionResult = appFunctionContext.let { handler.stopTimer() }
}
