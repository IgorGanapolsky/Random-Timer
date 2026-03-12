import Foundation
import AVFoundation
import os
import Security

internal let previewElapsedCue = "Thirty seconds. Stay locked in."
internal let defaultFallbackVoiceCue = "Stay sharp."

internal let elapsedVoiceCuesBySecond: [Int: String] = [
    30: "Thirty seconds.",
    60: "One minute. Keep moving.",
    90: "One minute thirty.",
    120: "Two minutes. Stay locked in.",
    180: "Three minutes. Drive forward.",
    300: "Five minutes. Finish strong.",
    600: "Ten minutes. Outstanding."
]

internal let commandVoiceCues = [
    "Stay sharp.",
    "Reset. Breathe."
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
    "Move now.": "cmd_move_now",
    "Stay sharp.": "cmd_stay_sharp",
    "Reset. Breathe.": "cmd_reset_breathe",
    "Push the pace.": "cmd_push_pace",
    "Drive forward.": "cmd_drive_forward",
    "Keep pressure.": "cmd_keep_pressure",
    "Push through it.": "cmd_push_through",
]

internal func voiceFilename(for text: String) -> String? {
    voiceFilenamesByText[text]
}

internal func voiceAudioURL(for filename: String, bundle: Bundle = .main) -> URL? {
    bundle.url(forResource: filename, withExtension: "mp3", subdirectory: "Audio")
        ?? bundle.url(forResource: filename, withExtension: "mp3")
}

internal func voiceFilenameOrFallback(for text: String) -> String {
    voiceFilename(for: text) ?? voiceFilename(for: defaultFallbackVoiceCue) ?? "cmd_stay_sharp"
}

@MainActor
final class AIVoiceCalloutService {
    static let shared = AIVoiceCalloutService()

    private var audioPlayer: AVAudioPlayer?
    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "voice")
    private var lastElapsedMilestone = 0
    private var nextCommandCueAt = 0
    private var lastCommandCueAt = 0

    private init() {
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, options: [.duckOthers])
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            Self.log.error("Audio session setup failed: \(error.localizedDescription)")
        }
    }

    private func speak(_ text: String) {
        let mappedFilename = voiceFilename(for: text)
        let filename = mappedFilename ?? voiceFilenameOrFallback(for: text)

        guard let url = voiceAudioURL(for: filename) else {
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
        lastElapsedMilestone = 0
        nextCommandCueAt = 0
        lastCommandCueAt = 0
    }

    func preview() {
        previewCommandCue()
    }

    func previewCommandCue() {
        speak(randomCommandCue())
    }

    func previewCountdownCue() {
        // With elapsed model, preview an elapsed milestone announcement
        speak(previewElapsedCue)
    }

    // Called every second with elapsed seconds since timer started.
    func triggerCallout(elapsedSeconds: Int) {
        // Elapsed milestone callouts — fire once per milestone
        if let callout = elapsedMilestone(for: elapsedSeconds) {
            speak(callout)
            lastElapsedMilestone = elapsedSeconds
            return
        }

        // Random command cues fire throughout the session
        if shouldFireCommandCue(elapsedSeconds: elapsedSeconds) {
            speak(randomCommandCue())
            lastCommandCueAt = elapsedSeconds
            nextCommandCueAt = elapsedSeconds + secureRandomInt(in: 12...25)
        }
    }

    private func elapsedMilestone(for elapsed: Int) -> String? {
        // Fire each milestone exactly once
        guard let text = elapsedVoiceCuesBySecond[elapsed], elapsed != lastElapsedMilestone else { return nil }
        return text
    }

    private func shouldFireCommandCue(elapsedSeconds: Int) -> Bool {
        if nextCommandCueAt == 0 {
            // First cue fires between 8–20s in
            nextCommandCueAt = secureRandomInt(in: 8...20)
        }
        return elapsedSeconds >= nextCommandCueAt
    }

    private func randomCommandCue() -> String {
        let index = secureRandomInt(in: 0...(commandVoiceCues.count - 1))
        return commandVoiceCues[index]
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
}
