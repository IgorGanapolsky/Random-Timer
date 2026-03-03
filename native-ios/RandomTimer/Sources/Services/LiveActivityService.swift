@preconcurrency import ActivityKit
import os

/// Live Activity wrapper to allow testing via protocol
@MainActor
final class LiveActivityService: TimerLiveActivityHandling {
    private var activity: Activity<TimerActivityAttributes>?

    func start(state: TimerState) async {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        // Use sanitized values to prevent timing leaks on lock screen
        let attributes = TimerActivityAttributes(
            endDate: state.liveActivityEndDate,
            minSeconds: state.config.minSeconds,
            maxSeconds: state.config.maxSeconds
        )
        let contentState = TimerActivityAttributes.ContentState(
            status: state.status,
            remainingSeconds: state.liveActivityRemainingSeconds
        )

        // Use real endDate for staleDate so iOS keeps the activity alive
        let staleDate = state.endDate

        do {
            activity = try Activity.request(
                attributes: attributes,
                content: .init(state: contentState, staleDate: staleDate),
                pushType: nil
            )
        } catch {
            Logger.liveActivity.error("Failed to start Live Activity: \(error)")
        }
    }

    func update(state: TimerState) async {
        // Use sanitized values to prevent timing leaks
        let contentState = TimerActivityAttributes.ContentState(
            status: state.status,
            remainingSeconds: state.liveActivityRemainingSeconds
        )

        // Use real endDate for staleDate so iOS keeps the activity alive
        let staleDate = state.endDate

        guard let currentActivity = activity else { return }
        await currentActivity.update(
            ActivityContent(state: contentState, staleDate: staleDate)
        )
    }

    func end() async {
        guard let currentActivity = activity else { return }
        await currentActivity.end(nil, dismissalPolicy: .immediate)
        activity = nil
    }

    func endAll() async {
        for activity in Activity<TimerActivityAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
    }
}
