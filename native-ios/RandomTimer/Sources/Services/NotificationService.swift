import Foundation
import UserNotifications
import AVFoundation
import CoreHaptics
import MediaPlayer
import UIKit
import os

/// Service for managing notifications and alarm sounds
@MainActor
final class NotificationService: NSObject, TimerNotificationHandling {

    private var audioPlayer: AVAudioPlayer?
    private let notificationCenter = UNUserNotificationCenter.current()
    /// Set to true when user taps the alarm notification
    private(set) var didTapAlarmNotification = false

    /// Callback invoked when Bluetooth/CarPlay media button is pressed during alarm.
    /// Must mirror tapping the timer circle: silence alarm and keep user on timer screen.
    var onMediaButtonSilence: (() -> Void)?

    /// Callback invoked when user taps "Stop" action on the notification.
    var onNotificationStop: (() -> Void)?

    /// Callback invoked when user taps "Silence" action on the notification
    var onNotificationSilence: (() -> Void)?

    // MARK: - Core Haptics

    private var hapticEngine: CHHapticEngine?
    private var hapticPlayer: CHHapticPatternPlayer?
    private var vibrationTimer: Timer?

    override init() {
        super.init()
        notificationCenter.delegate = self
        registerNotificationActions()
        prepareHapticEngine()
        // Notification permission deferred to first timer start (not on launch)
    }

    // MARK: - Permissions

    func requestNotificationPermission() async {
        // Avoid blocking unit tests on system permission dialogs
        if ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil {
            return
        }
        do {
            let granted = try await notificationCenter.requestAuthorization(
                options: [.alert, .sound]
            )
            Logger.notification.debug("Notification permission granted: \(granted)")
        } catch {
            Logger.notification.error("Failed to request notification permission: \(error)")
        }
    }

    // MARK: - Notification Actions

    private func registerNotificationActions() {
        let stopAction = UNNotificationAction(
            identifier: "STOP_ACTION",
            title: "Stop",
            options: [.destructive, .foreground]
        )

        let silenceAction = UNNotificationAction(
            identifier: "SILENCE_ACTION",
            title: "Silence",
            options: []
        )

        let alarmCategory = UNNotificationCategory(
            identifier: "TIMER_ALARM",
            actions: [silenceAction, stopAction],
            intentIdentifiers: [],
            options: [.customDismissAction]
        )

        notificationCenter.setNotificationCategories([alarmCategory])
    }

    // MARK: - Notifications

    func scheduleAlarmNotification(at date: Date, soundType: SoundType = .intense) async {
        await requestNotificationPermission()

        let content = UNMutableNotificationContent()
        content.title = "Time's Up!"
        content.body = "Your random timer has finished"
        content.sound = UNNotificationSound(named: UNNotificationSoundName(soundType.notificationSoundName))
        content.interruptionLevel = .timeSensitive
        content.categoryIdentifier = "TIMER_ALARM"

        let trigger = UNTimeIntervalNotificationTrigger(
            timeInterval: max(1, date.timeIntervalSinceNow),
            repeats: false
        )

        let request = UNNotificationRequest(
            identifier: "timer_alarm",
            content: content,
            trigger: trigger
        )

        do {
            try await notificationCenter.add(request)
        } catch {
            Logger.notification.error("Failed to schedule notification: \(error)")
        }
    }

    func cancelPendingNotifications() async {
        notificationCenter.removeAllPendingNotificationRequests()
        notificationCenter.removeAllDeliveredNotifications()
    }

    // MARK: - Audio

    private func activateAudioSession(forAlarm: Bool) {
        do {
            try AVAudioSession.sharedInstance().setCategory(
                .playback,
                mode: .default,
                options: forAlarm ? [.duckOthers] : [.mixWithOthers]
            )
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            Logger.notification.error("Failed to activate audio session: \(error)")
        }
    }

    private func deactivateAudioSession() {
        do {
            try AVAudioSession.sharedInstance().setActive(
                false,
                options: .notifyOthersOnDeactivation
            )
        } catch {
            Logger.notification.error("Failed to deactivate audio session: \(error)")
        }
    }

    func playAlarmSound(type: SoundType = .intense, volume: Float = 1.0) {
        // Activate audio session with ducking for alarm
        activateAudioSession(forAlarm: true)

        // Activate media session for Bluetooth/CarPlay dismiss
        activateMediaSession()

        // Observe audio interruptions (phone calls, etc.)
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleAudioInterruption(_:)),
            name: AVAudioSession.interruptionNotification,
            object: AVAudioSession.sharedInstance()
        )

        let resourceName = soundResourceName(for: type)

        if let url = Bundle.main.url(forResource: resourceName, withExtension: "mp3") {
            do {
                audioPlayer = try AVAudioPlayer(contentsOf: url)
                audioPlayer?.numberOfLoops = -1 // Loop indefinitely
                audioPlayer?.volume = volume
                audioPlayer?.prepareToPlay()
                audioPlayer?.play()
                Logger.notification.info("Playing alarm sound: \(resourceName) at volume \(volume)")
            } catch {
                Logger.notification.error("Failed to create audio player: \(error)")
            }
        } else {
            Logger.notification.error("Sound file not found in bundle: \(resourceName).mp3")
        }
    }

    @objc private func handleAudioInterruption(_ notification: Notification) {
        guard let userInfo = notification.userInfo,
              let typeValue = userInfo[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: typeValue) else { return }

        switch type {
        case .began:
            // Phone call or Siri — audio paused automatically by system
            Logger.notification.debug("Audio interruption began")
        case .ended:
            // Interruption ended — resume if we should
            if let optionsValue = userInfo[AVAudioSessionInterruptionOptionKey] as? UInt {
                let options = AVAudioSession.InterruptionOptions(rawValue: optionsValue)
                if options.contains(.shouldResume) {
                    audioPlayer?.play()
                    Logger.notification.debug("Audio interruption ended, resuming playback")
                }
            }
        @unknown default:
            break
        }
    }

    private var previewTimer: Timer?
    private var currentlyPreviewingSound: SoundType?
    private let previewVolumeStopDelay: TimeInterval = 1.5

    func playPreviewSound(type: SoundType, volume: Float) {
        // If same sound is already playing, stop it (toggle behavior)
        if currentlyPreviewingSound == type && audioPlayer?.isPlaying == true {
            stopPreview()
            return
        }

        stopPreview()
        activateAudioSession(forAlarm: false)

        let resourceName = soundResourceName(for: type)

        if let url = Bundle.main.url(forResource: resourceName, withExtension: "mp3") {
            do {
                audioPlayer = try AVAudioPlayer(contentsOf: url)
                audioPlayer?.numberOfLoops = -1 // Loop while playing
                audioPlayer?.volume = volume
                audioPlayer?.prepareToPlay()
                audioPlayer?.play()
                currentlyPreviewingSound = type
                Logger.notification.debug("Playing preview sound: \(resourceName) at volume \(volume)")

                // Stop after 5 seconds
                schedulePreviewStop(after: 5.0)
            } catch {
                Logger.notification.error("Failed to play preview: \(error)")
            }
        } else {
            Logger.notification.error("Preview sound file not found: \(resourceName).mp3")
        }
    }

    func previewVolume(type: SoundType, volume: Float) {
        if currentlyPreviewingSound == type && audioPlayer?.isPlaying == true {
            audioPlayer?.volume = volume
            schedulePreviewStop(after: previewVolumeStopDelay)
            return
        }

        playPreviewSound(type: type, volume: volume)
        schedulePreviewStop(after: previewVolumeStopDelay)
    }

    func stopPreview() {
        previewTimer?.invalidate()
        previewTimer = nil
        audioPlayer?.stop()
        audioPlayer = nil
        currentlyPreviewingSound = nil
        deactivateAudioSession()
    }

    func updatePreviewVolume(_ volume: Float) {
        audioPlayer?.volume = volume
    }

    private func schedulePreviewStop(after delay: TimeInterval) {
        previewTimer?.invalidate()
        previewTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            Task { @MainActor in
                self?.stopPreview()
            }
        }
    }

    private func soundResourceName(for type: SoundType) -> String {
        switch type {
        case .intense: return "alarm"
        case .gentle: return "gentle-chime"
        }
    }

    // MARK: - Media Session (Bluetooth / CarPlay alarm controls)

    func handleMediaButtonSilenceAction() {
        onMediaButtonSilence?()
    }

    func handleNotificationStopAction() {
        didTapAlarmNotification = true
        onNotificationStop?()
    }

    func handleNotificationSilenceAction() {
        onNotificationSilence?()
    }

    func activateMediaSession() {
        let commandCenter = MPRemoteCommandCenter.shared()

        // Headset pause/play/stop should all behave like tapping the timer circle:
        // silence alarm and keep the user on the timer screen.
        commandCenter.pauseCommand.isEnabled = true
        commandCenter.pauseCommand.addTarget { [weak self] _ in
            self?.handleMediaButtonSilenceAction()
            return .success
        }

        // Some headsets map their single button to stop.
        commandCenter.stopCommand.isEnabled = true
        commandCenter.stopCommand.addTarget { [weak self] _ in
            self?.handleMediaButtonSilenceAction()
            return .success
        }

        // Some headsets map their single button to play/pause.
        commandCenter.playCommand.isEnabled = true
        commandCenter.playCommand.addTarget { [weak self] _ in
            self?.handleMediaButtonSilenceAction()
            return .success
        }

        // Set now playing info so the lock screen / Bluetooth shows our app
        MPNowPlayingInfoCenter.default().nowPlayingInfo = [
            MPMediaItemPropertyTitle: "Random Tactical Timer - Alarm",
            MPMediaItemPropertyArtist: "Random Tactical Timer"
        ]
    }

    func deactivateMediaSession() {
        let commandCenter = MPRemoteCommandCenter.shared()
        commandCenter.pauseCommand.removeTarget(nil)
        commandCenter.stopCommand.removeTarget(nil)
        commandCenter.playCommand.removeTarget(nil)
        commandCenter.pauseCommand.isEnabled = false
        commandCenter.stopCommand.isEnabled = false
        commandCenter.playCommand.isEnabled = false

        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }

    func stopAlarmSound() {
        NotificationCenter.default.removeObserver(
            self,
            name: AVAudioSession.interruptionNotification,
            object: AVAudioSession.sharedInstance()
        )
        deactivateMediaSession()
        audioPlayer?.stop()
        audioPlayer = nil
        deactivateAudioSession()
    }

    /// Stops sound and vibration but keeps alarm state active (alarm UI stays visible)
    func silenceAlarm() {
        stopAlarmSound()
        stopVibration()
    }

    func clearNotificationTapFlag() {
        didTapAlarmNotification = false
    }

    /// Test-only hook for simulating notification tap.
    func setDidTapAlarmNotificationForTesting(_ value: Bool) {
        didTapAlarmNotification = value
    }

    // MARK: - Haptics (Core Haptics)

    private func prepareHapticEngine() {
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics else { return }

        do {
            hapticEngine = try CHHapticEngine()
            hapticEngine?.resetHandler = { [weak self] in
                Task { @MainActor in
                    try? self?.hapticEngine?.start()
                }
            }
            try hapticEngine?.start()
        } catch {
            Logger.notification.error("Failed to start haptic engine: \(error)")
        }
    }

    func startVibration() {
        stopVibration()
        // Fire immediately
        triggerHapticBurst()
        // Repeat every 1.5 seconds
        vibrationTimer = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.triggerHapticBurst()
            }
        }
    }

    func stopVibration() {
        vibrationTimer?.invalidate()
        vibrationTimer = nil
        try? hapticPlayer?.stop(atTime: CHHapticTimeImmediate)
        hapticPlayer = nil
    }

    /// Plays a strong double-tap haptic pattern using Core Haptics
    private func triggerHapticBurst() {
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics,
              let engine = hapticEngine else {
            // Fallback for devices without haptic engine
            let generator = UINotificationFeedbackGenerator()
            generator.notificationOccurred(.error)
            return
        }

        do {
            // Double-tap pattern: strong hit, brief pause, strong hit
            let events: [CHHapticEvent] = [
                CHHapticEvent(
                    eventType: .hapticTransient,
                    parameters: [
                        CHHapticEventParameter(parameterID: .hapticIntensity, value: 1.0),
                        CHHapticEventParameter(parameterID: .hapticSharpness, value: 0.8)
                    ],
                    relativeTime: 0
                ),
                CHHapticEvent(
                    eventType: .hapticTransient,
                    parameters: [
                        CHHapticEventParameter(parameterID: .hapticIntensity, value: 1.0),
                        CHHapticEventParameter(parameterID: .hapticSharpness, value: 0.8)
                    ],
                    relativeTime: 0.15
                )
            ]

            let pattern = try CHHapticPattern(events: events, parameters: [])
            hapticPlayer = try engine.makePlayer(with: pattern)
            try hapticPlayer?.start(atTime: CHHapticTimeImmediate)
        } catch {
            Logger.notification.error("Failed to play haptic: \(error)")
            // Fallback
            let generator = UINotificationFeedbackGenerator()
            generator.notificationOccurred(.error)
        }
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension NotificationService: @preconcurrency UNUserNotificationCenterDelegate {
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        // App is foregrounded — suppress the notification banner since the
        // alarm UI is already visible. Alarm sound is handled by AVAudioPlayer.
        return []
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        guard response.notification.request.identifier == "timer_alarm" else { return }

        switch response.actionIdentifier {
        case "STOP_ACTION":
            // User tapped "Stop" — dismiss alarm and return to the app
            handleNotificationStopAction()
        case "SILENCE_ACTION":
            // User tapped "Silence" — stop sound but keep alarm UI
            handleNotificationSilenceAction()
        case UNNotificationDefaultActionIdentifier:
            // User tapped the notification body
            didTapAlarmNotification = true
        default:
            break
        }
    }
}
