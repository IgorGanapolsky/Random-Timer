package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.domain.model.TimerState
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.ui.components.CircularTimer
import com.iganapolsky.randomtimer.ui.components.DangerButton
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.components.SecondaryButton
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds
import kotlinx.coroutines.delay

@Composable
fun ActiveTimerScreen(
    state: TimerState,
    onStop: () -> Unit,
    onDismissAlarm: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit,
    onReset: () -> Unit,
    onLoopToggle: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val isComplete = state.status == TimerStatus.COMPLETE || state.status == TimerStatus.ALARM
    val isPaused = state.status == TimerStatus.PAUSED
    var loopEnabled by remember(state.config.repeatEnabled) { mutableStateOf(state.config.repeatEnabled) }
    var showResetFeedback by remember { mutableStateOf(false) }
    var resetFeedbackCounter by remember { mutableStateOf(0) }

    LaunchedEffect(resetFeedbackCounter) {
        if (resetFeedbackCounter == 0) return@LaunchedEffect
        showResetFeedback = true
        delay(1200)
        showResetFeedback = false
    }

    // Format range text (e.g., "30s - 2m")
    val rangeText = remember(state.config) {
        formatRangeText(state.config.minSeconds, state.config.maxSeconds)
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(TimerColors.BackgroundDark)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Top spacer to push content down
            Spacer(modifier = Modifier.weight(0.15f))

            // Loop badge at top (when not in alarm state) - like iOS
            if (!isComplete) {
                LoopBadge(
                    enabled = loopEnabled,
                    onClick = {
                        loopEnabled = !loopEnabled
                        onLoopToggle(loopEnabled)
                    }
                )
                Spacer(modifier = Modifier.height(16.dp))
            }

            // Status text
            AnimatedVisibility(
                visible = !isComplete && !isPaused,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Text(
                    // Random timer - just show "Timer running..." (no warning/danger messages)
                    text = "Timer running...",
                    style = MaterialTheme.typography.titleLarge,
                    color = TimerColors.TextSecondary,
                    textAlign = TextAlign.Center
                )
            }

            // Paused text
            AnimatedVisibility(
                visible = isPaused,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Text(
                    text = "Paused",
                    style = MaterialTheme.typography.titleLarge,
                    color = TimerColors.TextMuted,
                    textAlign = TextAlign.Center
                )
            }

            // Completion text is now shown inside the CircularTimer

            Spacer(modifier = Modifier.height(32.dp))

            // Circular Timer - ALWAYS show range (random timer - user should NEVER see countdown)
            // Hide progress ring since we're not revealing time info
            CircularTimer(
                remainingDuration = state.remainingDuration,
                progress = if (isComplete) 1f else 0f, // Full progress ring when complete
                status = state.status,
                modifier = Modifier.size(280.dp),
                rangeText = rangeText // ALWAYS show range, never countdown
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Info message
            if (showResetFeedback) {
                Text(
                    text = "Timer restarted",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TimerColors.AccentPrimary,
                    textAlign = TextAlign.Center
                )
            } else if (isComplete) {
                Text(
                    text = "Went off after ${formatDurationReadable(state.targetDuration)}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TimerColors.TextSecondary,
                    textAlign = TextAlign.Center
                )
            } else {
                Text(
                    text = "You don't know when it will go off...",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TimerColors.TextMuted,
                    textAlign = TextAlign.Center
                )
            }

            // Alarm countdown with loop badge
            AnimatedVisibility(
                visible = state.status == TimerStatus.ALARM,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                // Just show loop badge (no countdown - random timer)
                LoopBadge(
                    enabled = loopEnabled,
                    onClick = {
                        loopEnabled = !loopEnabled
                        onLoopToggle(loopEnabled)
                    }
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            // Action buttons
            if (isComplete) {
                // Stop - stops alarm and goes home
                DangerButton(
                    text = "Stop",
                    onClick = onDismissAlarm,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Reset - restart with same duration
                SecondaryButton(
                    text = "Reset",
                    onClick = {
                        resetFeedbackCounter += 1
                        onReset()
                    },
                    modifier = Modifier.fillMaxWidth()
                )
            } else {
                // Pause / Resume
                PrimaryButton(
                    text = if (isPaused) "Resume" else "Pause",
                    onClick = if (isPaused) onResume else onPause,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Reset (restart with same config)
                SecondaryButton(
                    text = "Reset",
                    onClick = {
                        resetFeedbackCounter += 1
                        onReset()
                    },
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Stop (go back to home screen)
                SecondaryButton(
                    text = "Stop",
                    onClick = onStop,
                    modifier = Modifier.fillMaxWidth()
                )
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun LoopBadge(
    enabled: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        onClick = onClick,
        modifier = modifier,
        shape = RoundedCornerShape(8.dp),
        color = TimerColors.GlassBackground,
        border = BorderStroke(
            width = 1.dp,
            color = if (enabled) TimerColors.AccentPrimary else TimerColors.GlassBorder
        )
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "🔁",
                style = MaterialTheme.typography.bodySmall
            )
            Text(
                text = if (enabled) "LOOP" else "LOOP OFF",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Medium,
                color = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted
            )
        }
    }
}

private fun formatDurationReadable(duration: kotlin.time.Duration): String {
    val totalSeconds = duration.inWholeSeconds.coerceAtLeast(0)
    val mins = totalSeconds / 60
    val secs = totalSeconds % 60
    return when {
        mins > 0 && secs > 0 -> "${mins}m ${secs}s"
        mins > 0 -> "${mins}m"
        else -> "${secs}s"
    }
}

private fun formatRangeText(minSeconds: Int, maxSeconds: Int): String {
    fun formatTime(seconds: Int): String {
        return if (seconds >= 60) {
            val mins = seconds / 60
            val secs = seconds % 60
            if (secs > 0) "${mins}m ${secs}s" else "${mins}m"
        } else {
            "${seconds}s"
        }
    }
    return "${formatTime(minSeconds)} - ${formatTime(maxSeconds)}"
}

@Preview(showBackground = true)
@Composable
private fun ActiveTimerScreenRunningPreview() {
    RandomTimerTheme {
        ActiveTimerScreen(
            state = TimerState(
                config = TimerConfig.DEFAULT,
                targetDuration = 5.minutes,
                remainingDuration = 2.minutes + 30.seconds,
                status = TimerStatus.RUNNING
            ),
            onStop = {},
            onDismissAlarm = {},
            onPause = {},
            onResume = {},
            onReset = {},
            onLoopToggle = {}
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun ActiveTimerScreenPausedPreview() {
    RandomTimerTheme {
        ActiveTimerScreen(
            state = TimerState(
                config = TimerConfig.DEFAULT,
                targetDuration = 5.minutes,
                remainingDuration = 2.minutes,
                status = TimerStatus.PAUSED
            ),
            onStop = {},
            onDismissAlarm = {},
            onPause = {},
            onResume = {},
            onReset = {},
            onLoopToggle = {}
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun ActiveTimerScreenCompletePreview() {
    RandomTimerTheme {
        ActiveTimerScreen(
            state = TimerState(
                config = TimerConfig.DEFAULT,
                targetDuration = 5.minutes,
                remainingDuration = 0.seconds,
                status = TimerStatus.ALARM
            ),
            onStop = {},
            onDismissAlarm = {},
            onPause = {},
            onResume = {},
            onReset = {},
            onLoopToggle = {}
        )
    }
}
