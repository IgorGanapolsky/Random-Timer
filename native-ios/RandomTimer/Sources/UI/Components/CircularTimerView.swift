import SwiftUI

/// Circular progress timer view with glow effects
struct CircularTimerView: View {
    let remainingDuration: TimeInterval
    let progress: Double
    let status: TimerStatus
    var isHiddenMode: Bool = false
    var rangeText: String = "" // e.g., "30s - 2m"

    private let strokeWidth: CGFloat = 12

    // Subtle breathing animation for timer display (adds suspense)
    @State private var pulseOpacity: Double = 1.0
    // Circle pulsing animation to show timer is active (drives alpha directly)
    @State private var circlePulseAlpha: Double = 0.3

    private var isComplete: Bool {
        status == .alarm || status == .complete
    }

    private var trackAlpha: Double {
        isComplete ? 0.15 : circlePulseAlpha
    }

    var body: some View {
        ZStack {
            // Background track with pulse animation (only pulse when timer is running)
            Circle()
                .stroke(
                    Color.white.opacity(trackAlpha),
                    style: StrokeStyle(lineWidth: strokeWidth, lineCap: .round)
                )

            // Progress arc with gradient
            Circle()
                .trim(from: 0, to: progress)
                .stroke(
                    AngularGradient(
                        gradient: Gradient(colors: [
                            status.color.opacity(0.3),
                            status.color,
                            status.color
                        ]),
                        center: .center,
                        startAngle: .degrees(-90),
                        endAngle: .degrees(270)
                    ),
                    style: StrokeStyle(lineWidth: strokeWidth, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut(duration: 0.3), value: progress)

            // Glow dot at progress tip
            if progress > 0 {
                Circle()
                    .fill(status.color.opacity(0.6))
                    .frame(width: strokeWidth * 1.5, height: strokeWidth * 1.5)
                    .offset(y: -140) // Radius - half stroke
                    .rotationEffect(.degrees(360 * progress - 90))
                    .blur(radius: 4)
            }

            // Tracking dot at start position (12 o'clock)
            if progress > 0 && progress < 1 {
                // Outer glow
                Circle()
                    .fill(status.color.opacity(0.3))
                    .frame(width: strokeWidth * 2, height: strokeWidth * 2)
                    .offset(y: -140)
                    .blur(radius: 2)
                // Inner dot
                Circle()
                    .fill(status.color.opacity(0.6))
                    .frame(width: strokeWidth * 1.2, height: strokeWidth * 1.2)
                    .offset(y: -140)
            }

            // Center display - show "Complete!" when alarm/complete, otherwise show range
            if isComplete {
                // Show completion message inside the circle (no animation when complete)
                Text("Complete!")
                    .font(.system(size: 32, weight: .bold, design: .rounded))
                    .foregroundColor(.timerComplete)
            } else if !rangeText.isEmpty {
                VStack(spacing: 4) {
                    Text("Range")
                        .font(.subheadline)
                        .foregroundColor(.textMuted)
                    Text(rangeText)
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundColor(.textPrimary)
                        .opacity(pulseOpacity)
                }
            } else {
                // Fallback - should not happen for random timer
                Text("...")
                    .font(.system(size: 32, weight: .bold, design: .rounded))
                    .foregroundColor(.textPrimary)
                    .opacity(pulseOpacity)
            }
        }
        .frame(width: 280, height: 280)
        .onAppear {
            startBreathingAnimation()
        }
        .onChange(of: status) { _, newStatus in
            // Stop animations when complete
            if newStatus == .alarm || newStatus == .complete {
                stopAnimations()
            }
        }
    }

    private func startBreathingAnimation() {
        guard !isComplete else { return }
        // Subtle pulse for text display
        withAnimation(
            .easeInOut(duration: 2.0)
            .repeatForever(autoreverses: true)
        ) {
            pulseOpacity = 0.85
        }
        // Circle pulse to show timer is active (matches Android: 0.3→0.7)
        withAnimation(
            .easeInOut(duration: 1.5)
            .repeatForever(autoreverses: true)
        ) {
            circlePulseAlpha = 0.7
        }
    }

    private func stopAnimations() {
        withAnimation(.easeOut(duration: 0.3)) {
            pulseOpacity = 1.0
            circlePulseAlpha = 0.15
        }
    }
}

#Preview("Running") {
    ZStack {
        Color.backgroundDark.ignoresSafeArea()

        CircularTimerView(
            remainingDuration: 150,
            progress: 0.5,
            status: .running
        )
    }
}

#Preview("Warning") {
    ZStack {
        Color.backgroundDark.ignoresSafeArea()

        CircularTimerView(
            remainingDuration: 25,
            progress: 0.9,
            status: .warning
        )
    }
}

#Preview("Danger") {
    ZStack {
        Color.backgroundDark.ignoresSafeArea()

        CircularTimerView(
            remainingDuration: 5,
            progress: 0.98,
            status: .danger
        )
    }
}
