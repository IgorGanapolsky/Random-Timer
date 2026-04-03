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

    @Before
    fun setUp() {
        handler = mockk()
        functions = RandomTimerAppFunctions(handler)
    }

    @Test
    fun `configureRandomTimer delegates to handler`() =
        runBlocking {
            val expected =
                TimerFunctionResult(
                    action = "configure_random_timer",
                    status = "configured",
                    message = "Saved timer configuration.",
                    entitlementLevel = "elite",
                    soundType = "INTENSE",
                    voiceGender = "FEMALE",
                )
            coEvery {
                handler.configureRandomTimer(
                    minSeconds = 10,
                    maxSeconds = 20,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = true,
                    voiceGender = "FEMALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = true,
                )
            } returns expected

            val result =
                functions.configureRandomTimer(
                    appFunctionContext = appFunctionContext,
                    minSeconds = 10,
                    maxSeconds = 20,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = true,
                    voiceGender = "FEMALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = true,
                )

            assertThat(result).isEqualTo(expected)
        }

    @Test
    fun `startRandomTimer delegates to handler`() =
        runBlocking {
            val expected =
                TimerFunctionResult(
                    action = "start_random_timer",
                    status = "running",
                    message = "Started random timer.",
                    entitlementLevel = "elite",
                    targetDurationSeconds = 20,
                    soundType = "INTENSE",
                    voiceGender = "MALE",
                )
            coEvery {
                handler.startRandomTimer(
                    minSeconds = 20,
                    maxSeconds = 20,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = false,
                    voiceGender = "MALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                )
            } returns expected

            val result =
                functions.startRandomTimer(
                    appFunctionContext = appFunctionContext,
                    minSeconds = 20,
                    maxSeconds = 20,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = false,
                    voiceGender = "MALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                )

            assertThat(result).isEqualTo(expected)
        }

    @Test
    fun `configureRandomTimer applies default alarm duration when omitted`() =
        runBlocking {
            val expected =
                TimerFunctionResult(
                    action = "configure_random_timer",
                    status = "configured",
                    message = "Saved timer configuration.",
                    entitlementLevel = "elite",
                    soundType = "INTENSE",
                    voiceGender = "MALE",
                )
            coEvery {
                handler.configureRandomTimer(
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
            } returns expected

            val result =
                functions.configureRandomTimer(
                    appFunctionContext = appFunctionContext,
                    minSeconds = 10,
                    maxSeconds = 20,
                    soundType = "INTENSE",
                    voiceGender = "MALE",
                )

            assertThat(result).isEqualTo(expected)
        }

    @Test
    fun `startRandomTimer applies default alarm duration when omitted`() =
        runBlocking {
            val expected =
                TimerFunctionResult(
                    action = "start_random_timer",
                    status = "running",
                    message = "Started random timer.",
                    entitlementLevel = "elite",
                    targetDurationSeconds = 20,
                    soundType = "INTENSE",
                    voiceGender = "MALE",
                )
            coEvery {
                handler.startRandomTimer(
                    minSeconds = 20,
                    maxSeconds = 20,
                    alarmDuration = 10,
                    soundType = "INTENSE",
                    voiceEnabled = false,
                    voiceGender = "MALE",
                    hiddenMode = false,
                    repeatEnabled = false,
                    vibrationEnabled = false,
                )
            } returns expected

            val result =
                functions.startRandomTimer(
                    appFunctionContext = appFunctionContext,
                    minSeconds = 20,
                    maxSeconds = 20,
                    soundType = "INTENSE",
                    voiceGender = "MALE",
                )

            assertThat(result).isEqualTo(expected)
        }

    @Test
    fun `pauseTimer delegates to handler`() =
        runBlocking {
            val expected =
                TimerFunctionResult(
                    action = "pause_timer",
                    status = "paused",
                    message = "Paused active timer.",
                    entitlementLevel = "elite",
                    soundType = "INTENSE",
                    voiceGender = "MALE",
                )
            coEvery { handler.pauseTimer() } returns expected

            val result = functions.pauseTimer(appFunctionContext)

            assertThat(result).isEqualTo(expected)
            coVerify(exactly = 1) { handler.pauseTimer() }
        }

    @Test
    fun `resumeTimer delegates to handler`() =
        runBlocking {
            val expected =
                TimerFunctionResult(
                    action = "resume_timer",
                    status = "running",
                    message = "Resumed active timer.",
                    entitlementLevel = "elite",
                    soundType = "INTENSE",
                    voiceGender = "MALE",
                )
            coEvery { handler.resumeTimer() } returns expected

            val result = functions.resumeTimer(appFunctionContext)

            assertThat(result).isEqualTo(expected)
            coVerify(exactly = 1) { handler.resumeTimer() }
        }

    @Test
    fun `stopTimer delegates to handler`() =
        runBlocking {
            val expected =
                TimerFunctionResult(
                    action = "stop_timer",
                    status = "stopped",
                    message = "Stopped active timer.",
                    entitlementLevel = "elite",
                    soundType = "INTENSE",
                    voiceGender = "MALE",
                )
            coEvery { handler.stopTimer() } returns expected

            val result = functions.stopTimer(appFunctionContext)

            assertThat(result).isEqualTo(expected)
            coVerify(exactly = 1) { handler.stopTimer() }
        }
}
