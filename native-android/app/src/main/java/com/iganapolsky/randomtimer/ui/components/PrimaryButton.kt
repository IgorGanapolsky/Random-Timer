package com.iganapolsky.randomtimer.ui.components

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors

private val ButtonShape = RoundedCornerShape(16.dp)

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

    val baseModifier = modifier
        .fillMaxWidth()
        .height(56.dp)
        .graphicsLayer {
            scaleX = scale
            scaleY = scale
            this.alpha = alpha
        }

    val styledModifier = if (useGradient && enabled) {
        baseModifier.background(
            brush = Brush.horizontalGradient(
                colors = listOf(TimerColors.IntensityRed, TimerColors.TacticalOrange),
            ),
            shape = ButtonShape,
        )
    } else {
        baseModifier
    }

    Button(
        onClick = onClick,
        modifier = styledModifier,
        enabled = enabled,
        interactionSource = interactionSource,
        shape = ButtonShape,
        colors = ButtonDefaults.buttonColors(
            containerColor = if (useGradient) Color.Transparent else backgroundColor,
            contentColor = contentColor,
            disabledContainerColor = backgroundColor.copy(alpha = 0.5f),
            disabledContentColor = contentColor.copy(alpha = 0.5f),
        ),
        contentPadding = PaddingValues(horizontal = 24.dp, vertical = 16.dp),
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.titleMedium,
        )
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
        modifier = modifier
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
        colors = ButtonDefaults.buttonColors(
            containerColor = TimerColors.GlassBackground,
            contentColor = TimerColors.TextPrimary,
            disabledContainerColor = TimerColors.GlassBackground.copy(alpha = 0.5f),
            disabledContentColor = TimerColors.TextPrimary.copy(alpha = 0.5f),
        ),
        contentPadding = PaddingValues(horizontal = 24.dp, vertical = 16.dp),
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.titleMedium,
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
