import Foundation
import AVFoundation
import os

internal let previewElapsedCue = "Thirty seconds. Stay locked in."
internal let previewCommandVoiceCue = "Stay sharp."
internal let defaultFallbackVoiceCue = previewCommandVoiceCue

internal let elapsedVoiceCuesBySecond: [Int: String] = [
    30: "Thirty seconds.",
    60: "One minute. Keep moving.",
    90: "One minute thirty.",
    120: "Two minutes. Stay locked in.",
    180: "Three minutes. Drive forward.",
    300: "Five minutes. Finish strong.",
    600: "Ten minutes. Outstanding."
]

internal let voiceFilenamesByText: [String: String] = [
    "Thirty seconds.": "elapsed_30s",
    "One minute. Keep moving.": "elapsed_60s",
    "One minute thirty.": "elapsed_90s",
    "Two minutes. Stay locked in.": "elapsed_120s",
    "Three minutes. Drive forward.": "elapsed_180s",
    "Five minutes. Finish strong.": "elapsed_300s",
    "Ten minutes. Outstanding.": "elapsed_600s",
    previewElapsedCue: "preview_elapsed",
    previewCommandVoiceCue: "cmd_stay_sharp",
]

internal func voiceFilename(for text: String) -> String? {
    voiceFilenamesByText[text]
}

internal func voiceAudioURL(for filename: String, bundle: Bundle = .main) -> URL? {
    bundle.url(forResource: filename, withExtension: "mp3", subdirectory: "Sounds")
        ?? bundle.url(forResource: filename, withExtension: "mp3")
}

internal func voiceFilenameOrFallback(for text: String) -> String {
    voiceFilename(for: text) ?? voiceFilename(for: defaultFallbackVoiceCue) ?? "cmd_stay_sharp"
}

internal func runtimeVoiceCue(for elapsedSeconds: Int, lastElapsedMilestone: Int) -> String? {
    guard elapsedSeconds != lastElapsedMilestone else { return nil }
    return elapsedVoiceCuesBySecond[elapsedSeconds]
}

@MainActor
final class AIVoiceCalloutService {
    static let shared = AIVoiceCalloutService()

    private var audioPlayer: AVAudioPlayer?
    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "voice")
    private var lastElapsedMilestone = 0

    private init() {
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, options: [.duckOthers])
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            Self.log.error("Audio session setup failed: \(error.localizedDescription)")
        }
    }

    private(set) var volume: Float = 1.0

    func setVolume(_ newVolume: Float) {
        volume = newVolume
        audioPlayer?.volume = newVolume
    }

    private func speak(_ text: String) {
        let mappedFilename = voiceFilename(for: text)
        let filename = mappedFilename ?? voiceFilenameOrFallback(for: text)

        guard let url = voiceAudioURL(for: filename) else {
            Self.log.error("Voice asset missing for cue: \(text, privacy: .public) (filename: \(filename, privacy: .public))")
            return
        }
        if mappedFilename == nil {
            Self.log.info("Unmapped cue requested, using bundled fallback: \(text, privacy: .public)")
        }
        
        Self.log.info("Playing voice asset: \(filename, privacy: .public) for text: \(text, privacy: .public)")
        
        do {
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.volume = volume
            audioPlayer?.prepareToPlay()
            audioPlayer?.play()
        } catch {
            Self.log.error("Audio playback failed for \(filename): \(error.localizedDescription)")
        }
    }

    func resetSession() {
        lastElapsedMilestone = 0
    }

    func preview() {
        previewCommandCue()
    }

    func previewCommandCue() {
        speak(previewCommandVoiceCue)
    }

    func previewCountdownCue() {
        // With elapsed model, preview an elapsed milestone announcement
        speak(previewElapsedCue)
    }

    // Called every second with elapsed seconds since timer started.
    func triggerCallout(elapsedSeconds: Int) {
        if let callout = runtimeVoiceCue(for: elapsedSeconds, lastElapsedMilestone: lastElapsedMilestone) {
            speak(callout)
            lastElapsedMilestone = elapsedSeconds
        }
    }
}
