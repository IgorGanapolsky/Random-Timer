package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimeRangeAdjuster
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.ui.components.GlassCard
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.theme.TimerColors

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
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
    onSecretUnlock: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val haptic = LocalHapticFeedback.current
    var showArsenal by remember { mutableStateOf(isPro) }
    var showDirectEntryMin by remember { mutableStateOf(false) }
    var showDirectEntryMax by remember { mutableStateOf(false) }

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

    if (showDirectEntryMin) {
        DirectTimeEntryDialog(
            title = "Set Minimum Time",
            initialSeconds = config.minSeconds,
            onDismiss = { showDirectEntryMin = false },
            onConfirm = { seconds ->
                val limit = if (isPro) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE
                val adjusted = TimeRangeAdjuster.adjustForMinChange(config.minSeconds, config.maxSeconds, seconds, limit)
                updateConfig(minSeconds = adjusted.min, maxSeconds = adjusted.max)
                showDirectEntryMin = false
            }
        )
    }

    if (showDirectEntryMax) {
        DirectTimeEntryDialog(
            title = "Set Maximum Time",
            initialSeconds = config.maxSeconds,
            onDismiss = { showDirectEntryMax = false },
            onConfirm = { seconds ->
                val limit = if (isPro) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE
                val adjusted = TimeRangeAdjuster.adjustForMaxChange(config.minSeconds, config.maxSeconds, seconds, limit)
                updateConfig(minSeconds = adjusted.min, maxSeconds = adjusted.max)
                showDirectEntryMax = false
            }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Random Tactical Timer", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = TimerColors.BackgroundDark)
            )
        },
        containerColor = TimerColors.BackgroundDark
    ) { padding ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(padding).padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            contentPadding = PaddingValues(top = 8.dp, bottom = 24.dp)
        ) {
            item {
                Text("STANDARD OPS", style = MaterialTheme.typography.labelSmall, color = TimerColors.TextMuted)
            }

            item {
                GlassCard(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("\u23F1\uFE0F Training Window", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
                            if (!isPro) {
                                Spacer(Modifier.weight(1f))
                                Text(
                                    "PRO: 1H \uD83D\uDD12",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = TimerColors.AccentPrimary,
                                    modifier = Modifier.combinedClickable(
                                        interactionSource = remember { MutableInteractionSource() },
                                        indication = null,
                                        onClick = onUpgradeTap,
                                        onLongClick = {
                                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                            onSecretUnlock()
                                        }
                                    )
                                )
                            }
                        }
                        
                        Spacer(Modifier.height(12.dp))
                        
                        TimeRangeScrubber(
                            minValue = config.minSeconds,
                            maxValue = config.maxSeconds,
                            maxLimit = (if (isPro) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE).toFloat(),
                            onRangeChange = { minVal, maxVal -> updateConfig(minSeconds = minVal, maxSeconds = maxVal) },
                            onMinClick = { showDirectEntryMin = true },
                            onMaxClick = { showDirectEntryMax = true }
                        )
                    }
                }
            }

            item {
                GlassCard(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("\uD83D\uDD14 Alarm Setup", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
                        Spacer(Modifier.height(12.dp))
                        
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            TimerConfig.ALARM_DURATION_OPTIONS.forEach { duration ->
                                FilterChip(
                                    selected = config.alarmDuration == duration,
                                    onClick = { updateConfig(alarmDuration = duration) },
                                    label = { Text("${duration}s") }
                                )
                            }
                        }

                        Spacer(Modifier.height(16.dp))

                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            SoundTypeButton(
                                label = "Intense \uD83D\uDD25",
                                selected = config.soundType == SoundType.INTENSE,
                                onClick = { updateConfig(soundType = SoundType.INTENSE); onSoundPreview(SoundType.INTENSE) },
                                modifier = Modifier.weight(1f)
                            )
                            SoundTypeButton(
                                label = "Gentle \uD83D\uDCA7",
                                selected = config.soundType == SoundType.GENTLE,
                                onClick = { updateConfig(soundType = SoundType.GENTLE); onSoundPreview(SoundType.GENTLE) },
                                modifier = Modifier.weight(1f)
                            )
                        }

                        Spacer(Modifier.height(20.dp))

                        VolumeSlider(config.volume) { updateConfig(volume = it); onVolumePreview(it) }

                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                            Text("\uD83D\uDCF3 Vibration", style = MaterialTheme.typography.labelMedium)
                            Spacer(Modifier.weight(1f))
                            Switch(checked = config.vibrationEnabled, onCheckedChange = { updateConfig(vibrationEnabled = it) })
                        }
                    }
                }
            }

            item {
                PrimaryButton(text = "Start Timer", onClick = onStartTimer)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TimeRangeScrubber(
    minValue: Int,
    maxValue: Int,
    maxLimit: Float,
    onRangeChange: (Int, Int) -> Unit,
    onMinClick: () -> Unit,
    onMaxClick: () -> Unit
) {
    val haptic = LocalHapticFeedback.current
    Column {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            TimeChip("Min", formatTime(minValue), onMinClick)
            Text("\u2192", color = TimerColors.TextMuted, modifier = Modifier.align(Alignment.CenterVertically))
            TimeChip("Max", formatTime(maxValue), onMaxClick)
        }
        Spacer(Modifier.height(16.dp))
        RangeSlider(
            value = minValue.toFloat()..maxValue.toFloat(),
            onValueChange = { range ->
                val newMin = (range.start / 5).toInt() * 5
                val newMax = (range.endInclusive / 5).toInt() * 5
                if (newMin != minValue || newMax != maxValue) {
                    haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                    onRangeChange(newMin, newMax)
                }
            },
            valueRange = 0f..maxLimit,
            colors = SliderDefaults.colors(thumbColor = TimerColors.AccentPrimary, activeTrackColor = TimerColors.AccentPrimary)
        )
    }
}

@Composable
private fun TimeChip(label: String, value: String, onClick: () -> Unit) {
    Column {
        Text(label, style = MaterialTheme.typography.labelSmall, color = TimerColors.TextMuted)
        Surface(
            onClick = onClick,
            color = TimerColors.GlassBackground,
            shape = RoundedCornerShape(8.dp),
            border = BorderStroke(1.dp, TimerColors.GlassBorder),
            modifier = Modifier.padding(top = 4.dp)
        ) {
            Text(value, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp))
        }
    }
}

@Composable
private fun DirectTimeEntryDialog(title: String, initialSeconds: Int, onDismiss: () -> Unit, onConfirm: (Int) -> Unit) {
    var minutes by remember { mutableStateOf((initialSeconds / 60).toString()) }
    var seconds by remember { mutableStateOf((initialSeconds % 60).toString()) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = minutes, onValueChange = { minutes = it.filter { c -> c.isDigit() } }, label = { Text("Min") }, modifier = Modifier.weight(1f), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                OutlinedTextField(value = seconds, onValueChange = { seconds = it.filter { c -> c.isDigit() } }, label = { Text("Sec") }, modifier = Modifier.weight(1f), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            }
        },
        confirmButton = { TextButton(onClick = { onConfirm((minutes.toIntOrNull() ?: 0) * 60 + (seconds.toIntOrNull() ?: 0)) }) { Text("Apply") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}

@Composable
private fun SoundTypeButton(label: String, selected: Boolean, onClick: () -> Unit, modifier: Modifier) {
    Surface(
        onClick = onClick,
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = if (selected) TimerColors.AccentPrimary.copy(alpha = 0.15f) else TimerColors.GlassBackground,
        border = BorderStroke(1.dp, if (selected) TimerColors.AccentPrimary else TimerColors.GlassBorder)
    ) {
        Text(label, modifier = Modifier.padding(16.dp), textAlign = TextAlign.Center, color = if (selected) TimerColors.AccentPrimary else TimerColors.TextPrimary)
    }
}

@Composable
private fun VolumeSlider(value: Float, onValueChange: (Float) -> Unit) {
    Slider(value = value, onValueChange = onValueChange, colors = SliderDefaults.colors(thumbColor = TimerColors.AccentPrimary, activeTrackColor = TimerColors.AccentPrimary))
}

private fun formatTime(seconds: Int): String = if (seconds >= 60) "${seconds/60}m ${seconds%60}s".replace(" 0s", "") else "${seconds}s"
