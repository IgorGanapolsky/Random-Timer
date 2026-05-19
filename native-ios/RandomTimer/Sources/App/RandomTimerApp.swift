import FirebaseCore
import OSLog
import SwiftUI

@main
struct RandomTimerApp: App {
    private static let logger = Logger(
        subsystem: Bundle.main.bundleIdentifier ?? "com.igorganapolsky.randomtimer",
        category: "App"
    )

    // swiftlint:disable:next no_state_object
    @StateObject private var timerManager = TimerManager()
    @State private var deepLinkRouter = DeepLinkRouter()
    @Environment(\.scenePhase) private var scenePhase

    /// Non-nil when the App Store advertises a newer version than this build.
    @State private var storeUpdateVersion: String?

    private let storeUpdateService = StoreUpdateService()

    /// GitHub Actions passes `OTHER_SWIFT_FLAGS=-D RT_SKIP_FIREBASE_FOR_CI` for `xcodebuild test`
    /// because the simulator app does not inherit shell env vars and CI uses a placeholder plist.
    private static var shouldSkipFirebaseForHostedTests: Bool {
        #if RT_SKIP_FIREBASE_FOR_CI
        return true
        #else
        return ProcessInfo.processInfo.environment["RT_SKIP_FIREBASE_FOR_TESTS"] == "1"
            || ProcessInfo.processInfo.arguments.contains("-SkipFirebaseForTesting")
        #endif
    }

    private static var hasBundledFirebaseConfig: Bool {
        Bundle.main.url(forResource: "GoogleService-Info", withExtension: "plist") != nil
    }

    init() {
        guard !Self.shouldSkipFirebaseForHostedTests else { return }
        guard Self.hasBundledFirebaseConfig else {
            Self.logger.warning("Skipping Firebase initialization because GoogleService-Info.plist is not bundled.")
            AnalyticsService.shared.initialize()
            return
        }
        FirebaseApp.configure()
        CrashReportingService.shared.initialize()
        AnalyticsService.shared.initialize()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(timerManager)
                .environmentObject(ProManager.shared)
                .environment(deepLinkRouter)
                .preferredColorScheme(.dark)
                .onOpenURL { url in
                    AnalyticsService.shared.trackDeepLink(url)
                    deepLinkRouter.handle(url)
                }
                .alert("Update Available", isPresented: Binding(
                    get: { storeUpdateVersion != nil },
                    set: { if !$0 { storeUpdateVersion = nil } }
                )) {
                    Button("Update") {
                        if let url = URL(string: "https://apps.apple.com/app/id6758355312") {
                            UIApplication.shared.open(url)
                        }
                    }
                    Button("Not Now", role: .cancel) {}
                } message: {
                    Text("A new version (\(storeUpdateVersion ?? "")) is available on the App Store with new features and fixes.")
                }
        }
        .onChange(of: scenePhase) { _, newPhase in
            switch newPhase {
            case .active:
                Task {
                    await refreshAppActiveServices()
                }
            case .background:
                timerManager.handleBackground()
            default:
                break
            }
        }
        .task {
            await refreshAppActiveServices()
        }
    }

    @MainActor
    private func refreshAppActiveServices() async {
        if let newerVersion = await storeUpdateService.checkForUpdates() {
            storeUpdateVersion = newerVersion
        }
        await ProAudioPackStore.shared.refreshIfNeeded(isPro: ProManager.shared.isPro)
        await timerManager.configureMonthlyContentReminderIfNeeded()
        await timerManager.handleForeground()
    }
}

struct ContentView: View {
    @EnvironmentObject var timerManager: TimerManager
    @Environment(DeepLinkRouter.self) private var deepLinkRouter
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
            .onChange(of: timerManager.timerState) { oldValue, newValue in
                if oldValue != nil && newValue == nil {
                    StoreReviewManager.shared.presentPendingReviewPromptIfQueued()
                }
            }
        }
        .environment(deepLinkRouter)
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
        .environment(DeepLinkRouter())
}
