package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.changedToUp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import kotlinx.coroutines.withTimeoutOrNull

internal const val HIDDEN_UNLOCK_HOLD_DURATION_MS = 8_000L
internal const val PAYWALL_HEADLINE = "Unlock Full Training Mode"
internal const val PAYWALL_SUBHEADLINE = "Longer sessions, voice coaching, more sounds, and repeatable rounds."
internal const val PAYWALL_AUDIENCE_LINE = "Built for dry fire, sparring, drills, and reaction training."
internal const val PAYWALL_PRICING_FOOTER = "Cancel anytime. Auto-renews yearly."
internal val PAYWALL_FEATURE_ROWS =
    listOf(
        "Train up to 60-minute sessions",
        "Get voice callouts during training",
        "Use loop mode with round limits",
        "Unlock the full sound library",
        "New Pro voice callouts and sound packs every 30 days",
    )

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PaywallSheet(
    proPrice: String,
    onPurchase: (String) -> Unit,
    onRestore: () -> Unit,
    onDismiss: () -> Unit,
    onDebugUnlock: (() -> Unit)? = null,
) {
    val haptic = LocalHapticFeedback.current
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = TimerColors.BackgroundDark,
    ) {
        Column(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = "Not now",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextSecondary,
                modifier =
                    Modifier
                        .align(Alignment.Start)
                        .clickable(onClick = onDismiss),
            )

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = PAYWALL_HEADLINE,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = TimerColors.TextPrimary,
                textAlign = TextAlign.Center,
                modifier =
                    Modifier.fillMaxWidth().then(
                        if (onDebugUnlock != null) {
                            Modifier.holdForHiddenUnlock(
                                holdDurationMs = HIDDEN_UNLOCK_HOLD_DURATION_MS,
                                haptic = haptic,
                                onHoldComplete = onDebugUnlock,
                            )
                        } else {
                            Modifier
                        },
                    ),
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = PAYWALL_SUBHEADLINE,
                style = MaterialTheme.typography.bodySmall,
                color = TimerColors.TextSecondary,
                textAlign = TextAlign.Center,
            )
            Text(
                text = PAYWALL_AUDIENCE_LINE,
                style = MaterialTheme.typography.bodySmall,
                color = TimerColors.TextSecondary,
                textAlign = TextAlign.Center,
            )
            Text(
                text = PAYWALL_PRICING_FOOTER,
                style = MaterialTheme.typography.bodySmall,
                color = TimerColors.TextSecondary,
                textAlign = TextAlign.Center,
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "PRO FEATURES",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = TimerColors.AccentPrimary,
                modifier = Modifier.align(Alignment.Start),
            )

            Spacer(modifier = Modifier.height(8.dp))

            PAYWALL_FEATURE_ROWS.forEach { feature ->
                ProFeatureRow(text = feature)
            }

            Spacer(modifier = Modifier.height(24.dp))

            PrimaryButton(
                text = "Start Pro \u2022 ${normalizedPriceLabel(proPrice)}",
                onClick = { onPurchase("elite_tactical") },
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Restore purchase",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextSecondary,
                modifier =
                    Modifier
                        .clickable(onClick = onRestore),
                textAlign = TextAlign.Center,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Not now",
                style = MaterialTheme.typography.labelMedium,
                color = TimerColors.TextSecondary,
                modifier =
                    Modifier
                        .clickable(onClick = onDismiss),
                textAlign = TextAlign.Center,
            )

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

internal fun normalizedPriceLabel(price: String): String {
    val trimmed = price.trim()
    val lowered = trimmed.lowercase()
    return if ("/yr" in lowered || "/year" in lowered) {
        trimmed
    } else {
        "$trimmed/year"
    }
}

private fun Modifier.holdForHiddenUnlock(
    holdDurationMs: Long,
    haptic: androidx.compose.ui.hapticfeedback.HapticFeedback,
    onHoldComplete: () -> Unit,
): Modifier =
    pointerInput(holdDurationMs, onHoldComplete) {
        awaitPointerEventScope {
            while (true) {
                awaitFirstDown(requireUnconsumed = false)
                val success =
                    withTimeoutOrNull(holdDurationMs) {
                        var released = false
                        while (!released) {
                            val event = awaitPointerEvent()
                            if (event.changes.any { it.changedToUp() }) {
                                released = true
                            }
                        }
                        false // Released before timeout
                    } ?: true

                if (success) {
                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                    onHoldComplete()
                    // Wait for the final up event before allowing next hold
                    while (true) {
                        val event = awaitPointerEvent()
                        if (event.changes.any { it.changedToUp() }) break
                    }
                }
            }
        }
    }

@Composable
private fun ProFeatureRow(text: String) {
    Row(
        modifier =
            Modifier
                .fillMaxWidth()
                .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.Start,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = "\u2713",
            style = MaterialTheme.typography.bodyMedium,
            color = TimerColors.AccentPrimary,
            modifier = Modifier.padding(end = 12.dp),
        )
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = TimerColors.TextPrimary,
        )
    }
}
