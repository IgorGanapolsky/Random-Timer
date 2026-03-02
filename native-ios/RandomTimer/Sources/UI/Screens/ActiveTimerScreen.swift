import SwiftUI

struct ActiveTimerScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @Environment(\.dismiss) private var dismiss
    @State private var showingStopConfirm = false

    var body: some View {
        ZStack {
            Color.backgroundDark.ignoresSafeArea()

            VStack(spacing: 40) {
                Spacer()

                if let state = timerManager.state {
                    CircularTimerView(
                        progress: state.progress,
                        status: state.status,
                        isHiddenMode: state.config.hiddenMode,
                        rangeText: "\(state.config.minSeconds)s - \(state.config.maxSeconds)s"
                    )

                    VStack(spacing: 8) {
                        Text(state.status == .complete ? "TIME'S UP" : "TRAINING ACTIVE")
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(.textMuted)
                            .tracking(2)

                        if !state.config.hiddenMode || state.status == .complete {
                            Text(state.remainingDuration.formattedMMSS)
                                .font(.system(size: 64, weight: .bold, design: .monospaced))
                                .foregroundColor(.textPrimary)
                        } else {
                            Text("??:??")
                                .font(.system(size: 64, weight: .bold, design: .monospaced))
                                .foregroundColor(.textMuted)
                        }
                    }
                }

                Spacer()

                // Controls
                HStack(spacing: 32) {
                    if timerManager.state?.status == .complete {
                        PrimaryButton(title: "Reset") {
                            timerManager.resetTimer()
                        }
                    } else {
                        Button {
                            if timerManager.state?.status == .paused {
                                timerManager.resumeTimer()
                            } else {
                                timerManager.pauseTimer()
                            }
                        } label: {
                            Image(systemName: timerManager.state?.status == .paused ? "play.fill" : "pause.fill")
                                .font(.title)
                                .foregroundColor(.textPrimary)
                                .frame(width: 80, height: 80)
                                .background(Color.glassBackground)
                                .clipShape(Circle())
                                .overlay(Circle().stroke(Color.glassBorder, lineWidth: 1))
                        }

                        Button {
                            showingStopConfirm = true
                        } label: {
                            Image(systemName: "stop.fill")
                                .font(.title)
                                .foregroundColor(.timerWarning)
                                .frame(width: 80, height: 80)
                                .background(Color.glassBackground)
                                .clipShape(Circle())
                                .overlay(Circle().stroke(Color.glassBorder, lineWidth: 1))
                        }
                    }
                }
                .padding(.bottom, 40)
            }
        }
        .alert("Stop Timer?", isPresented: $showingStopConfirm) {
            Button("Cancel", role: .cancel) { }
            Button("Stop", role: .destructive) {
                timerManager.cancelTimer()
            }
        }
    }
}
