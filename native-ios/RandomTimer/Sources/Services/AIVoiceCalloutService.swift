import Foundation
import AVFoundation
import os
import Security

@MainActor
final class AIVoiceCalloutService {
    static let shared = AIVoiceCalloutService()

    private let synthesizer = AVSpeechSynthesizer()
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
        let filename = textToFilename(text)
        guard !filename.isEmpty,
              let url = Bundle.main.url(forResource: filename, withExtension: "mp3") else {
            // Fallback to system TTS
            let utterance = AVSpeechUtterance(string: text)
            utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
            utterance.rate = 0.52
            utterance.pitchMultiplier = 0.85
            synthesizer.speak(utterance)
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

    private func textToFilename(_ text: String) -> String {
        elapsedFilename(text) ?? commandFilename(text) ?? ""
    }

    private func elapsedFilename(_ text: String) -> String? {
        switch text {
        case "Thirty seconds.":                  return "elapsed_30s"
        case "One minute. Keep moving.":         return "elapsed_60s"
        case "One minute thirty.":               return "elapsed_90s"
        case "Two minutes. Stay locked in.":     return "elapsed_120s"
        case "Three minutes. Drive forward.":    return "elapsed_180s"
        case "Five minutes. Finish strong.":     return "elapsed_300s"
        case "Ten minutes. Outstanding.":        return "elapsed_600s"
        case "Thirty seconds. Stay locked in.":  return "preview_elapsed"
        default:                                 return nil
        }
    }

    private func commandFilename(_ text: String) -> String? {
        switch text {
        case "Move now.":        return "cmd_move_now"
        case "Stay sharp.":      return "cmd_stay_sharp"
        case "Reset. Breathe.":  return "cmd_reset_breathe"
        case "Push the pace.":   return "cmd_push_pace"
        case "Drive forward.":   return "cmd_drive_forward"
        case "Keep pressure.":   return "cmd_keep_pressure"
        case "Push through it.": return "cmd_push_through"
        default:                 return nil
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
        speak("Thirty seconds. Stay locked in.")
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
        let milestones: [Int: String] = [
            30: "Thirty seconds.",
            60: "One minute. Keep moving.",
            90: "One minute thirty.",
            120: "Two minutes. Stay locked in.",
            180: "Three minutes. Drive forward.",
            240: "Four minutes. Hold the line.",
            300: "Five minutes. Finish strong.",
            360: "Six minutes.",
            420: "Seven minutes.",
            480: "Eight minutes.",
            540: "Nine minutes.",
            600: "Ten minutes. Outstanding."
        ]
        guard let text = milestones[elapsed], elapsed != lastElapsedMilestone else { return nil }
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
        let cues = [
            "Move now.",
            "Stay sharp.",
            "Eyes front.",
            "Hands up.",
            "Reset. Breathe.",
            "Push the pace.",
            "Explode.",
            "Recover. Then go.",
            "Hold the line.",
            "Drive forward.",
            "Keep pressure.",
            "Lock in.",
            "Finish strong.",
            "Breathe and move.",
            "Switch stance.",
            "Double up.",
            "Check your six.",
            "Dig deeper.",
            "Tighten up.",
            "Push through it."
        ]
        let index = secureRandomInt(in: 0...(cues.count - 1))
        return cues[index]
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
