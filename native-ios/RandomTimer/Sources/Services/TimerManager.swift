import Foundation
import Combine
import os
import ActivityKit
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

@MainActor
final class TimerManager: ObservableObject {
    @Published private(set) var state: TimerState?
    @Published var config: TimerConfig = .default

    private var timer: AnyCancellable?
    private var calloutTimer: AnyCancellable?
    private let notificationService: TimerNotificationHandling
    private let liveActivityService: TimerLiveActivityHandling
    private let storageService: TimerStorage
    private let analytics: AnalyticsHandling
    private let aiCalloutService = AIVoiceCalloutService.shared
    
    private static let log = Logger(subsystem: "com.iganapolsky.randomtimer", category: "timer")

    init(
        notificationService: TimerNotificationHandling = NotificationService(),
        liveActivityService: TimerLiveActivityHandling = LiveActivityService(),
        storageService: TimerStorage = StorageService(),
        analytics: AnalyticsHandling = AnalyticsService.shared
    ) {
        self.notificationService = notificationService
        self.liveActivityService = liveActivityService
        self.storageService = storageService
        self.analytics = analytics

        Task {
            await loadInitialData()
        }
    }

    private func loadInitialData() async {
        config = await storageService.getTimerConfig()
        if let savedState = await storageService.loadTimerState() {
            if savedState.status == .alarm || savedState.status == .complete {
                await storageService.clearTimerState()
            } else if savedState.status == .running || savedState.status == .paused {
                self.state = savedState
                if savedState.status == .running {
                    startInternalTimer()
                }
            }
        }
    }

    func updateConfig(_ newConfig: TimerConfig) {
        config = newConfig
        Task {
            await storageService.saveTimerConfig(newConfig)
        }
    }

    func startTimer() async {
        stopAlarm()
        notificationService.stopPreview()

        let duration = TimeInterval.random(in: config.minDuration...config.maxDuration)
        let newState = TimerState(config: config, targetDuration: duration)
        state = newState

        await storageService.saveTimerState(newState)
        await liveActivityService.start(state: newState)
        await notificationService.scheduleAlarmNotification(at: newState.endDate, soundType: config.soundType)

        analytics.event("timer_started", properties: [
            "min_duration": config.minSeconds,
            "max_duration": config.maxSeconds,
            "target_duration": Int(duration),
            "ai_callouts": config.eliteConfig.aiCalloutsEnabled
        ])

        startInternalTimer()
        
        if config.eliteConfig.aiCalloutsEnabled {
            startCalloutTimer()
        }
    }

    func cancelTimer() {
        stopInternalTimer()
        stopCalloutTimer()
        state = nil
        Task {
            await storageService.clearTimerState()
            liveActivityService.end()
            await notificationService.cancelPendingNotifications()
        }
        analytics.event("timer_stopped", properties: [ "source": "user" ])
    }

    func pauseTimer() {
        guard var currentState = state, currentState.status == .running else { return }
        stopInternalTimer()
        stopCalloutTimer()
        currentState.status = .paused
        state = currentState
        Task {
            await storageService.saveTimerState(currentState)
            await notificationService.cancelPendingNotifications()
            liveActivityService.update(state: currentState)
        }
        analytics.event("timer_paused", properties: [ "source": "user" ])
    }

    func resumeTimer() {
        guard var currentState = state, currentState.status == .paused else { return }
        currentState.status = .running
        state = currentState
        Task {
            await storageService.saveTimerState(currentState)
            await notificationService.scheduleAlarmNotification(at: currentState.endDate, soundType: config.soundType)
            liveActivityService.update(state: currentState)
        }
        startInternalTimer()
        if config.eliteConfig.aiCalloutsEnabled {
            startCalloutTimer()
        }
        analytics.event("timer_resumed", properties: [ "source": "user" ])
    }

    func resetTimer() {
        analytics.event("timer_reset", properties: [ "source": "user" ])
        Task { await startTimer() }
    }

    func stopAlarm() {
        notificationService.stopAlarmSound()
        notificationService.stopVibration()
        stopCalloutTimer()
        if state?.status == .alarm || state?.status == .complete {
            state = nil
            Task {
                await storageService.clearTimerState()
                liveActivityService.end()
            }
        }
    }

    func previewSound() {
        notificationService.playPreviewSound(
            type: config.soundType,
            volume: config.volume
        )
    }

    func previewSound(type: SoundType) {
        notificationService.playPreviewSound(
            type: type,
            volume: config.volume
        )
    }

    func updatePreviewVolume() {
        notificationService.updatePreviewVolume(config.volume)
    }

    func previewVolume() {
        notificationService.previewVolume(type: config.soundType, volume: config.volume)
    }

    private func startInternalTimer() {
        timer?.cancel()
        timer = Timer.publish(every: 0.1, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.tick()
            }
    }

    private func stopInternalTimer() {
        timer?.cancel()
        timer = nil
    }
    
    private func startCalloutTimer() {
        calloutTimer?.cancel()
        let interval = config.eliteConfig.calloutFrequency
        calloutTimer = Timer.publish(every: interval, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.triggerCallout()
            }
    }
    
    private func stopCalloutTimer() {
        calloutTimer?.cancel()
        calloutTimer = nil
        aiCalloutService.stop()
    }
    
    private func triggerCallout() {
        guard state?.status == .running else { return }
        if Double.random(in: 0...1) < config.eliteConfig.calloutIntensity {
            aiCalloutService.speakRandomCue()
        }
    }

    private func tick() {
        guard var currentState = state, currentState.status == .running else { return }
        
        let now = Date()
        let elapsed = now.timeIntervalSince(currentState.startedAt)
        currentState.remainingDuration = max(0, currentState.targetDuration - elapsed)
        
        if currentState.remainingDuration <= 0 {
            completeTimer()
        } else {
            state = currentState
            if Int(elapsed * 10) % 100 == 0 {
                liveActivityService.update(state: currentState)
            }
        }
    }

    private func completeTimer() {
        stopInternalTimer()
        stopCalloutTimer()
        guard var currentState = state else { return }
        currentState.status = .complete
        currentState.remainingDuration = 0
        state = currentState

        notificationService.playAlarmSound(type: config.soundType, volume: config.volume)
        if config.vibrationEnabled {
            notificationService.startVibration()
        }

        analytics.event("timer_completed", properties: [
            "target_duration": Int(currentState.targetDuration)
        ])

        Task {
            await storageService.saveTimerState(currentState)
            liveActivityService.update(state: currentState)
            notificationService.scheduleReengagementReminder()
        }
    }
}
