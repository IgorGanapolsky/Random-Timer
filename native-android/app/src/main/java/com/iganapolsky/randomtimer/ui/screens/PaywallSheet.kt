package com.iganapolsky.randomtimer.ui.screens

import android.app.Activity
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.billing.ProManager
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PaywallSheet(
    activity: Activity?,
    proManager: ProManager,
    onDismiss: () -> Unit,
    onSecretUnlock: () -> Unit = {}
) {
    val scope = rememberCoroutineScope()
    
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = TimerColors.BackgroundDark,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            // Secret backdoor: Custom 8s hold logic
            var pressTimestamp by remember { mutableStateOf(0L) }
            
            Text(
                text = "Choose Your Level",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = TimerColors.TextPrimary,
                modifier = Modifier.pointerInput(Unit) {
                    detectTapGestures(
                        onPress = {
                            val start = System.currentTimeMillis()
                            val success = tryAwaitRelease()
                            if (System.currentTimeMillis() - start >= 8000) {
                                onSecretUnlock()
                            }
                        }
                    )
                }
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Elite Tactical Card
            TierCard(
                title = "ELITE TACTICAL",
                price = proManager.getFormattedPrice(ProManager.ELITE_TACTICAL_ID),
                period = "/ year",
                description = "The complete tactical partner.",
                features = listOf("AI Voice Callouts", "Wearable Integration", "Unlimited History", "Chaos Drill Mode"),
                isElite = true,
                onClick = { activity?.let { proManager.launchPurchase(it, ProManager.ELITE_TACTICAL_ID) } }
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Base Pro Card
            TierCard(
                title = "BASE PRO",
                price = proManager.getFormattedPrice(ProManager.PRO_BASE_ID),
                period = "one-time",
                description = "Essential training tools.",
                features = listOf("1h Training Window", "10 Alarm Sounds", "No Ads"),
                isElite = false,
                onClick = { activity?.let { proManager.launchPurchase(it, ProManager.PRO_BASE_ID) } }
            )

            Spacer(modifier = Modifier.height(24.dp))

            TextButton(onClick = { proManager.restorePurchases() }) {
                Text("Restore purchase", color = TimerColors.TextSecondary)
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun TierCard(
    title: String,
    price: String,
    period: String,
    description: String,
    features: List<String>,
    isElite: Boolean,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(16.dp),
        color = if (isElite) TimerColors.AccentPrimary.copy(alpha = 0.05f) else TimerColors.GlassBackground.copy(alpha = 0.5f),
        border = BorderStroke(1.dp, if (isElite) TimerColors.AccentPrimary.copy(alpha = 0.3f) else TimerColors.GlassBorder)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = if (isElite) TimerColors.AccentPrimary else TimerColors.TextPrimary)
                    Text(description, style = MaterialTheme.typography.labelSmall, color = TimerColors.TextSecondary)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(price, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = TimerColors.TextPrimary)
                    Text(period, style = MaterialTheme.typography.labelSmall, color = TimerColors.TextMuted)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            features.forEach { feature ->
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 4.dp)) {
                    Text("\u2713", color = if (isElite) TimerColors.AccentPrimary else TimerColors.TextMuted, modifier = Modifier.padding(end = 8.dp))
                    Text(feature, style = MaterialTheme.typography.bodySmall, color = TimerColors.TextPrimary)
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            Button(
                onClick = onClick,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isElite) TimerColors.AccentPrimary else TimerColors.GlassBackground,
                    contentColor = if (isElite) TimerColors.BackgroundDark else TimerColors.TextPrimary
                )
            ) {
                Text(if (isElite) "Start Elite Mission" else "Unlock Base", fontWeight = FontWeight.Bold)
            }
        }
    }
}
