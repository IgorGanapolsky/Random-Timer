import Foundation
import AVFoundation
import os
import Security

@MainActor
final class AIVoiceCalloutService {
    static let shared = AIVoiceCalloutService()

    private let synthesizer = AVSpeechSynthesizer()
    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "voice")
    private let tacticalPitch: Float = 0.8
    private let tacticalRate: Float = 0.42
    private let preferredVoiceNames = [
        "Siri Voice 4",
        "Daniel",
        "Aaron",
        "Nathan"
    ]
    private var lastChaosCueTime = 0
    private var nextChaosCueAt = 0
    private let countdownPreviewCues = [
        "Thirty seconds remaining. Hold your position.",
        "Ten seconds. Prepare for impact.",
        "Five. Four. Three. Two. One."
    ]
    private let drillCommands = [
        "Switch stance!",
        "Move! Move! Move!",
        "Breathe. Reset.",
        "Double up!",
        "Change levels!",
        "Check your six!",
        "Pick up the pace!",
        "Stay sharp!",
        "Dig deeper!",
        "Eyes up!",
        "Recover now!",
        "Explode!",
        "Control the center!",
        "Tighten up!",
        "Push through it!"
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
        let voices = AVSpeechSynthesisVoice.speechVoices()
        if let namedVoice = voices.first(where: { voice in
            preferredVoiceNames.contains(where: { preferred in
                voice.name.localizedCaseInsensitiveContains(preferred)
            })
        }) {
            return namedVoice
        }
        return AVSpeechSynthesisVoice(language: "en-US")
    }

    func resetSession() {
        lastChaosCueTime = 0
        nextChaosCueAt = 0
    }

    func previewCountdownCue() {
        let index = secureRandomInt(in: 0...(countdownPreviewCues.count - 1))
        speak(countdownPreviewCues[index])
    }

    func previewDrillCommand() {
        speak(randomChaosCue())
    }

    func triggerCallout(remainingSeconds: Int) {
        // Fixed countdown callouts
        let countdownCallouts: [Int: String] = [
            30: "Thirty seconds remaining. Hold your position.",
            10: "Ten seconds. Prepare for impact.",
            5: "Five. Four. Three. Two. One."
        ]

        if let callout = countdownCallouts[remainingSeconds] {
            speak(callout)
            return
        }

        // Chaos Drill: randomized tactical cues at unpredictable intervals
        if remainingSeconds > 30, shouldFireChaosCue(remainingSeconds: remainingSeconds) {
            speak(randomChaosCue())
            lastChaosCueTime = remainingSeconds
            nextChaosCueAt = remainingSeconds - secureRandomInt(in: 8...19)
        }
    }

    private func shouldFireChaosCue(remainingSeconds: Int) -> Bool {
        if nextChaosCueAt == 0 {
            // First cue: fire within first 5-15 seconds of timer running
            nextChaosCueAt = remainingSeconds - secureRandomInt(in: 5...15)
        }
        return remainingSeconds <= nextChaosCueAt
    }

    private func randomChaosCue() -> String {
        let index = secureRandomInt(in: 0...(drillCommands.count - 1))
        return drillCommands[index]
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
