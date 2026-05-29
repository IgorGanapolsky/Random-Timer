import XCTest
@testable import RandomTimer

final class ProSoundAccessTests: XCTestCase {
    func testProUsersCanEquipProSounds() {
        XCTAssertTrue(ProSoundAccess.canEquipProSound(isPro: true, hasTrialUnlock: false))
    }

    func testTrialUnlockAllowsEquipWithoutSubscription() {
        XCTAssertTrue(ProSoundAccess.canEquipProSound(isPro: false, hasTrialUnlock: true))
    }

    func testFreeUsersWithoutTrialCannotEquip() {
        XCTAssertFalse(ProSoundAccess.canEquipProSound(isPro: false, hasTrialUnlock: false))
    }

    func testConsumesTrialWhenEquippingFirstProSound() {
        XCTAssertTrue(
            ProSoundAccess.shouldConsumeTrialOnEquip(
                isPro: false,
                hasTrialUnlock: true,
                previousSound: .intense,
                newSound: .klaxon
            )
        )
    }

    func testDoesNotConsumeWhenSwitchingBetweenProSounds() {
        XCTAssertFalse(
            ProSoundAccess.shouldConsumeTrialOnEquip(
                isPro: false,
                hasTrialUnlock: true,
                previousSound: .klaxon,
                newSound: .whistle
            )
        )
    }
}
