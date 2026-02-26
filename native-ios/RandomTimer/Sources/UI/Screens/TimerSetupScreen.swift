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

    private var maxSliderRange: Double { Double(proManager.maxSecondsLimit) }
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

                // 1. Training Window Card
                GlassCard {
                    VStack(alignment: .leading) {
                        HStack {
                            Label("Training Window", systemImage: "timer")
                                .font(.headline)
                                .fontWeight(.semibold)
                                .foregroundColor(.textPrimary)
                            
                            if !proManager.isPro {
                                Spacer()
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
                            maxSecondsLimit: proManager.maxSecondsLimit,
                            onRangeChange: { newMin, newMax in
                                updateConfig(minSeconds: newMin, maxSeconds: newMax)
                            }
                        )
                    }
                }

                // 2. Alarm Setup (Unified: Duration, Sounds, Volume, Vibration)
                GlassCard {
                    VStack(alignment: .leading) {
                        Label("Alarm Setup", systemImage: "bell.fill")
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
                            Text(showArsenal ? "Hide Arsenal" : "View Arsenal")
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
                                                presentPaywall(entryPoint: .soundGate)
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
                                                presentPaywall(entryPoint: .soundGate)
                                            }
                                        }
                                    )
                                }
                                }
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
        vibrationEnabled: Bool? = nil
    ) {
        let newConfig = TimerConfig(
            minSeconds: minSeconds ?? config.minSeconds,
            maxSeconds: maxSeconds ?? config.maxSeconds,
            alarmDuration: alarmDuration ?? config.alarmDuration,
            hiddenMode: false,
            repeatEnabled: config.repeatEnabled,
            soundType: soundType ?? config.soundType,
            volume: volume ?? config.volume,
            vibrationEnabled: vibrationEnabled ?? config.vibrationEnabled
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
                    NudgeButton(icon: "minus.circle.fill", enabled: enabled && minValue >= fineStep) {
                        adjustMin(by: -coarseStep)
                    }

                    Slider(
                        value: Binding(
                            get: { Double(minValue) },
                            set: { adjustMin(to: Int($0)) }
                        ),
                        in: 0...Double(maxValue - 30),
                        step: 5
                    )
                    .tint(enabled ? .accentPrimary : .textMuted)

                    NudgeButton(icon: "plus.circle.fill", enabled: enabled && minValue <= maxValue - 30 - fineStep) {
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
                    NudgeButton(icon: "minus.circle.fill", enabled: enabled && maxValue >= minValue + 30 + fineStep) {
                        adjustMax(by: -coarseStep)
                    }

                    Slider(
                        value: Binding(
                            get: { Double(maxValue) },
                            set: { adjustMax(to: Int($0)) }
                        ),
                        in: Double(minValue + 30)...Double(maxSecondsLimit),
                        step: 5
                    )
                    .tint(enabled ? .accentPrimary : .textMuted)

                    NudgeButton(icon: "plus.circle.fill", enabled: enabled && maxValue <= maxSecondsLimit - fineStep) {
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
        let adjusted = TimeRangeAdjuster.adjustForMinChange(
            currentMinSeconds: minValue,
            currentMaxSeconds: maxValue,
            newMinSeconds: Swift.max(0, newVal),
            maxSecondsLimit: maxSecondsLimit
        )
        onRangeChange(adjusted.min, adjusted.max)
    }

    private func adjustMax(by delta: Int) {
        adjustMax(to: maxValue + delta)
    }

    private func adjustMax(to newVal: Int) {
        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: minValue,
            currentMaxSeconds: maxValue,
            newMaxSeconds: Swift.max(30, newVal),
            maxSecondsLimit: maxSecondsLimit
        )
        onRangeChange(adjusted.min, adjusted.max)
    }
}

private struct NudgeButton: View {
    let icon: String
    let enabled: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(enabled ? .accentPrimary : .textMuted)
        }
        .disabled(!enabled)
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
