package com.iganapolsky.randomtimer.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RangeSlider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import kotlin.time.Duration
import kotlin.time.Duration.Companion.minutes

@Composable
fun DurationRangeSlider(
    minValue: Duration,
    maxValue: Duration,
    onRangeChange: (min: Duration, max: Duration) -> Unit,
    modifier: Modifier = Modifier,
    valueRange: ClosedFloatingPointRange<Float> = 1f..60f,
    steps: Int = 58 // 1-minute steps for 1-60 range
) {
    var sliderPosition by remember(minValue, maxValue) {
        mutableStateOf(
            minValue.inWholeMinutes.toFloat()..maxValue.inWholeMinutes.toFloat()
        )
    }

    Column(modifier = modifier) {
        // Labels
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "Min: ${sliderPosition.start.toInt()} min",
                style = MaterialTheme.typography.bodyMedium,
                color = TimerColors.TextSecondary
            )
            Text(
                text = "Max: ${sliderPosition.endInclusive.toInt()} min",
                style = MaterialTheme.typography.bodyMedium,
                color = TimerColors.TextSecondary
            )
        }

        // Range display
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "${sliderPosition.start.toInt()}",
                style = MaterialTheme.typography.headlineMedium,
                color = TimerColors.TextPrimary
            )
            Text(
                text = " - ",
                style = MaterialTheme.typography.headlineMedium,
                color = TimerColors.TextSecondary
            )
            Text(
                text = "${sliderPosition.endInclusive.toInt()}",
                style = MaterialTheme.typography.headlineMedium,
                color = TimerColors.TextPrimary
            )
            Text(
                text = " min",
                style = MaterialTheme.typography.titleMedium,
                color = TimerColors.TextMuted,
                modifier = Modifier.padding(start = 8.dp)
            )
        }

        // Material 3 Range Slider
        RangeSlider(
            value = sliderPosition,
            onValueChange = { range ->
                // Ensure min is at least 1 minute and there's at least 1 minute difference
                val adjustedStart = range.start.coerceAtLeast(1f)
                val adjustedEnd = range.endInclusive.coerceAtLeast(adjustedStart + 1f)
                sliderPosition = adjustedStart..adjustedEnd.coerceAtMost(valueRange.endInclusive)
            },
            onValueChangeFinished = {
                onRangeChange(
                    sliderPosition.start.toInt().minutes,
                    sliderPosition.endInclusive.toInt().minutes
                )
            },
            valueRange = valueRange,
            steps = steps,
            colors = SliderDefaults.colors(
                thumbColor = TimerColors.SliderThumb,
                activeTrackColor = TimerColors.AccentPrimary,
                activeTickColor = TimerColors.AccentPrimary,
                inactiveTrackColor = TimerColors.SliderTrack,
                inactiveTickColor = TimerColors.SliderTrack
            ),
            modifier = Modifier.fillMaxWidth()
        )

        // Helper text
        Text(
            text = "Timer will go off at a random time within this range",
            style = MaterialTheme.typography.bodySmall,
            color = TimerColors.TextMuted,
            modifier = Modifier.padding(top = 8.dp)
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0F0A1A)
@Composable
private fun DurationRangeSliderPreview() {
    RandomTimerTheme {
        DurationRangeSlider(
            minValue = 5.minutes,
            maxValue = 15.minutes,
            onRangeChange = { _, _ -> },
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        )
    }
}
