import CryptoKit
import Foundation
import os

internal struct ProSoundCatalog: Codable {
    struct Sound: Codable, Hashable {
        let soundType: String
        let filename: String
        let durationSeconds: Double
    }

    let packId: String
    let releaseMonth: String
    let entitlement: String
    let sounds: [Sound]

    var filenameByType: [SoundType: String] {
        Dictionary(uniqueKeysWithValues: sounds.compactMap { sound in
            guard let soundType = SoundType.fromLoose(sound.soundType) else { return nil }
            return (soundType, sound.filename)
        })
    }
}

internal let soundCatalogResourceName = "sound_arsenal"

private let fallbackProSoundCatalog = ProSoundCatalog(
    packId: "fallback",
    releaseMonth: "fallback",
    entitlement: "pro",
    sounds: [
        .init(soundType: "intense", filename: "alarm", durationSeconds: 4),
        .init(soundType: "gentle", filename: "gentle-chime", durationSeconds: 4),
        .init(soundType: "klaxon", filename: "klaxon", durationSeconds: 4),
        .init(soundType: "whistle", filename: "whistle", durationSeconds: 3),
        .init(soundType: "buzzer", filename: "buzzer", durationSeconds: 3),
        .init(soundType: "gong", filename: "gong", durationSeconds: 5),
        .init(soundType: "airhorn", filename: "airhorn", durationSeconds: 3),
        .init(soundType: "drumRoll", filename: "drum_roll", durationSeconds: 4),
        .init(soundType: "siren", filename: "siren", durationSeconds: 4),
        .init(soundType: "bell", filename: "bell", durationSeconds: 4),
    ]
)

internal func loadProSoundCatalog(bundle: Bundle = .main) -> ProSoundCatalog {
    guard let url = bundle.url(forResource: soundCatalogResourceName, withExtension: "json", subdirectory: "Audio")
        ?? bundle.url(forResource: soundCatalogResourceName, withExtension: "json")
    else {
        return fallbackProSoundCatalog
    }

    do {
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(ProSoundCatalog.self, from: data)
    } catch {
        return fallbackProSoundCatalog
    }
}

internal func bundledProSoundAudioURL(for type: SoundType, bundle: Bundle = .main) -> URL? {
    let resourceName = proSoundResourceName(for: type, bundle: bundle)
    return bundle.url(forResource: resourceName, withExtension: "mp3")
        ?? bundle.url(forResource: resourceName, withExtension: "mp3", subdirectory: "Sounds")
}

internal func proSoundResourceName(for type: SoundType, bundle: Bundle = .main) -> String {
    loadProSoundCatalog(bundle: bundle).filenameByType[type] ?? type.notificationSoundName.replacingOccurrences(of: ".mp3", with: "")
}

internal enum RemoteProAudioAssetKind: String, Codable {
    case voice
    case sound
}

internal struct RemoteProAudioManifestAsset: Codable, Hashable {
    let kind: RemoteProAudioAssetKind
    let filename: String
    let relativePath: String
    let url: URL
    let sha256: String
    let bytes: Int
}

internal struct RemoteProAudioManifest: Codable {
    let schemaVersion: Int
    let packId: String
    let releaseMonth: String
    let entitlement: String
    let generatedAt: String
    let voiceCatalog: VoiceCueCatalog
    let soundCatalog: ProSoundCatalog
    let assets: [RemoteProAudioManifestAsset]

    var voiceAssetsByFilename: [String: RemoteProAudioManifestAsset] {
        Dictionary(uniqueKeysWithValues: assets.compactMap {
            guard $0.kind == .voice else { return nil }
            return ($0.filename, $0)
        })
    }

    var soundAssetsByFilename: [String: RemoteProAudioManifestAsset] {
        Dictionary(uniqueKeysWithValues: assets.compactMap {
            guard $0.kind == .sound else { return nil }
            return ($0.filename, $0)
        })
    }
}

internal final class ProAudioPackStore: @unchecked Sendable {
    static let shared = ProAudioPackStore()

    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "pro-audio-pack")
    private let bundle: Bundle
    private let fileManager: FileManager
    private let cacheRoot: URL
    private let manifestURL: URL?
    private let session: URLSession
    private let lock = NSLock()
    private var activeManifest: RemoteProAudioManifest?

    init(
        bundle: Bundle = .main,
        manifestURL: URL? = nil,
        cacheRoot: URL? = nil,
        fileManager: FileManager = .default,
        session: URLSession = .shared
    ) {
        self.bundle = bundle
        self.fileManager = fileManager
        self.session = session
        self.manifestURL = manifestURL ?? Self.configuredManifestURL(bundle: bundle)
        self.cacheRoot = cacheRoot ?? Self.defaultCacheRoot(fileManager: fileManager)

        do {
            try fileManager.createDirectory(at: self.cacheRoot, withIntermediateDirectories: true, attributes: nil)
        } catch {
            Self.log.error("Failed to prepare Pro audio cache root: \(error.localizedDescription)")
        }

        self.activeManifest = Self.loadCachedManifest(at: self.manifestFileURL, fileManager: fileManager)
    }

    func refreshIfNeeded(isPro: Bool) async {
        guard isPro, let manifestURL else { return }

        do {
            let (manifestData, response) = try await session.data(from: manifestURL)
            try Self.validateHTTP(response, url: manifestURL)
            let manifest = try JSONDecoder().decode(RemoteProAudioManifest.self, from: manifestData)

            if isInstalled(manifest: manifest) {
                return
            }

            let stagingRoot = cacheRoot.appendingPathComponent("staging-\(UUID().uuidString)", isDirectory: true)
            try fileManager.createDirectory(at: stagingRoot, withIntermediateDirectories: true, attributes: nil)
            defer { try? fileManager.removeItem(at: stagingRoot) }

            try await stageAssets(for: manifest, into: stagingRoot)
            try install(manifest: manifest, manifestData: manifestData, stagedRoot: stagingRoot)
            Self.log.info("Installed remote Pro audio pack \(manifest.packId, privacy: .public)")
        } catch {
            Self.log.error("Remote Pro audio refresh failed: \(error.localizedDescription)")
        }
    }

    func voiceCatalog(bundle: Bundle = .main) -> VoiceCueCatalog {
        lock.lock()
        let manifest = activeManifest
        lock.unlock()
        return manifest?.voiceCatalog ?? loadVoiceCalloutCatalog(bundle: bundle)
    }

    func voiceAudioURL(for filename: String, bundle: Bundle = .main) -> URL? {
        if let assetURL = cachedAssetURL(kind: .voice, filename: filename) {
            return assetURL
        }
        return bundledVoiceAudioURL(for: filename, bundle: bundle)
    }

    func soundCatalog(bundle: Bundle = .main) -> ProSoundCatalog {
        lock.lock()
        let manifest = activeManifest
        lock.unlock()
        return manifest?.soundCatalog ?? loadProSoundCatalog(bundle: bundle)
    }

    func soundAudioURL(for type: SoundType, bundle: Bundle = .main) -> URL? {
        let catalog = soundCatalog(bundle: bundle)
        if let filename = catalog.filenameByType[type],
           let assetURL = cachedAssetURL(kind: .sound, filename: filename) {
            return assetURL
        }
        return bundledProSoundAudioURL(for: type, bundle: bundle)
    }

    func _installForTesting(
        manifest: RemoteProAudioManifest,
        payloadsByKey: [String: Data]
    ) throws {
        let stagingRoot = cacheRoot.appendingPathComponent("test-staging-\(UUID().uuidString)", isDirectory: true)
        try fileManager.createDirectory(at: stagingRoot, withIntermediateDirectories: true, attributes: nil)
        defer { try? fileManager.removeItem(at: stagingRoot) }

        for asset in manifest.assets {
            let key = "\(asset.kind.rawValue):\(asset.filename)"
            guard let payload = payloadsByKey[key] else {
                throw NSError(domain: "ProAudioPackStore", code: 2, userInfo: [NSLocalizedDescriptionKey: "Missing test payload for \(key)"])
            }
            try Self.validateAsset(payload, expected: asset)
            let destination = try resolve(relativePath: asset.relativePath, root: stagingRoot)
            try fileManager.createDirectory(at: destination.deletingLastPathComponent(), withIntermediateDirectories: true, attributes: nil)
            try payload.write(to: destination, options: .atomic)
        }

        let manifestData = try JSONEncoder().encode(manifest)
        try install(manifest: manifest, manifestData: manifestData, stagedRoot: stagingRoot)
    }

    private func isInstalled(manifest: RemoteProAudioManifest) -> Bool {
        lock.lock()
        defer { lock.unlock() }
        guard activeManifest?.packId == manifest.packId else { return false }
        return manifest.assets.allSatisfy { asset in
            if let url = try? resolve(relativePath: asset.relativePath, root: cacheRoot) {
                return fileManager.fileExists(atPath: url.path)
            }
            return false
        }
    }

    private func stageAssets(for manifest: RemoteProAudioManifest, into stagingRoot: URL) async throws {
        for asset in manifest.assets {
            let (data, response) = try await session.data(from: asset.url)
            try Self.validateHTTP(response, url: asset.url)
            try Self.validateAsset(data, expected: asset)
            let destination = try resolve(relativePath: asset.relativePath, root: stagingRoot)
            try fileManager.createDirectory(at: destination.deletingLastPathComponent(), withIntermediateDirectories: true, attributes: nil)
            try data.write(to: destination, options: .atomic)
        }
    }

    private func install(
        manifest: RemoteProAudioManifest,
        manifestData: Data,
        stagedRoot: URL
    ) throws {
        let packsRoot = cacheRoot.appendingPathComponent("packs", isDirectory: true)
        if fileManager.fileExists(atPath: packsRoot.path) {
            try fileManager.removeItem(at: packsRoot)
        }
        try fileManager.createDirectory(at: cacheRoot, withIntermediateDirectories: true, attributes: nil)

        let stagedPacks = stagedRoot.appendingPathComponent("packs", isDirectory: true)
        if fileManager.fileExists(atPath: stagedPacks.path) {
            try fileManager.moveItem(at: stagedPacks, to: packsRoot)
        }
        try manifestData.write(to: manifestFileURL, options: .atomic)

        lock.lock()
        activeManifest = manifest
        lock.unlock()
    }

    private func cachedAssetURL(kind: RemoteProAudioAssetKind, filename: String) -> URL? {
        lock.lock()
        let manifest = activeManifest
        lock.unlock()

        let asset: RemoteProAudioManifestAsset?
        switch kind {
        case .voice:
            asset = manifest?.voiceAssetsByFilename[filename]
        case .sound:
            asset = manifest?.soundAssetsByFilename[filename]
        }

        guard let asset else { return nil }
        guard let url = try? resolve(relativePath: asset.relativePath, root: cacheRoot) else { return nil }
        return fileManager.fileExists(atPath: url.path) ? url : nil
    }

    private func resolve(relativePath: String, root: URL) throws -> URL {
        guard relativePath.contains("..") == false else {
            throw NSError(domain: "ProAudioPackStore", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid relative path \(relativePath)"])
        }
        return root.appendingPathComponent(relativePath, isDirectory: false)
    }

    private var manifestFileURL: URL {
        cacheRoot.appendingPathComponent("latest.json", isDirectory: false)
    }

    private static func validateHTTP(_ response: URLResponse, url: URL) throws {
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw NSError(
                domain: "ProAudioPackStore",
                code: http.statusCode,
                userInfo: [NSLocalizedDescriptionKey: "Unexpected HTTP \(http.statusCode) for \(url.absoluteString)"]
            )
        }
    }

    private static func validateAsset(_ data: Data, expected: RemoteProAudioManifestAsset) throws {
        if expected.bytes > 0 && data.count != expected.bytes {
            throw NSError(
                domain: "ProAudioPackStore",
                code: 3,
                userInfo: [NSLocalizedDescriptionKey: "Unexpected size for \(expected.filename). Expected \(expected.bytes), got \(data.count)."]
            )
        }

        let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        guard digest == expected.sha256.lowercased() else {
            throw NSError(
                domain: "ProAudioPackStore",
                code: 4,
                userInfo: [NSLocalizedDescriptionKey: "Checksum mismatch for \(expected.filename)."]
            )
        }
    }

    private static func defaultCacheRoot(fileManager: FileManager) -> URL {
        fileManager.urls(for: .cachesDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("ProAudio", isDirectory: true)
    }

    private static func configuredManifestURL(bundle: Bundle) -> URL? {
        let configured = bundle.object(forInfoDictionaryKey: "PRO_AUDIO_MANIFEST_URL") as? String
        return configured.flatMap(URL.init(string:))
    }

    private static func loadCachedManifest(at url: URL, fileManager: FileManager) -> RemoteProAudioManifest? {
        guard fileManager.fileExists(atPath: url.path),
              let data = try? Data(contentsOf: url) else {
            return nil
        }
        return try? JSONDecoder().decode(RemoteProAudioManifest.self, from: data)
    }
}
