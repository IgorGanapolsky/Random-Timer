import SwiftUI

struct CircularTimerView: View {
    let progress: Double
    let status: TimerStatus
    var isHiddenMode: Bool = false
    var rangeText: String = ""

    private let strokeWidth: CGFloat = 12
    @ScaledMetric(relativeTo: .title) private var timerSize: CGFloat = 280
    @ScaledMetric(relativeTo: .title) private var rangeTextSize: CGFloat = 32

    @State private var pulseOpacity: Double = 1.0
    @State private var animationStartDate: Date = .now

    private var isComplete: Bool { status == .alarm || status == .complete }
    private var isPaused: Bool { status == .paused }
    private var shouldPauseAnimations: Bool { isComplete || isPaused }

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 60.0, paused: shouldPauseAnimations)) { timeline in
            let elapsed = shouldPauseAnimations ? 0.0 : timeline.date.timeIntervalSince(animationStartDate)
            let shimmerFraction = elapsed.truncatingRemainder(dividingBy: 5.0) / 5.0
            let pulseCycle = elapsed.truncatingRemainder(dividingBy: 5.0) / 5.0
            let pulseT = Self.computePulseT(pulseCycle)
            let trackAlpha = isComplete ? 0.15 : (isPaused ? 0.45 : 0.3 + 0.4 * pulseT)

            ZStack {
                Canvas { context, size in
                    let diameter = min(size.width, size.height)
                    let radius = diameter / 2
                    let strokePx = strokeWidth
                    let center = CGPoint(x: size.width / 2, y: size.height / 2)
                    let glowInset = strokePx * 2.5
                    let arcRadius = radius - glowInset

                    let trackRect = CGRect(x: center.x - arcRadius, y: center.y - arcRadius, width: arcRadius * 2, height: arcRadius * 2)
                    context.stroke(Path(ellipseIn: trackRect), with: .color(.white.opacity(trackAlpha)), style: StrokeStyle(lineWidth: strokePx, lineCap: .round))

                    if !shouldPauseAnimations {
                        let shimmerAngleRad = shimmerFraction * 2.0 * .pi - .pi / 2
                        let shimmerPoint = CGPoint(x: center.x + arcRadius * cos(shimmerAngleRad), y: center.y + arcRadius * sin(shimmerAngleRad))
                        context.fill(Path(ellipseIn: CGRect(x: shimmerPoint.x - strokePx * 2.5, y: shimmerPoint.y - strokePx * 2.5, width: strokePx * 5, height: strokePx * 5)), with: .color(.white.opacity(0.15)))
                        context.fill(Path(ellipseIn: CGRect(x: shimmerPoint.x - strokePx, y: shimmerPoint.y - strokePx, width: strokePx * 2, height: strokePx * 2)), with: .color(.white.opacity(0.5)))
                    }

                    if progress > 0 {
                        let sweepAngle = Angle.degrees(360 * progress)
                        context.stroke(Path { p in p.addArc(center: center, radius: arcRadius, startAngle: .degrees(-90), endAngle: .degrees(-90) + sweepAngle, clockwise: false) }, with: .color(status.color), style: StrokeStyle(lineWidth: strokePx, lineCap: .round))
                    }
                }

                if isComplete {
                    Text("Complete!").font(.system(size: min(rangeTextSize, 40), weight: .bold, design: .rounded)).foregroundColor(.timerComplete).minimumScaleFactor(0.7)
                } else {
                    VStack(spacing: 4) {
                        Text("Range").font(.subheadline).foregroundColor(isPaused ? .textSecondary : .textMuted)
                        Text(rangeText).font(.system(size: min(rangeTextSize, 40), weight: .bold, design: .rounded)).foregroundColor(.textPrimary).opacity(pulseOpacity).minimumScaleFactor(0.7)
                    }
                }
            }
        }
        .frame(width: min(timerSize, 340), height: min(timerSize, 340))
        .onAppear {
            animationStartDate = .now
            if Self.shouldBreatheText(for: status) { startTextBreathing() }
        }
        .onChange(of: status) { _, newStatus in
            if Self.shouldResetTextBreathing(for: newStatus) { stopAnimations() }
            else if Self.shouldBreatheText(for: newStatus) { animationStartDate = .now; startTextBreathing() }
        }
    }

    static func computePulseT(_ cycle: Double) -> Double { cycle < 0.5 ? fastOutSlowIn(cycle * 2.0) : 1.0 - fastOutSlowIn((cycle - 0.5) * 2.0) }
    static func shouldBreatheText(for status: TimerStatus) -> Bool { status == .running || status == .warning || status == .danger }
    static func shouldResetTextBreathing(for status: TimerStatus) -> Bool { status == .paused || status == .alarm || status == .complete }
    static func fastOutSlowIn(_ t: Double) -> Double { t } 
    private func startTextBreathing() { withAnimation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true)) { pulseOpacity = 0.85 } }
    private func stopAnimations() { withAnimation(.easeOut(duration: 0.3)) { pulseOpacity = 1.0 } }
}
