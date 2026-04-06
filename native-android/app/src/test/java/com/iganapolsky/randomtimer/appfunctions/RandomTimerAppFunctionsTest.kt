package com.iganapolsky.randomtimer.appfunctions

import androidx.appfunctions.AppFunctionContext
import com.google.common.truth.Truth.assertThat
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Test

class RandomTimerAppFunctionsTest {
    private lateinit var handler: RandomTimerAppFunctionHandler
    private lateinit var functions: RandomTimerAppFunctions
    private val appFunctionContext = mockk<AppFunctionContext>(relaxed = true)
    private val defaultRequest =
        TimerFunctionRequest(
            minSeconds = 10,
            maxSeconds = 20,
            alarmDuration = 10,
            soundType = "INTENSE",
            voiceEnabled = false,
            voiceGender = "MALE",
            hiddenMode = false,
            repeatEnabled = false,
            vibrationEnabled = false,
        )

    @Before
    fun setUp() {
        handler = mockk()
        functions = RandomTimerAppFunctions(handler)
    }

    @Test
    fun configureRandomTimerDelegatesToHandler() =
        runBlocking {
            val request = defaultRequest.copy(voiceEnabled = true, voiceGender = "FEMALE", vibrationEnabled = true)
            val expected =
                timerResult(
                    action = "configure_random_timer",
                    status = "configured",
                    message = "Saved timer configuration.",
                    voiceGender = "FEMALE",
                )

            coEvery { handler.configureRandomTimer(request) } returns expected

            val result =
                functions.configureRandomTimer(
                    appFunctionContext = appFunctionContext,
                    request = request,
                )

            assertThat(result).isEqualTo(expected)
        }

    @Test
    fun startRandomTimerDelegatesToHandler() =
        runBlocking {
            val request = defaultRequest.copy(minSeconds = 20, maxSeconds = 20)
            val expected =
                timerResult(
                    action = "start_random_timer",
                    status = "running",
                    message = "Started random timer.",
                    targetDurationSeconds = 20,
                )

            coEvery { handler.startRandomTimer(request) } returns expected

            val result =
                functions.startRandomTimer(
                    appFunctionContext = appFunctionContext,
                    request = request,
                )

            assertThat(result).isEqualTo(expected)
        }

    @Test
    fun pauseTimerDelegatesToHandler() =
        assertLifecycleDelegation(
            expected = timerResult(action = "pause_timer", status = "paused", message = "Paused active timer."),
            callHandler = { handler.pauseTimer() },
            callFunction = { functions.pauseTimer(appFunctionContext) },
            verifyHandler = { coVerify(exactly = 1) { handler.pauseTimer() } },
        )

    @Test
    fun resumeTimerDelegatesToHandler() =
        assertLifecycleDelegation(
            expected = timerResult(action = "resume_timer", status = "running", message = "Resumed active timer."),
            callHandler = { handler.resumeTimer() },
            callFunction = { functions.resumeTimer(appFunctionContext) },
            verifyHandler = { coVerify(exactly = 1) { handler.resumeTimer() } },
        )

    @Test
    fun stopTimerDelegatesToHandler() =
        assertLifecycleDelegation(
            expected = timerResult(action = "stop_timer", status = "stopped", message = "Stopped active timer."),
            callHandler = { handler.stopTimer() },
            callFunction = { functions.stopTimer(appFunctionContext) },
            verifyHandler = { coVerify(exactly = 1) { handler.stopTimer() } },
        )

    private fun assertLifecycleDelegation(
        expected: TimerFunctionResult,
        callHandler: suspend () -> TimerFunctionResult,
        callFunction: suspend () -> TimerFunctionResult,
        verifyHandler: () -> Unit,
    ) = runBlocking {
        coEvery { callHandler() } returns expected

        val result = callFunction()

        assertThat(result).isEqualTo(expected)
        verifyHandler()
    }

    private fun timerResult(
        action: String,
        status: String,
        message: String,
        targetDurationSeconds: Int = 0,
        voiceGender: String = "MALE",
    ) = TimerFunctionResult(
        action = action,
        status = status,
        message = message,
        entitlementLevel = "elite",
        targetDurationSeconds = targetDurationSeconds,
        soundType = "INTENSE",
        voiceGender = voiceGender,
    )
}
