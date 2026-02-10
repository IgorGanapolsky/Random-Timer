import Foundation
import UserNotifications
import AVFoundation
import MediaPlayer
import UIKit

/// Service for managing notifications and alarm sounds
@MainActor
final class NotificationService: NSObject, TimerNotificationHandling {

    private var audioPlayer: AVAudioPlayer?
    private let notificationCenter = UNUserNotificationCenter.current()
    /// Set to true when user taps the alarm notification
    private(set) var didTapAlarmNotification = false

    /// Callback invoked when Bluetooth/CarPlay media button is pressed during alarm
    var onMediaButtonDismiss: (() -> Void)?

    override init() {
        super.init()
        setupAudioSession()
        notificationCenter.delegate = self
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
                options: [.alert, .sound, .badge]
            )
            print("Notification permission granted: \(granted)")
        } catch {
            print("Failed to request notification permission: \(error)")
        }
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
            print("Failed to schedule notification: \(error)")
        }
    }

    func cancelPendingNotifications() async {
        notificationCenter.removeAllPendingNotificationRequests()
        notificationCenter.removeAllDeliveredNotifications()
    }

    // MARK: - Audio

    private func setupAudioSession() {
        do {
            try AVAudioSession.sharedInstance().setCategory(
                .playback,
                mode: .default,
                options: [.mixWithOthers]
            )
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            print("Failed to setup audio session: \(error)")
        }
    }

    func playAlarmSound(type: SoundType = .intense, volume: Float = 1.0) {
        // Activate media session for Bluetooth/CarPlay dismiss, then play
        activateMediaSession()

        let resourceName = soundResourceName(for: type)

        if let url = Bundle.main.url(forResource: resourceName, withExtension: "mp3") {
            do {
                audioPlayer = try AVAudioPlayer(contentsOf: url)
                audioPlayer?.numberOfLoops = -1 // Loop indefinitely
                audioPlayer?.volume = volume
                audioPlayer?.prepareToPlay()
                audioPlayer?.play()
                print("Playing alarm sound: \(resourceName) at volume \(volume)")
            } catch {
                print("Failed to create audio player: \(error)")
                playSystemAlarmSound()
            }
        } else {
            print("Sound file not found in bundle: \(resourceName).mp3")
            playSystemAlarmSound()
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
        setupAudioSession()

        let resourceName = soundResourceName(for: type)

        if let url = Bundle.main.url(forResource: resourceName, withExtension: "mp3") {
            do {
                audioPlayer = try AVAudioPlayer(contentsOf: url)
                audioPlayer?.numberOfLoops = -1 // Loop while playing
                audioPlayer?.volume = volume
                audioPlayer?.prepareToPlay()
                audioPlayer?.play()
                currentlyPreviewingSound = type
                print("Playing preview sound: \(resourceName) at volume \(volume)")

                // Stop after 5 seconds
                schedulePreviewStop(after: 5.0)
            } catch {
                print("Failed to play preview: \(error)")
            }
        } else {
            print("Preview sound file not found: \(resourceName).mp3")
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

    private func playSystemAlarmSound() {
        AudioServicesPlaySystemSound(kSystemSoundID_Vibrate)
    }

    // MARK: - Media Session (Bluetooth / CarPlay alarm dismiss)

    func activateMediaSession() {
        // Take audio focus (remove .mixWithOthers so Bluetooth routes to us)
        do {
            try AVAudioSession.sharedInstance().setCategory(
                .playback,
                mode: .default,
                options: []
            )
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            print("Failed to activate media session: \(error)")
        }

        let commandCenter = MPRemoteCommandCenter.shared()

        commandCenter.pauseCommand.isEnabled = true
        commandCenter.pauseCommand.addTarget { [weak self] _ in
            self?.onMediaButtonDismiss?()
            return .success
        }

        commandCenter.stopCommand.isEnabled = true
        commandCenter.stopCommand.addTarget { [weak self] _ in
            self?.onMediaButtonDismiss?()
            return .success
        }

        commandCenter.playCommand.isEnabled = true
        commandCenter.playCommand.addTarget { [weak self] _ in
            self?.onMediaButtonDismiss?()
            return .success
        }

        // Set now playing info so the lock screen / Bluetooth shows our app
        MPNowPlayingInfoCenter.default().nowPlayingInfo = [
            MPMediaItemPropertyTitle: "Random Timer - Alarm",
            MPMediaItemPropertyArtist: "Random Timer"
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

        // Restore mixWithOthers for normal operation
        do {
            try AVAudioSession.sharedInstance().setCategory(
                .playback,
                mode: .default,
                options: [.mixWithOthers]
            )
        } catch {
            print("Failed to deactivate media session: \(error)")
        }
    }

    func stopAlarmSound() {
        deactivateMediaSession()
        audioPlayer?.stop()
        audioPlayer = nil
    }

    func clearNotificationTapFlag() {
        didTapAlarmNotification = false
    }

    // MARK: - Haptics

    private var vibrationTimer: Timer?

    func startVibration() {
        stopVibration()
        // Vibrate immediately
        triggerVibration()
        // Then vibrate every 1.5 seconds
        vibrationTimer = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.triggerVibration()
            }
        }
    }

    func stopVibration() {
        vibrationTimer?.invalidate()
        vibrationTimer = nil
    }

    private func triggerVibration() {
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.warning)
        AudioServicesPlaySystemSound(kSystemSoundID_Vibrate)
    }

    // Legacy method for single vibration
    func vibrate() {
        triggerVibration()
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
        // User tapped the alarm notification — flag it so handleForeground
        // skips replaying the alarm sound (notification already played it)
        if response.notification.request.identifier == "timer_alarm" {
            didTapAlarmNotification = true
        }
    }
}
