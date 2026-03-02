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
            contentLayout
        }
        .background(Color.backgroundDark.ignoresSafeArea())
        .sheet(isPresented: $showPaywall) { PaywallSheet(entryPoint: paywallEntryPoint).environmentObject(proManager) }
        .sheet(isPresented: $showDirectEntry) { DirectEntrySheet(isMin: directEntryIsMin, currentSeconds: directEntryIsMin ? config.minSeconds : config.maxSeconds, maxLimit: proManager.maxSecondsLimit) { updateConfig(minSeconds: directEntryIsMin ? $0 : config.minSeconds, maxSeconds: directEntryIsMin ? config.maxSeconds : $0); showDirectEntry = false } }
    }

    private var contentLayout: some View {
        VStack(alignment: .leading, spacing: 20) {
            missionHeader
            standardOpsCard
            tacticalExpansionCard
            aiCoachCard
            signalHeader
            alarmSetupCard
            startButton
            arsenalCard
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

                if isExpanded && !isLocked {
                    VStack(spacing: 16) {
                        TimeRangeScrubber(minValue: minValue, maxValue: maxValue, maxLimit: maxLimit, onRangeChange: onRangeChange, onLabelTap: onLabelTap)
                    }
                    .padding(.top, 16)
                }
            }
        }
    }
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
            VStack(spacing: 0) {
                Slider(value: Binding(get: { Double(minValue) }, set: { onRangeChange(Int($0), maxValue) }), in: 0...Double(Swift.min(maxValue - 30, maxLimit - 30)), step: 5).tint(.accentPrimary)
                Slider(value: Binding(get: { Double(maxValue) }, set: { onRangeChange(minValue, Int($0)) }), in: Double(minValue + 30)...Double(maxLimit), step: 5).tint(.accentPrimary)
            }
        }
    }
}

private struct TimeChip: View {
    let label: String; let value: String; let onClick: () -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label).font(.caption2).foregroundColor(.textMuted)
            Button(action: onClick) {
                Text(value).font(.title3).fontWeight(.bold).foregroundColor(.textPrimary)
                    .padding(.horizontal, 12).padding(.vertical, 6)
                    .background(Color.glassBackground).cornerRadius(8).overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.glassBorder, lineWidth: 1))
            }
        }
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
