import Foundation
import AVFoundation
import os
import Security

@MainActor
final class AIVoiceCalloutService {
    static let shared = AIVoiceCalloutService()

    private let synthesizer = AVSpeechSynthesizer()
    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "voice")
    private var lastChaosCueTime = 0
    private var nextChaosCueAt = 0

    private init() {}

    func speak(_ text: String) {
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = 0.5

        Self.log.info("Voice Callout: \(text)")
        synthesizer.speak(utterance)
    }

    func resetSession() {
        lastChaosCueTime = 0
        nextChaosCueAt = 0
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
        let cues = [
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
