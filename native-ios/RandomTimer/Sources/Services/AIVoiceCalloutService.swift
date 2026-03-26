import AVFoundation
import Foundation
import Security
import os

internal struct VoiceCueCatalog: Codable {
    struct Cue: Codable, Hashable {
        let filename: String
        let text: String
    }

    struct ElapsedCue: Codable, Hashable {
        let second: Int
        let filename: String
        let text: String
    }

    let previewElapsed: Cue
    let fallbackCommandFilename: String
    let elapsedCues: [ElapsedCue]
    let commandCues: [Cue]

    var elapsedCueBySecond: [Int: ElapsedCue] {
        var mapping = [Int: ElapsedCue]()
        for cue in elapsedCues where mapping[cue.second] == nil {
            mapping[cue.second] = cue
        }
        return mapping
    }

    var fallbackCommandCue: Cue {
        commandCues.first(where: { $0.filename == fallbackCommandFilename }) ?? commandCues.first ?? previewElapsed
    }

    var filenameByText: [String: String] {
        var mapping = [String: String]()

        if mapping[previewElapsed.text] == nil {
            mapping[previewElapsed.text] = previewElapsed.filename
        }

        for cue in elapsedCues where mapping[cue.text] == nil {
            mapping[cue.text] = cue.filename
        }

        for cue in commandCues where mapping[cue.text] == nil {
            mapping[cue.text] = cue.filename
        }

        return mapping
    }

    var bundledFilenames: [String] {
        [previewElapsed.filename]
            + elapsedCues.map(\.filename)
            + commandCues.map(\.filename)
    }
}

internal let voiceCatalogResourceName = "voice_callouts"

private let fallbackVoiceCueCatalog = VoiceCueCatalog(
    previewElapsed: .init(
        filename: "preview_elapsed",
        text: "Thirty seconds elapsed. Move with a purpose."
    ),
    fallbackCommandFilename: "cmd_move_with_a_purpose",
    elapsedCues: [
        .init(second: 30, filename: "elapsed_30s", text: "Thirty seconds elapsed. Move with a purpose.")
    ],
    commandCues: [
        .init(filename: "cmd_move_with_a_purpose", text: "Move with a purpose."),
        .init(filename: "cmd_stay_locked_in", text: "Stay locked in.")
    ]
)

internal func loadVoiceCalloutCatalog(bundle: Bundle = .main) -> VoiceCueCatalog {
    guard let url = bundle.url(forResource: voiceCatalogResourceName, withExtension: "json", subdirectory: "Audio")
        ?? bundle.url(forResource: voiceCatalogResourceName, withExtension: "json")
    else {
        return fallbackVoiceCueCatalog
    }

    do {
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(VoiceCueCatalog.self, from: data)
    } catch {
        return fallbackVoiceCueCatalog
    }
}

internal func voiceFilename(for text: String, bundle: Bundle = .main) -> String? {
    loadVoiceCalloutCatalog(bundle: bundle).filenameByText[text]
}

internal func bundledVoiceAudioURL(for filename: String, bundle: Bundle = .main) -> URL? {
    bundle.url(forResource: filename, withExtension: "mp3", subdirectory: "Audio")
        ?? bundle.url(forResource: filename, withExtension: "mp3")
}

internal func voiceFilenameOrFallback(for text: String, bundle: Bundle = .main) -> String {
    let catalog = loadVoiceCalloutCatalog(bundle: bundle)
    return catalog.filenameByText[text] ?? catalog.fallbackCommandCue.filename
}

internal func nextCommandCue(
    from cues: [VoiceCueCatalog.Cue],
    lastFilename: String?,
    pickIndex: (Int) -> Int
) -> VoiceCueCatalog.Cue {
    guard !cues.isEmpty else {
        return fallbackVoiceCueCatalog.fallbackCommandCue
    }

    if cues.count == 1 {
        return cues[0]
    }

    let boundedIndex = max(0, min(cues.count - 1, pickIndex(cues.count)))
    let candidate = cues[boundedIndex]
    guard candidate.filename == lastFilename else {
        return candidate
    }

    let nextIndex = (boundedIndex + 1) % cues.count
    return cues[nextIndex]
}

internal func initialFollowupCommandCueSecond(totalDurationSeconds: Int) -> Int {
    switch totalDurationSeconds {
    case ...29:
        return .max
    default:
        return 30
    }
}

@MainActor
final class AIVoiceCalloutService {
    struct StateSnapshot {
        let lastElapsedMilestone: Int
        let nextCommandCueAt: Int
        let lastCommandCueFilename: String?
    }

    typealias AudioSessionActivator = @MainActor () -> Void

    static let shared = AIVoiceCalloutService()

    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "voice")
    private static func activateVoiceAudioSession() {
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, options: [.duckOthers])
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            log.error("Audio session setup failed: \(error.localizedDescription)")
        }
    }

    private let bundle: Bundle
    private let packStore: ProAudioPackStore
    private let activateAudioSession: AudioSessionActivator
    private var audioPlayer: AVAudioPlayer?
    private var lastElapsedMilestone = 0
    private var nextCommandCueAt = 0
    private var lastCommandCueFilename: String?

    init(
        bundle: Bundle = .main,
        packStore: ProAudioPackStore = .shared,
        activateAudioSession: @escaping AudioSessionActivator = AIVoiceCalloutService.activateVoiceAudioSession
    ) {
        self.bundle = bundle
        self.packStore = packStore
        self.activateAudioSession = activateAudioSession
        self.activateAudioSession()
    }

    func speak(_ text: String) {
        activateAudioSession()

        let catalog = packStore.voiceCatalog(bundle: bundle)
        let mappedFilename = catalog.filenameByText[text]
        let filename = mappedFilename ?? catalog.fallbackCommandCue.filename

        guard let url = packStore.voiceAudioURL(for: filename, bundle: bundle) else {
            Self.log.error("Voice asset missing for cue: \(text, privacy: .public)")
            return
        }

        if mappedFilename == nil {
            Self.log.error("Unmapped cue requested, using bundled fallback: \(text, privacy: .public)")
        }

        do {
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.volume = 1.0
            audioPlayer?.play()
        } catch {
            Self.log.error("Audio playback failed: \(error.localizedDescription)")
        }
    }

    func resetSession() {
        audioPlayer?.stop()
        audioPlayer = nil
        lastElapsedMilestone = 0
        nextCommandCueAt = 0
        lastCommandCueFilename = nil
    }

    func preview() {
        previewCommandCue()
    }

    func previewCommandCue() {
        let cue = randomCommandCue()
        speak(cue.text)
    }

    func previewCountdownCue() {
        let catalog = packStore.voiceCatalog(bundle: bundle)
        speak(catalog.previewElapsed.text)
    }

    func beginSession(totalDurationSeconds: Int) {
        nextCommandCueAt = initialFollowupCommandCueSecond(totalDurationSeconds: totalDurationSeconds)
    }

    func triggerCallout(elapsedSeconds: Int) {
        if let callout = elapsedMilestone(for: elapsedSeconds) {
            speak(callout.text)
            lastElapsedMilestone = elapsedSeconds
            return
        }

        // Command cues disabled — only elapsed cues fire at 30s intervals
    }

    private func elapsedMilestone(for elapsed: Int) -> VoiceCueCatalog.ElapsedCue? {
        let catalog = packStore.voiceCatalog(bundle: bundle)
        guard let cue = catalog.elapsedCueBySecond[elapsed], elapsed != lastElapsedMilestone else {
            return nil
        }
        return cue
    }

    private func shouldFireCommandCue(elapsedSeconds: Int) -> Bool {
        if nextCommandCueAt == 0 {
            nextCommandCueAt = 30
        }
        if nextCommandCueAt == .max {
            return false
        }
        return elapsedSeconds >= nextCommandCueAt
    }

    private func randomCommandCue() -> VoiceCueCatalog.Cue {
        let catalog = packStore.voiceCatalog(bundle: bundle)
        let cue = nextCommandCue(from: catalog.commandCues, lastFilename: lastCommandCueFilename) { upperBound in
            secureRandomInt(in: 0...(upperBound - 1))
        }
        lastCommandCueFilename = cue.filename
        return cue
    }

    private func secureRandomInt(in range: ClosedRange<Int>) -> Int {
        let count = range.upperBound - range.lowerBound + 1
        var randomValue: UInt32 = 0
        let status = SecRandomCopyBytes(kSecRandomDefault, MemoryLayout<UInt32>.size, &randomValue)

        if status == errSecSuccess {
            return range.lowerBound + Int(randomValue % UInt32(count))
        } else {
            return Int.random(in: range)
        }
    }

    func _stateSnapshotForTesting() -> StateSnapshot {
        StateSnapshot(
            lastElapsedMilestone: lastElapsedMilestone,
            nextCommandCueAt: nextCommandCueAt,
            lastCommandCueFilename: lastCommandCueFilename
        )
    }
}
