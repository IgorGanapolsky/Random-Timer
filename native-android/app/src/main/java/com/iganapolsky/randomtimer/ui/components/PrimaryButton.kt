package com.iganapolsky.randomtimer.ui.components

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors

private val ButtonShape = RoundedCornerShape(16.dp)

/** Visible CTA copy: never return whitespace-only (Material labels can collapse visually). */
internal fun nonBlankButtonLabel(label: String): String = label.trim().ifBlank { "Continue" }

@Composable
fun PrimaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    backgroundColor: Color = TimerColors.AccentPrimary,
    contentColor: Color = TimerColors.TextPrimary,
    useGradient: Boolean = true,
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

    val baseModifier =
        modifier
            .fillMaxWidth()
            .height(56.dp)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                this.alpha = alpha
            }

    // Draw fill inside the button slot so label is never composited under a transparent M3 surface edge case.
    val innerBackgroundModifier =
        if (useGradient) {
            val end =
                if (enabled) TimerColors.AccentSecondary else TimerColors.AccentSecondary.copy(alpha = 0.5f)
            val start = if (enabled) backgroundColor else backgroundColor.copy(alpha = 0.5f)
            Modifier.background(
                brush = Brush.horizontalGradient(colors = listOf(start, end)),
                shape = ButtonShape,
            )
        } else {
            Modifier.background(
                color = if (enabled) backgroundColor else backgroundColor.copy(alpha = 0.5f),
                shape = ButtonShape,
            )
        }

    Button(
        onClick = onClick,
        modifier = baseModifier,
        enabled = enabled,
        interactionSource = interactionSource,
        shape = ButtonShape,
        colors =
            ButtonDefaults.buttonColors(
                containerColor = Color.Transparent,
                contentColor = contentColor,
                disabledContainerColor = Color.Transparent,
                disabledContentColor = contentColor.copy(alpha = 0.5f),
            ),
        contentPadding = PaddingValues(0.dp),
    ) {
        Box(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .fillMaxHeight()
                    .then(innerBackgroundModifier),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = nonBlankButtonLabel(text),
                style = MaterialTheme.typography.titleMedium,
                color = if (enabled) contentColor else contentColor.copy(alpha = 0.5f),
                textAlign = TextAlign.Center,
                maxLines = 3,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
            )
        }
    }
}

@Composable
fun SecondaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
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

    Button(
        onClick = onClick,
        modifier =
            modifier
                .fillMaxWidth()
                .height(56.dp)
                .graphicsLayer {
                    scaleX = scale
                    scaleY = scale
                    this.alpha = alpha
                },
        enabled = enabled,
        interactionSource = interactionSource,
        shape = ButtonShape,
        colors =
            ButtonDefaults.buttonColors(
                containerColor = TimerColors.GlassBackground,
                contentColor = TimerColors.TextPrimary,
                disabledContainerColor = TimerColors.GlassBackground.copy(alpha = 0.5f),
                disabledContentColor = TimerColors.TextPrimary.copy(alpha = 0.5f),
            ),
        contentPadding = PaddingValues(horizontal = 24.dp, vertical = 16.dp),
    ) {
        Text(
            text = nonBlankButtonLabel(text),
            style = MaterialTheme.typography.titleMedium,
            color = TimerColors.TextPrimary,
            textAlign = TextAlign.Center,
            maxLines = 3,
        )
    }
}

@Composable
fun DangerButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    PrimaryButton(
        text = text,
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        backgroundColor = TimerColors.TimerDanger,
        useGradient = false,
    )
}

@Preview(showBackground = true, backgroundColor = 0xFF0F0A1A)
@Composable
private fun PrimaryButtonPreview() {
    RandomTimerTheme {
        PrimaryButton(
            text = "Start Timer",
            onClick = {},
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0F0A1A)
@Composable
private fun SecondaryButtonPreview() {
    RandomTimerTheme {
        SecondaryButton(
            text = "Cancel",
            onClick = {},
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF0F0A1A)
@Composable
private fun DangerButtonPreview() {
    RandomTimerTheme {
        DangerButton(
            text = "Stop Alarm",
            onClick = {},
        )
    }
}
