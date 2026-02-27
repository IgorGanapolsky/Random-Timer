import SwiftUI

struct TimerSetupScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @EnvironmentObject var proManager: ProManager
    @State private var showPaywall = false
    @State private var paywallEntryPoint: PaywallEntryPoint = .unknown
    @State private var showArsenal = false
    @State private var showDirectEntry = false
    @State private var directEntryIsMin = true
    @AppStorage("hasCompletedFirstTimer") private var hasCompletedFirstTimer = false

    private var config: TimerConfig { timerManager.config }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
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
                            if !proManager.isPro {
                                Spacer()
                                Text("PRO: 1H \u{1F512}")
                                    .font(.caption2)
                                    .foregroundColor(.accentPrimary)
                                    .onTapGesture { presentPaywall(entryPoint: .rangeGate) }
                                    .onLongPressGesture(minimumDuration: 3.0) { proManager.forcePro() }
                            }
                        }
                        Spacer().frame(height: 12)
                        TimeRangeScrubber(
                            minValue: config.minSeconds,
                            maxValue: config.maxSeconds,
                            maxLimit: proManager.maxSecondsLimit,
                            onRangeChange: { min, max in updateConfig(minSeconds: min, maxSeconds: max) },
                            onLabelTap: { isMin in directEntryIsMin = isMin; showDirectEntry = true }
                        )
                    }
                }

                // 2. Alarm Setup
                GlassCard {
                    VStack(alignment: .leading) {
                        Label("Alarm Setup", systemImage: "bell.fill").font(.headline).fontWeight(.semibold)
                        Spacer().frame(height: 12)
                        HStack(spacing: 8) {
                            ForEach(TimerConfig.alarmDurationOptions, id: \.self) { d in
                                DurationChip(duration: d, selected: config.alarmDuration == d) { updateConfig(alarmDuration: d) }
                            }
                        }
                        Spacer().frame(height: 20)
                        HStack(spacing: 12) {
                            SoundTypeButton(label: "Intense", systemImage: "flame.fill", selected: config.soundType == .intense) {
                                updateConfig(soundType: .intense); timerManager.previewSound()
                            }
                            SoundTypeButton(label: "Gentle", systemImage: "drop.fill", selected: config.soundType == .gentle) {
                                updateConfig(soundType: .gentle); timerManager.previewSound()
                            }
                        }
                        Spacer().frame(height: 20)
                        VolumeSliderView(value: config.volume) { updateConfig(volume: $0); timerManager.previewVolume() }
                        Toggle("Vibration", isOn: Binding(get: { config.vibrationEnabled }, set: { updateConfig(vibrationEnabled: $0) })).tint(.accentPrimary)
                    }
                }

                PrimaryButton(title: "Start Timer") { Task { await timerManager.startTimer() } }
                    .scaleEffect(1.02).padding(.vertical, 8)

                // Tactical Expansion
                HStack {
                    Text("TACTICAL EXPANSION").font(.caption2).fontWeight(.bold).foregroundColor(proManager.isPro ? .accentPrimary : .textMuted)
                        .onLongPressGesture(minimumDuration: 3.0) { proManager.forcePro() }
                }
            }
            .padding(.horizontal, 24)
        }
        .background(Color.backgroundDark.ignoresSafeArea())
        .sheet(isPresented: $showPaywall) { PaywallSheet(entryPoint: paywallEntryPoint).environmentObject(proManager) }
        .sheet(isPresented: $showDirectEntry) { DirectEntrySheet(isMin: directEntryIsMin, currentSeconds: directEntryIsMin ? config.minSeconds : config.maxSeconds, maxLimit: proManager.maxSecondsLimit) { updateConfig(minSeconds: directEntryIsMin ? $0 : config.minSeconds, maxSeconds: directEntryIsMin ? config.maxSeconds : $0); showDirectEntry = false } }
    }

    private func updateConfig(minSeconds: Int? = nil, maxSeconds: Int? = nil, alarmDuration: Int? = nil, soundType: SoundType? = nil, volume: Float? = nil, vibrationEnabled: Bool? = nil) {
        let newConfig = TimerConfig(
            minSeconds: minSeconds ?? config.minSeconds,
            maxSeconds: maxSeconds ?? config.maxSeconds,
            alarmDuration: alarmDuration ?? config.alarmDuration,
            hiddenMode: config.hiddenMode,
            repeatEnabled: config.repeatEnabled,
            soundType: soundType ?? config.soundType,
            volume: volume ?? config.volume,
            vibrationEnabled: vibrationEnabled ?? config.vibrationEnabled
        )
        timerManager.updateConfig(newConfig)
    }

    private func presentPaywall(entryPoint: PaywallEntryPoint) { paywallEntryPoint = entryPoint; showPaywall = true }
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
                Slider(value: Binding(get: { Double(minValue) }, set: { onRangeChange(Int($0), maxValue) }), in: 0...Double(maxValue - 30), step: 5).tint(.accentPrimary)
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
