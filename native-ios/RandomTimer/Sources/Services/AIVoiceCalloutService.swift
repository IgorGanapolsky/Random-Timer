import Foundation
import AVFoundation
import os
import Security

@MainActor
final class AIVoiceCalloutService {
    static let shared = AIVoiceCalloutService()

    private let synthesizer = AVSpeechSynthesizer()
    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "voice")
    private let tacticalPitch: Float = 0.72
    private let tacticalRate: Float = 0.38
    private let preferredVoiceNames = [
        "Aaron",
        "Nathan",
        "Daniel",
        "Siri Voice 4",
        "Siri Voice 3"
    ]
    private var lastCommandCueTime = 0
    private var nextCommandCueAt = 0
    private let countdownPreviewCues = [
        "Thirty seconds. Stay ready.",
        "Ten seconds. Stand by.",
        "Five. Four. Three. Two. One."
    ]
    private let commandCues = [
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
        "Stand by.",
        "Lock in.",
        "Finish strong.",
        "Breathe and move."
    ]

    private init() {}

    func speak(_ text: String) {
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = preferredVoice()
        utterance.rate = tacticalRate
        utterance.pitchMultiplier = tacticalPitch

        Self.log.info("Voice Callout: \(text)")
        synthesizer.speak(utterance)
    }

    private func preferredVoice() -> AVSpeechSynthesisVoice? {
        let voices = AVSpeechSynthesisVoice.speechVoices().filter { voice in
            voice.language.hasPrefix("en-US")
        }
        let preferredVoices = voices.filter { voice in
            preferredVoiceNames.contains(where: { preferred in
                voice.name.localizedCaseInsensitiveContains(preferred)
            })
        }
        if let namedVoice = preferredVoices.sorted(by: { $0.quality.rawValue > $1.quality.rawValue }).first {
            return namedVoice
        }
        return AVSpeechSynthesisVoice(language: "en-US")
    }

    func resetSession() {
        lastCommandCueTime = 0
        nextCommandCueAt = 0
    }

    func previewCountdownCue() {
        let index = secureRandomInt(in: 0...(countdownPreviewCues.count - 1))
        speak(countdownPreviewCues[index])
    }

    func previewCommandCue() {
        speak(randomCommandCue())
    }

    func preview() {
        let previewCues = [
            "Thirty seconds remaining. Hold your position.",
            "Ten seconds. Prepare for impact.",
            "Switch stance!",
            "Move! Move! Move!",
            "Stay sharp!",
            "Explode!",
            "Check your six!",
            "Eyes up!"
        ]
        let index = Int.random(in: 0..<previewCues.count)
        speak(previewCues[index])
    }

    func triggerCallout(remainingSeconds: Int) {
        // Fixed countdown callouts
        let countdownCallouts: [Int: String] = [
            30: "Thirty seconds. Stay ready.",
            10: "Ten seconds. Stand by.",
            5: "Five. Four. Three. Two. One."
        ]

        if let callout = countdownCallouts[remainingSeconds] {
            speak(callout)
            return
        }

        // Randomized command cues break predictability during longer timers.
        if remainingSeconds > 30, shouldFireCommandCue(remainingSeconds: remainingSeconds) {
            speak(randomCommandCue())
            lastCommandCueTime = remainingSeconds
            nextCommandCueAt = remainingSeconds - secureRandomInt(in: 8...19)
        }
    }

    private func shouldFireCommandCue(remainingSeconds: Int) -> Bool {
        if nextCommandCueAt == 0 {
            // First cue: fire within first 5-15 seconds of timer running
            nextCommandCueAt = remainingSeconds - secureRandomInt(in: 5...15)
        }
        return remainingSeconds <= nextCommandCueAt
    }

    private func randomCommandCue() -> String {
        let index = secureRandomInt(in: 0...(commandCues.count - 1))
        return commandCues[index]
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
