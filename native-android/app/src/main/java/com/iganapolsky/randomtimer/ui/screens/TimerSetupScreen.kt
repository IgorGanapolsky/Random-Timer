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
import androidx.compose.foundation.gestures.detectTapGestures
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
import androidx.compose.ui.input.pointer.pointerInput
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
import kotlin.math.roundToInt

private object SetupSpacing {
    val OuterHorizontal = 16.dp
    val ListItem = 16.dp
    val ListTop = 8.dp
    val ListBottom = 24.dp
    val CardContent = 12.dp
    val HeaderToContent = 12.dp
}

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
    isElite: Boolean = false,
    onUpgradeTap: () -> Unit = {},
    onSecretUnlock: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val haptic = LocalHapticFeedback.current
    val scope = rememberCoroutineScope()
    
    // Expanded states for the two Training Window options
    var standardExpanded by remember { mutableStateOf(config.maxSeconds <= TimerConfig.MAX_SECONDS_FREE) }
    var tacticalExpanded by remember { mutableStateOf(config.maxSeconds > TimerConfig.MAX_SECONDS_FREE) }
    var arsenalVisible by remember { mutableStateOf(isPro) }
    
    var showDirectEntryMin by remember { mutableStateOf(false) }
    var showDirectEntryMax by remember { mutableStateOf(false) }

    fun updateConfig(
        newMin: Int = config.minSeconds,
        newMax: Int = config.maxSeconds,
        alarmDuration: Int = config.alarmDuration,
        repeatEnabled: Boolean = config.repeatEnabled,
        soundType: SoundType = config.soundType,
        volume: Float = config.volume,
        vibrationEnabled: Boolean = config.vibrationEnabled,
    ) {
        onConfigChange(
            config.copy(
                minSeconds = newMin,
                maxSeconds = newMax,
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
                val limit = if (tacticalExpanded) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE
                val pair = TimeRangeAdjuster.adjustForMinChange(config.minSeconds, config.maxSeconds, seconds, maxSecondsLimit = limit)
                updateConfig(newMin = pair.first, newMax = pair.second)
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
                val limit = if (tacticalExpanded) TimerConfig.MAX_SECONDS_PRO else TimerConfig.MAX_SECONDS_FREE
                val pair = TimeRangeAdjuster.adjustForMaxChange(config.minSeconds, config.maxSeconds, seconds, maxSecondsLimit = limit)
                updateConfig(newMin = pair.first, newMax = pair.second)
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
            verticalArrangement = Arrangement.spacedBy(SetupSpacing.ListItem),
            contentPadding = PaddingValues(top = 8.dp, bottom = 24.dp)
        ) {
            item {
                Text("TRAINING MISSIONS", style = MaterialTheme.typography.labelSmall, color = TimerColors.TextMuted)
            }

            // 1. Standard Ops Card
            item {
                ExpandableTrainingCard(
                    title = "Standard Ops (5m)",
                    subtitle = "High-precision short drills",
                    isExpanded = standardExpanded,
                    onExpandToggle = { 
                        standardExpanded = !standardExpanded
                        if (standardExpanded) tacticalExpanded = false 
                    },
                    minValue = config.minSeconds,
                    maxValue = config.maxSeconds,
                    maxLimit = TimerConfig.MAX_SECONDS_FREE.toFloat(),
                    onRangeChange = { rMin, rMax -> updateConfig(newMin = rMin, newMax = rMax) },
                    onMinClick = { showDirectEntryMin = true },
                    onMaxClick = { showDirectEntryMax = true }
                )
            }

            // 2. Tactical Expansion Card
            item {
                ExpandableTrainingCard(
                    title = "Tactical Expansion (1h)",
                    subtitle = "Extended endurance training",
                    isExpanded = tacticalExpanded,
                    isLocked = !isPro,
                    onExpandToggle = { 
                        if (isPro) {
                            tacticalExpanded = !tacticalExpanded
                            if (tacticalExpanded) standardExpanded = false
                        } else {
                            onUpgradeTap()
                        }
                    },
                    minValue = config.minSeconds,
                    maxValue = config.maxSeconds,
                    maxLimit = TimerConfig.MAX_SECONDS_PRO.toFloat(),
                    onRangeChange = { rMin, rMax -> updateConfig(newMin = rMin, newMax = rMax) },
                    onMinClick = { showDirectEntryMin = true },
                    onMaxClick = { showDirectEntryMax = true },
                    onSecretUnlock = onSecretUnlock
                )
            }

            // 3. AI Coach Section (ELITE ONLY)
            if (isElite || tacticalExpanded) {
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
                                    modifier =
                                        Modifier.combinedClickable(
                                            interactionSource = remember { MutableInteractionSource() },
                                            indication = null,
                                            onClick = { onUpgradeTap() },
                                            onLongClick = {
                                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                onSecretUnlock()
                                            },
                                        ),
                                )
                            }
                        }
                    }
                }
            }

            item {
                Spacer(Modifier.height(8.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("SIGNAL CONFIGURATION", style = MaterialTheme.typography.labelSmall, color = TimerColors.TextMuted)
                    if (!isPro) {
                        Text(
                            text = if (arsenalVisible) "Hide Arsenal" else "View Arsenal",
                            style = MaterialTheme.typography.labelSmall,
                            color = TimerColors.AccentPrimary,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.clickable { arsenalVisible = !arsenalVisible }
                        )
                    }
                }
            }

            // Signal Configuration Card
            item {
                GlassCard(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("\uD83D\uDD14 Output Control", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
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

            // 3. Pro Sound Arsenal
            item {
                AnimatedVisibility(
                    visible = arsenalVisible || isPro,
                    enter = fadeIn() + expandVertically(),
                    exit = fadeOut() + shrinkVertically()
                ) {
                    GlassCard(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("\uD83C\uDFA7 Sound Arsenal", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
                            Spacer(Modifier.height(12.dp))

                            val proSounds = SoundType.PRO
                            proSounds.chunked(2).forEach { row ->
                                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                    row.forEach { sound ->
                                        SoundTypeButton(
                                            label = sound.name.lowercase().replaceFirstChar { it.uppercase() } + (if (isPro) "" else " \uD83D\uDD12"),
                                            selected = config.soundType == sound,
                                            onClick = {
                                                if (isPro) {
                                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                    updateConfig(soundType = sound)
                                                    onSoundPreview(sound)
                                                } else {
                                                    onSoundPreview(sound)
                                                }
                                            },
                                            modifier = Modifier.weight(1f)
                                        )
                                    }
                                    if (row.size == 1) Spacer(Modifier.weight(1f))
                                }
                                Spacer(Modifier.height(8.dp))
                            }

                            if (!isPro) {
                                Column(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                ) {
                                    Text(
                                        text = "Tap a sound to preview. Unlock Pro to equip it.",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = TimerColors.TextMuted,
                                        textAlign = TextAlign.Center,
                                    )
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        text = "Unlock Pro",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = TimerColors.AccentPrimary,
                                        fontWeight = FontWeight.SemiBold,
                                        modifier = Modifier.clickable(onClick = onUpgradeTap),
                                    )
                                }
                            }
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

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ExpandableTrainingCard(
    title: String,
    subtitle: String,
    isExpanded: Boolean,
    isLocked: Boolean = false,
    onExpandToggle: () -> Unit,
    minValue: Int,
    maxValue: Int,
    maxLimit: Float,
    onRangeChange: (Int, Int) -> Unit,
    onMinClick: () -> Unit,
    onMaxClick: () -> Unit,
    onSecretUnlock: () -> Unit = {}
) {
    val haptic = LocalHapticFeedback.current
    
    GlassCard(
        modifier = Modifier.fillMaxWidth().clickable { onExpandToggle() },
        padding = 0.dp
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(
                        title + if (isLocked) " \uD83D\uDD12" else "",
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.Bold,
                        color = if (isLocked) TimerColors.TextMuted else TimerColors.TextPrimary,
                        modifier = Modifier.combinedClickable(
                            interactionSource = remember { MutableInteractionSource() },
                            indication = null,
                            onClick = onExpandToggle,
                            onLongClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                onSecretUnlock()
                            }
                        )
                    )
                    Text(subtitle, style = MaterialTheme.typography.labelSmall, color = TimerColors.TextMuted)
                }
                Text(text = if (isExpanded) "\u25B4" else "\u25BE", color = TimerColors.TextMuted)
            }

            AnimatedVisibility(visible = isExpanded && !isLocked) {
                Column(Modifier.padding(top = 16.dp)) {
                    TimeRangeScrubber(minValue, maxValue, maxLimit, onRangeChange, onMinClick, onMaxClick)
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TimeRangeScrubber(minValue: Int, maxValue: Int, maxLimit: Float, onRangeChange: (Int, Int) -> Unit, onMinClick: () -> Unit, onMaxClick: () -> Unit) {
    val haptic = LocalHapticFeedback.current
    val coarseNudgeStep = 5
    val fineNudgeStep = 1
    val minGapSeconds = TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS
    val maxSliderRangeInt = maxSliderRange.toInt()
    val minSliderMaxInt = minSliderMax.toInt()

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
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
        Text(
            text = "Coarse: slider + \u00B15s  \u2022  Fine: \u00B11s buttons",
            style = MaterialTheme.typography.labelSmall,
            color = TimerColors.TextMuted,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Center,
        )

        // Min slider with nudge
        Column {
            Text(
                text = "Minimum: ${formatTime(minValue)}",
                style = MaterialTheme.typography.labelSmall,
                color = TimerColors.TextMuted,
                modifier = Modifier.fillMaxWidth(),
                textAlign = TextAlign.Center,
            )
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                NudgeButton(
                    label = "-5s",
                    enabled = enabled && minValue >= coarseNudgeStep,
                    onClick = { onMinChange(minValue - coarseNudgeStep) },
                )
                Slider(
                    value = minValue.toFloat(),
                    onValueChange = { raw ->
                        val snapped = snapToStep(raw, coarseNudgeStep, 0, minSliderMaxInt)
                        if (snapped != minValue) {
                            haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                        }
                        onMinChange(snapped)
                    },
                    enabled = enabled,
                    valueRange = 0f..minSliderMax,
                    modifier =
                        Modifier.weight(1f).semantics { contentDescription = "Minimum time slider" },
                    colors =
                        SliderDefaults.colors(
                            thumbColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted,
                            activeTrackColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted.copy(alpha = 0.5f),
                            inactiveTrackColor = TimerColors.SliderTrack,
                        ),
                )
                NudgeButton(
                    label = "+5s",
                    enabled = enabled && minValue <= (maxValue - minGapSeconds - coarseNudgeStep),
                    onClick = { onMinChange(minValue + coarseNudgeStep) },
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                NudgeButton(
                    label = "-1s",
                    enabled = enabled && minValue >= fineNudgeStep,
                    onClick = { onMinChange(minValue - fineNudgeStep) },
                )
                Spacer(modifier = Modifier.width(8.dp))
                NudgeButton(
                    label = "+1s",
                    enabled = enabled && minValue <= (maxValue - minGapSeconds - fineNudgeStep),
                    onClick = { onMinChange(minValue + fineNudgeStep) },
                )
            }
        }

        // Max slider with nudge
        Column {
            Text(
                text = "Maximum: ${formatTime(maxValue)}",
                style = MaterialTheme.typography.labelSmall,
                color = TimerColors.TextMuted,
                modifier = Modifier.fillMaxWidth(),
                textAlign = TextAlign.Center,
            )
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                NudgeButton(
                    label = "-5s",
                    enabled = enabled && maxValue >= (minValue + minGapSeconds + coarseNudgeStep),
                    onClick = { onMaxChange(maxValue - coarseNudgeStep) },
                )
                Slider(
                    value = maxValue.toFloat(),
                    onValueChange = { raw ->
                        val dynamicMin = minValue + minGapSeconds
                        val snapped = snapToStep(raw, coarseNudgeStep, dynamicMin, maxSliderRangeInt)
                        if (snapped != maxValue) {
                            haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                        }
                        onMaxChange(snapped)
                    },
                    enabled = enabled,
                    valueRange = (minValue + minGapSeconds).toFloat()..maxSliderRange,
                    modifier =
                        Modifier.weight(1f).semantics { contentDescription = "Maximum time slider" },
                    colors =
                        SliderDefaults.colors(
                            thumbColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted,
                            activeTrackColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted.copy(alpha = 0.5f),
                            inactiveTrackColor = TimerColors.SliderTrack,
                        ),
                )
                NudgeButton(
                    label = "+5s",
                    enabled = enabled && maxValue <= (maxSliderRangeInt - coarseNudgeStep),
                    onClick = { onMaxChange(maxValue + coarseNudgeStep) },
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                NudgeButton(
                    label = "-1s",
                    enabled = enabled && maxValue >= (minValue + minGapSeconds + fineNudgeStep),
                    onClick = { onMaxChange(maxValue - fineNudgeStep) },
                )
                Spacer(modifier = Modifier.width(8.dp))
                NudgeButton(
                    label = "+1s",
                    enabled = enabled && maxValue <= (maxSliderRangeInt - fineNudgeStep),
                    onClick = { onMaxChange(maxValue + fineNudgeStep) },
                )
            }
        }
    }
}

private fun snapToStep(
    rawValue: Float,
    stepSize: Int,
    min: Int,
    max: Int,
): Int {
    val snapped = (rawValue / stepSize).roundToInt() * stepSize
    return snapped.coerceIn(min, max)
}

@Composable
private fun NudgeButton(
    label: String,
    enabled: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(10.dp),
        color = if (enabled) TimerColors.GlassBackground else TimerColors.BackgroundDark,
        border =
            BorderStroke(
                1.dp,
                if (enabled) TimerColors.GlassBorder else TimerColors.GlassBorder.copy(alpha = 0.5f),
            ),
        modifier = modifier.width(52.dp).height(40.dp),
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold,
                color = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted,
                textAlign = TextAlign.Center,
            )
        }
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
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            TimeChip("Min", formatTime(minValue), onMinClick)
            Text("\u2192", color = TimerColors.TextMuted, modifier = Modifier.align(Alignment.CenterVertically))
            TimeChip("Max", formatTime(maxValue), onMaxClick)
        }
        Spacer(Modifier.height(16.dp))
        RangeSlider(
            value = minValue.coerceAtMost(maxLimit.toInt()).toFloat()..maxValue.coerceAtMost(maxLimit.toInt()).toFloat(),
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
        Surface(onClick = onClick, color = TimerColors.GlassBackground, shape = RoundedCornerShape(8.dp), border = BorderStroke(1.dp, TimerColors.GlassBorder), modifier = Modifier.padding(top = 4.dp)) {
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
    Surface(onClick = onClick, modifier = modifier, shape = RoundedCornerShape(12.dp), color = if (selected) TimerColors.AccentPrimary.copy(alpha = 0.15f) else TimerColors.GlassBackground, border = BorderStroke(1.dp, if (selected) TimerColors.AccentPrimary else TimerColors.GlassBorder)) {
        Text(label, modifier = Modifier.padding(16.dp), textAlign = TextAlign.Center, color = if (selected) TimerColors.AccentPrimary else TimerColors.TextPrimary)
    }
}

@Composable
private fun VolumeSlider(value: Float, onValueChange: (Float) -> Unit) {
    androidx.compose.material3.Slider(value = value, onValueChange = onValueChange, colors = SliderDefaults.colors(thumbColor = TimerColors.AccentPrimary, activeTrackColor = TimerColors.AccentPrimary))
}

private fun formatTime(seconds: Int): String = if (seconds >= 60) "${seconds/60}m ${seconds%60}s".replace(" 0s", "") else "${seconds}s"
