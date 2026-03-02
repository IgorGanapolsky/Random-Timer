import SwiftUI

@main
struct RandomTimerApp: App {
    @StateObject private var timerManager = TimerManager()
    @StateObject private var proManager = ProManager.shared
    @Environment(\.scenePhase) private var scenePhase

    init() {
        AnalyticsService.shared.initialize()
    }

    var body: some Scene {
        WindowGroup {
            Group {
                // If a timer is running, show the active screen
                if timerManager.state != nil {
                    ActiveTimerScreen()
                } else {
                    TimerSetupScreen()
                }
            }
            .environmentObject(timerManager)
            .environmentObject(proManager)
            .preferredColorScheme(.dark)
            .animation(.easeInOut(duration: 0.3), value: timerManager.state != nil)
            .onOpenURL { url in
                AnalyticsService.shared.event("deep_link_opened", properties: ["url": url.absoluteString])
            }
        }
        .onChange(of: scenePhase) { _, newPhase in
            if newPhase == .active {
                // Refresh state on return
            }
        }
    }
}
