import XCTest
@testable import RandomTimer

final class DeepLinkRouterTests: XCTestCase {
    func testCustomSchemeUpgradeRoutesToSoundArsenalPaywall() throws {
        let url = try XCTUnwrap(URL(string: "randomtimer://open/upgrade?feature=pro_sounds"))

        XCTAssertEqual(DeepLinkRouter.paywallEntryPoint(from: url), .soundArsenalGate)
    }

    func testWebUpgradeRoutesToVoicePaywall() throws {
        let url = try XCTUnwrap(
            URL(string: "https://igorganapolsky.github.io/Random-Timer/upgrade?entry_point=voice_gate")
        )

        XCTAssertEqual(DeepLinkRouter.paywallEntryPoint(from: url), .voiceGate)
    }

    func testNonUpgradeLinkDoesNotOpenPaywall() throws {
        let url = try XCTUnwrap(URL(string: "randomtimer://open/timer"))

        XCTAssertNil(DeepLinkRouter.paywallEntryPoint(from: url))
    }
}
