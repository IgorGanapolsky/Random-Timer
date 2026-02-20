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
                .preferredColorScheme(.dark)
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
}
