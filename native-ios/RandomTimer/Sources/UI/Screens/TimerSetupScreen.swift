import SwiftUI

/// Initial screen for configuring and starting a timer
struct TimerSetupScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @EnvironmentObject var proManager: ProManager
    @State private var showPaywall = false
    @State private var paywallEntryPoint: PaywallEntryPoint = .unknown
    @State private var showArsenal = false
    @AppStorage("hasCompletedFirstTimer") private var hasCompletedFirstTimer = false

    // Read directly from timerManager.config to avoid animation issues
    private var config: TimerConfig { timerManager.config }

    private var maxSliderRange: Double {
        if proManager.isPro && config.useExtendedRange {
            return Double(TimerConfig.maxSecondsPro)
        } else {
            return Double(TimerConfig.maxSecondsFree)
        }
    }
    private var minSliderMax: Double { maxSliderRange - 30 }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                
                // Zone 1: Standard Ops
                Text("STANDARD OPS")
                    .font(.caption2)
                    .fontWeight(.bold)
                    .foregroundColor(.textMuted)
                    .padding(.top, 16)
                    .padding(.leading, 4)

                // 1. Timer Range Card
                GlassCard {
                    VStack(alignment: .leading) {
                        HStack {
                            Label("Timer Range", systemImage: "timer")
                                .font(.headline)
                                .fontWeight(.semibold)
                                .foregroundColor(.textPrimary)
                            
                            Spacer()

                            if proManager.isPro {
                                Button {
                                    let generator = UIImpactFeedbackGenerator(style: .medium)
                                    generator.impactOccurred()
                                    let newExtended = !config.useExtendedRange
                                    if !newExtended && config.maxSeconds > TimerConfig.maxSecondsFree {
                                        // Clamp if shrinking
                                        let clampedMax = TimerConfig.maxSecondsFree
                                        let clampedMin = Swift.min(config.minSeconds, clampedMax - TimeRangeAdjuster.defaultMinGapSeconds)
                                        updateConfig(maxSeconds: clampedMax, minSeconds: clampedMin, useExtendedRange: false)
                                    } else {
                                        updateConfig(useExtendedRange: newExtended)
                                    }
                                } label: {
                                    Text(config.useExtendedRange ? "60M MODE" : "5M MODE")
                                        .font(.caption2.weight(.bold))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(config.useExtendedRange ? Color.accentPrimary.opacity(0.2) : Color.glassBackground)
                                        .foregroundColor(config.useExtendedRange ? .accentPrimary : .textSecondary)
                                        .cornerRadius(4)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 4)
                                                .stroke(config.useExtendedRange ? Color.accentPrimary : Color.glassBorder, lineWidth: 0.5)
                                        )
                                }
                            } else {
                                Text("PRO: 1H \u{1F512}")
                                    .font(.caption2)
                                    .foregroundColor(.accentPrimary)
                                    .onTapGesture {
                                        presentPaywall(entryPoint: .rangeGate)
                                    }
                            }
                        }

                        Spacer().frame(height: 16)

                        TimeRangeSliders(
                            minValue: config.minSeconds,
                            maxValue: config.maxSeconds,
                            maxSecondsLimit: Int(maxSliderRange),
                            onRangeChange: { newMin, newMax in
                                updateConfig(minSeconds: newMin, maxSeconds: newMax)
                            }
                        )
                    }
                }

                // 2. Alarm Sound (Unified: Duration, Sounds, Volume, Vibration)
                GlassCard {
                    VStack(alignment: .leading) {
                        Label("Alarm Sound", systemImage: "bell.fill")
                            .font(.headline)
                            .fontWeight(.semibold)
                            .foregroundColor(.textPrimary)

                        Spacer().frame(height: 12)

                        // Duration Chips
                        HStack(spacing: 8) {
                            ForEach(TimerConfig.alarmDurationOptions, id: \.self) { duration in
                                DurationChip(
                                    duration: duration,
                                    selected: config.alarmDuration == duration,
                                    onTap: {
                                        updateConfig(alarmDuration: duration)
                                    }
                                )
                            }
                        }

                        Spacer().frame(height: 20)

                        // Voice Callouts (Pro Feature)
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Label("Voice Callouts", systemImage: "waveform")
                                    .font(.subheadline)
                                    .fontWeight(.semibold)
                                    .foregroundColor(proManager.isPro ? .textPrimary : .textMuted)
                                
                                Text("Prompts during countdown")
                                    .font(.caption2)
                                    .foregroundColor(.textMuted)
                            }
                            
                            Spacer()
                            
                            HStack(spacing: 8) {
                                // Preview Button (always enabled)
                                Button {
                                    timerManager.previewCommandCue()
                                } label: {
                                    Text("PREVIEW")
                                        .font(.caption2.weight(.bold))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(Color.accentPrimary.opacity(0.1))
                                        .foregroundColor(.accentPrimary)
                                        .cornerRadius(4)
                                }

                                if proManager.isPro {
                                    Text("ENABLED")
                                        .font(.caption2)
                                        .fontWeight(.bold)
                                        .foregroundColor(.accentPrimary)
                                } else {
                                    Button {
                                        presentPaywall(entryPoint: .soundGate)
                                    } label: {
                                        HStack(spacing: 4) {
                                            Text("PRO")
                                            Image(systemName: "lock.fill")
                                        }
                                        .font(.caption2.weight(.bold))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(Color.accentPrimary.opacity(0.1))
                                        .foregroundColor(.accentPrimary)
                                        .cornerRadius(4)
                                    }
                                }
                            }
                        }
                        .padding(.vertical, 8)
                        .opacity(proManager.isPro ? 1.0 : 0.6)

                        Spacer().frame(height: 20)

                        // Core Sounds
                        HStack(spacing: 12) {
                            SoundTypeButton(
                                label: "Intense",
                                systemImage: "flame.fill",
                                selected: config.soundType == .intense,
                                onTap: {
                                    updateConfig(soundType: .intense)
                                    timerManager.previewSound()
                                }
                            )
                            SoundTypeButton(
                                label: "Gentle",
                                systemImage: "bolt.fill",
                                selected: config.soundType == .gentle,
                                onTap: {
                                    updateConfig(soundType: .gentle)
                                    timerManager.previewSound()
                                }
                            )
                        }

                        Spacer().frame(height: 24)

                        // Volume Slider
                        VolumeSliderView(
                            value: config.volume,
                            onChanged: { newVolume in
                                updateConfig(volume: newVolume)
                            },
                            onSliding: { newVolume in
                                updateConfig(volume: newVolume)
                                timerManager.previewVolume()
                            },
                            systemImage: "speaker.wave.3.fill"
                        )

                        Spacer().frame(height: 12)

                        // Vibration Toggle
                        HStack {
                            Text("Vibration")
                                .font(.subheadline)
                                .foregroundColor(.textSecondary)

                            Spacer()

                            Toggle("Vibration", isOn: Binding(
                                get: { config.vibrationEnabled },
                                set: { updateConfig(vibrationEnabled: $0) }
                            ))
                            .tint(.accentPrimary)
                            .labelsHidden()
                        }
                        .transaction { $0.animation = nil }
                    }
                }

                // Start Button
                PrimaryButton(title: "Start Timer") {
                    Task {
                        await timerManager.startTimer()
                    }
                }
                .scaleEffect(1.02)
                .padding(.vertical, 8)

                // Zone 2: Tactical Expansion (PRO)
                HStack {
                    Text("TACTICAL EXPANSION (PRO)")
                        .font(.caption2)
                        .fontWeight(.bold)
                        .foregroundColor(proManager.isPro ? .accentPrimary : .textMuted)
                        .onTapGesture {
                            if !proManager.isPro {
                                presentPaywall(entryPoint: .soundGate)
                            }
                        }
                    
                    if !proManager.isPro {
                        Image(systemName: "lock.fill")
                            .font(.caption2)
                            .foregroundColor(.textMuted)
                        
                        Spacer()
                        
                        Button {
                            withAnimation(.spring()) {
                                showArsenal.toggle()
                            }
                        } label: {
                            Text(showArsenal ? "Hide Sound Arsenal" : "View Sound Arsenal")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .foregroundColor(.accentPrimary)
                        }
                    }
                }
                .padding(.top, 8)
                .padding(.leading, 4)

                // Pro Sound Arsenal (Adaptive Visibility)
                if proManager.isPro || showArsenal {
                    GlassCard {
                        VStack(alignment: .leading) {
                            Label("Sound Arsenal", systemImage: "speaker.wave.3.fill")
                                .font(.headline)
                                .fontWeight(.semibold)
                                .foregroundColor(proManager.isPro ? .textPrimary : .textMuted)

                            Spacer().frame(height: 12)

                            let lockSuffix = proManager.isPro ? "" : " \u{1F512}"
                            let proSounds = SoundType.proSounds
                            ForEach(Array(stride(from: 0, to: proSounds.count, by: 2)), id: \.self) { i in
                                HStack(spacing: 12) {
                                    let sound = proSounds[i]
                                    SoundTypeButton(
                                        label: sound.rawValue.capitalized + lockSuffix,
                                        selected: config.soundType == sound,
                                        onTap: {
                                            if proManager.isPro {
                                                updateConfig(soundType: sound)
                                                timerManager.previewSound()
                                            } else {
                                                timerManager.previewSound(type: sound)
                                            }
                                        }
                                    )
                                    if i + 1 < proSounds.count {
                                        let sound2 = proSounds[i + 1]
                                        SoundTypeButton(
                                            label: sound2.rawValue.capitalized + lockSuffix,
                                            selected: config.soundType == sound2,
                                            onTap: {
                                            if proManager.isPro {
                                                updateConfig(soundType: sound2)
                                                timerManager.previewSound()
                                            } else {
                                                timerManager.previewSound(type: sound2)
                                            }
                                        }
                                    )
                                }
                                }
                            }

                            if !proManager.isPro {
                                VStack(alignment: .leading, spacing: 6) {
                                    Text("Tap a sound to preview. Unlock Pro to equip it.")
                                        .font(.caption2)
                                        .foregroundColor(.textMuted)

                                    Button("Unlock Pro") {
                                        presentPaywall(entryPoint: .soundGate)
                                    }
                                    .font(.caption2.weight(.semibold))
                                    .foregroundColor(.accentPrimary)
                                }
                                .padding(.top, 8)
                            }
                        }
                    }
                    .opacity(proManager.isPro ? 1.0 : 0.7)
                    .transition(.move(edge: .top).combined(with: .opacity))
                }

                Spacer(minLength: 32)
            }
            .padding(.horizontal, 24)
        }
        .background(Color.backgroundDark.ignoresSafeArea())
        .navigationTitle("Random Tactical Timer")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showPaywall) {
            PaywallSheet(entryPoint: paywallEntryPoint)
                .environmentObject(proManager)
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
                .interactiveDismissDisabled(false)
        }
        .onAppear {
            AnalyticsService.shared.screen(AnalyticsScreens.timerSetup)
            // Ensure Arsenal state matches Pro status on load
            if proManager.isPro {
                showArsenal = true
            }
        }
    }

    // Helper to update config with specific field changes
    private func updateConfig(
        minSeconds: Int? = nil,
        maxSeconds: Int? = nil,
        alarmDuration: Int? = nil,
        soundType: SoundType? = nil,
        volume: Float? = nil,
        vibrationEnabled: Bool? = nil,
        useExtendedRange: Bool? = nil
    ) {
        let newConfig = TimerConfig(
            minSeconds: minSeconds ?? config.minSeconds,
            maxSeconds: maxSeconds ?? config.maxSeconds,
            alarmDuration: alarmDuration ?? config.alarmDuration,
            hiddenMode: false,
            repeatEnabled: config.repeatEnabled,
            soundType: soundType ?? config.soundType,
            volume: volume ?? config.volume,
            vibrationEnabled: vibrationEnabled ?? config.vibrationEnabled,
            useExtendedRange: useExtendedRange ?? config.useExtendedRange
        )
        timerManager.updateConfig(newConfig)
    }

    private func presentPaywall(entryPoint: PaywallEntryPoint) {
        paywallEntryPoint = entryPoint
        showPaywall = true
    }
}

// MARK: - Time Range Sliders

private struct TimeRangeSliders: View {
    let minValue: Int
    let maxValue: Int
    var maxSecondsLimit: Int = TimerConfig.maxSecondsFree
    var enabled: Bool = true
    let onRangeChange: (Int, Int) -> Void

    // Precision nudge step (1 second for fine-tuning)
    private let fineStep = 1
    private let coarseStep = 5
    private let minGap = TimeRangeAdjuster.defaultMinGapSeconds

    private var minSliderUpperBound: Int {
        Swift.max(0, maxValue - minGap)
    }

    private var maxSliderLowerBound: Int {
        Swift.min(maxSecondsLimit, minValue + minGap)
    }

    private var minSliderRange: ClosedRange<Double> {
        let lower = 0.0
        let upper = Double(minSliderUpperBound)
        return lower < upper ? lower...upper : lower...(lower + 1)
    }

    private var maxSliderRange: ClosedRange<Double> {
        let lower = Double(maxSliderLowerBound)
        let upper = Double(maxSecondsLimit)
        return lower < upper ? lower...upper : lower...(lower + 1)
    }

    var body: some View {
        VStack(spacing: 16) {
            // Display
            HStack {
                Spacer()
                Text(TimeInterval(minValue).formattedDuration)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(enabled ? .textPrimary : .textMuted)

                Text(" - ")
                    .font(.title2)
                    .foregroundColor(.textSecondary)

                Text(TimeInterval(maxValue).formattedDuration)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(enabled ? .textPrimary : .textMuted)
                Spacer()
            }

            // Min slider with Nudge buttons
            VStack(spacing: 4) {
                Text("Minimum: \(TimeInterval(minValue).formattedDuration)")
                    .font(.caption2)
                    .foregroundColor(.textMuted)

                HStack(spacing: 12) {
                    StepAdjustButton(
                        systemImage: "minus.circle.fill",
                        enabled: enabled && canAdjustMin(by: -coarseStep),
                        accessibilityLabel: "Decrease minimum"
                    ) {
                        adjustMin(by: -coarseStep)
                    }

                    Slider(
                        value: Binding(
                            get: { Double(Swift.min(Swift.max(minValue, 0), minSliderUpperBound)) },
                            set: { newValue in
                                let snapped = Int((newValue / Double(coarseStep)).rounded()) * coarseStep
                                adjustMin(to: snapped)
                            }
                        ),
                        in: minSliderRange
                    )
                    .tint(enabled ? .accentPrimary : .textMuted)
                    .accessibilityLabel("Minimum time slider")
                    .accessibilityValue(TimeInterval(minValue).formattedDuration)

                    StepAdjustButton(
                        systemImage: "plus.circle.fill",
                        enabled: enabled && canAdjustMin(by: coarseStep),
                        accessibilityLabel: "Increase minimum"
                    ) {
                        adjustMin(by: coarseStep)
                    }
                }
            }

            // Max slider with Nudge buttons
            VStack(spacing: 4) {
                Text("Maximum: \(TimeInterval(maxValue).formattedDuration)")
                    .font(.caption2)
                    .foregroundColor(.textMuted)

                HStack(spacing: 12) {
                    StepAdjustButton(
                        systemImage: "minus.circle.fill",
                        enabled: enabled && canAdjustMax(by: -coarseStep),
                        accessibilityLabel: "Decrease maximum"
                    ) {
                        adjustMax(by: -coarseStep)
                    }

                    Slider(
                        value: Binding(
                            get: { Double(Swift.min(Swift.max(maxValue, maxSliderLowerBound), maxSecondsLimit)) },
                            set: { newValue in
                                let snapped = Int((newValue / Double(coarseStep)).rounded()) * coarseStep
                                adjustMax(to: snapped)
                            }
                        ),
                        in: maxSliderRange
                    )
                    .tint(enabled ? .accentPrimary : .textMuted)
                    .accessibilityLabel("Maximum time slider")
                    .accessibilityValue(TimeInterval(maxValue).formattedDuration)

                    StepAdjustButton(
                        systemImage: "plus.circle.fill",
                        enabled: enabled && canAdjustMax(by: coarseStep),
                        accessibilityLabel: "Increase maximum"
                    ) {
                        adjustMax(by: coarseStep)
                    }
                }
            }
        }
        .disabled(!enabled)
        .transaction { $0.animation = nil }
    }

    private func adjustMin(by delta: Int) {
        adjustMin(to: minValue + delta)
    }

    private func adjustMin(to newVal: Int) {
        let adjusted = adjustedRangeForMin(newValue: newVal)
        applyAdjustedRangeIfChanged(adjusted)
    }

    private func adjustMax(by delta: Int) {
        adjustMax(to: maxValue + delta)
    }

    private func adjustMax(to newVal: Int) {
        let adjusted = adjustedRangeForMax(newValue: newVal)
        applyAdjustedRangeIfChanged(adjusted)
    }

    private func canAdjustMin(by delta: Int) -> Bool {
        let adjusted = adjustedRangeForMin(newValue: minValue + delta)
        return adjusted.min != minValue || adjusted.max != maxValue
    }

    private func canAdjustMax(by delta: Int) -> Bool {
        let adjusted = adjustedRangeForMax(newValue: maxValue + delta)
        return adjusted.min != minValue || adjusted.max != maxValue
    }

    private func adjustedRangeForMin(newValue: Int) -> (min: Int, max: Int) {
        TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: minValue,
            currentMaxSeconds: maxValue,
            newMinSeconds: Swift.max(0, newValue),
            maxSecondsLimit: maxSecondsLimit
        )
    }

    private func adjustedRangeForMax(newValue: Int) -> (min: Int, max: Int) {
        TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: minValue,
            currentMaxSeconds: maxValue,
            newMaxSeconds: Swift.max(minGap, newValue),
            maxSecondsLimit: maxSecondsLimit
        )
    }

    private func applyAdjustedRangeIfChanged(_ adjusted: (min: Int, max: Int)) {
        guard adjusted.min != minValue || adjusted.max != maxValue else { return }
        onRangeChange(adjusted.min, adjusted.max)
    }
}

private struct StepAdjustButton: View {
    let systemImage: String
    let enabled: Bool
    let accessibilityLabel: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: systemImage)
                .font(.title3)
                .fontWeight(.bold)
                .foregroundColor(enabled ? .accentPrimary : .textMuted)
                .padding(8)
                .background(
                    Circle()
                        .fill(enabled ? Color.accentPrimary.opacity(0.12) : Color.glassBackground)
                )
                .overlay(
                    Circle()
                        .stroke(enabled ? Color.accentPrimary.opacity(0.6) : Color.glassBorder, lineWidth: 1)
                )
        }
        .disabled(!enabled)
        .accessibilityLabel(accessibilityLabel)
    }
}

// MARK: - Duration Chip

private struct DurationChip: View {
    let duration: Int
    let selected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            Text("\(duration)s")
                .font(.subheadline)
                .foregroundColor(selected ? .accentPrimary : .textSecondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(selected ? Color.accentPrimary.opacity(0.2) : Color.glassBackground)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(selected ? Color.accentPrimary : Color.glassBorder, lineWidth: 1)
                )
        }
        .accessibilityLabel("\(duration) seconds")
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}

// MARK: - Sound Type Button

private struct SoundTypeButton: View {
    let label: String
    var systemImage: String = ""
    let selected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            Label(label, systemImage: systemImage)
                .font(.body)
                .foregroundColor(selected ? .accentPrimary : .textPrimary)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(selected ? Color.accentPrimary.opacity(0.15) : Color.glassBackground)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(selected ? Color.accentPrimary : Color.glassBorder, lineWidth: 1)
                )
        }
        .accessibilityLabel("\(label) sound")
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}

// MARK: - Volume Slider

private struct VolumeSliderView: View {
    let value: Float
    let onChanged: (Float) -> Void
    var onSliding: ((Float) -> Void)? = nil
    var systemImage: String = "speaker.wave.3.fill"

    var body: some View {
        VStack {
            HStack {
                Label("Volume", systemImage: systemImage)
                    .font(.subheadline)
                    .foregroundColor(.textSecondary)

                Spacer()

                Text("\(Int(value * 100))%")
                    .font(.subheadline)
                    .foregroundColor(.textPrimary)
            }

            Slider(
                value: Binding(
                    get: { Double(value) },
                    set: { newValue in
                        onSliding?(Float(newValue))
                    }
                ),
                in: 0...1,
                onEditingChanged: { editing in
                    if !editing {
                        onChanged(value)
                    }
                }
            )
            .tint(.accentPrimary)
        }
        .transaction { $0.animation = nil } // Completely disable all animations
    }
}

#Preview {
    NavigationStack {
        TimerSetupScreen()
            .environmentObject(TimerManager())
            .environmentObject(ProManager.shared)
    }
}
