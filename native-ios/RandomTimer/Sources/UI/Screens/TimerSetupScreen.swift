import SwiftUI

struct TimerSetupScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @EnvironmentObject var proManager: ProManager
    @State private var showPaywall = false
    @State private var paywallEntryPoint: PaywallEntryPoint = .unknown
    @State private var showDirectEntry = false
    @State private var directEntryIsMin = true
    
    @State private var standardExpanded = true
    @State private var tacticalExpanded = false

    private var config: TimerConfig { timerManager.config }

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
        .padding(.horizontal, 24)
    }

    // MARK: - Subviews

    private var missionHeader: some View {
        Text("TRAINING MISSIONS")
            .font(.caption2).fontWeight(.bold).foregroundColor(.textMuted).padding(.top, 16).padding(.leading, 4)
    }

    private var standardOpsCard: some View {
        ExpandableTrainingCard(
            title: "Standard Ops (5m)",
            subtitle: "High-precision tactical drills",
            isExpanded: standardExpanded,
            onExpandToggle: { withAnimation(.spring()) { standardExpanded.toggle(); if standardExpanded { tacticalExpanded = false } } },
            minValue: config.minSeconds,
            maxValue: config.maxSeconds,
            maxLimit: TimerConfig.maxSecondsFree,
            onRangeChange: { min, max in updateConfig(minSeconds: min, maxSeconds: max) },
            onLabelTap: { isMin in directEntryIsMin = isMin; showDirectEntry = true }
        )
    }

    private var tacticalExpansionCard: some View {
        ExpandableTrainingCard(
            title: "Tactical Expansion (1h)",
            subtitle: "Extended endurance & mission duration",
            isExpanded: tacticalExpanded,
            isLocked: !proManager.isPro,
            onExpandToggle: {
                if proManager.isPro {
                    withAnimation(.spring()) { tacticalExpanded.toggle(); if tacticalExpanded { standardExpanded = false } }
                } else { presentPaywall(entryPoint: .rangeGate) }
            },
            minValue: config.minSeconds,
            maxValue: config.maxSeconds,
            maxLimit: TimerConfig.maxSecondsPro,
            onRangeChange: { min, max in updateConfig(minSeconds: min, maxSeconds: max) },
            onLabelTap: { isMin in directEntryIsMin = isMin; showDirectEntry = true },
            onSecretUnlock: { proManager.forcePro() }
        )
    }

    @ViewBuilder
    private var aiCoachCard: some View {
        if proManager.isElite || tacticalExpanded {
            GlassCard {
                VStack(alignment: .leading, spacing: 16) {
                    aiCoachHeader
                    aiCoachToggle
                    if config.eliteConfig.aiCalloutsEnabled {
                        aiCoachFrequencySlider
                    }
                }
            }
        }
    }

    private var aiCoachHeader: some View {
        HStack {
            Label("AI Tactical Coach", systemImage: "brain.head.profile.fill").font(.headline).fontWeight(.semibold)
            Spacer()
            if !proManager.isElite { Image(systemName: "crown.fill").foregroundColor(.accentPrimary) }
        }
    }

    private var aiCoachToggle: some View {
        Toggle("Enable AI Callouts", isOn: Binding(
            get: { config.eliteConfig.aiCalloutsEnabled },
            set: { enabled in
                if proManager.isElite { updateEliteConfig(aiCalloutsEnabled: enabled) }
                else { presentPaywall(entryPoint: .settings) }
            }
        )).tint(.accentPrimary)
    }

    private var aiCoachFrequencySlider: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Callout Frequency: \(Int(config.eliteConfig.calloutFrequency))s").font(.caption).foregroundColor(.textMuted)
            Slider(value: Binding(
                get: { config.eliteConfig.calloutFrequency },
                set: { freq in updateEliteConfig(calloutFrequency: freq) }
            ), in: 3...15, step: 1).tint(.accentPrimary)
        }
    }

    private var signalHeader: some View {
        Text("SIGNAL CONFIGURATION")
            .font(.caption2).fontWeight(.bold).foregroundColor(.textMuted).padding(.leading, 4)
    }

    private var alarmSetupCard: some View {
        GlassCard {
            VStack(alignment: .leading) {
                Label("Signal Output", systemImage: "bell.fill").font(.headline).fontWeight(.semibold)
                Spacer().frame(height: 12)
                HStack(spacing: 8) {
                    ForEach(TimerConfig.alarmDurationOptions, id: \.self) { d in
                        DurationChip(duration: d, selected: config.alarmDuration == d) { updateConfig(alarmDuration: d) }
                    }
                }
                Spacer().frame(height: 20)
                HStack(spacing: 12) {
                    SoundTypeButton(label: "Intense", systemImage: "flame.fill", selected: config.soundType == .intense) { updateConfig(soundType: .intense); timerManager.previewSound() }
                    SoundTypeButton(label: "Gentle", systemImage: "drop.fill", selected: config.soundType == .gentle) { updateConfig(soundType: .gentle); timerManager.previewSound() }
                }
                Spacer().frame(height: 20)
                VolumeSliderView(value: config.volume) { updateConfig(volume: $0); timerManager.previewVolume() }
                Toggle("Vibration", isOn: Binding(get: { config.vibrationEnabled }, set: { updateConfig(vibrationEnabled: $0) })).tint(.accentPrimary)
            }
        }
    }

    private var startButton: some View {
        PrimaryButton(title: "Start Timer") { Task { await timerManager.startTimer() } }
            .scaleEffect(1.02).padding(.vertical, 8)
    }

    @ViewBuilder
    private var arsenalCard: some View {
        if proManager.isPro || tacticalExpanded {
            ProSoundArsenalCard(
                proManager: proManager,
                currentSound: config.soundType,
                onSoundTap: { sound in
                    updateConfig(soundType: sound)
                    timerManager.previewSound()
                    if !proManager.isPro {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                            presentPaywall(entryPoint: .soundGate)
                        }
                    }
                }
            )
        }
    }

    // MARK: - Helper Methods

    private func updateConfig(minSeconds: Int? = nil, maxSeconds: Int? = nil, alarmDuration: Int? = nil, soundType: SoundType? = nil, volume: Float? = nil, vibrationEnabled: Bool? = nil) {
        let newConfig = TimerConfig(
            minSeconds: minSeconds ?? config.minSeconds,
            maxSeconds: maxSeconds ?? config.maxSeconds,
            alarmDuration: alarmDuration ?? config.alarmDuration,
            hiddenMode: config.hiddenMode,
            repeatEnabled: config.repeatEnabled,
            soundType: soundType ?? config.soundType,
            volume: volume ?? config.volume,
            vibrationEnabled: vibrationEnabled ?? config.vibrationEnabled,
            eliteConfig: config.eliteConfig
        )
        timerManager.updateConfig(newConfig)
    }
    
    private func updateEliteConfig(aiCalloutsEnabled: Bool? = nil, calloutFrequency: Double? = nil) {
        var newElite = config.eliteConfig
        if let enabled = aiCalloutsEnabled { newElite.aiCalloutsEnabled = enabled }
        if let freq = calloutFrequency { newElite.calloutFrequency = freq }
        let newConfig = TimerConfig(minSeconds: config.minSeconds, maxSeconds: config.maxSeconds, alarmDuration: config.alarmDuration, hiddenMode: config.hiddenMode, repeatEnabled: config.repeatEnabled, soundType: config.soundType, volume: config.volume, vibrationEnabled: config.vibrationEnabled, eliteConfig: newElite)
        timerManager.updateConfig(newConfig)
    }

    private func presentPaywall(entryPoint: PaywallEntryPoint) { paywallEntryPoint = entryPoint; showPaywall = true }
}

private struct ProSoundArsenalCard: View {
    let proManager: ProManager
    let currentSound: SoundType
    let onSoundTap: (SoundType) -> Void
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading) {
                Label("Sound Arsenal", systemImage: "speaker.wave.3.fill").font(.headline).fontWeight(.semibold)
                Spacer().frame(height: 12)
                let proSounds = SoundType.proSounds
                ForEach(Array(stride(from: 0, to: proSounds.count, by: 2)), id: \.self) { i in
                    HStack(spacing: 12) {
                        ForEach(0..<2) { j in
                            if i + j < proSounds.count {
                                let sound = proSounds[i + j]
                                SoundTypeButton(
                                    label: sound.rawValue.capitalized + (proManager.isPro ? "" : " \u{1F512}"),
                                    systemImage: "waveform",
                                    selected: currentSound == sound,
                                    onTap: { onSoundTap(sound) }
                                ).frame(maxWidth: .infinity)
                            } else { Spacer().frame(maxWidth: .infinity) }
                        }
                    }
                }
            }
        }
    }
}

private struct ExpandableTrainingCard: View {
    let title: String; let subtitle: String; let isExpanded: Bool; var isLocked: Bool = false
    let onExpandToggle: () -> Void; let minValue: Int; let maxValue: Int; let maxLimit: Int
    let onRangeChange: (Int, Int) -> Void; let onLabelTap: (Bool) -> Void
    var onSecretUnlock: (() -> Void)? = nil

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 0) {
                Button(action: onExpandToggle) {
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(title + (isLocked ? " \u{1F512}" : ""))
                                .font(.headline).fontWeight(.bold).foregroundColor(isLocked ? .textMuted : .textPrimary)
                                .onLongPressGesture(minimumDuration: 8.0) { onSecretUnlock?() }
                            Text(subtitle).font(.caption2).foregroundColor(.textMuted)
                        }
                        Spacer()
                        Image(systemName: isExpanded ? "chevron.up" : "chevron.down").foregroundColor(.textMuted)
                    }
                }
                .buttonStyle(PlainButtonStyle())

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

private struct TimeRangeScrubber: View {
    let minValue: Int; let maxValue: Int; var maxLimit: Int
    let onRangeChange: (Int, Int) -> Void; let onLabelTap: (Bool) -> Void
    var body: some View {
        VStack(spacing: 16) {
            HStack {
                TimeChip(label: "Min", value: TimeInterval(minValue).formattedDuration) { onLabelTap(true) }
                Spacer(); Image(systemName: "arrow.right").foregroundColor(.textMuted); Spacer()
                TimeChip(label: "Max", value: TimeInterval(maxValue).formattedDuration) { onLabelTap(false) }
            }

            // Min slider with Nudge buttons
            VStack(spacing: 4) {
                Text("Minimum: \(TimeInterval(minValue).formattedDuration)")
                    .font(.caption2)
                    .foregroundColor(.textMuted)

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

                HStack(spacing: 8) {
                    StepAdjustButton(
                        label: "-5s",
                        enabled: enabled && canAdjustMin(by: -coarseStep),
                        accessibilityLabel: "Decrease minimum by 5 seconds"
                    ) {
                        adjustMin(by: -coarseStep)
                    }

                    StepAdjustButton(
                        label: "-1s",
                        enabled: enabled && canAdjustMin(by: -fineStep),
                        accessibilityLabel: "Decrease minimum by 1 second"
                    ) {
                        adjustMin(by: -fineStep)
                    }

                    Spacer(minLength: 8)

                    StepAdjustButton(
                        label: "+1s",
                        enabled: enabled && canAdjustMin(by: fineStep),
                        accessibilityLabel: "Increase minimum by 1 second"
                    ) {
                        adjustMin(by: fineStep)
                    }

                    StepAdjustButton(
                        label: "+5s",
                        enabled: enabled && canAdjustMin(by: coarseStep),
                        accessibilityLabel: "Increase minimum by 5 seconds"
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

                Slider(
                    value: Binding(
                        get: { Double(Swift.max(Swift.min(maxValue, maxSecondsLimit), maxSliderLowerBound)) },
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

                HStack(spacing: 8) {
                    StepAdjustButton(
                        label: "-5s",
                        enabled: enabled && canAdjustMax(by: -coarseStep),
                        accessibilityLabel: "Decrease maximum by 5 seconds"
                    ) {
                        adjustMax(by: -coarseStep)
                    }

                    StepAdjustButton(
                        label: "-1s",
                        enabled: enabled && canAdjustMax(by: -fineStep),
                        accessibilityLabel: "Decrease maximum by 1 second"
                    ) {
                        adjustMax(by: -fineStep)
                    }

                    Spacer(minLength: 8)

                    StepAdjustButton(
                        label: "+1s",
                        enabled: enabled && canAdjustMax(by: fineStep),
                        accessibilityLabel: "Increase maximum by 1 second"
                    ) {
                        adjustMax(by: fineStep)
                    }

                    StepAdjustButton(
                        label: "+5s",
                        enabled: enabled && canAdjustMax(by: coarseStep),
                        accessibilityLabel: "Increase maximum by 5 seconds"
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
            newMaxSeconds: Swift.max(30, newValue),
            maxSecondsLimit: maxSecondsLimit
        )
    }

    private func applyAdjustedRangeIfChanged(_ adjusted: (min: Int, max: Int)) {
        guard adjusted.min != minValue || adjusted.max != maxValue else { return }
        onRangeChange(adjusted.min, adjusted.max)
    }
}

private struct StepAdjustButton: View {
    let label: String
    let enabled: Bool
    let accessibilityLabel: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(enabled ? .accentPrimary : .textMuted)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(enabled ? Color.accentPrimary.opacity(0.12) : Color.glassBackground)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(enabled ? Color.accentPrimary.opacity(0.6) : Color.glassBorder, lineWidth: 1)
                )
        }
        .disabled(!enabled)
        .accessibilityLabel(accessibilityLabel)
    }
}

private struct DirectEntrySheet: View {
    let isMin: Bool; let currentSeconds: Int; let maxLimit: Int; let onConfirm: (Int) -> Void
    @Environment(\.dismiss) var dismiss
    @State private var minutes: String; @State private var seconds: String
    init(isMin: Bool, currentSeconds: Int, maxLimit: Int, onConfirm: @escaping (Int) -> Void) {
        self.isMin = isMin; self.currentSeconds = currentSeconds; self.maxLimit = maxLimit; self.onConfirm = onConfirm
        _minutes = State(initialValue: String(currentSeconds / 60)); _seconds = State(initialValue: String(currentSeconds % 60))
    }
    var body: some View {
        NavigationView {
            VStack(spacing: 32) {
                Text("Set \(isMin ? "Minimum" : "Maximum") Time").font(.headline)
                HStack(spacing: 16) {
                    TextField("Min", text: $minutes).keyboardType(.numberPad).multilineTextAlignment(.center).font(.system(size: 48, weight: .bold, design: .monospaced)).frame(width: 100, height: 80).background(Color.glassBackground).cornerRadius(12)
                    Text(":").font(.system(size: 48, weight: .bold))
                    TextField("Sec", text: $seconds).keyboardType(.numberPad).multilineTextAlignment(.center).font(.system(size: 48, weight: .bold, design: .monospaced)).frame(width: 100, height: 80).background(Color.glassBackground).cornerRadius(12)
                }
                PrimaryButton(title: "Apply") { onConfirm((Int(minutes) ?? 0) * 60 + (Int(seconds) ?? 0)) }.padding(.horizontal, 40)
                Spacer()
            }.background(Color.backgroundDark.ignoresSafeArea())
            .toolbar { ToolbarItem(placement: .navigationBarLeading) { Button("Cancel") { dismiss() } } }
        }
    }
}

private struct DurationChip: View {
    let duration: Int; let selected: Bool; let onTap: () -> Void
    var body: some View {
        Button(action: onTap) {
            Text("\(duration)s").font(.subheadline).foregroundColor(selected ? .accentPrimary : .textSecondary)
                .padding(.horizontal, 12).padding(.vertical, 8)
                .background(RoundedRectangle(cornerRadius: 8).fill(selected ? Color.accentPrimary.opacity(0.2) : Color.glassBackground))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(selected ? Color.accentPrimary : Color.glassBorder, lineWidth: 1))
        }
    }
}

private struct SoundTypeButton: View {
    let label: String; let systemImage: String; let selected: Bool; let onTap: () -> Void
    var body: some View {
        Button(action: onTap) {
            Label(label, systemImage: systemImage).font(.body).foregroundColor(selected ? .accentPrimary : .textPrimary)
                .padding(16).frame(maxWidth: .infinity)
                .background(RoundedRectangle(cornerRadius: 12).fill(selected ? Color.accentPrimary.opacity(0.15) : Color.glassBackground))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(selected ? Color.accentPrimary : Color.glassBorder, lineWidth: 1))
        }
    }
}

private struct VolumeSliderView: View {
    let value: Float; let onChanged: (Float) -> Void
    var body: some View {
        VStack {
            HStack { Label("Volume", systemImage: "speaker.wave.3.fill"); Spacer(); Text("\(Int(value * 100))%") }
            Slider(value: Binding(get: { Double(value) }, set: { onChanged(Float($0)) }), in: 0...1).tint(.accentPrimary)
        }
    }
}
