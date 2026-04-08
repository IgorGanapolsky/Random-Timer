import XCTest
@testable import RandomTimer

final class DistributionChannelResolverTests: XCTestCase {
    func testDebugIsDev() {
        XCTAssertEqual(
            DistributionChannelResolver.iosChannel(
                isDebugBuild: true,
                isSimulator: false,
                hasUiTestStateArg: false,
                mobileProvisionText: nil,
            ),
            DistributionChannelResolver.dev,
        )
    }

    func testSimulatorChannel() {
        XCTAssertEqual(
            DistributionChannelResolver.iosChannel(
                isDebugBuild: false,
                isSimulator: true,
                hasUiTestStateArg: false,
                mobileProvisionText: nil,
            ),
            DistributionChannelResolver.simulator,
        )
    }

    func testUiTestArg() {
        XCTAssertEqual(
            DistributionChannelResolver.iosChannel(
                isDebugBuild: false,
                isSimulator: false,
                hasUiTestStateArg: true,
                mobileProvisionText: nil,
            ),
            DistributionChannelResolver.uiTest,
        )
    }

    func testTestFlightHeuristic() {
        let provision = "foo beta-reports-active bar"
        XCTAssertEqual(
            DistributionChannelResolver.iosChannel(
                isDebugBuild: false,
                isSimulator: false,
                hasUiTestStateArg: false,
                mobileProvisionText: provision,
            ),
            DistributionChannelResolver.testflight,
        )
    }

    func testAppStoreWhenNoBetaFlag() {
        XCTAssertEqual(
            DistributionChannelResolver.iosChannel(
                isDebugBuild: false,
                isSimulator: false,
                hasUiTestStateArg: false,
                mobileProvisionText: "some provision without marker",
            ),
            DistributionChannelResolver.appStore,
        )
    }
}
