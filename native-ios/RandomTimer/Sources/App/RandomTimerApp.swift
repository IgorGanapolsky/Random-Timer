import SwiftUI
import FirebaseCrashlytics

@main
struct RandomTimerApp: App {
    @StateObject private var timerManager = TimerManager()
    @Environment(\.scenePhase) private var scenePhase

    init() {
        AnalyticsService.shared.initialize()
        setupCrashReporting()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(timerManager)
                .environmentObject(ProManager.shared)
                .preferredColorScheme(.dark)
                .onOpenURL { url in
                    AnalyticsService.shared.trackDeepLink(url)
                }
        }
        .onChange(of: scenePhase) { _, newPhase in
            switch newPhase {
            case .active:
                Task {
                    await timerManager.handleForeground()
                }
            case .background:
                timerManager.handleBackground()
            default:
                break
            }
        }
    }

    private func setupCrashReporting() {
        CrashReportingService.shared.initialize()

        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown"
        let build = Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "unknown"

        let tracker = AppUpgradeTracker()
        let info = tracker.evaluateLaunch(currentVersion: version, currentBuild: build)

        // Attach version/build to every crash report.
        CrashReportingService.shared.setCustomValue(info.toVersion, forKey: "app_version")
        CrashReportingService.shared.setCustomValue(info.toBuild, forKey: "app_build")
        CrashReportingService.shared.setCustomValue(info.isFirstLaunch, forKey: "is_first_launch")
        CrashReportingService.shared.setCustomValue(info.isUpgrade, forKey: "is_upgrade_launch")

        if info.isUpgrade {
            if let fromVersion = info.fromVersion {
                CrashReportingService.shared.setCustomValue(fromVersion, forKey: "upgrade_from_version")
            }
            if let fromBuild = info.fromBuild {
                CrashReportingService.shared.setCustomValue(fromBuild, forKey: "upgrade_from_build")
            }
            CrashReportingService.shared.log(
                "App upgraded from \(info.fromVersion ?? "?") (\(info.fromBuild ?? "?")) " +
                "to \(info.toVersion) (\(info.toBuild))"
            )
        } else if info.isFirstLaunch {
            CrashReportingService.shared.log("First launch for version \(info.toVersion) (\(info.toBuild))")
        } else {
            CrashReportingService.shared.log("Repeat launch for version \(info.toVersion) (\(info.toBuild))")
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var timerManager: TimerManager
    @State private var didApplyUITestSeed: Bool = false

    var body: some View {
        NavigationStack {
            Group {
                if timerManager.timerState != nil {
                    ActiveTimerScreen()
                } else {
                    TimerSetupScreen()
                }
            }
            .animation(.easeInOut(duration: 0.3), value: timerManager.timerState != nil)
        }
        .onAppear {
#if DEBUG
            guard didApplyUITestSeed == false else { return }
            didApplyUITestSeed = true

            let args = ProcessInfo.processInfo.arguments
            guard let index = args.firstIndex(of: "-ui-test-state"),
                  args.indices.contains(index + 1) else { return }

            let stateArg = args[index + 1].lowercased()

            switch stateArg {
            case "running":
                let config = TimerConfig()
                let seededState = TimerState(
                    config: config,
                    targetDuration: 195,
                    remainingDuration: 135,
                    status: .running,
                    alarmTimeRemaining: 0,
                    alarmStartedAt: nil
                )
                timerManager._setTimerStateForTesting(seededState)

            case "paused":
                let config = TimerConfig()
                let seededState = TimerState(
                    config: config,
                    targetDuration: 195,
                    remainingDuration: 135,
                    status: .paused,
                    alarmTimeRemaining: 0,
                    alarmStartedAt: nil
                )
                timerManager._setTimerStateForTesting(seededState)

            case "alarm":
                let config = TimerConfig()
                let seededState = TimerState(
                    config: config,
                    targetDuration: 5,
                    remainingDuration: 0,
                    status: .alarm,
                    alarmTimeRemaining: TimeInterval(config.alarmDuration),
                    alarmStartedAt: Date()
                )
                timerManager._setTimerStateForTesting(seededState)

            case "complete":
                let config = TimerConfig()
                let seededState = TimerState(
                    config: config,
                    targetDuration: 5,
                    remainingDuration: 0,
                    status: .complete,
                    alarmTimeRemaining: 0,
                    alarmStartedAt: nil
                )
                timerManager._setTimerStateForTesting(seededState)

            default:
                break
            }
#endif
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(TimerManager())
        .environmentObject(ProManager.shared)
}
