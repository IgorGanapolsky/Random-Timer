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
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
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
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimeRangeAdjuster
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import com.iganapolsky.randomtimer.ui.components.GlassCard
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.math.roundToInt

private data class SetupSpacingValues(
    val outerHorizontal: Dp,
    val listItem: Dp,
    val listTop: Dp,
    val listBottom: Dp,
    val cardContent: Dp,
    val headerToContent: Dp,
    val chipGap: Dp,
    val startButtonTop: Dp,
)

private object SetupSpacing {
    val regular =
        SetupSpacingValues(
            outerHorizontal = 16.dp,
            listItem = 8.dp,
            listTop = 8.dp,
            listBottom = 80.dp, // Leave space for sticky button
            cardContent = 12.dp,
            headerToContent = 4.dp,
            chipGap = 8.dp,
            startButtonTop = 16.dp,
        )

    val compact =
        SetupSpacingValues(
            outerHorizontal = 12.dp,
            listItem = 6.dp,
            listTop = 4.dp,
            listBottom = 70.dp, // Leave space for sticky button
            cardContent = 10.dp,
            headerToContent = 2.dp,
            chipGap = 6.dp,
            startButtonTop = 8.dp,
        )
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun TimerSetupScreen(
    config: TimerConfig,
    onConfigChange: (TimerConfig) -> Unit,
    onStartTimer: () -> Unit,
    onSoundPreview: (SoundType) -> Unit,
    onVolumePreview: (Float) -> Unit,
    onCommandCuePreview: () -> Unit,
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
    var showArsenal by remember { mutableStateOf(isPro) }

    fun updateConfig(
        minSeconds: Int = config.minSeconds,
        maxSeconds: Int = config.maxSeconds,
        alarmDuration: Int = config.alarmDuration,
        repeatEnabled: Boolean = config.repeatEnabled,
        soundType: SoundType = config.soundType,
        volume: Float = config.volume,
        vibrationEnabled: Boolean = config.vibrationEnabled,
        useExtendedRange: Boolean = config.useExtendedRange,
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
                useExtendedRange = useExtendedRange,
            ),
        )
    }

    BoxWithConstraints(modifier = modifier.fillMaxSize()) {
        val isCompactHeight = TimerSetupLayoutPolicy.isCompactHeightViewport(maxHeight.value.toInt())
        val spacing = if (isCompactHeight) SetupSpacing.compact else SetupSpacing.regular
        var showArsenalSheet by remember(isCompactHeight) { mutableStateOf(false) }

        Scaffold(
            topBar = {
                if (!isCompactHeight) {
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
                }
            },
            containerColor = TimerColors.BackgroundDark,
            modifier = Modifier.fillMaxSize(),
        ) { paddingValues ->
            Box(
                modifier =
                    Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
            ) {
                LazyColumn(
                    modifier =
                        Modifier
                            .fillMaxSize()
                            .padding(horizontal = spacing.outerHorizontal),
                    verticalArrangement = Arrangement.spacedBy(spacing.listItem),
                    contentPadding =
                        PaddingValues(
                            top = spacing.listTop,
                            bottom = spacing.listBottom,
                        ),
                ) {
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

                    // 1. Timer Range Card
                    item {
                        GlassCard(modifier = Modifier.fillMaxWidth(), padding = spacing.cardContent) {
                            Column {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text(
                                        text = "\u23F1\uFE0F Timer Range",
                                        style = MaterialTheme.typography.bodyMedium,
                                        fontWeight = FontWeight.SemiBold,
                                        color = TimerColors.TextPrimary,
                                    )
                                    Spacer(modifier = Modifier.weight(1f))
                                    if (isPro) {
                                        Surface(
                                            onClick = {
                                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                val newExtended = !config.useExtendedRange
                                                if (!newExtended && config.maxSeconds > TimerConfig.MAX_SECONDS_FREE) {
                                                    // Clamp if shrinking
                                                    val clampedMax = TimerConfig.MAX_SECONDS_FREE
                                                    val clampedMin =
                                                        minOf(
                                                            config.minSeconds,
                                                            clampedMax - TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS,
                                                        )
                                                    updateConfig(useExtendedRange = false, minSeconds = clampedMin, maxSeconds = clampedMax)
                                                } else {
                                                    updateConfig(useExtendedRange = newExtended)
                                                }
                                            },
                                            shape = RoundedCornerShape(4.dp),
                                            color =
                                                if (config.useExtendedRange) {
                                                    TimerColors.AccentPrimary.copy(
                                                        alpha = 0.2f,
                                                    )
                                                } else {
                                                    TimerColors.GlassBackground
                                                },
                                            border =
                                                BorderStroke(
                                                    0.5.dp,
                                                    if (config.useExtendedRange) TimerColors.AccentPrimary else TimerColors.GlassBorder,
                                                ),
                                        ) {
                                            Text(
                                                text = if (config.useExtendedRange) "60M MODE" else "5M MODE",
                                                style = MaterialTheme.typography.labelSmall,
                                                fontWeight = FontWeight.Bold,
                                                color = if (config.useExtendedRange) TimerColors.AccentPrimary else TimerColors.TextSecondary,
                                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                            )
                                        }
                                    } else {
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
                                Spacer(modifier = Modifier.height(spacing.headerToContent))

                                val maxRange =
                                    if (isPro &&
                                        config.useExtendedRange
                                    ) {
                                        TimerConfig.MAX_SECONDS_PRO
                                    } else {
                                        TimerConfig.MAX_SECONDS_FREE
                                    }
                                TimeRangeSliders(
                                    minValue = config.minSeconds,
                                    maxValue = config.maxSeconds,
                                    maxSliderRange = maxRange.toFloat(),
                                    minSliderMax = maxRange - 30f,
                                    compactMode = isCompactHeight,
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
                                        val (adjMin, adjMax) =
                                            TimeRangeAdjuster.adjustForMaxChange(
                                                currentMinSeconds = config.minSeconds,
                                                currentMaxSeconds = config.maxSeconds,
                                                newMaxSeconds = newMax,
                                                maxSecondsLimit = maxRange,
                                            )
                                        updateConfig(minSeconds = adjMin, maxSeconds = adjMax)
                                    },
                                )
                            }
                        }
                    }

                    // 2. Alarm Sound (Unified: Duration, Sounds, Volume, Vibration)
                    item {
                        GlassCard(modifier = Modifier.fillMaxWidth(), padding = spacing.cardContent) {
                            Column {
                                Text(
                                    text = "\uD83D\uDD14 Alarm Sound",
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontWeight = FontWeight.SemiBold,
                                    color = TimerColors.TextPrimary,
                                )

                                Spacer(modifier = Modifier.height(spacing.headerToContent))

                                // Duration Chips
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(spacing.chipGap),
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

                                // AI Voice Callouts (Elite Feature)
                                Row(
                                    modifier =
                                        Modifier
                                            .fillMaxWidth()
                                            .padding(vertical = 8.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = "\uD83D\uDCE2 AI Voice Callouts",
                                            style = MaterialTheme.typography.labelMedium,
                                            fontWeight = FontWeight.SemiBold,
                                            color = if (isElite) TimerColors.TextPrimary else TimerColors.TextMuted,
                                        )
                                        Text(
                                            text = "Prompts during countdown",
                                            style = MaterialTheme.typography.labelSmall,
                                            color = TimerColors.TextMuted,
                                        )
                                    }

                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        // Preview Button (always enabled to sell the feature)
                                        Surface(
                                            onClick = {
                                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                onCommandCuePreview()
                                            },
                                            shape = RoundedCornerShape(4.dp),
                                            color = TimerColors.AccentPrimary.copy(alpha = 0.1f),
                                            modifier = Modifier.padding(end = 8.dp),
                                        ) {
                                            Text(
                                                text = "PREVIEW",
                                                style = MaterialTheme.typography.labelSmall,
                                                fontWeight = FontWeight.Bold,
                                                color = TimerColors.AccentPrimary,
                                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                            )
                                        }

                                        if (isElite) {
                                            Text(
                                                text = "ENABLED",
                                                style = MaterialTheme.typography.labelSmall,
                                                fontWeight = FontWeight.Bold,
                                                color = TimerColors.AccentPrimary,
                                            )
                                        } else {
                                            Surface(
                                                onClick = onUpgradeTap,
                                                shape = RoundedCornerShape(4.dp),
                                                color = TimerColors.AccentPrimary.copy(alpha = 0.1f),
                                            ) {
                                                Row(
                                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                                    verticalAlignment = Alignment.CenterVertically,
                                                ) {
                                                    Text(
                                                        text = "ELITE ",
                                                        style = MaterialTheme.typography.labelSmall,
                                                        fontWeight = FontWeight.Bold,
                                                        color = TimerColors.AccentPrimary,
                                                    )
                                                    Text(
                                                        text = "\uD83D\uDD12",
                                                        style = MaterialTheme.typography.labelSmall,
                                                        color = TimerColors.AccentPrimary,
                                                    )
                                                }
                                            }
                                        }
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

                    // Zone 2: Tactical Expansion (PRO)
                    item {
                        Spacer(modifier = Modifier.height(if (isCompactHeight) 8.dp else 16.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(horizontal = 4.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                text = if (isPro) "TACTICAL EXPANSION (PRO) \uD83D\uDD13" else "TACTICAL EXPANSION (PRO) \uD83D\uDD12",
                                style = MaterialTheme.typography.labelSmall,
                                color = if (isPro) TimerColors.AccentPrimary else TimerColors.TextMuted,
                                modifier =
                                    Modifier.pointerInput(Unit) {
                                        detectTapGestures(
                                            onTap = {
                                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                if (isPro) {
                                                    if (isCompactHeight) {
                                                        showArsenalSheet = true
                                                    } else {
                                                        showArsenal = !showArsenal
                                                    }
                                                } else {
                                                    onUpgradeTap()
                                                }
                                            },
                                            onPress = {
                                                val released = withTimeoutOrNull(8000L) { tryAwaitRelease() }
                                                if (released == null) {
                                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                                    onSecretUnlock()
                                                }
                                            },
                                        )
                                    },
                            )

                            val actionLabel =
                                when {
                                    isCompactHeight -> "Open Sound Arsenal"
                                    !isPro -> if (showArsenal) "Hide Sound Arsenal" else "View Sound Arsenal"
                                    else -> "View Sound Arsenal"
                                }
                            Text(
                                text = actionLabel,
                                style = MaterialTheme.typography.labelSmall,
                                color = TimerColors.AccentPrimary,
                                fontWeight = FontWeight.Bold,
                                modifier =
                                    Modifier.clickable {
                                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                        if (isCompactHeight) {
                                            showArsenalSheet = true
                                        } else {
                                            showArsenal = !showArsenal
                                        }
                                    },
                            )
                        }
                    }

                    // Pro Sound Arsenal
                    item {
                        if (!isCompactHeight) {
                            AnimatedVisibility(
                                visible = showArsenal,
                                enter = fadeIn() + expandVertically(),
                                exit = fadeOut() + shrinkVertically(),
                            ) {
                                SoundArsenalCard(
                                    config = config,
                                    isPro = isPro,
                                    padding = spacing.cardContent,
                                    headerToContent = spacing.headerToContent,
                                    onSelectSound = { sound ->
                                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                        updateConfig(soundType = sound)
                                        onSoundPreview(sound)
                                    },
                                    onPreviewSound = onSoundPreview,
                                    onUpgradeTap = onUpgradeTap,
                                )
                            }
                        }
                    }
                }

                // Sticky Bottom Action Bar
                Surface(
                    modifier =
                        Modifier
                            .align(Alignment.BottomCenter)
                            .fillMaxWidth(),
                    color = TimerColors.BackgroundDark.copy(alpha = 0.9f),
                    border = BorderStroke(0.5.dp, TimerColors.GlassBorder),
                ) {
                    Column(
                        modifier =
                            Modifier
                                .padding(horizontal = 24.dp)
                                .padding(top = 12.dp, bottom = 24.dp),
                    ) {
                        PrimaryButton(
                            text = "Start Timer",
                            onClick = onStartTimer,
                        )
                    }
                }
            }

            if (isCompactHeight && showArsenalSheet) {
                ModalBottomSheet(
                    onDismissRequest = { showArsenalSheet = false },
                    containerColor = TimerColors.BackgroundDark,
                    contentColor = TimerColors.TextPrimary,
                ) {
                    SoundArsenalCard(
                        config = config,
                        isPro = isPro,
                        padding = spacing.cardContent,
                        headerToContent = spacing.headerToContent,
                        onSelectSound = { sound ->
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            updateConfig(soundType = sound)
                            onSoundPreview(sound)
                        },
                        onPreviewSound = onSoundPreview,
                        onUpgradeTap = onUpgradeTap,
                    )
                }
            }
        }
    }
}

@Composable
private fun SoundArsenalCard(
    config: TimerConfig,
    isPro: Boolean,
    padding: Dp,
    headerToContent: Dp,
    onSelectSound: (SoundType) -> Unit,
    onPreviewSound: (SoundType) -> Unit,
    onUpgradeTap: () -> Unit,
) {
    GlassCard(
        modifier =
            Modifier.fillMaxWidth().graphicsLayer {
                alpha = if (isPro) 1f else 0.6f
            },
        padding = padding,
    ) {
        Column {
            Text(
                text = "\uD83C\uDFA7 Sound Arsenal",
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                color = if (isPro) TimerColors.TextPrimary else TimerColors.TextMuted,
            )
            Spacer(modifier = Modifier.height(headerToContent))

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
                                    onSelectSound(sound)
                                } else {
                                    onPreviewSound(sound)
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

@Composable
private fun TimeRangeSliders(
    minValue: Int,
    maxValue: Int,
    maxSliderRange: Float = TimerConfig.MAX_SECONDS_FREE.toFloat(),
    minSliderMax: Float = maxSliderRange - 30f,
    compactMode: Boolean = false,
    enabled: Boolean = true,
    onMinChange: (Int) -> Unit,
    onMaxChange: (Int) -> Unit,
) {
    val haptic = LocalHapticFeedback.current
    val coarseNudgeStep = 5
    val fineNudgeStep = 1
    val minGapSeconds = TimeRangeAdjuster.DEFAULT_MIN_GAP_SECONDS
    val maxSliderRangeInt = maxSliderRange.toInt()
    val minSliderMaxInt = minSliderMax.toInt()
    val sectionGap = if (compactMode) 8.dp else 12.dp
    val rowGap = 4.dp
    val nudgeSize = 32.dp

    Column(verticalArrangement = Arrangement.spacedBy(sectionGap)) {
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

        // Min slider
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
                horizontalArrangement = Arrangement.spacedBy(rowGap),
            ) {
                NudgeButton(
                    label = "\u2212",
                    enabled = enabled && minValue >= coarseNudgeStep,
                    onClick = { onMinChange(minValue - coarseNudgeStep) },
                    width = nudgeSize,
                    height = nudgeSize,
                )
                Slider(
                    value = minValue.toFloat(),
                    onValueChange = { raw ->
                        val snapped = snapToStep(raw, coarseNudgeStep, 0, maxSliderRangeInt - minGapSeconds)
                        onMinChange(snapped)
                    },
                    enabled = enabled,
                    valueRange = 0f..(maxSliderRangeInt - minGapSeconds).toFloat(),
                    modifier = Modifier.weight(1f).semantics { contentDescription = "Minimum time slider" },
                    colors =
                        SliderDefaults.colors(
                            thumbColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted,
                            activeTrackColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted.copy(alpha = 0.5f),
                            inactiveTrackColor = TimerColors.SliderTrack,
                        ),
                )
                NudgeButton(
                    label = "+",
                    enabled = enabled && minValue <= (maxValue - minGapSeconds - coarseNudgeStep),
                    onClick = { onMinChange(minValue + coarseNudgeStep) },
                    width = nudgeSize,
                    height = nudgeSize,
                )
            }
        }

        // Max slider
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
                horizontalArrangement = Arrangement.spacedBy(rowGap),
            ) {
                NudgeButton(
                    label = "\u2212",
                    enabled = enabled && maxValue >= (minValue + minGapSeconds + coarseNudgeStep),
                    onClick = { onMaxChange(maxValue - coarseNudgeStep) },
                    width = nudgeSize,
                    height = nudgeSize,
                )
                Slider(
                    value = maxValue.toFloat(),
                    onValueChange = { raw ->
                        val snapped = snapToStep(raw, coarseNudgeStep, minGapSeconds, maxSliderRangeInt)
                        onMaxChange(snapped)
                    },
                    enabled = enabled,
                    valueRange = minGapSeconds.toFloat()..maxSliderRange,
                    modifier = Modifier.weight(1f).semantics { contentDescription = "Maximum time slider" },
                    colors =
                        SliderDefaults.colors(
                            thumbColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted,
                            activeTrackColor = if (enabled) TimerColors.AccentPrimary else TimerColors.TextMuted.copy(alpha = 0.5f),
                            inactiveTrackColor = TimerColors.SliderTrack,
                        ),
                )
                NudgeButton(
                    label = "+",
                    enabled = enabled && maxValue <= (maxSliderRangeInt - coarseNudgeStep),
                    onClick = { onMaxChange(maxValue + coarseNudgeStep) },
                    width = nudgeSize,
                    height = nudgeSize,
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
    width: Dp,
    height: Dp,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        enabled = enabled,
        shape = CircleShape,
        color = if (enabled) TimerColors.GlassBackground.copy(alpha = 0.3f) else TimerColors.BackgroundDark,
        border =
            BorderStroke(
                0.5.dp,
                if (enabled) TimerColors.GlassBorder.copy(alpha = 0.4f) else TimerColors.GlassBorder.copy(alpha = 0.2f),
            ),
        modifier = modifier.size(width),
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
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            NudgeButton(
                label = "\u2212",
                enabled = value > 0f,
                onClick = { onValueChange((value - 0.05f).coerceAtLeast(0f)) },
                width = 32.dp,
                height = 32.dp,
            )
            Slider(
                value = value,
                onValueChange = onValueChange,
                onValueChangeFinished = onValueChangeFinished,
                modifier = Modifier.weight(1f),
                colors =
                    SliderDefaults.colors(
                        thumbColor = TimerColors.AccentPrimary,
                        activeTrackColor = TimerColors.AccentPrimary,
                        inactiveTrackColor = TimerColors.SliderTrack,
                    ),
            )
            NudgeButton(
                label = "+",
                enabled = value < 1f,
                onClick = { onValueChange((value + 0.05f).coerceAtMost(1f)) },
                width = 32.dp,
                height = 32.dp,
            )
        }
    }
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
            onCommandCuePreview = {},
        )
    }
}
