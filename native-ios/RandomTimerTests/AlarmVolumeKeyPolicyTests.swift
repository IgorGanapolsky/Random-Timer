import XCTest
@testable import RandomTimer

final class AlarmVolumeKeyPolicyTests: XCTestCase {

    func testVolumeChangeDuringAlarmShouldSilence() {
        XCTAssertTrue(
            AlarmVolumeKeyPolicy.shouldSilenceOnVolumeChange(
                status: .alarm,
                isAlarmSilenced: false,
                previousVolume: 0.5,
                newVolume: 0.6
            )
        )
    }

    func testVolumeChangeWhenAlarmAlreadySilencedIsIgnored() {
        XCTAssertFalse(
            AlarmVolumeKeyPolicy.shouldSilenceOnVolumeChange(
                status: .alarm,
                isAlarmSilenced: true,
                previousVolume: 0.5,
                newVolume: 0.6
            )
        )
    }

    func testVolumeChangeWhileRunningIsIgnored() {
        XCTAssertFalse(
            AlarmVolumeKeyPolicy.shouldSilenceOnVolumeChange(
                status: .running,
                isAlarmSilenced: false,
                previousVolume: 0.5,
                newVolume: 0.6
            )
        )
    }

    func testUnchangedVolumeIsIgnored() {
        XCTAssertFalse(
            AlarmVolumeKeyPolicy.shouldSilenceOnVolumeChange(
                status: .alarm,
                isAlarmSilenced: false,
                previousVolume: 0.5,
                newVolume: 0.5
            )
        )
    }
}
