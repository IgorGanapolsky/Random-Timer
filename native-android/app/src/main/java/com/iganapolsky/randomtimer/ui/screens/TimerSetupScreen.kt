package com.iganapolsky.randomtimer.ui.screens

import android.content.Intent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimeRangeAdjuster
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.ui.components.GlassCard
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors

private object SetupSpacing {
    val OuterHorizontal = 16.dp
    val ListItem = 16.dp
    val ListTop = 8.dp
    val ListBottom = 24.dp
    val CardContent = 16.dp
    val HeaderToContent = 8.dp
    val ChipGap = 8.dp
    val StartButtonTop = 16.dp
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TimerSetupScreen(
    config: TimerConfig,
    onConfigChange: (TimerConfig) -> Unit,
    onStartTimer: () -> Unit,
    onSoundPreview: (SoundType) -> Unit,
    onVolumePreview: (Float) -> Unit,
    totalSessions: Int = 0,
    currentStreak: Int = 0,
    hasCompletedFirstTimer: Boolean = false,
    isPro: Boolean = false,
    onUpgradeTap: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val haptic = LocalHapticFeedback.current
    var showArsenal by remember { mutableStateOf(isPro) }

    fun updateConfig(
        minSeconds: Int = config.minSeconds,
        maxSeconds: Int = config.maxSeconds,
        alarmDuration: Int = config.alarmDuration,
        repeatEnabled: Boolean = config.repeatEnabled,
        soundType: SoundType = config.soundType,
        volume: Float = config.volume,
        vibrationEnabled: Boolean = config.vibrationEnabled,
    ) {
        onConfigChange(
            config.copy(
                minSeconds = minSeconds,
                maxSeconds = maxSeconds,
                alarmDuration = alarmDuration,
                hiddenMode = false,
                repeatEnabled = repeatEnabled,
                soundType = soundType,
                volume = volume,
                vibrationEnabled = vibrationEnabled,
            ),
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Random Tactical Timer",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = TimerColors.TextPrimary,
                    )
                },
                colors =
                    TopAppBarDefaults.topAppBarColors(
                        containerColor = TimerColors.BackgroundDark,
                    ),
            )
        },
        containerColor = TimerColors.BackgroundDark,
        modifier = modifier,
    ) { paddingValues ->
        LazyColumn(
            modifier =
                Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = SetupSpacing.OuterHorizontal),
            verticalArrangement = Arrangement.spacedBy(SetupSpacing.ListItem),
            contentPadding =
                PaddingValues(
                    top = SetupSpacing.ListTop,
                    bottom = SetupSpacing.ListBottom,
                ),
        ) {
            // Zone 1: Standard Ops
            item {
                Text(
                    text = "STANDARD OPS",
                    style = MaterialTheme.typography.labelSmall,
                    color = TimerColors.TextMuted,
                    modifier = Modifier.padding(start = 4.dp, bottom = 4.dp),
                )
            }

            // Training Stats
            if (hasCompletedFirstTimer) {
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = "Session #${totalSessions + 1}",
                            style = MaterialTheme.typography.labelSmall,
                            color = TimerColors.TextSecondary,
                        )
                        if (currentStreak > 1) {
                            Text(
                                text = "\uD83D\uDD25 $currentStreak day streak",
                                style = MaterialTheme.typography.labelSmall,
                                color = TimerColors.AccentPrimary,
                            )
                        }
                    }
                }
            }

            // 1. Training Window Card
            item {
                GlassCard(modifier = Modifier.fillMaxWidth(), padding = SetupSpacing.CardContent) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "\u23F1\uFE0F Training Window",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.SemiBold,
                                color = TimerColors.TextPrimary,
                            )
                            if (!isPro) {
                                Spacer(modifier = Modifier.weight(1f))
                                Text(
                                    text = "PRO: 1H \uD83D\uDD12",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = TimerColors.AccentPrimary,
                                    modifier = Modifier.clickable { onUpgradeTap() },
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(SetupSpacing.HeaderToContent))

                        val maxRange = if (isPro) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE
                        TimeRangeSliders(
                            minValue = config.minSeconds,
                            maxValue = config.maxSeconds,
                            maxSliderRange = maxRange.toFloat(),
                            minSliderMax = maxRange - 30f,
                            onMinChange = { newMin ->
                                val (min, max) =
                                    TimeRangeAdjuster.adjustForMinChange(
                                        currentMinSeconds = config.minSeconds,
                                        currentMaxSeconds = config.maxSeconds,
                                        newMinSeconds = newMin,
                                        maxSecondsLimit = maxRange,
                                    )
                                updateConfig(minSeconds = min, maxSeconds = max)
                            },
                            onMaxChange = { newMax ->
                                val (min, max) =
                                    TimeRangeAdjuster.adjustForMaxChange(
                                        currentMinSeconds = config.minSeconds,
                                        currentMaxSeconds = config.maxSeconds,
                                        newMaxSeconds = newMax,
                                        maxSecondsLimit = maxRange,
                                    )
                                updateConfig(minSeconds = min, maxSeconds = max)
                            },
                        )
                    }
                }
            }

            // 2. Alarm Setup (Unified: Duration, Sounds, Volume, Vibration)
            item {
                GlassCard(modifier = Modifier.fillMaxWidth(), padding = SetupSpacing.CardContent) {
                    Column {
                        Text(
                            text = "\uD83D\uDD14 Alarm Setup",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.SemiBold,
                            color = TimerColors.TextPrimary,
                        )
                        Spacer(modifier = Modifier.height(SetupSpacing.HeaderToContent))

                        // Duration Chips
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(SetupSpacing.ChipGap),
                        ) {
                            TimerConfig.ALARM_DURATION_OPTIONS.forEach { duration ->
                                FilterChip(
                                    selected = config.alarmDuration == duration,
                                    onClick = {
                                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                        updateConfig(alarmDuration = duration)
                                    },
                                    label = {
                                        Text(
                                            text = "${duration}s",
                                            style = MaterialTheme.typography.labelSmall,
                                            color =
                                                if (config.alarmDuration ==
                                                    duration
                                                ) {
                                                    TimerColors.AccentPrimary
                                                } else {
                                                    TimerColors.TextSecondary
                                                },
                                        )
                                    },
                                    colors =
                                        FilterChipDefaults.filterChipColors(
                                            containerColor = TimerColors.GlassBackground,
                                            selectedContainerColor = TimerColors.AccentPrimary.copy(alpha = 0.2f),
                                        ),
                                    border =
                                        FilterChipDefaults.filterChipBorder(
                                            borderColor = TimerColors.GlassBorder,
                                            selectedBorderColor = TimerColors.AccentPrimary,
                                            enabled = true,
                                            selected = config.alarmDuration == duration,
                                        ),
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        // Core Sounds
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            SoundTypeButton(
                                label = "\uD83D\uDCAA Intense",
                                selected = config.soundType == SoundType.INTENSE,
                                onClick = {
                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                    updateConfig(soundType = SoundType.INTENSE)
                                    onSoundPreview(SoundType.INTENSE)
                                },
                                modifier = Modifier.weight(1f),
                            )
                            SoundTypeButton(
                                label = "\u26A1 Gentle",
                                selected = config.soundType == SoundType.GENTLE,
                                onClick = {
                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                    updateConfig(soundType = SoundType.GENTLE)
                                    onSoundPreview(SoundType.GENTLE)
                                },
                                modifier = Modifier.weight(1f),
                            )
                        }

                        Spacer(modifier = Modifier.height(20.dp))

                        // Volume
                        VolumeSlider(
                            value = config.volume,
                            onValueChange = {
                                updateConfig(volume = it)
                                onVolumePreview(it)
                            },
                            onValueChangeFinished = { },
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        // Vibration
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                text = "\uD83D\uDCF3 Vibration",
                                style = MaterialTheme.typography.labelMedium,
                                color = TimerColors.TextSecondary,
                            )
                            Switch(
                                checked = config.vibrationEnabled,
                                onCheckedChange = { newValue ->
                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                    onConfigChange(
                                        config.copy(vibrationEnabled = newValue),
                                    )
                                },
                                colors =
                                    SwitchDefaults.colors(
                                        checkedThumbColor = TimerColors.AccentPrimary,
                                        checkedTrackColor = TimerColors.AccentPrimary.copy(alpha = 0.5f),
                                        uncheckedThumbColor = TimerColors.TextMuted,
                                        uncheckedTrackColor = TimerColors.SliderTrack,
                                    ),
                            )
                        }
                    }
                }
            }

            // Start Button
            item {
                PrimaryButton(
                    text = "Start Timer",
                    onClick = onStartTimer,
                    modifier =
                        Modifier.padding(top = SetupSpacing.StartButtonTop).graphicsLayer {
                            scaleX = 1.02f
                            scaleY = 1.02f
                        },
                )
            }

            // Zone 2: Tactical Expansion (PRO)
            item {
                Spacer(modifier = Modifier.height(16.dp))
                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = "TACTICAL EXPANSION (PRO) \uD83D\uDD12",
                        style = MaterialTheme.typography.labelSmall,
                        color = if (isPro) TimerColors.AccentPrimary else TimerColors.TextMuted,
                    )

                    if (!isPro) {
                        Text(
                            text = if (showArsenal) "Hide Arsenal" else "View Arsenal",
                            style = MaterialTheme.typography.labelSmall,
                            color = TimerColors.AccentPrimary,
                            fontWeight = FontWeight.Bold,
                            modifier =
                                Modifier.clickable {
                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                    showArsenal = !showArsenal
                                },
                        )
                    }
                }
            }

            // Pro Sound Arsenal
            item {
                AnimatedVisibility(
                    visible = showArsenal,
                    enter = fadeIn() + expandVertically(),
                    exit = fadeOut() + shrinkVertically(),
                ) {
                    GlassCard(
                        modifier =
                            Modifier.fillMaxWidth().graphicsLayer {
                                alpha = if (isPro) 1f else 0.6f
                            },
                        padding = SetupSpacing.CardContent,
                    ) {
                        Column {
                            Text(
                                text = "\uD83C\uDFA7 Sound Arsenal",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.SemiBold,
                                color = if (isPro) TimerColors.TextPrimary else TimerColors.TextMuted,
                            )
                            Spacer(modifier = Modifier.height(SetupSpacing.HeaderToContent))

                            val proSounds = SoundType.PRO
                            for (row in proSounds.chunked(2)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                                ) {
                                    for (sound in row) {
                                        SoundTypeButton(
                                            label =
                                                sound.name
                                                    .lowercase()
                                                    .replaceFirstChar { it.uppercase() }
                                                    .replace("_", " ") +
                                                    if (!isPro) " \uD83D\uDD12" else "",
                                            selected = config.soundType == sound,
                                            onClick = {
                                                if (isPro) {
                                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                    updateConfig(soundType = sound)
                                                    onSoundPreview(sound)
                                                } else {
                                                    onUpgradeTap()
                                                }
                                            },
                                            modifier = Modifier.weight(1f),
                                        )
                                    }
                                    if (row.size == 1) {
                                        Spacer(modifier = Modifier.weight(1f))
                                    }
                                }
                                Spacer(modifier = Modifier.height(8.dp))
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun TimeRangeSliders(
    minValue: Int,
    maxValue: Int,
    maxSliderRange: Float = TimerConfig.MAX_SECONDS_FREE.toFloat(),
    minSliderMax: Float = maxSliderRange - 30f,
    enabled: Boolean = true,
    onMinChange: (Int) -> Unit,
    onMaxChange: (Int) -> Unit,
) {
    val haptic = LocalHapticFeedback.current

    Column {
        // Display
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = formatTime(minValue),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = if (enabled) TimerColors.TextPrimary else TimerColors.TextMuted,
            )
            Text(
                text = " - ",
                style = MaterialTheme.typography.titleMedium,
                color = TimerColors.TextSecondary,
            )
            Text(
                text = formatTime(maxValue),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = if (enabled) TimerColors.TextPrimary else TimerColors.TextMuted,
            )
        }

        // Min slider - label centered above
        Text(
            text = "Minimum: ${formatTime(minValue)}",
            style = MaterialTheme.typography.labelSmall,
            color = TimerColors.TextMuted,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Center,
        )
        Slider(
            value = minValue.toFloat(),
            onValueChange = { raw ->
                val snapped = (raw / 5).toInt() * 5
                if (snapped != minValue) {
                    haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                }
                onMinChange(snapped)
            },
            enabled = enabled,
            valueRange = 0f..minSliderMax,
            modifier = Modifier.semantics { contentDescription = "Minimum time slider" },
            colors =
                SliderDefaults.colors(
                    thumbColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted,
                    activeTrackColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted.copy(alpha = 0.5f),
                    inactiveTrackColor = TimerColors.SliderTrack,
                ),
        )
        PrecisionAdjustRow(
            label = "Fine tune minimum",
            onAdjustLargeDown = { onMinChange((minValue - 30).coerceAtLeast(0)) },
            onAdjustSmallDown = { onMinChange((minValue - 1).coerceAtLeast(0)) },
            onAdjustSmallUp = { onMinChange((minValue + 1).coerceAtMost(minSliderMax.toInt())) },
            onAdjustLargeUp = { onMinChange((minValue + 30).coerceAtMost(minSliderMax.toInt())) },
            enabled = enabled,
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Max slider - label centered above
        Text(
            text = "Maximum: ${formatTime(maxValue)}",
            style = MaterialTheme.typography.labelSmall,
            color = TimerColors.TextMuted,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Center,
        )
        Slider(
            value = maxValue.toFloat(),
            onValueChange = { raw ->
                val snapped = (raw / 5).toInt() * 5
                if (snapped != maxValue) {
                    haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                }
                onMaxChange(snapped)
            },
            enabled = enabled,
            valueRange = 30f..maxSliderRange,
            modifier = Modifier.semantics { contentDescription = "Maximum time slider" },
            colors =
                SliderDefaults.colors(
                    thumbColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted,
                    activeTrackColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted.copy(alpha = 0.5f),
                    inactiveTrackColor = TimerColors.SliderTrack,
                ),
        )
        PrecisionAdjustRow(
            label = "Fine tune maximum",
            onAdjustLargeDown = { onMaxChange((maxValue - 30).coerceAtLeast(30)) },
            onAdjustSmallDown = { onMaxChange((maxValue - 1).coerceAtLeast(30)) },
            onAdjustSmallUp = { onMaxChange((maxValue + 1).coerceAtMost(maxSliderRange.toInt())) },
            onAdjustLargeUp = { onMaxChange((maxValue + 30).coerceAtMost(maxSliderRange.toInt())) },
            enabled = enabled,
        )
    }
}

@Composable
private fun PrecisionAdjustRow(
    label: String,
    onAdjustLargeDown: () -> Unit,
    onAdjustSmallDown: () -> Unit,
    onAdjustSmallUp: () -> Unit,
    onAdjustLargeUp: () -> Unit,
    enabled: Boolean,
) {
    val haptic = LocalHapticFeedback.current
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = TimerColors.TextMuted,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Center,
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            PrecisionButton(label = "-30s", enabled = enabled) {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onAdjustLargeDown()
            }
            PrecisionButton(label = "-1s", enabled = enabled) {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onAdjustSmallDown()
            }
            PrecisionButton(label = "+1s", enabled = enabled) {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onAdjustSmallUp()
            }
            PrecisionButton(label = "+30s", enabled = enabled) {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onAdjustLargeUp()
            }
        }
    }
}

@Composable
private fun PrecisionButton(
    label: String,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(10.dp),
        color = TimerColors.GlassBackground,
        border = BorderStroke(1.dp, TimerColors.GlassBorder),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = if (enabled) TimerColors.TextSecondary else TimerColors.TextMuted,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
        )
    }
}

@Composable
private fun SoundTypeButton(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (isPressed) 0.97f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessMediumLow),
        label = "pressScale",
    )
    val alpha by animateFloatAsState(
        targetValue = if (isPressed) 0.85f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessMediumLow),
        label = "pressAlpha",
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
        shape = RoundedCornerShape(12.dp),
        color =
            if (selected) {
                TimerColors.AccentPrimary.copy(alpha = 0.15f)
            } else {
                TimerColors.GlassBackground
            },
        border =
            BorderStroke(
                width = 1.dp,
                color = if (selected) TimerColors.AccentPrimary else TimerColors.GlassBorder,
            ),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = if (selected) TimerColors.AccentPrimary else TimerColors.TextPrimary,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
        )
    }
}

@Composable
private fun VolumeSlider(
    value: Float,
    onValueChange: (Float) -> Unit,
    onValueChangeFinished: () -> Unit,
) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(
                text = "\uD83D\uDD0A Volume",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextSecondary,
            )
            Text(
                text = "${(value * 100).toInt()}%",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextPrimary,
            )
        }
        Slider(
            value = value,
            onValueChange = onValueChange,
            onValueChangeFinished = onValueChangeFinished,
            colors =
                SliderDefaults.colors(
                    thumbColor = TimerColors.AccentPrimary,
                    activeTrackColor = TimerColors.AccentPrimary,
                    inactiveTrackColor = TimerColors.SliderTrack,
                ),
        )
    }
}

private fun formatTime(seconds: Int): String =
    if (seconds >= 60) {
        val mins = seconds / 60
        val secs = seconds % 60
        if (secs > 0) "${mins}m ${secs}s" else "${mins}m"
    } else {
        "${seconds}s"
    }

@Preview(showBackground = true)
@Composable
private fun TimerSetupScreenPreview() {
    RandomTimerTheme {
        TimerSetupScreen(
            config = TimerConfig.DEFAULT,
            onConfigChange = {},
            onStartTimer = {},
            onSoundPreview = { _ -> },
            onVolumePreview = { _ -> },
        )
    }
}
