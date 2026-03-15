import Foundation
import AVFoundation
import os

internal let previewElapsedCue = "Thirty seconds. Stay locked in."
internal let previewCommandVoiceCue = "Stay sharp."
internal let defaultFallbackVoiceCue = previewCommandVoiceCue

internal let runtimeCommandCuesByElapsedSecond: [Int: String] = [
    30: previewCommandVoiceCue,
    60: "Move now.",
    90: "Keep pressure.",
    120: "Drive forward.",
    180: "Push the pace.",
    300: "Push through.",
    600: "Reset and breathe."
]

internal let voiceFilenamesByText: [String: String] = [
    previewCommandVoiceCue: "cmd_stay_sharp",
    "Move now.": "cmd_move_now",
    "Keep pressure.": "cmd_keep_pressure",
    "Drive forward.": "cmd_drive_forward",
    "Push the pace.": "cmd_push_pace",
    "Push through.": "cmd_push_through",
    "Reset and breathe.": "cmd_reset_breathe",
    previewElapsedCue: "preview_elapsed",
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
    return runtimeCommandCuesByElapsedSecond[elapsedSeconds]
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
            Self.log.error(
                "Voice asset missing for cue: \(text, privacy: .public) (filename: \(filename, privacy: .public))"
            )
            return
        }
        if mappedFilename == nil {
            Self.log.info("Unmapped cue requested, using bundled fallback: \(text, privacy: .public)")
        }

        Self.log.info(
            "Playing voice asset: \(filename, privacy: .public) for text: \(text, privacy: .public)"
        )

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

    func previewElapsedMilestoneCue() {
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
