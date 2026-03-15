import SwiftUI

/// Circular progress timer view with glow effects and shimmer animation.
/// Uses TimelineView for frame-accurate Canvas redraw with animation timing
/// matched to Android's Compose Animatable durations.
struct CircularTimerView: View {
    let progress: Double
    let status: TimerStatus
    var isHiddenMode: Bool = false
    var rangeText: String = "" // e.g., "30s - 2m"

    private let strokeWidth: CGFloat = 16
    @ScaledMetric(relativeTo: .title) private var timerSize: CGFloat = 320
    @ScaledMetric(relativeTo: .title) private var rangeTextSize: CGFloat = 28 // Reduced from 32

    private var effectiveRangeTextSize: CGFloat {
        if rangeText.count >= 20 {
            return rangeTextSize * 0.75
        } else if rangeText.count >= 14 {
            return rangeTextSize * 0.85
        } else {
            return rangeTextSize
        }
    }

    // Animation timing matched to Android CircularTimerAnimationConfig:
    // Android shimmer: tween(3000ms, LinearEasing, Restart) = 3.0s per orbit
    // Android circle pulse: tween(1500ms, Reverse) = 1.5s one-way, 3.0s full cycle, 0.3→0.7
    // Android text breathing: tween(2000ms, Reverse) = 2.0s one-way, 4.0s full cycle, 1.0→0.85

    // Text breathing (uses withAnimation, not TimelineView)
    @State private var pulseOpacity: Double = 1.0
    // Track the animation start time so we can compute elapsed time
    @State private var animationStartDate: Date = .now

    private var isComplete: Bool {
        status == .alarm || status == .complete
    }

    private var isPaused: Bool {
        status == .paused
    }

    private var isActivelyRunning: Bool {
        Self.shouldBreatheText(for: status)
    }

    /// Whether all animations (shimmer, pulse) should freeze
    private var shouldPauseAnimations: Bool {
        isComplete || isPaused
    }

    var body: some View {
        // Cap at 60fps to match Android's typical display refresh and prevent
        // ProMotion 120Hz from making animations appear 2x faster perceptually.
        TimelineView(.animation(minimumInterval: 1.0 / 60.0, paused: shouldPauseAnimations)) { timeline in
            let elapsed = shouldPauseAnimations ? 0.0 : timeline.date.timeIntervalSince(animationStartDate)

            // Ball orbit: 5.0s per full rotation on iOS.
            // Android uses tween(3000ms) but ProMotion displays + SwiftUI TimelineView
            // make identical durations appear perceptually faster. Tuned to match visually.
            let shimmerFraction = elapsed.truncatingRemainder(dividingBy: 5.0) / 5.0

            // Circle pulse: 5.0s full cycle on iOS (vs Android 3.0s).
            // Same perceptual tuning as shimmer orbit above.
            let pulseCycle = elapsed.truncatingRemainder(dividingBy: 5.0) / 5.0
            let pulseT = Self.computePulseT(pulseCycle)
            let trackAlpha = isComplete ? 0.15 : (isPaused ? 0.45 : 0.3 + 0.4 * pulseT)

            ZStack {
                Canvas { context, size in
                    let diameter = min(size.width, size.height)
                    let radius = diameter / 2
                    let strokePx = strokeWidth
                    let center = CGPoint(x: size.width / 2, y: size.height / 2)
                    // Inset arc so the shimmer ball's outer glow (2.5*strokePx)
                    // stays within the Canvas bounds and doesn't get clipped.
                    let glowInset = strokePx * 2.5
                    let arcRadius = radius - glowInset

                    // 1. Background track with pulse
                    let trackRect = CGRect(
                        x: center.x - arcRadius,
                        y: center.y - arcRadius,
                        width: arcRadius * 2,
                        height: arcRadius * 2
                    )
                    let trackPath = Path { p in
                        p.addEllipse(in: trackRect)
                    }
                    context.stroke(
                        trackPath,
                        with: .color(.white.opacity(trackAlpha)),
                        style: StrokeStyle(lineWidth: strokePx, lineCap: .round)
                    )

                    // 2. Shimmer highlight — orbiting bright spot
                    if !shouldPauseAnimations {
                        let shimmerAngleRad = shimmerFraction * 2.0 * .pi - .pi / 2
                        let shimmerX = center.x + arcRadius * cos(shimmerAngleRad)
                        let shimmerY = center.y + arcRadius * sin(shimmerAngleRad)
                        let shimmerPoint = CGPoint(x: shimmerX, y: shimmerY)

                        // Outer glow (large, soft)
                        let outerGlow = Path(ellipseIn: CGRect(
                            x: shimmerPoint.x - strokePx * 2.5,
                            y: shimmerPoint.y - strokePx * 2.5,
                            width: strokePx * 5,
                            height: strokePx * 5
                        ))
                        context.fill(outerGlow, with: .color(.white.opacity(0.15)))

                        // Inner bright spot
                        let innerGlow = Path(ellipseIn: CGRect(
                            x: shimmerPoint.x - strokePx,
                            y: shimmerPoint.y - strokePx,
                            width: strokePx * 2,
                            height: strokePx * 2
                        ))
                        context.fill(innerGlow, with: .color(.white.opacity(0.5)))
                    }

                    // 3. Progress arc
                    if progress > 0 {
                        let sweepAngle = Angle.degrees(360 * progress)
                        let arcPath = Path { p in
                            p.addArc(
                                center: center,
                                radius: arcRadius,
                                startAngle: .degrees(-90),
                                endAngle: .degrees(-90) + sweepAngle,
                                clockwise: false
                            )
                        }
                        context.stroke(
                            arcPath,
                            with: .color(status.color),
                            style: StrokeStyle(lineWidth: strokePx, lineCap: .round)
                        )

                        // Glow dot at progress tip
                        let tipAngle = (-90.0 + 360.0 * progress) * .pi / 180.0
                        let tipX = center.x + arcRadius * cos(tipAngle)
                        let tipY = center.y + arcRadius * sin(tipAngle)
                        let tipGlow = Path(ellipseIn: CGRect(
                            x: tipX - strokePx,
                            y: tipY - strokePx,
                            width: strokePx * 2,
                            height: strokePx * 2
                        ))
                        context.fill(tipGlow, with: .color(status.color.opacity(0.6)))
                    }

                    // 4. Tracking dot at start of progress arc (matches Android)
                    if progress > 0 && progress < 1 {
                        let startAngleRad = -Double.pi / 2
                        let trackDotX = center.x + arcRadius * cos(startAngleRad)
                        let trackDotY = center.y + arcRadius * sin(startAngleRad)
                        let trackDotPoint = CGPoint(x: trackDotX, y: trackDotY)

                        // Outer glow
                        let outerDot = Path(ellipseIn: CGRect(
                            x: trackDotPoint.x - strokePx * 1.5,
                            y: trackDotPoint.y - strokePx * 1.5,
                            width: strokePx * 3,
                            height: strokePx * 3
                        ))
                        context.fill(outerDot, with: .color(status.color.opacity(0.3)))

                        // Inner dot
                        let innerDot = Path(ellipseIn: CGRect(
                            x: trackDotPoint.x - strokePx * 0.8,
                            y: trackDotPoint.y - strokePx * 0.8,
                            width: strokePx * 1.6,
                            height: strokePx * 1.6
                        ))
                        context.fill(innerDot, with: .color(status.color.opacity(0.6)))
                    }
                }

                // Center display (text overlay)
                if isComplete {
                    Text("Complete!")
                        .font(.system(size: min(effectiveRangeTextSize, 40), weight: .bold, design: .rounded))
                        .foregroundColor(.timerComplete)
                        .minimumScaleFactor(0.7)
                } else if !rangeText.isEmpty {
                    VStack(spacing: 4) {
                        Text("Range")
                            .font(.subheadline)
                            .foregroundColor(isPaused ? .textSecondary : .textMuted)
                        Text(rangeText)
                            .font(.system(size: min(effectiveRangeTextSize, 40), weight: .bold, design: .rounded))
                            .foregroundColor(.textPrimary)
                            .opacity(pulseOpacity)
                            .lineLimit(1)
                            .minimumScaleFactor(0.6)
                            .frame(maxWidth: timerSize * 0.75) // Safety margin
                    }
                } else {
                    Text("...")
                        .font(.system(size: min(effectiveRangeTextSize, 40), weight: .bold, design: .rounded))
                        .foregroundColor(.textPrimary)
                        .opacity(pulseOpacity)
                }
            }
        }
        .frame(width: min(timerSize, 380), height: min(timerSize, 380))
        .onAppear {
            animationStartDate = .now
            if Self.shouldBreatheText(for: status) {
                startTextBreathing()
            }
        }
        .onChange(of: status) { _, newStatus in
            if Self.shouldResetTextBreathing(for: newStatus) {
                stopAnimations()
            } else if Self.shouldBreatheText(for: newStatus) {
                animationStartDate = .now
                startTextBreathing()
            }
        }
    }

    /// Compute pulse value for a given cycle fraction [0, 1).
    /// First half goes up with FastOutSlowIn easing, second half comes back down.
    /// Matches Android tween(1500ms, default easing, RepeatMode.Reverse).
    static func computePulseT(_ cycle: Double) -> Double {
        if cycle < 0.5 {
            return fastOutSlowIn(cycle * 2.0)
        } else {
            return 1.0 - fastOutSlowIn((cycle - 0.5) * 2.0)
        }
    }

    static func shouldBreatheText(for status: TimerStatus) -> Bool {
        status == .running || status == .warning || status == .danger
    }

    static func shouldResetTextBreathing(for status: TimerStatus) -> Bool {
        status == .paused || status == .alarm || status == .complete
    }

    /// Android FastOutSlowInEasing = CubicBezier(0.4, 0.0, 0.2, 1.0)
    static func fastOutSlowIn(_ t: Double) -> Double {
        let x1 = 0.4, y1 = 0.0, x2 = 0.2, y2 = 1.0
        var u = t
        for _ in 0..<8 {
            let bx = bezierComponent(u, p1: x1, p2: x2) - t
            let dbx = bezierComponentDerivative(u, p1: x1, p2: x2)
            if abs(dbx) < 1e-12 { break }
            u -= bx / dbx
            u = min(max(u, 0.0), 1.0)
        }
        return bezierComponent(u, p1: y1, p2: y2)
    }

    private static func bezierComponent(_ t: Double, p1: Double, p2: Double) -> Double {
        let oneMinusT = 1.0 - t
        return 3.0 * oneMinusT * oneMinusT * t * p1
             + 3.0 * oneMinusT * t * t * p2
             + t * t * t
    }

    private static func bezierComponentDerivative(_ t: Double, p1: Double, p2: Double) -> Double {
        let oneMinusT = 1.0 - t
        return 3.0 * oneMinusT * oneMinusT * p1
             + 6.0 * oneMinusT * t * (p2 - p1)
             + 3.0 * t * t * (1.0 - p2)
    }

    private func startTextBreathing() {
        guard !isComplete else { return }
        // Android: tween(2000ms, Reverse) = 2.0s one-way, 4.0s full cycle
        withAnimation(
            .easeInOut(duration: 2.0)
            .repeatForever(autoreverses: true)
        ) {
            pulseOpacity = 0.85
        }
    }

    private func stopAnimations() {
        withAnimation(.easeOut(duration: 0.3)) {
            pulseOpacity = 1.0
        }
    }
}

#Preview("Running") {
    ZStack {
        Color.backgroundDark.ignoresSafeArea()

        CircularTimerView(
            progress: 0.0,
            status: .running,
            rangeText: "30s - 2m"
        )
    }
}

#Preview("Complete") {
    ZStack {
        Color.backgroundDark.ignoresSafeArea()

        CircularTimerView(
            progress: 1.0,
            status: .complete
        )
    }
}
