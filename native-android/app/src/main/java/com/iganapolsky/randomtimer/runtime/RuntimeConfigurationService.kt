package com.iganapolsky.randomtimer.runtime

import com.iganapolsky.randomtimer.BuildConfig
import com.iganapolsky.randomtimer.domain.model.SoundType
import com.iganapolsky.randomtimer.domain.model.TimerConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.absoluteValue

data class RuntimeConfigurationSnapshot(
    val defaultConfig: TimerConfig = TimerConfig.DEFAULT,
    val configSource: String = "bundled",
    val configVersion: String = "bundled",
    val experiments: Map<String, String> = emptyMap(),
) {
    fun analyticsProperties(): Map<String, Any> =
        buildMap {
            put("runtime_config_source", configSource)
            put("runtime_config_version", configVersion)
            experiments.forEach { (key, value) ->
                put("experiment_$key", value)
            }
        }
}

data class RuntimeConfigurationPayload(
    val configVersion: String,
    val defaultTimerConfig: TimerConfig,
    val experiments: List<RuntimeExperimentDefinition>,
) {
    fun toSnapshot(distinctId: String): RuntimeConfigurationSnapshot =
        RuntimeConfigurationSnapshot(
            defaultConfig = defaultTimerConfig,
            configSource = "insforge_storage",
            configVersion = configVersion,
            experiments = RuntimeExperimentAssigner.assign(distinctId, experiments),
        )
}

data class RuntimeExperimentDefinition(
    val key: String,
    val variants: List<RuntimeExperimentVariant>,
)

data class RuntimeExperimentVariant(
    val key: String,
    val rolloutPercent: Int,
)

internal object RuntimeExperimentAssigner {
    fun assign(
        distinctId: String,
        experiments: List<RuntimeExperimentDefinition>,
    ): Map<String, String> =
        experiments
            .mapNotNull { definition ->
                chooseVariant(distinctId, definition)?.let { definition.key to it }
            }.toMap()

    private fun chooseVariant(
        distinctId: String,
        definition: RuntimeExperimentDefinition,
    ): String? {
        if (definition.variants.isEmpty()) return null

        val bucket = bucketFor("${definition.key}:$distinctId")
        var cumulative = 0
        definition.variants.forEach { variant ->
            val rollout = variant.rolloutPercent.coerceIn(0, 100)
            cumulative += rollout
            if (bucket < cumulative) {
                return variant.key
            }
        }
        return null
    }

    private fun bucketFor(seed: String): Int {
        val digest = MessageDigest.getInstance("SHA-256").digest(seed.toByteArray())
        val raw =
            digest.take(8).fold(0L) { acc, byte ->
                (acc shl 8) or (byte.toLong() and 0xff)
            }
        return (raw.absoluteValue % 100).toInt()
    }
}

@Singleton
class RuntimeConfigurationService
    @Inject
    constructor() {
        private val _snapshot = MutableStateFlow(RuntimeConfigurationSnapshot())
        val snapshot: StateFlow<RuntimeConfigurationSnapshot> = _snapshot.asStateFlow()

        suspend fun refresh(distinctId: String?) {
            val baseUrl = BuildConfig.INSFORGE_API_BASE_URL.trim().removeSuffix("/")
            val apiKey = BuildConfig.INSFORGE_API_KEY.trim()
            if (distinctId.isNullOrBlank() || baseUrl.isBlank() || apiKey.isBlank()) {
                return
            }

            val payload =
                runCatching {
                    fetchPayload(
                        objectUrl = "$baseUrl/api/storage/buckets/training_assets/objects/runtime/mobile-runtime-config.json",
                        apiKey = apiKey,
                    )
                }.getOrNull() ?: return

            _snapshot.value = payload.toSnapshot(distinctId)
        }

        internal fun applyPayloadForTesting(
            payload: RuntimeConfigurationPayload,
            distinctId: String,
        ) {
            _snapshot.value = payload.toSnapshot(distinctId)
        }

        private suspend fun fetchPayload(
            objectUrl: String,
            apiKey: String,
        ): RuntimeConfigurationPayload =
            withContext(Dispatchers.IO) {
                val connection =
                    (URL(objectUrl).openConnection() as HttpURLConnection).apply {
                        requestMethod = "GET"
                        setRequestProperty("x-api-key", apiKey)
                        setRequestProperty("accept", "application/json")
                        connectTimeout = 5000
                        readTimeout = 5000
                        instanceFollowRedirects = true
                    }
                try {
                    val code = connection.responseCode
                    require(code in 200..299) { "Runtime config fetch failed with HTTP $code" }
                    val body = connection.inputStream.bufferedReader().use { it.readText() }
                    parsePayload(body)
                } finally {
                    connection.disconnect()
                }
            }

        companion object {
            internal fun parsePayload(json: String): RuntimeConfigurationPayload {
                val root = JSONObject(json)
                val configVersion = root.optString("configVersion").ifBlank { "unknown" }
                val timer = root.optJSONObject("defaultTimerConfig") ?: JSONObject()
                val experiments = root.optJSONArray("experiments") ?: JSONArray()

                return RuntimeConfigurationPayload(
                    configVersion = configVersion,
                    defaultTimerConfig =
                        TimerConfig(
                            minSeconds = timer.optInt("minSeconds", TimerConfig.DEFAULT.minSeconds),
                            maxSeconds = timer.optInt("maxSeconds", TimerConfig.DEFAULT.maxSeconds),
                            alarmDuration = timer.optInt("alarmDuration", TimerConfig.DEFAULT.alarmDuration),
                            hiddenMode = timer.optBoolean("hiddenMode", TimerConfig.DEFAULT.hiddenMode),
                            repeatEnabled = timer.optBoolean("repeatEnabled", TimerConfig.DEFAULT.repeatEnabled),
                            soundType = parseSoundType(timer.optString("soundType")),
                            volume = timer.optDouble("volume", TimerConfig.DEFAULT.volume.toDouble()).toFloat(),
                            vibrationEnabled = timer.optBoolean("vibrationEnabled", TimerConfig.DEFAULT.vibrationEnabled),
                        ),
                    experiments =
                        buildList {
                            for (index in 0 until experiments.length()) {
                                val experiment = experiments.optJSONObject(index) ?: continue
                                val key = experiment.optString("key")
                                if (key.isBlank()) continue
                                val variantsJson = experiment.optJSONArray("variants") ?: JSONArray()
                                val variants =
                                    buildList {
                                        for (variantIndex in 0 until variantsJson.length()) {
                                            val variant = variantsJson.optJSONObject(variantIndex) ?: continue
                                            val variantKey = variant.optString("key")
                                            if (variantKey.isBlank()) continue
                                            add(
                                                RuntimeExperimentVariant(
                                                    key = variantKey,
                                                    rolloutPercent = variant.optInt("rolloutPercent", 0),
                                                ),
                                            )
                                        }
                                    }
                                add(RuntimeExperimentDefinition(key = key, variants = variants))
                            }
                        },
                )
            }

            private fun parseSoundType(raw: String?): SoundType =
                runCatching {
                    SoundType.valueOf(raw.orEmpty().trim().uppercase())
                }.getOrDefault(TimerConfig.DEFAULT.soundType)
        }
    }
