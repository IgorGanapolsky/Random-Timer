package com.iganapolsky.randomtimer.domain.model

object PresetLibrary {
    val presets: List<TimerPreset> =
        listOf(
            // FREE presets
            TimerPreset(
                id = "quick_drill",
                name = "Quick Drill",
                emoji = "\u26A1",
                minSeconds = 30,
                maxSeconds = 60,
                soundType = SoundType.INTENSE,
                alarmDuration = 10,
                isPro = false,
            ),
            TimerPreset(
                id = "basic_round",
                name = "Basic Round",
                emoji = "\u23F0",
                minSeconds = 60,
                maxSeconds = 180,
                soundType = SoundType.GENTLE,
                alarmDuration = 10,
                isPro = false,
            ),
            // PRO presets
            TimerPreset(
                id = "boxing_3min",
                name = "Boxing 3min",
                emoji = "\uD83E\uDD4A",
                minSeconds = 120,
                maxSeconds = 180,
                soundType = SoundType.INTENSE,
                alarmDuration = 10,
                isPro = true,
            ),
            TimerPreset(
                id = "mma_5min",
                name = "MMA 5min",
                emoji = "\uD83E\uDD3C",
                minSeconds = 240,
                maxSeconds = 300,
                soundType = SoundType.INTENSE,
                alarmDuration = 10,
                isPro = true,
            ),
            TimerPreset(
                id = "tabata",
                name = "Tabata",
                emoji = "\uD83D\uDD25",
                minSeconds = 10,
                maxSeconds = 20,
                soundType = SoundType.INTENSE,
                alarmDuration = 5,
                isPro = true,
            ),
            TimerPreset(
                id = "muay_thai",
                name = "Muay Thai",
                emoji = "\uD83E\uDDB5",
                minSeconds = 120,
                maxSeconds = 180,
                soundType = SoundType.INTENSE,
                alarmDuration = 10,
                isPro = true,
            ),
            TimerPreset(
                id = "bjj_scramble",
                name = "BJJ Scramble",
                emoji = "\uD83E\uDD4B",
                minSeconds = 30,
                maxSeconds = 120,
                soundType = SoundType.INTENSE,
                alarmDuration = 10,
                isPro = true,
            ),
            TimerPreset(
                id = "hiit_sprint",
                name = "HIIT Sprint",
                emoji = "\uD83C\uDFC3",
                minSeconds = 15,
                maxSeconds = 45,
                soundType = SoundType.INTENSE,
                alarmDuration = 5,
                isPro = true,
            ),
            TimerPreset(
                id = "endurance",
                name = "Endurance",
                emoji = "\uD83C\uDFCB\uFE0F",
                minSeconds = 300,
                maxSeconds = 600,
                soundType = SoundType.GENTLE,
                alarmDuration = 15,
                isPro = true,
            ),
            TimerPreset(
                id = "sparring",
                name = "Sparring",
                emoji = "\uD83E\uDD3A",
                minSeconds = 180,
                maxSeconds = 300,
                soundType = SoundType.INTENSE,
                alarmDuration = 10,
                isPro = true,
            ),
        )

    val freePresets: List<TimerPreset> = presets.filter { !it.isPro }
    val proPresets: List<TimerPreset> = presets.filter { it.isPro }

    fun findMatchingPreset(config: TimerConfig): TimerPreset? =
        presets.firstOrNull { preset ->
            preset.minSeconds == config.minSeconds && preset.maxSeconds == config.maxSeconds
        }
}
