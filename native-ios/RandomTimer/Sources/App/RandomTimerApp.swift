import SwiftUI

@main
struct RandomTimerApp: App {
    @StateObject private var timerManager = TimerManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(timerManager)
                .preferredColorScheme(.dark)
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var timerManager: TimerManager

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
    }
}

#Preview {
    ContentView()
        .environmentObject(TimerManager())
}
