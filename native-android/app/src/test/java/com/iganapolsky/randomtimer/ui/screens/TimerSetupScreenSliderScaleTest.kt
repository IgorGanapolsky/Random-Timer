package com.iganapolsky.randomtimer.ui.screens

import com.iganapolsky.randomtimer.domain.model.TimerConfig
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs

private val rawVisualForTest = ::sliderVisualValue
private val rawActualForTest = ::actualValueFromSlider
private val rawPrecisionForTest = ::usesPrecisionSlider

private fun visualForTest(
    value: Int,
    min: Int,
    max: Int,
    precisionMode: Boolean,
): Float = rawVisualForTest(value, min, max, precisionMode)

private fun actualForTest(
    sliderValue: Float,
    min: Int,
    max: Int,
    stepSize: Int,
    precisionMode: Boolean,
): Int = rawActualForTest(sliderValue, min, max, stepSize, precisionMode)

private fun precisionEnabledForTest(maxRangeSeconds: Int): Boolean = rawPrecisionForTest(maxRangeSeconds)

class TimerSetupScreenSliderScaleTest {
    @Test
    fun `free range keeps linear slider mapping`() {
        val value = 90
        val visual = visualForTest(value, min = 0, max = TimerConfig.MAX_SECONDS_FREE, precisionMode = false)
        val actual =
            actualForTest(
                sliderValue = visual,
                min = 0,
                max = TimerConfig.MAX_SECONDS_FREE,
                stepSize = 5,
                precisionMode = false,
            )

        assertEquals(90f, visual)
        assertEquals(value, actual)
        assertTrue(!precisionEnabledForTest(TimerConfig.MAX_SECONDS_FREE))
    }

    @Test
    fun `pro range uses precision slider mapping`() {
        assertTrue(precisionEnabledForTest(TimerConfig.MAX_SECONDS_PRO))
    }

    @Test
    fun `pro precision slider round trips low and mid values with fine control`() {
        val values = listOf(5, 30, 60, 300, 1200)

        values.forEach { value ->
            val visual =
                visualForTest(
                    value = value,
                    min = 0,
                    max = TimerConfig.MAX_SECONDS_PRO,
                    precisionMode = true,
                )
            val actual =
                actualForTest(
                    sliderValue = visual,
                    min = 0,
                    max = TimerConfig.MAX_SECONDS_PRO,
                    stepSize = 1,
                    precisionMode = true,
                )

            assertTrue(
                "Expected pro slider round-trip within 1s for $value but was $actual",
                abs(actual - value) <= 1,
            )
        }
    }
}
