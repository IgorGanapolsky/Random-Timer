package com.iganapolsky.randomtimer.ui.screens

import com.google.common.truth.Truth.assertWithMessage
import org.junit.Test
import java.io.File

class CompetitionWarmupRemovalGuardTest {
    private val repoRoot: File by lazy {
        generateSequence(File(System.getProperty("user.dir"))) { it.parentFile }
            .first { dir -> File(dir, "native-android").isDirectory }
    }

    private val guardedSources =
        listOf(
            "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt",
            "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt",
            "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/navigation/Navigation.kt",
            "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/viewmodel/TimerViewModel.kt",
        )

    private val forbiddenFragments =
        listOf(
            "Competition Warmup",
            "Competition Prep",
            "STANDARD OPS",
            "TrainingPreset",
            "competition_warmup",
            "onTrainingPresetApplied",
            "showCompetitionPrep",
            "competitionPrepSectionTitle",
        )

    @Test
    fun timerSetupSourcesContainNoCompetitionWarmupUi() {
        for (relativePath in guardedSources) {
            val file = File(repoRoot, relativePath)
            assertWithMessage("Missing guarded source: $relativePath").that(file.isFile).isTrue()
            val source = file.readText()
            for (fragment in forbiddenFragments) {
                assertWithMessage("$relativePath must not contain '$fragment'")
                    .that(source.contains(fragment, ignoreCase = true))
                    .isFalse()
            }
        }
    }
}
