package com.iganapolsky.randomtimer.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.ui.theme.RandomTimerTheme
import com.iganapolsky.randomtimer.ui.theme.TimerColors

@Composable
fun GlassCard(
    modifier: Modifier = Modifier,
    cornerRadius: Dp = 24.dp,
    padding: Dp = 16.dp,
    content: @Composable BoxScope.() -> Unit,
) {
    val shape = RoundedCornerShape(cornerRadius)

    Box(
        modifier = modifier
            .clip(shape)
            .background(TimerColors.GlassBackground)
            .drawWithContent {
                drawContent()
                // Subtle top-edge glow simulating light reflection on glass
                val glowHeight = 3.dp.toPx()
                drawRect(
                    brush = Brush.verticalGradient(
                        colors = listOf(
                            Color.White.copy(alpha = 0.08f),
                            Color.Transparent,
                        ),
                        startY = 0f,
                        endY = glowHeight,
                    ),
                    size = Size(size.width, glowHeight),
                )
            }
            .border(
                width = 1.dp,
                color = TimerColors.GlassBorder,
                shape = shape,
            )
            .padding(padding),
        content = content,
    )
}

@Preview(showBackground = true, backgroundColor = 0xFF0F0A1A)
@Composable
private fun GlassCardPreview() {
    RandomTimerTheme {
        GlassCard(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
        ) {
            Text(
                text = "Glassmorphism Card",
                style = MaterialTheme.typography.titleMedium,
                color = TimerColors.TextPrimary,
            )
        }
    }
}
