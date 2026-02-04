import Foundation
import UserNotifications
import AVFoundation
import UIKit

/// Service for managing notifications and alarm sounds
@MainActor
final class NotificationService: NSObject {

    private var audioPlayer: AVAudioPlayer?
    private let notificationCenter = UNUserNotificationCenter.current()

    override init() {
        super.init()
        setupAudioSession()
        requestNotificationPermission()
    }

    // MARK: - Permissions

    private func requestNotificationPermission() {
        Task {
            do {
                let granted = try await notificationCenter.requestAuthorization(
                    options: [.alert, .sound, .badge, .criticalAlert]
                )
                print("Notification permission granted: \(granted)")
            } catch {
                print("Failed to request notification permission: \(error)")
            }
        }
    }

    // MARK: - Notifications

    func scheduleAlarmNotification(at date: Date) async {
        let content = UNMutableNotificationContent()
        content.title = "Time's Up!"
        content.body = "Your random timer has finished"
        content.sound = .defaultCritical
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
        // Re-activate audio session before playing
        setupAudioSession()

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
                previewTimer?.invalidate()
                previewTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: false) { [weak self] _ in
                    self?.stopPreview()
                }
            } catch {
                print("Failed to play preview: \(error)")
            }
        } else {
            print("Preview sound file not found: \(resourceName).mp3")
        }
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

    private func soundResourceName(for type: SoundType) -> String {
        switch type {
        case .intense: return "alarm"
        case .gentle: return "gentle-chime"
        }
    }

    private func playSystemAlarmSound() {
        AudioServicesPlaySystemSound(kSystemSoundID_Vibrate)
    }

    func stopAlarmSound() {
        audioPlayer?.stop()
        audioPlayer = nil
    }

    // MARK: - Haptics

    private var vibrationTimer: Timer?

    func startVibration() {
        stopVibration()
        // Vibrate immediately
        triggerVibration()
        // Then vibrate every 1.5 seconds
        vibrationTimer = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: true) { [weak self] _ in
            self?.triggerVibration()
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
