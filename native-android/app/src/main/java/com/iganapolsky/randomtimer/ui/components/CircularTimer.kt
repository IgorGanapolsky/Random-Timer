package com.iganapolsky.randomtimer.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.domain.model.TimerStatus
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import kotlin.time.Duration
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

@Composable
fun CircularTimer(
    remainingDuration: Duration,
    progress: Float,
    status: TimerStatus,
    modifier: Modifier = Modifier,
    strokeWidth: Dp = 12.dp,
    isHiddenMode: Boolean = false,
    rangeText: String = "" // e.g., "30s - 2m"
) {
    val animatedProgress by animateFloatAsState(
        targetValue = progress,
        animationSpec = tween(durationMillis = 300),
        label = "progress"
    )

    // For random timer, don't reveal warning/danger states - just show running until complete
    val statusColor = when (status) {
        TimerStatus.RUNNING, TimerStatus.WARNING, TimerStatus.DANGER -> TimerColors.TimerActive
        TimerStatus.COMPLETE, TimerStatus.ALARM -> TimerColors.TimerComplete
        else -> TimerColors.TextSecondary
    }

    val animatedColor by animateColorAsState(
        targetValue = statusColor,
        animationSpec = tween(durationMillis = 500),
        label = "color"
    )

    // Subtle breathing animation for timer display (adds suspense)
    val infiniteTransition = rememberInfiniteTransition(label = "timerPulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.85f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 2000),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )

    // Circle pulse animation to show timer is active
    val circlePulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.7f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1500),
            repeatMode = RepeatMode.Reverse
        ),
        label = "circlePulseAlpha"
    )

    Box(
        modifier = modifier
            .aspectRatio(1f)
            .padding(16.dp),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val diameter = size.minDimension
            val radius = diameter / 2
            val strokePx = strokeWidth.toPx()

            // Background track (glass effect) - full circle with pulse animation
            drawCircle(
                color = TimerColors.GlassBackground.copy(alpha = circlePulseAlpha),
                radius = radius - strokePx / 2,
                style = Stroke(width = strokePx, cap = StrokeCap.Round)
            )

            // Progress arc
            val sweepAngle = 360f * animatedProgress
            drawArc(
                brush = Brush.sweepGradient(
                    colors = listOf(
                        animatedColor.copy(alpha = 0.3f),
                        animatedColor,
                        animatedColor
                    )
                ),
                startAngle = -90f,
                sweepAngle = sweepAngle,
                useCenter = false,
                topLeft = Offset(strokePx / 2, strokePx / 2),
                size = Size(diameter - strokePx, diameter - strokePx),
                style = Stroke(width = strokePx, cap = StrokeCap.Round)
            )

            // Glow effect at the tip (end of progress arc)
            if (animatedProgress > 0f) {
                val angle = Math.toRadians((-90 + sweepAngle).toDouble())
                val glowX = (radius + (radius - strokePx / 2) * kotlin.math.cos(angle)).toFloat()
                val glowY = (radius + (radius - strokePx / 2) * kotlin.math.sin(angle)).toFloat()

                drawCircle(
                    color = animatedColor.copy(alpha = 0.6f),
                    radius = strokePx,
                    center = Offset(glowX, glowY)
                )
            }

            // Tracking dot at the start of progress (like iOS)
            if (animatedProgress > 0f && animatedProgress < 1f) {
                val startAngle = Math.toRadians(-90.0)
                val trackDotX = (radius + (radius - strokePx / 2) * kotlin.math.cos(startAngle)).toFloat()
                val trackDotY = (radius + (radius - strokePx / 2) * kotlin.math.sin(startAngle)).toFloat()

                // Outer glow
                drawCircle(
                    color = animatedColor.copy(alpha = 0.3f),
                    radius = strokePx * 1.5f,
                    center = Offset(trackDotX, trackDotY)
                )
                // Inner dot
                drawCircle(
                    color = animatedColor.copy(alpha = 0.6f),
                    radius = strokePx * 0.8f,
                    center = Offset(trackDotX, trackDotY)
                )
            }
        }

        // Center display - show "Complete!" when alarm/complete, otherwise show range
        val isAlarmOrComplete = status == TimerStatus.ALARM || status == TimerStatus.COMPLETE

        if (isAlarmOrComplete) {
            // Show completion message inside the circle - "Complete!" is less abrasive than "Time's up!"
            Text(
                text = "Complete!",
                style = MaterialTheme.typography.headlineMedium,
                color = TimerColors.TimerComplete.copy(alpha = pulseAlpha),
                textAlign = TextAlign.Center
            )
        } else if (rangeText.isNotEmpty()) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Range",
                    style = MaterialTheme.typography.labelMedium,
                    color = TimerColors.TextMuted,
                    textAlign = TextAlign.Center
                )
                Text(
                    text = rangeText,
                    style = MaterialTheme.typography.headlineLarge,
                    color = TimerColors.TextPrimary.copy(alpha = pulseAlpha),
                    textAlign = TextAlign.Center
                )
            }
        } else {
            // Fallback - should not happen for random timer
            Text(
                text = "...",
                style = MaterialTheme.typography.displayLarge,
                color = TimerColors.TextPrimary.copy(alpha = pulseAlpha),
                textAlign = TextAlign.Center
            )
        }
    }
}

fun formatDuration(duration: Duration): String {
    val totalSeconds = duration.inWholeSeconds.coerceAtLeast(0)
    val minutes = totalSeconds / 60
    val seconds = totalSeconds % 60
    return "%02d:%02d".format(minutes, seconds)
}

@Preview(showBackground = true, backgroundColor = 0xFF0F0A1A)
@Composable
private fun CircularTimerPreview() {
    RandomTimerTheme {
        CircularTimer(
            remainingDuration = 2.minutes + 30.seconds,
            progress = 0.5f,
            status = TimerStatus.RUNNING,
            modifier = Modifier.size(280.dp)
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0F0A1A)
@Composable
private fun CircularTimerWarningPreview() {
    RandomTimerTheme {
        CircularTimer(
            remainingDuration = 25.seconds,
            progress = 0.9f,
            status = TimerStatus.WARNING,
            modifier = Modifier.size(280.dp)
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0F0A1A)
@Composable
private fun CircularTimerDangerPreview() {
    RandomTimerTheme {
        CircularTimer(
            remainingDuration = 5.seconds,
            progress = 0.98f,
            status = TimerStatus.DANGER,
            modifier = Modifier.size(280.dp)
        )
    }
}
