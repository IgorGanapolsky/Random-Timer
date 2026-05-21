package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
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
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
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
import kotlinx.coroutines.delay
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

@Composable
fun ActiveTimerScreen(
    state: TimerState,
    isPro: Boolean,
    onStop: () -> Unit,
    onDismissAlarm: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit,
    onReset: () -> Unit,
    onLoopToggle: (Boolean) -> Unit,
    onVoiceToggle: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
) {
    val haptic = LocalHapticFeedback.current
    val isComplete = state.status == TimerStatus.COMPLETE || state.status == TimerStatus.ALARM
    val isPaused = state.status == TimerStatus.PAUSED
    var loopEnabled by remember(state.config.repeatEnabled) { mutableStateOf(state.config.repeatEnabled) }
    var voiceEnabled by remember(state.config.voiceEnabled, isPro) { mutableStateOf(isPro && state.config.voiceEnabled) }
    var showResetFeedback by remember { mutableStateOf(false) }
    var resetFeedbackCounter by remember { mutableStateOf(0) }
    val toggleLoop = {
        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
        loopEnabled = !loopEnabled
        onLoopToggle(loopEnabled)
    }
    val toggleVoice = {
        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
        if (isPro) {
            voiceEnabled = !voiceEnabled
            onVoiceToggle(voiceEnabled)
        }
    }

    LaunchedEffect(resetFeedbackCounter) {
        if (resetFeedbackCounter == 0) return@LaunchedEffect
        showResetFeedback = true
        delay(1200)
        showResetFeedback = false
    }

    // Format range text (e.g., "30s - 2m")
    val rangeText =
        remember(state.config) {
            formatRangeText(state.config.minSeconds, state.config.maxSeconds)
        }

    Box(
        modifier =
            modifier
                .fillMaxSize()
                .background(TimerColors.BackgroundDark),
    ) {
        BoxWithConstraints(
            modifier =
                Modifier
                    .fillMaxSize()
                    .windowInsetsPadding(WindowInsets.safeDrawing)
                    .padding(24.dp),
        ) {
            val isLandscape = maxWidth > maxHeight
            val circleSize = if (isLandscape) 220.dp else 280.dp

            @Composable
            fun ActionButtons(modifier: Modifier = Modifier) {
                if (isComplete) {
                    DangerButton(
                        text = "Stop",
                        onClick = onDismissAlarm,
                        modifier = modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    SecondaryButton(
                        text = "Reset",
                        onClick = {
                            resetFeedbackCounter += 1
                            onReset()
                        },
                        modifier = modifier.fillMaxWidth(),
                    )
                } else {
                    PrimaryButton(
                        text = if (isPaused) "Resume" else "Pause",
                        onClick = if (isPaused) onResume else onPause,
                        modifier = modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    SecondaryButton(
                        text = "Reset",
                        onClick = {
                            resetFeedbackCounter += 1
                            onReset()
                        },
                        modifier = modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    SecondaryButton(
                        text = "Stop",
                        onClick = onStop,
                        modifier = modifier.fillMaxWidth(),
                    )
                }
            }

            @Composable
            fun StatusText() {
                val statusText =
                    when {
                        isComplete -> ""
                        isPaused -> "Paused"
                        else -> "Timer running..."
                    }
                Crossfade(
                    targetState = statusText,
                    animationSpec = tween(200),
                    label = "statusText",
                ) { text ->
                    Text(
                        text = text,
                        style = MaterialTheme.typography.titleLarge,
                        color = TimerColors.TextSecondary,
                        textAlign = TextAlign.Center,
                    )
                }
            }

            @Composable
            fun TimerCircle() {
                CircularTimer(
                    progress = state.progress,
                    status = state.status,
                    modifier =
                        Modifier
                            .size(circleSize)
                            .then(
                                if (isComplete) {
                                    Modifier.clickable(
                                        indication = null,
                                        interactionSource = remember { MutableInteractionSource() },
                                    ) {
                                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                        onDismissAlarm()
                                    }
                                } else {
                                    Modifier
                                },
                            ),
                    isHiddenMode = state.config.hiddenMode,
                    rangeText = rangeText,
                )
            }

            @Composable
            fun InfoMessage() {
                if (showResetFeedback) {
                    Text(
                        text = "Timer restarted",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TimerColors.AccentPrimary,
                        textAlign = TextAlign.Center,
                    )
                } else if (isComplete) {
                    Text(
                        text = "Went off after ${formatDurationReadable(state.targetDuration)}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TimerColors.TextSecondary,
                        textAlign = TextAlign.Center,
                    )
                } else {
                    Text(
                        text = "You don't know when it will go off...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = if (isPaused) TimerColors.TextSecondary else TimerColors.TextMuted,
                        textAlign = TextAlign.Center,
                    )
                }
            }

            @Composable
            fun AlarmLoopBadge() {
                AnimatedVisibility(
                    visible = state.status == TimerStatus.ALARM,
                    enter = fadeIn(),
                    exit = fadeOut(),
                ) {
                    LoopBadge(
                        enabled = loopEnabled,
                        repeatRounds = state.config.repeatRounds,
                        roundCount = state.roundCount,
                        onClick = toggleLoop,
                    )
                }
            }

            @Composable
            fun ControlBadges() {
                Box(
                    modifier = Modifier.height(36.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    if (!isComplete) {
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            LoopBadge(
                                enabled = loopEnabled,
                                repeatRounds = state.config.repeatRounds,
                                roundCount = state.roundCount,
                                onClick = toggleLoop,
                            )
                            if (shouldShowVoiceBadge(isPro)) {
                                VoiceBadge(
                                    enabled = voiceEnabled,
                                    isPro = isPro,
                                    onClick = toggleVoice,
                                )
                            }
                        }
                    }
                }
            }

            if (isLandscape) {
                Row(
                    modifier = Modifier.fillMaxSize(),
                    horizontalArrangement = Arrangement.spacedBy(32.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(
                        modifier = Modifier.weight(1f).fillMaxHeight(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                    ) {
                        ControlBadges()
                        Spacer(modifier = Modifier.height(12.dp))

                        StatusText()
                        Spacer(modifier = Modifier.height(16.dp))
                        TimerCircle()
                        Spacer(modifier = Modifier.height(16.dp))
                        InfoMessage()
                        Spacer(modifier = Modifier.height(12.dp))
                        AlarmLoopBadge()
                    }

                    Column(
                        modifier =
                            Modifier
                                .weight(1f)
                                .fillMaxHeight(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                    ) {
                        ActionButtons(modifier = Modifier.fillMaxWidth(0.92f).widthIn(max = 520.dp))
                    }
                }
            } else {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Spacer(modifier = Modifier.weight(0.15f))

                    ControlBadges()
                    Spacer(modifier = Modifier.height(16.dp))

                    StatusText()
                    Spacer(modifier = Modifier.height(32.dp))
                    TimerCircle()
                    Spacer(modifier = Modifier.height(32.dp))
                    InfoMessage()
                    Spacer(modifier = Modifier.height(12.dp))
                    AlarmLoopBadge()
                    Spacer(modifier = Modifier.weight(1f))
                    ActionButtons()
                    Spacer(modifier = Modifier.height(32.dp))
                }
            }
        }
    }
}

@Composable
private fun LoopBadge(
    enabled: Boolean,
    repeatRounds: Int,
    roundCount: Int,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    ToggleBadge(
        icon = "🔁",
        text = loopBadgeText(enabled = enabled, repeatRounds = repeatRounds, roundCount = roundCount),
        enabled = enabled,
        onClick = onClick,
        modifier = modifier,
        scaleLabel = "loopPressScale",
        alphaLabel = "loopPressAlpha",
    )
}

@Composable
private fun VoiceBadge(
    enabled: Boolean,
    isPro: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    ToggleBadge(
        icon = "🔊",
        text = voiceBadgeText(enabled = enabled, isPro = isPro),
        enabled = isPro && enabled,
        onClick = onClick,
        modifier = modifier,
        scaleLabel = "voicePressScale",
        alphaLabel = "voicePressAlpha",
    )
}

@Composable
private fun ToggleBadge(
    icon: String,
    text: String,
    enabled: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    scaleLabel: String,
    alphaLabel: String,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (isPressed) 0.95f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessMediumLow),
        label = scaleLabel,
    )
    val alpha by animateFloatAsState(
        targetValue = if (isPressed) 0.85f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessMediumLow),
        label = alphaLabel,
    )

    Surface(
        onClick = onClick,
        modifier =
            modifier.graphicsLayer {
                scaleX = scale
                scaleY = scale
                this.alpha = alpha
            },
        interactionSource = interactionSource,
        shape = RoundedCornerShape(8.dp),
        color = TimerColors.GlassBackground,
        border =
            BorderStroke(
                width = 1.dp,
                color = if (enabled) TimerColors.AccentPrimary else TimerColors.GlassBorder,
            ),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = icon,
                style = MaterialTheme.typography.bodySmall,
            )
            Text(
                text = text,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Medium,
                color = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted,
            )
        }
    }
}

internal fun loopBadgeText(
    enabled: Boolean,
    repeatRounds: Int,
    roundCount: Int,
): String {
    if (!enabled) {
        return "Loop Off"
    }
    if (repeatRounds == 0) {
        return "Infinite Loop"
    }

    val clampedRound = roundCount.coerceIn(1, repeatRounds)
    return "Loop On · Round $clampedRound/$repeatRounds"
}

internal fun voiceBadgeText(
    enabled: Boolean,
    isPro: Boolean,
): String =
    when {
        !isPro -> "Voice Callouts Locked"
        enabled -> "Voice Callouts On"
        else -> "Voice Callouts Off"
    }

internal fun shouldShowVoiceBadge(isPro: Boolean): Boolean = isPro

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

private fun formatRangeText(
    minSeconds: Int,
    maxSeconds: Int,
): String {
    fun formatTime(seconds: Int): String =
        if (seconds >= 3600) {
            val hrs = seconds / 3600
            val mins = (seconds % 3600) / 60
            if (mins > 0) "${hrs}h ${mins}m" else "${hrs}h"
        } else if (seconds >= 60) {
            val mins = seconds / 60
            val secs = seconds % 60
            if (secs > 0) "$mins:${"%02d".format(secs)}" else "${mins}m"
        } else {
            "${seconds}s"
        }
    return "${formatTime(minSeconds)} - ${formatTime(maxSeconds)}"
}

@Preview(showBackground = true)
@Composable
private fun ActiveTimerScreenRunningPreview() {
    RandomTimerTheme {
        ActiveTimerScreen(
            state =
                TimerState(
                    config = TimerConfig.DEFAULT,
                    targetDuration = 5.minutes,
                    remainingDuration = 2.minutes + 30.seconds,
                    status = TimerStatus.RUNNING,
                ),
            isPro = false,
            onStop = {},
            onDismissAlarm = {},
            onPause = {},
            onResume = {},
            onReset = {},
            onLoopToggle = {},
            onVoiceToggle = {},
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun ActiveTimerScreenPausedPreview() {
    RandomTimerTheme {
        ActiveTimerScreen(
            state =
                TimerState(
                    config = TimerConfig.DEFAULT,
                    targetDuration = 5.minutes,
                    remainingDuration = 2.minutes,
                    status = TimerStatus.PAUSED,
                ),
            isPro = false,
            onStop = {},
            onDismissAlarm = {},
            onPause = {},
            onResume = {},
            onReset = {},
            onLoopToggle = {},
            onVoiceToggle = {},
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun ActiveTimerScreenCompletePreview() {
    RandomTimerTheme {
        ActiveTimerScreen(
            state =
                TimerState(
                    config = TimerConfig.DEFAULT,
                    targetDuration = 5.minutes,
                    remainingDuration = 0.seconds,
                    status = TimerStatus.ALARM,
                ),
            isPro = false,
            onStop = {},
            onDismissAlarm = {},
            onPause = {},
            onResume = {},
            onReset = {},
            onLoopToggle = {},
            onVoiceToggle = {},
        )
    }
}
