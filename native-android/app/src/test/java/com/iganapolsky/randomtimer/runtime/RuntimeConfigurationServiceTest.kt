package com.iganapolsky.randomtimer.runtime

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class RuntimeConfigurationServiceTest {
    @Test
    fun parsePayload_reads_default_config_and_experiments() {
        val payload =
            RuntimeConfigurationService.parsePayload(
                """
                {
                  "configVersion": "2026-03-16",
                  "defaultTimerConfig": {
                    "minSeconds": 0,
                    "maxSeconds": 300,
                    "alarmDuration": 15,
                    "hiddenMode": false,
                    "repeatEnabled": false,
                    "soundType": "gentle",
                    "volume": 0.7,
                    "vibrationEnabled": true
                  },
                  "experiments": [
                    {
                      "key": "paywall_copy",
                      "variants": [
                        {"key": "control", "rolloutPercent": 50},
                        {"key": "drill_sergeant", "rolloutPercent": 50}
                      ]
                    }
                  ]
                }
                """.trimIndent(),
            )

        assertThat(payload.configVersion).isEqualTo("2026-03-16")
        assertThat(payload.defaultTimerConfig.maxSeconds).isEqualTo(300)
        assertThat(payload.defaultTimerConfig.alarmDuration).isEqualTo(15)
        assertThat(payload.defaultTimerConfig.vibrationEnabled).isTrue()
        assertThat(payload.experiments).hasSize(1)
        assertThat(payload.experiments.single().variants).hasSize(2)
    }

    @Test
    fun experimentAssignment_is_deterministic_for_same_device() {
        val experiments =
            listOf(
                RuntimeExperimentDefinition(
                    key = "paywall_copy",
                    variants =
                        listOf(
                            RuntimeExperimentVariant("control", 50),
                            RuntimeExperimentVariant("drill_sergeant", 50),
                        ),
                ),
            )

        val first = RuntimeExperimentAssigner.assign("device-123", experiments)
        val second = RuntimeExperimentAssigner.assign("device-123", experiments)

        assertThat(first).isEqualTo(second)
        assertThat(first["paywall_copy"]).isNotNull()
    }
}
