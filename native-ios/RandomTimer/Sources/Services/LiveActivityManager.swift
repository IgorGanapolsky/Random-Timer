import ActivityKit
import Foundation

@MainActor
final class LiveActivityManager: TimerLiveActivityHandling {

    private var activity: Activity<TimerActivityAttributes>?

    func start(state: TimerState) async {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        let attributes = TimerActivityAttributes(
            endDate: state.endDate,
            minSeconds: state.config.minSeconds,
            maxSeconds: state.config.maxSeconds
        )
        let contentState = TimerActivityAttributes.ContentState(
            status: state.status,
            remainingSeconds: Int(state.remainingDuration)
        )

        let staleDate = state.endDate

        do {
            activity = try Activity.request(
                attributes: attributes,
                content: .init(state: contentState, staleDate: staleDate),
                pushType: nil
            )
        } catch {
            print("Failed to start Live Activity: \(error)")
        }
    }

    func update(state: TimerState) {
        let contentState = TimerActivityAttributes.ContentState(
            status: state.status,
            remainingSeconds: Int(state.remainingDuration)
        )

        let staleDate = state.endDate

        guard let currentActivity = activity else { return }
        Task {
            await currentActivity.update(
                ActivityContent(state: contentState, staleDate: staleDate)
            )
        }
    }

    func end() {
        guard let currentActivity = activity else { return }
        Task {
            await currentActivity.end(nil, dismissalPolicy: .immediate)
        }
        activity = nil
    }

    func endAll() async {
        for activity in Activity<TimerActivityAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
    }
}
