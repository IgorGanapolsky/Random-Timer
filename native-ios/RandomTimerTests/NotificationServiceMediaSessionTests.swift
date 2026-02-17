import XCTest
import MediaPlayer
@testable import RandomTimer

final class NotificationServiceMediaSessionTests: XCTestCase {

    func testActivateMediaSessionSetsNowPlayingInfoAndEnablesCommands() {
        let service = NotificationService()

        let originalNowPlaying = MPNowPlayingInfoCenter.default().nowPlayingInfo
        defer {
            service.deactivateMediaSession()
            MPNowPlayingInfoCenter.default().nowPlayingInfo = originalNowPlaying
        }

        service.activateMediaSession()

        let info = MPNowPlayingInfoCenter.default().nowPlayingInfo
        XCTAssertNotNil(info)
        XCTAssertEqual(info?[MPMediaItemPropertyTitle] as? String, "Random Tactical Timer - Alarm")

        let commandCenter = MPRemoteCommandCenter.shared()
        XCTAssertTrue(commandCenter.playCommand.isEnabled)
        XCTAssertTrue(commandCenter.pauseCommand.isEnabled)
        XCTAssertTrue(commandCenter.stopCommand.isEnabled)
    }

    func testDeactivateMediaSessionClearsNowPlayingInfoAndDisablesCommands() {
        let service = NotificationService()

        let originalNowPlaying = MPNowPlayingInfoCenter.default().nowPlayingInfo
        defer { MPNowPlayingInfoCenter.default().nowPlayingInfo = originalNowPlaying }

        service.activateMediaSession()
        service.deactivateMediaSession()

        XCTAssertNil(MPNowPlayingInfoCenter.default().nowPlayingInfo)

        let commandCenter = MPRemoteCommandCenter.shared()
        XCTAssertFalse(commandCenter.playCommand.isEnabled)
        XCTAssertFalse(commandCenter.pauseCommand.isEnabled)
        XCTAssertFalse(commandCenter.stopCommand.isEnabled)
    }

    func testHandleMediaButtonSilenceActionInvokesSilenceCallbackOnly() {
        let service = NotificationService()
        var didSilence = false
        var didStop = false

        service.onMediaButtonSilence = { didSilence = true }
        service.onNotificationStop = { didStop = true }

        service.handleMediaButtonSilenceAction()

        XCTAssertTrue(didSilence)
        XCTAssertFalse(didStop)
    }

    func testHandleNotificationStopActionSetsTapFlagAndInvokesStopCallback() {
        let service = NotificationService()
        var didStop = false

        service.onNotificationStop = { didStop = true }

        service.handleNotificationStopAction()

        XCTAssertTrue(service.didTapAlarmNotification)
        XCTAssertTrue(didStop)
    }

    func testHandleNotificationSilenceActionInvokesSilenceCallback() {
        let service = NotificationService()
        var didSilence = false

        service.onNotificationSilence = { didSilence = true }

        service.handleNotificationSilenceAction()

        XCTAssertTrue(didSilence)
    }
}
