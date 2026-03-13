import SwiftUI
import UIKit

// swiftlint:disable no_environment_object
@MainActor
func shouldKeepScreenAwake(timerState: TimerState?) -> Bool {
    guard let timerState else { return false }
    return timerState.status != .idle && timerState.status != .complete
}

@main
struct RandomTimerApp: App {
    @StateObject private var timerManager = TimerManager()
    @Environment(\.scenePhase) private var scenePhase

    init() {
        AnalyticsService.shared.initialize()
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
                UIApplication.shared.isIdleTimerDisabled = shouldKeepScreenAwake(timerState: timerManager.timerState)
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
}

struct ContentView: View {
    private enum Route: Hashable {
        case activeTimer
    }

    @EnvironmentObject var timerManager: TimerManager
    @State private var didApplyUITestSeed: Bool = false
    @State private var navigationPath: [Route] = []
    @State private var hadActiveTimer = false
    @State private var previousTimerStatus: TimerStatus?

    var body: some View {
        NavigationStack(path: $navigationPath) {
            TimerSetupScreen()
                .navigationDestination(for: Route.self) { route in
                    switch route {
                    case .activeTimer:
                        ActiveTimerScreen()
                    }
                }
        }
        .onAppear {
            syncNavigationState()
            updateIdleTimerState()
#if DEBUG
            guard didApplyUITestSeed == false else { return }
            didApplyUITestSeed = true

            Task {
                // Short delay to ensure environment is fully ready
                try? await Task.sleep(for: .seconds(0.5))

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
            }
#endif
        }
        .onChange(of: timerManager.timerState?.status) { _, _ in
            syncNavigationState()
            updateIdleTimerState()
        }
        .onDisappear {
            UIApplication.shared.isIdleTimerDisabled = false
        }
    }

    private func syncNavigationState() {
        let currentStatus = timerManager.timerState?.status
        let hasActiveTimer = currentStatus != nil
        let startedTimer = !hadActiveTimer && hasActiveTimer
        let enteredAlarm = currentStatus == .alarm && previousTimerStatus != .alarm

        if startedTimer || enteredAlarm {
            if navigationPath.last != .activeTimer {
                navigationPath = [.activeTimer]
            }
        } else if !hasActiveTimer {
            navigationPath.removeAll()
        }

        hadActiveTimer = hasActiveTimer
        previousTimerStatus = currentStatus
    }

    private func updateIdleTimerState() {
        UIApplication.shared.isIdleTimerDisabled = shouldKeepScreenAwake(timerState: timerManager.timerState)
    }
}

#Preview {
    ContentView()
        .environmentObject(TimerManager())
        .environmentObject(ProManager.shared)
}
// swiftlint:enable no_environment_object
