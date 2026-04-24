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

private enum VoicePreviewSampleCatalog {
    static let maleCommandFilenames = [
        "cmd_move_with_a_purpose", "cmd_stay_locked_in", "cmd_no_hesitation_move", "cmd_sound_off_and_drive",
        "cmd_snap_back_and_drive", "cmd_stay_disciplined", "cmd_keep_your_bearing", "cmd_reset_and_attack",
        "cmd_sharp_movement_sharp_focus", "cmd_stay_in_the_fight",
    ]
    static let maleElapsedFilename = "preview_elapsed"
    static let femaleCommandFilenames = [
        "female/cmd_move_with_a_purpose", "female/cmd_no_hesitation_move", "female/cmd_stay_in_the_fight",
        "female/cmd_push_pace", "female/cmd_keep_tempo_high", "female/cmd_finish_rep_keep_pushing",
        "female/cmd_drive_forward", "female/cmd_own_this_rep", "female/cmd_pick_it_up",
        "female/cmd_strong_feet_strong_pace",
    ]

    static let femaleElapsedFilename = "female/preview_elapsed"
}

private let fallbackVoiceCueCatalog = VoiceCueCatalog(
    previewElapsed: .init(
        filename: "preview_elapsed",
        text: "Thirty seconds elapsed. Move with a purpose."
    ),
    fallbackCommandFilename: "cmd_move_with_a_purpose",
    elapsedCues: [
        .init(second: 60, filename: "elapsed_60s", text: "One minute elapsed. Keep pressure on.")
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
        ?? {
            let path = filename as NSString
            let subdirectory = path.deletingLastPathComponent
            guard !subdirectory.isEmpty else { return nil }
            let resource = path.lastPathComponent
            return bundle.url(forResource: resource, withExtension: "mp3", subdirectory: "Audio/\(subdirectory)")
                ?? bundle.url(forResource: resource, withExtension: "mp3", subdirectory: subdirectory)
        }()
}

internal func voiceFilenameOrFallback(for text: String, bundle: Bundle = .main) -> String {
    let catalog = loadVoiceCalloutCatalog(bundle: bundle)
    return catalog.filenameByText[text] ?? catalog.fallbackCommandCue.filename
}

internal func genderedVoiceFilename(_ filename: String, gender: VoiceGender) -> String {
    switch gender {
    case .male:
        return filename
    case .female:
        if filename.hasPrefix("female/") {
            return filename
        }
        return "female/\(filename)"
    }
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

internal func nextPreviewFilename(
    from filenames: [String],
    lastFilename: String?,
    usedFilenames: inout Set<String>,
    pickIndex: (Int) -> Int
) -> String {
    guard !filenames.isEmpty else {
        return fallbackVoiceCueCatalog.fallbackCommandFilename
    }
    if filenames.count == 1 {
        let only = filenames[0]
        usedFilenames = [only]
        return only
    }
    var pool = filenames.filter { !usedFilenames.contains($0) }
    if pool.isEmpty {
        usedFilenames.removeAll()
        pool = filenames.filter { $0 != lastFilename }
        if pool.isEmpty {
            pool = filenames
        }
    }
    let boundedIndex = max(0, min(pool.count - 1, pickIndex(pool.count)))
    let candidate = pool[boundedIndex]
    let selected = candidate == lastFilename && pool.count > 1 ? pool[(boundedIndex + 1) % pool.count] : candidate
    usedFilenames.insert(selected)
    return selected
}

internal func initialFollowupCommandCueSecond(totalDurationSeconds: Int) -> Int {
    switch totalDurationSeconds {
    case ...30:
        return .max
    default:
        return 30
    }
}

internal protocol BackgroundVoiceKeepAliveEngine: AnyObject {
    var isRunning: Bool { get }
    var mainMixerNode: AVAudioMixerNode { get }
    func attach(_ node: AVAudioNode)
    func connect(_ node1: AVAudioNode, to node2: AVAudioNode, format: AVAudioFormat?)
    func prepare()
    func start() throws
    func stop()
    func reset()
}

extension AVAudioEngine: BackgroundVoiceKeepAliveEngine {}

@MainActor
final class BackgroundVoiceKeepAliveService: BackgroundVoiceKeepAliveHandling {
    typealias AudioSessionActivator = @MainActor () -> Void
    typealias AudioSessionDeactivator = @MainActor () -> Void
    typealias EngineFactory = @MainActor () -> BackgroundVoiceKeepAliveEngine

    static let shared = BackgroundVoiceKeepAliveService()

    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "voice-keepalive")

    private static func activateBackgroundAudioSession() {
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default, options: [.mixWithOthers])
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            log.error("Background voice audio session setup failed: \(error.localizedDescription)")
        }
    }

    private static func deactivateBackgroundAudioSession() {
        do {
            try AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        } catch {
            log.error("Background voice audio session teardown failed: \(error.localizedDescription)")
        }
    }

    private let makeEngine: EngineFactory
    private let activateAudioSession: AudioSessionActivator
    private let deactivateAudioSession: AudioSessionDeactivator
    private var audioEngine: BackgroundVoiceKeepAliveEngine?
    private var sourceNode: AVAudioSourceNode?

    var isActive: Bool {
        audioEngine?.isRunning == true
    }

    init(
        makeEngine: @escaping EngineFactory = { AVAudioEngine() },
        activateAudioSession: @escaping AudioSessionActivator =
            BackgroundVoiceKeepAliveService.activateBackgroundAudioSession,
        deactivateAudioSession: @escaping AudioSessionDeactivator =
            BackgroundVoiceKeepAliveService.deactivateBackgroundAudioSession
    ) {
        self.makeEngine = makeEngine
        self.activateAudioSession = activateAudioSession
        self.deactivateAudioSession = deactivateAudioSession
    }

    func start() {
        guard !isActive else { return }

        activateAudioSession()

        let engine = makeEngine()
        let format = AVAudioFormat(standardFormatWithSampleRate: 44_100, channels: 1)
        let silenceSource = AVAudioSourceNode { _, _, _, audioBufferList -> OSStatus in
            let buffers = UnsafeMutableAudioBufferListPointer(audioBufferList)
            for buffer in buffers {
                if let data = buffer.mData {
                    memset(data, 0, Int(buffer.mDataByteSize))
                }
            }
            return 0
        }

        engine.attach(silenceSource)
        engine.connect(silenceSource, to: engine.mainMixerNode, format: format)
        engine.mainMixerNode.outputVolume = 0
        engine.prepare()

        do {
            try engine.start()
            audioEngine = engine
            sourceNode = silenceSource
        } catch {
            Self.log.error("Background voice keepalive failed to start: \(error.localizedDescription)")
            sourceNode = nil
            audioEngine = nil
            deactivateAudioSession()
        }
    }

    func stop() {
        sourceNode = nil
        audioEngine?.stop()
        audioEngine?.reset()
        audioEngine = nil
        deactivateAudioSession()
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

    /// Current voice gender preference, set from TimerManager based on config.
    /// Male = drill sergeant, Female = HIIT instructor.
    var currentGender: VoiceGender = .male

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
    private var usedCommandCueFilenames: Set<String> = []
    private var lastCueFiredAtElapsed: Int?
    private var lastPreviewCommandFilenameByGender: [VoiceGender: String] = [:]
    private var usedPreviewCommandFilenamesByGender: [VoiceGender: Set<String>] = [:]

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
        let baseFilename = mappedFilename ?? catalog.fallbackCommandCue.filename
        let filename = genderedVoiceFilename(baseFilename, gender: currentGender)

        if mappedFilename == nil {
            Self.log.error("Unmapped cue requested, using bundled fallback: \(text, privacy: .public)")
        }

        playVoiceFile(named: filename, cueText: text)
    }

    private func speak(_ cue: VoiceCueCatalog.Cue) {
        activateAudioSession()

        let filename = genderedVoiceFilename(cue.filename, gender: currentGender)
        playVoiceFile(named: filename, cueText: cue.text)
    }

    func resetSession() {
        audioPlayer?.stop()
        audioPlayer = nil
        lastElapsedMilestone = 0
        nextCommandCueAt = 0
        lastCommandCueFilename = nil
        usedCommandCueFilenames.removeAll()
        lastPreviewCommandFilenameByGender.removeAll()
        usedPreviewCommandFilenamesByGender.removeAll()
        lastCueFiredAtElapsed = nil
    }

    func preview() {
        previewCommandCue(gender: currentGender)
    }

    func previewCommandCue(gender: VoiceGender = .male) {
        currentGender = gender
        activateAudioSession()

        let previewPool =
            gender == .female
            ? VoicePreviewSampleCatalog.femaleCommandFilenames
            : VoicePreviewSampleCatalog.maleCommandFilenames
        var usedFilenames = usedPreviewCommandFilenamesByGender[gender] ?? []
        let previewFilename = nextPreviewFilename(
            from: previewPool,
            lastFilename: lastPreviewCommandFilenameByGender[gender],
            usedFilenames: &usedFilenames
        ) { upperBound in
            secureRandomInt(in: 0...(upperBound - 1))
        }
        usedPreviewCommandFilenamesByGender[gender] = usedFilenames
        lastPreviewCommandFilenameByGender[gender] = previewFilename
        playVoiceFile(
            named: previewFilename,
            cueText: gender == .female ? "Female preview command sample" : "Male preview command sample"
        )
    }

    func previewCountdownCue(gender: VoiceGender = .male) {
        currentGender = gender
        activateAudioSession()

        let previewElapsedFilename =
            gender == .female
            ? VoicePreviewSampleCatalog.femaleElapsedFilename
            : VoicePreviewSampleCatalog.maleElapsedFilename
        playVoiceFile(
            named: previewElapsedFilename,
            cueText: gender == .female ? "Female preview elapsed sample" : "Male preview elapsed sample"
        )
    }

    func beginSession(totalDurationSeconds: Int, gender: VoiceGender = .male) {
        currentGender = gender
        nextCommandCueAt = initialFollowupCommandCueSecond(totalDurationSeconds: totalDurationSeconds)
    }

    private func playVoiceFile(named filename: String, cueText: String) {
        guard let url = packStore.voiceAudioURL(for: filename, bundle: bundle) else {
            Self.log.error("Voice asset missing for cue: \(cueText, privacy: .public)")
            return
        }

        do {
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.volume = 1.0
            audioPlayer?.play()
        } catch {
            Self.log.error("Audio playback failed: \(error.localizedDescription)")
        }
    }

    func triggerCallout(elapsedSeconds: Int) {
        if let last = lastCueFiredAtElapsed, elapsedSeconds - last < 30 {
            return
        }

        if let callout = elapsedMilestone(for: elapsedSeconds) {
            speak(.init(filename: callout.filename, text: callout.text))
            lastElapsedMilestone = callout.second
            if nextCommandCueAt <= elapsedSeconds {
                nextCommandCueAt = elapsedSeconds + 30
            }
            lastCueFiredAtElapsed = elapsedSeconds
            return
        }

        if shouldFireCommandCue(elapsedSeconds: elapsedSeconds) {
            let cue = randomCommandCue()
            speak(cue)
            lastCommandCueFilename = cue.filename
            nextCommandCueAt = elapsedSeconds + 30
            lastCueFiredAtElapsed = elapsedSeconds
        }
    }

    /// Returns the latest crossed "time elapsed" line on full-minute marks (60, 120, …).
    /// Sub-minute elapsed rows stay out of runtime so command coaching keeps its own cadence.
    private func elapsedMilestone(for elapsed: Int) -> VoiceCueCatalog.ElapsedCue? {
        let catalog = packStore.voiceCatalog(bundle: bundle)
        return catalog.elapsedCues
            .filter { $0.second > lastElapsedMilestone && $0.second <= elapsed && $0.second.isMultiple(of: 60) }
            .max(by: { $0.second < $1.second })
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
        // Only consider cues whose audio is actually resolvable. Without this, unbundled
        // cues cause playback to fall back to `cmd_move_with_a_purpose` and the user hears
        // the same line on repeat while dedup thinks different cues were picked.
        let playable = catalog.commandCues.filter { cueHasAudio($0.filename) }
        let baseline = playable.isEmpty ? catalog.commandCues : playable
        var pool = baseline.filter { !usedCommandCueFilenames.contains($0.filename) }
        if pool.isEmpty {
            usedCommandCueFilenames.removeAll()
            pool = baseline.filter { $0.filename != lastCommandCueFilename }
            if pool.isEmpty { pool = baseline }
        }
        let cue = nextCommandCue(from: pool, lastFilename: lastCommandCueFilename) { upperBound in
            secureRandomInt(in: 0...(upperBound - 1))
        }
        lastCommandCueFilename = cue.filename
        usedCommandCueFilenames.insert(cue.filename)
        return cue
    }

    private func cueHasAudio(_ filename: String) -> Bool {
        let gendered = genderedVoiceFilename(filename, gender: currentGender)
        return packStore.voiceAudioURL(for: gendered, bundle: bundle) != nil
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
