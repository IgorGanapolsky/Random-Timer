package com.iganapolsky.randomtimer.notifications

import com.iganapolsky.randomtimer.BuildConfig
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Reads `releaseMonth` from the hosted Pro audio runtime manifest.
 */
object ProMonthlyManifestReader {
    fun fetchReleaseMonth(
        manifestUrl: String = BuildConfig.PRO_AUDIO_MANIFEST_URL.trim(),
    ): String? {
        if (manifestUrl.isEmpty()) {
            return null
        }
        return runCatching {
            val connection = URL(manifestUrl).openConnection() as HttpURLConnection
            connection.connectTimeout = 10_000
            connection.readTimeout = 10_000
            connection.requestMethod = "GET"
            connection.inputStream.bufferedReader().use { reader ->
                val json = JSONObject(reader.readText())
                json.optString("releaseMonth").takeIf { it.isNotBlank() }
            }
        }.getOrNull()
    }
}
