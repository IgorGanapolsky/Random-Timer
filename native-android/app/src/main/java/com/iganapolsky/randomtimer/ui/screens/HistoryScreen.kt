package com.iganapolsky.randomtimer.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.iganapolsky.randomtimer.domain.model.WorkoutSession
import com.iganapolsky.randomtimer.ui.components.GlassCard
import com.iganapolsky.randomtimer.ui.theme.TimerColors
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(
    sessions: List<WorkoutSession>,
    totalSessions: Int,
    currentStreak: Int,
    totalTrainingTimeSeconds: Long,
    isPro: Boolean,
    onBack: () -> Unit,
    onUpgradeTap: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val visibleSessions = if (isPro) sessions else sessions.take(FREE_SESSION_LIMIT)

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Workout History",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = TimerColors.TextPrimary,
                    )
                },
                navigationIcon = {
                    Text(
                        text = "\u2190",
                        style = MaterialTheme.typography.titleLarge,
                        color = TimerColors.TextPrimary,
                        modifier =
                            Modifier
                                .clickable(onClick = onBack)
                                .padding(horizontal = 12.dp),
                    )
                },
                colors =
                    TopAppBarDefaults.topAppBarColors(
                        containerColor = TimerColors.BackgroundDark,
                    ),
            )
        },
        containerColor = TimerColors.BackgroundDark,
        modifier = modifier.fillMaxSize(),
    ) { paddingValues ->
        LazyColumn(
            modifier =
                Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(top = 8.dp, bottom = 24.dp),
        ) {
            // Stats Banner
            item {
                GlassCard(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                    ) {
                        StatColumn(
                            value = totalSessions.toString(),
                            label = "Sessions",
                        )
                        StatColumn(
                            value = if (currentStreak > 0) "$currentStreak" else "0",
                            label = "Day Streak",
                        )
                        StatColumn(
                            value = formatTotalTime(totalTrainingTimeSeconds),
                            label = "Total Time",
                        )
                    }
                }
            }

            // Pro gate banner for free users
            if (!isPro && sessions.size > FREE_SESSION_LIMIT) {
                item {
                    Surface(
                        onClick = onUpgradeTap,
                        shape = RoundedCornerShape(12.dp),
                        color = TimerColors.AccentPrimary.copy(alpha = 0.15f),
                    ) {
                        Text(
                            text = "Unlock Pro to see full history (${sessions.size} sessions)",
                            style = MaterialTheme.typography.labelMedium,
                            color = TimerColors.AccentPrimary,
                            fontWeight = FontWeight.SemiBold,
                            textAlign = TextAlign.Center,
                            modifier =
                                Modifier
                                    .fillMaxWidth()
                                    .padding(horizontal = 16.dp, vertical = 12.dp),
                        )
                    }
                }
            }

            if (visibleSessions.isEmpty()) {
                // Empty state
                item {
                    Column(
                        modifier =
                            Modifier
                                .fillMaxWidth()
                                .padding(top = 48.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Text(
                            text = "\u23F1\uFE0F",
                            style = MaterialTheme.typography.displayLarge,
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "No sessions yet.",
                            style = MaterialTheme.typography.titleMedium,
                            color = TimerColors.TextPrimary,
                            fontWeight = FontWeight.SemiBold,
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Start your first drill!",
                            style = MaterialTheme.typography.bodyMedium,
                            color = TimerColors.TextSecondary,
                        )
                    }
                }
            } else {
                // Session cards
                itemsIndexed(visibleSessions) { _, session ->
                    SessionCard(session = session)
                }
            }
        }
    }
}

@Composable
private fun StatColumn(
    value: String,
    label: String,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = value,
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            color = TimerColors.AccentPrimary,
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = TimerColors.TextMuted,
        )
    }
}

@Composable
private fun SessionCard(
    session: WorkoutSession,
    modifier: Modifier = Modifier,
) {
    GlassCard(modifier = modifier.fillMaxWidth(), padding = 14.dp) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = formatSessionDate(session.timestamp),
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = TimerColors.TextPrimary,
                )
                CompletionBadge(completed = session.completed)
            }
            Spacer(modifier = Modifier.height(6.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    text = formatDuration(session.targetDurationSeconds),
                    style = MaterialTheme.typography.bodySmall,
                    color = TimerColors.TextSecondary,
                )
                Text(
                    text =
                        session.soundType.name
                            .lowercase()
                            .replaceFirstChar { it.uppercase() }
                            .replace("_", " "),
                    style = MaterialTheme.typography.bodySmall,
                    color = TimerColors.TextMuted,
                )
            }
        }
    }
}

@Composable
private fun CompletionBadge(
    completed: Boolean,
    modifier: Modifier = Modifier,
) {
    val backgroundColor =
        if (completed) {
            TimerColors.TimerActive.copy(alpha = 0.15f)
        } else {
            TimerColors.TimerDanger.copy(alpha = 0.15f)
        }
    val textColor = if (completed) TimerColors.TimerActive else TimerColors.TimerDanger
    val label = if (completed) "Completed" else "Abandoned"

    Box(
        modifier =
            modifier
                .background(
                    color = backgroundColor,
                    shape = RoundedCornerShape(6.dp),
                ).padding(horizontal = 8.dp, vertical = 3.dp),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.SemiBold,
            color = textColor,
        )
    }
}

private fun formatSessionDate(timestamp: Long): String {
    val sdf = SimpleDateFormat("MMM d, yyyy  h:mm a", Locale.getDefault())
    return sdf.format(Date(timestamp))
}

private fun formatDuration(seconds: Int): String =
    if (seconds >= 60) {
        val mins = seconds / 60
        val secs = seconds % 60
        if (secs > 0) "${mins}m ${secs}s" else "${mins}m"
    } else {
        "${seconds}s"
    }

private fun formatTotalTime(totalSeconds: Long): String {
    val hours = totalSeconds / 3600
    val minutes = (totalSeconds % 3600) / 60
    return when {
        hours > 0 -> "${hours}h ${minutes}m"
        minutes > 0 -> "${minutes}m"
        else -> "${totalSeconds}s"
    }
}

private const val FREE_SESSION_LIMIT = 3
