package com.iganapolsky.randomtimer.service

import android.content.Context
import android.util.Log
import com.iganapolsky.randomtimer.BuildConfig
import com.iganapolsky.randomtimer.domain.model.SoundType
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URI
import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton

data class ProSoundCatalogEntry(
    val soundType: String,
    val filename: String,
)

data class ProSoundCatalog(
    val packId: String,
    val releaseMonth: String,
    val entitlement: String,
    val sounds: List<ProSoundCatalogEntry>,
) {
    val filenameByType: Map<SoundType, String>
        get() =
            sounds
                .mapNotNull { entry ->
                    soundTypeFromLoose(entry.soundType)?.let { it to entry.filename }
                }.toMap()
}

internal enum class RemoteProAudioAssetKind {
    VOICE,
    SOUND,
}

internal data class RemoteProAudioManifestAsset(
    val kind: RemoteProAudioAssetKind,
    val filename: String,
    val relativePath: String,
    val url: String,
    val sha256: String,
    val bytes: Int,
)

internal data class RemoteProAudioManifest(
    val schemaVersion: Int,
    val packId: String,
    val releaseMonth: String,
    val entitlement: String,
    val generatedAt: String,
    val voiceCatalog: VoiceCueCatalog,
    val soundCatalog: ProSoundCatalog,
    val assets: List<RemoteProAudioManifestAsset>,
) {
    val voiceAssetsByFilename: Map<String, RemoteProAudioManifestAsset>
        get() = assets.filter { it.kind == RemoteProAudioAssetKind.VOICE }.associateBy { it.filename }

    val soundAssetsByFilename: Map<String, RemoteProAudioManifestAsset>
        get() = assets.filter { it.kind == RemoteProAudioAssetKind.SOUND }.associateBy { it.filename }
}

private const val SOUND_CATALOG_ASSET = "sound_arsenal.json"

private val fallbackProSoundCatalog =
    ProSoundCatalog(
        packId = "fallback",
        releaseMonth = "fallback",
        entitlement = "pro",
        sounds =
            listOf(
                ProSoundCatalogEntry("intense", "alarm"),
                ProSoundCatalogEntry("gentle", "gentle_chime"),
                ProSoundCatalogEntry("klaxon", "klaxon"),
                ProSoundCatalogEntry("whistle", "whistle"),
                ProSoundCatalogEntry("buzzer", "buzzer"),
                ProSoundCatalogEntry("gong", "gong"),
                ProSoundCatalogEntry("airhorn", "airhorn"),
                ProSoundCatalogEntry("drum_roll", "drum_roll"),
                ProSoundCatalogEntry("siren", "siren"),
                ProSoundCatalogEntry("bell", "bell"),
            ),
    )

private fun soundTypeFromLoose(rawValue: String): SoundType? =
    when (
        rawValue
            .trim()
            .lowercase()
            .replace("_", "")
            .replace("-", "")
            .replace(" ", "")
    ) {
        "intense" -> SoundType.INTENSE
        "gentle" -> SoundType.GENTLE
        "klaxon" -> SoundType.KLAXON
        "whistle" -> SoundType.WHISTLE
        "buzzer" -> SoundType.BUZZER
        "gong" -> SoundType.GONG
        "airhorn" -> SoundType.AIRHORN
        "drumroll" -> SoundType.DRUM_ROLL
        "siren" -> SoundType.SIREN
        "bell" -> SoundType.BELL
        else -> null
    }

internal fun parseProSoundCatalog(json: String): ProSoundCatalog {
    val root = JSONObject(json)
    val soundsArray = root.getJSONArray("sounds")
    return ProSoundCatalog(
        packId = root.getString("packId"),
        releaseMonth = root.getString("releaseMonth"),
        entitlement = root.getString("entitlement"),
        sounds = soundsArray.toSoundEntries(),
    )
}

internal fun parseRemoteProAudioManifest(json: String): RemoteProAudioManifest {
    val root = JSONObject(json)
    return RemoteProAudioManifest(
        schemaVersion = root.getInt("schemaVersion"),
        packId = root.getString("packId"),
        releaseMonth = root.getString("releaseMonth"),
        entitlement = root.getString("entitlement"),
        generatedAt = root.getString("generatedAt"),
        voiceCatalog = parseVoiceCalloutCatalog(root.getJSONObject("voiceCatalog").toString()),
        soundCatalog = parseProSoundCatalog(root.getJSONObject("soundCatalog").toString()),
        assets = root.getJSONArray("assets").toRemoteAssets(),
    )
}

private fun JSONArray.toSoundEntries(): List<ProSoundCatalogEntry> =
    buildList {
        for (index in 0 until length()) {
            val item = getJSONObject(index)
            add(
                ProSoundCatalogEntry(
                    soundType = item.getString("soundType"),
                    filename = item.getString("filename"),
                ),
            )
        }
    }

private fun JSONArray.toRemoteAssets(): List<RemoteProAudioManifestAsset> =
    buildList {
        for (index in 0 until length()) {
            val item = getJSONObject(index)
            add(
                RemoteProAudioManifestAsset(
                    kind = RemoteProAudioAssetKind.valueOf(item.getString("kind").uppercase()),
                    filename = item.getString("filename"),
                    relativePath = item.getString("relativePath"),
                    url = item.getString("url"),
                    sha256 = item.getString("sha256"),
                    bytes = item.getInt("bytes"),
                ),
            )
        }
    }

internal fun loadProSoundCatalog(context: Context): ProSoundCatalog =
    runCatching {
        context.assets
            .open(SOUND_CATALOG_ASSET)
            .bufferedReader()
            .use { parseProSoundCatalog(it.readText()) }
    }.getOrElse { fallbackProSoundCatalog }

internal fun resolveBundledProSoundFilename(
    context: Context,
    soundType: SoundType,
): String =
    (loadProSoundCatalog(context).filenameByType[soundType] ?: fallbackProSoundCatalog.filenameByType.getValue(soundType))
        .replace("-", "_")

internal fun resolveProSoundResId(
    context: Context,
    soundType: SoundType,
): Int {
    val filename = resolveBundledProSoundFilename(context, soundType)
    return context.resources.getIdentifier(filename, "raw", context.packageName)
}

@Singleton
class ProAudioPackStore
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
        private val externalScope: CoroutineScope,
    ) {
        private val cacheRoot = File(context.cacheDir, "pro-audio")

        @Volatile
        private var activeManifest: RemoteProAudioManifest? = loadCachedManifest()

        init {
            cacheRoot.mkdirs()
        }

        fun refreshIfNeeded(isPro: Boolean) {
            if (!isPro) {
                return
            }
            externalScope.launch(Dispatchers.IO) {
                runCatching { refreshBlocking() }
                    .onFailure { error ->
                        Log.e("ProAudioPackStore", "Remote Pro audio refresh failed", error)
                    }
            }
        }

        internal fun voiceCatalog(): VoiceCueCatalog = activeManifest?.voiceCatalog ?: loadVoiceCalloutCatalog(context)

        internal fun soundCatalog(): ProSoundCatalog = activeManifest?.soundCatalog ?: loadProSoundCatalog(context)

        internal fun voiceFile(filename: String): File? =
            activeManifest
                ?.voiceAssetsByFilename
                ?.get(filename)
                ?.let(::resolveCachedFile)
                ?.takeIf(File::exists)

        internal fun soundFile(soundType: SoundType): File? {
            val filename = soundCatalog().filenameByType[soundType] ?: return null
            return activeManifest
                ?.soundAssetsByFilename
                ?.get(filename)
                ?.let(::resolveCachedFile)
                ?.takeIf(File::exists)
        }

        internal fun installForTesting(
            manifest: RemoteProAudioManifest,
            payloadsByKey: Map<String, ByteArray>,
        ) {
            val packsRoot = File(cacheRoot, "packs")
            packsRoot.deleteRecursively()

            manifest.assets.forEach { asset ->
                val key = "${asset.kind.name.lowercase()}:${asset.filename}"
                val bytes =
                    payloadsByKey[key]
                        ?: error("Missing test payload for $key")
                validateAsset(bytes, asset)
                val destination = resolveCachedFile(asset)
                destination.parentFile?.mkdirs()
                destination.writeBytes(bytes)
            }

            activeManifest = manifest
        }

        private fun refreshBlocking() {
            val manifestUrl = BuildConfig.PRO_AUDIO_MANIFEST_URL.trim()
            if (manifestUrl.isEmpty()) {
                return
            }

            val manifestJson = downloadText(manifestUrl)
            val manifest = parseRemoteProAudioManifest(manifestJson)
            if (isInstalled(manifest)) {
                return
            }

            val stagingRoot = File(cacheRoot, "staging-${System.currentTimeMillis()}")
            stagingRoot.mkdirs()
            try {
                manifest.assets.forEach { asset ->
                    val bytes = downloadBytes(asset.url)
                    validateAsset(bytes, asset)
                    val destination = resolveFile(stagingRoot, asset.relativePath)
                    destination.parentFile?.mkdirs()
                    destination.writeBytes(bytes)
                }

                installManifest(manifest, manifestJson, stagingRoot)
                Log.i("ProAudioPackStore", "Installed remote Pro audio pack ${manifest.packId}")
            } finally {
                stagingRoot.deleteRecursively()
            }
        }

        private fun installManifest(
            manifest: RemoteProAudioManifest,
            manifestJson: String,
            stagingRoot: File,
        ) {
            val packsRoot = File(cacheRoot, "packs")
            packsRoot.deleteRecursively()
            val stagedPacks = File(stagingRoot, "packs")
            if (stagedPacks.exists()) {
                stagedPacks.copyRecursively(packsRoot, overwrite = true)
            }
            File(cacheRoot, "latest.json").writeText(manifestJson)
            activeManifest = manifest
        }

        private fun isInstalled(manifest: RemoteProAudioManifest): Boolean {
            val current = activeManifest ?: return false
            if (current.packId != manifest.packId) {
                return false
            }
            return manifest.assets.all { asset -> resolveCachedFile(asset).exists() }
        }

        private fun resolveCachedFile(asset: RemoteProAudioManifestAsset): File = resolveFile(cacheRoot, asset.relativePath)

        private fun resolveFile(
            root: File,
            relativePath: String,
        ): File {
            require(!relativePath.contains("..")) { "Invalid relative path $relativePath" }
            return File(root, relativePath)
        }

        private fun loadCachedManifest(): RemoteProAudioManifest? {
            val manifestFile = File(cacheRoot, "latest.json")
            if (!manifestFile.exists()) {
                return null
            }
            return runCatching { parseRemoteProAudioManifest(manifestFile.readText()) }.getOrNull()
        }

        private fun downloadText(url: String): String = downloadBytes(url).decodeToString()

        private fun downloadBytes(url: String): ByteArray {
            val connection = URI.create(url).toURL().openConnection() as HttpURLConnection
            try {
                connection.requestMethod = "GET"
                connection.connectTimeout = 15_000
                connection.readTimeout = 30_000
                connection.instanceFollowRedirects = true
                val status = connection.responseCode
                if (status !in 200..299) {
                    connection.errorStream?.close()
                    throw IllegalStateException("Unexpected HTTP $status for $url")
                }
                return connection.inputStream.use { stream -> stream.readBytes() }
            } finally {
                connection.disconnect()
            }
        }

        private fun validateAsset(
            bytes: ByteArray,
            asset: RemoteProAudioManifestAsset,
        ) {
            check(asset.bytes <= 0 || bytes.size == asset.bytes) {
                "Unexpected size for ${asset.filename}: expected ${asset.bytes}, got ${bytes.size}"
            }
            val digest =
                MessageDigest
                    .getInstance("SHA-256")
                    .digest(bytes)
                    .joinToString(separator = "") { "%02x".format(it) }
            check(digest == asset.sha256.lowercase()) { "Checksum mismatch for ${asset.filename}" }
        }
    }
