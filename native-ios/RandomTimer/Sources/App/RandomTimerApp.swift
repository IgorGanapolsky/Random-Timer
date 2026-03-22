import SwiftUI

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
                .onReceive(ProManager.shared.$newProUnlockEventID) { eventID in
                    guard eventID > 0 else { return }
                    timerManager.enableExtendedRangeDefaultForNewProUnlock()
                }
        }
        .onChange(of: scenePhase) { _, newPhase in
            switch newPhase {
            case .active:
                Task {
                    await ProAudioPackStore.shared.refreshIfNeeded(isPro: ProManager.shared.isPro)
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
