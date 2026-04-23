package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.border
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
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.changedToUp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.analytics.PaywallValueFraming
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.ui.components.PrimaryButton
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import kotlinx.coroutines.withTimeoutOrNull

internal const val HIDDEN_UNLOCK_HOLD_DURATION_MS = 8_000L
internal const val PAYWALL_HEADLINE = "Unlock Full Fight-Ready Training"
internal const val PAYWALL_SUBHEADLINE =
    "Unlock 60-minute random windows, combat voice callouts, round-capped loops, and the full sound arsenal built for pressure drills."
internal const val PAYWALL_HEADLINE_OUTCOMES_FIRST = "Finish Strong With Full Random Pressure"
internal const val PAYWALL_SUBHEADLINE_OUTCOMES_FIRST =
    "Longer random windows, combat callouts, and full-spectrum sounds — built so every rep feels closer to live pressure."
internal const val PAYWALL_PRICING_FOOTER = "Cancel anytime. Subscription auto-renews until cancelled."
internal val PAYWALL_FEATURE_ROWS =
    listOf(
        "60-minute random windows for full-length drills",
        "Combat and MMA voice callouts with live time checks",
        "Round-capped loops for pad work, sparring, and circuits",
        "Full sound arsenal — bells, horns, sirens, and more",
        "Fresh pro audio drops when new packs land",
    )

/** Identifies which subscription plan the user has selected on the paywall. */
internal enum class SubscriptionPlanSelection {
    MONTHLY,
    ANNUAL,
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PaywallSheet(
    proPrice: String,
    monthlyPrice: String = "$3.99",
    defaultToAnnualPlan: Boolean = false,
    valueFramingVariant: String = PaywallValueFraming.CONTROL,
    trialEligibilityByProductId: Map<String, Boolean> = emptyMap(),
    onPurchase: (String) -> Unit,
    onPlanSelected: (plan: String, productId: String) -> Unit = { _, _ -> },
    onRestore: () -> Unit,
    onDismiss: () -> Unit,
    onDebugUnlock: (() -> Unit)? = null,
) {
    val haptic = LocalHapticFeedback.current
    val initialSelection =
        if (defaultToAnnualPlan) SubscriptionPlanSelection.ANNUAL else SubscriptionPlanSelection.MONTHLY
    var selectedPlan by remember(defaultToAnnualPlan) { mutableStateOf(initialSelection) }
    val headline =
        if (valueFramingVariant == PaywallValueFraming.OUTCOMES_FIRST) {
            PAYWALL_HEADLINE_OUTCOMES_FIRST
        } else {
            PAYWALL_HEADLINE
        }
    val subheadline =
        if (valueFramingVariant == PaywallValueFraming.OUTCOMES_FIRST) {
            PAYWALL_SUBHEADLINE_OUTCOMES_FIRST
        } else {
            PAYWALL_SUBHEADLINE
        }
    LaunchedEffect(defaultToAnnualPlan) {
        if (defaultToAnnualPlan) {
            onPlanSelected("annual", ProManager.ELITE_PRODUCT_ID)
        } else {
            onPlanSelected("monthly", ProManager.MONTHLY_PRODUCT_ID)
        }
    }

    val purchaseProductId = productIdForPlan(selectedPlan)
    val ctaLabel =
        ctaLabelForPlan(
            selectedPlan = selectedPlan,
            proPrice = proPrice,
            monthlyPrice = monthlyPrice,
            trialEligibilityByProductId = trialEligibilityByProductId,
        )

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = TimerColors.BackgroundDark,
    ) {
        val scrollState = rememberScrollState()
        Scaffold(
            containerColor = TimerColors.BackgroundDark,
            contentColor = TimerColors.TextPrimary,
            bottomBar = {
                val uriHandler = LocalUriHandler.current
                Column(
                    modifier =
                        Modifier
                            .fillMaxWidth()
                            .navigationBarsPadding()
                            .padding(horizontal = 24.dp, vertical = 10.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    HorizontalDivider(color = TimerColors.TextSecondary.copy(alpha = 0.28f))
                    Spacer(modifier = Modifier.height(12.dp))
                    PrimaryButton(
                        text = ctaLabel,
                        onClick = {
                            onPlanSelected(planNameForSelection(selectedPlan), purchaseProductId)
                            onPurchase(purchaseProductId)
                        },
                        modifier =
                            Modifier
                                .fillMaxWidth()
                                .border(
                                    width = 2.5.dp,
                                    color = Color.White.copy(alpha = 0.95f),
                                    shape = RoundedCornerShape(16.dp),
                                ),
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Restore purchase",
                        style = MaterialTheme.typography.labelMedium,
                        color = TimerColors.TextSecondary,
                        modifier = Modifier.clickable(onClick = onRestore),
                        textAlign = TextAlign.Center,
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Not now",
                        style = MaterialTheme.typography.labelMedium,
                        color = TimerColors.TextSecondary,
                        modifier = Modifier.clickable(onClick = onDismiss),
                        textAlign = TextAlign.Center,
                    )
                    Spacer(modifier = Modifier.height(10.dp))
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(16.dp),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(
                            text = "Privacy Policy",
                            style = MaterialTheme.typography.labelSmall,
                            color = TimerColors.TextSecondary,
                            modifier =
                                Modifier.clickable {
                                    uriHandler.openUri("https://igorganapolsky.github.io/Random-Timer/privacy-policy/")
                                },
                        )
                        Text(
                            text = "Terms of Use",
                            style = MaterialTheme.typography.labelSmall,
                            color = TimerColors.TextSecondary,
                            modifier =
                                Modifier.clickable {
                                    uriHandler.openUri("https://igorganapolsky.github.io/Random-Timer/eula/")
                                },
                        )
                    }
                }
            },
        ) { innerPadding ->
            Column(
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .padding(innerPadding)
                        .verticalScroll(scrollState)
                        .padding(horizontal = 24.dp, vertical = 16.dp)
                        .padding(bottom = 12.dp),
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
                    text = headline,
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
                    text = subheadline,
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

                Text(
                    text = "CHOOSE A PLAN",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = TimerColors.AccentPrimary,
                    modifier = Modifier.align(Alignment.Start),
                )

                Spacer(modifier = Modifier.height(8.dp))

                PlanOptionCard(
                    title = "Monthly",
                    priceLabel = "${stripPriceSuffix(monthlyPrice)}/month",
                    badge = null,
                    isSelected = selectedPlan == SubscriptionPlanSelection.MONTHLY,
                    onClick = {
                        selectedPlan = SubscriptionPlanSelection.MONTHLY
                        onPlanSelected("monthly", ProManager.MONTHLY_PRODUCT_ID)
                    },
                )

                Spacer(modifier = Modifier.height(8.dp))

                PlanOptionCard(
                    title = "Annual",
                    priceLabel = "${stripPriceSuffix(proPrice)}/year",
                    badge = "Best Value",
                    isSelected = selectedPlan == SubscriptionPlanSelection.ANNUAL,
                    onClick = {
                        selectedPlan = SubscriptionPlanSelection.ANNUAL
                        onPlanSelected("annual", ProManager.ELITE_PRODUCT_ID)
                    },
                )

                Spacer(modifier = Modifier.height(20.dp))
            }
        }
    }
}

internal fun productIdForPlan(plan: SubscriptionPlanSelection): String =
    when (plan) {
        SubscriptionPlanSelection.MONTHLY -> ProManager.MONTHLY_PRODUCT_ID
        SubscriptionPlanSelection.ANNUAL -> ProManager.ELITE_PRODUCT_ID
    }

internal fun planNameForSelection(plan: SubscriptionPlanSelection): String =
    when (plan) {
        SubscriptionPlanSelection.MONTHLY -> "monthly"
        SubscriptionPlanSelection.ANNUAL -> "annual"
    }

internal fun ctaLabelForPlan(
    selectedPlan: SubscriptionPlanSelection,
    proPrice: String,
    monthlyPrice: String,
    trialEligibilityByProductId: Map<String, Boolean>,
): String {
    val productId = productIdForPlan(selectedPlan)
    if (trialEligibilityByProductId[productId] == true) {
        return "Start 7-Day Free Trial"
    }
    return when (selectedPlan) {
        SubscriptionPlanSelection.MONTHLY -> "Start Monthly \u2022 ${stripPriceSuffix(monthlyPrice)}/mo"
        SubscriptionPlanSelection.ANNUAL -> "Start Annual \u2022 ${stripPriceSuffix(proPrice)}/yr"
    }
}

@Composable
private fun PlanOptionCard(
    title: String,
    priceLabel: String,
    badge: String?,
    isSelected: Boolean,
    onClick: () -> Unit,
) {
    val borderColor = if (isSelected) TimerColors.AccentPrimary else TimerColors.TextSecondary.copy(alpha = 0.3f)
    val bgColor = if (isSelected) TimerColors.AccentPrimary.copy(alpha = 0.08f) else TimerColors.BackgroundDark

    Card(
        modifier =
            Modifier
                .fillMaxWidth()
                .clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(width = if (isSelected) 2.dp else 1.dp, color = borderColor),
        colors = CardDefaults.cardColors(containerColor = bgColor),
    ) {
        Row(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = TimerColors.TextPrimary,
                )
                Text(
                    text = priceLabel,
                    style = MaterialTheme.typography.bodySmall,
                    color = TimerColors.TextSecondary,
                )
            }
            if (badge != null) {
                Text(
                    text = badge,
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = TimerColors.AccentPrimary,
                    modifier = Modifier.padding(start = 8.dp),
                )
            }
        }
    }
}

/** Strips any existing /yr, /year, /mo, /month suffix so callers can append their own unit. */
internal fun stripPriceSuffix(price: String): String = price.trim().substringBefore("/")

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
