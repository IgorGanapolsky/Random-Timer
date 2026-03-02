import Foundation
import AVFoundation

/// Handles AI-driven voice callouts for the "Elite Tactical" tier.
final class AIVoiceCalloutService: NSObject, AVSpeechSynthesizerDelegate {
    static let shared = AIVoiceCalloutService()
    
    private let synthesizer = AVSpeechSynthesizer()
    private let combatCues = ["Jab", "Cross", "Hook", "Sprawl", "Move", "Double up", "Circle left", "Circle right"]
    private let shootingCues = ["Reload", "Transition", "Move", "Low port", "Scan", "Safety on"]
    
    private override init() {
        super.init()
        synthesizer.delegate = self
    }
    
    func speakRandomCue(focus: TrainingFocus = .combat) {
        let cues = focus == .combat ? combatCues : shootingCues
        guard let cue = cues.randomElement() else { return }
        
        let utterance = AVSpeechUtterance(string: cue)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = 0.55
        utterance.pitchMultiplier = 1.0
        utterance.volume = 1.0
        
        synthesizer.speak(utterance)
    }
    
    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
    }
}

enum TrainingFocus {
    case combat, shooting
}
