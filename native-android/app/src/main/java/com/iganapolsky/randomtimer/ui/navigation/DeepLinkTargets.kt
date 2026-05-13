package com.iganapolsky.randomtimer.ui.navigation

import java.net.URI
import java.net.URLDecoder
import java.nio.charset.StandardCharsets

internal data class MonetizationDeepLink(
    val entryPoint: String,
    val feature: String,
)

internal fun monetizationDeepLinkFromUri(rawUri: String?): MonetizationDeepLink? {
    if (rawUri.isNullOrBlank()) return null
    val uri = runCatching { URI(rawUri) }.getOrNull() ?: return null
    val params = parseQueryParams(uri.rawQuery)
    val screen = params["screen"] ?: params["route"] ?: params["target"]
    val path = uri.path.orEmpty().trim('/')
    val isUpgradeIntent =
        screen in setOf("upgrade", "paywall", "pro") ||
            path.split('/').any { it in setOf("upgrade", "paywall", "pro") }

    val isSupportedScheme =
        (uri.scheme == "randomtimer" && uri.host == "open") ||
            (
                uri.scheme in setOf("http", "https") &&
                    uri.host == "igorganapolsky.github.io" &&
                    path.startsWith("Random-Timer")
            )

    if (!isSupportedScheme || !isUpgradeIntent) return null

    val requested = params["entry_point"] ?: params["feature"] ?: "setup_upgrade_cta"
    val entryPoint = normalizePaywallEntryPoint(requested)
    return MonetizationDeepLink(
        entryPoint = entryPoint,
        feature = featureForPaywallEntryPoint(entryPoint),
    )
}

internal fun normalizePaywallEntryPoint(value: String): String {
    val trimmed = value.trim()
    val knownEntryPoints =
        setOf(
            "setup_upgrade_cta",
            "range_gate",
            "voice_gate",
            "repeat_gate",
            "sound_arsenal_gate",
        )
    if (trimmed in knownEntryPoints) return trimmed
    return paywallEntryPointForFeature(trimmed)
        .takeUnless { it == "unknown" }
        ?: "setup_upgrade_cta"
}

internal fun featureForPaywallEntryPoint(entryPoint: String): String =
    when (entryPoint) {
        "range_gate" -> "extended_range"
        "voice_gate" -> "voice_callouts"
        "repeat_gate" -> "repeat_loop"
        "sound_arsenal_gate" -> "pro_sounds"
        else -> "setup_upgrade_cta"
    }

private fun parseQueryParams(rawQuery: String?): Map<String, String> {
    if (rawQuery.isNullOrBlank()) return emptyMap()
    return rawQuery
        .split('&')
        .mapNotNull { part ->
            val key = part.substringBefore('=', missingDelimiterValue = "").decodeQueryComponent()
            if (key.isBlank()) return@mapNotNull null
            val value = part.substringAfter('=', missingDelimiterValue = "").decodeQueryComponent()
            key to value
        }.toMap()
}

private fun String.decodeQueryComponent(): String = URLDecoder.decode(this, StandardCharsets.UTF_8.name())
