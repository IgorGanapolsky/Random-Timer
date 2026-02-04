import SwiftUI

/// Initial screen for configuring and starting a timer
struct TimerSetupScreen: View {
    @EnvironmentObject var timerManager: TimerManager

    // Read directly from timerManager.config to avoid animation issues
    private var config: TimerConfig { timerManager.config }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Spacer().frame(height: 8)

                // Time Range Card
                GlassCard {
                    VStack(alignment: .leading) {
                        Text("⏱️ Goes Off In This Range")
                            .font(.headline)
                            .fontWeight(.semibold)
                            .foregroundColor(.textPrimary)

                        Spacer().frame(height: 16)

                        TimeRangeSliders(
                            minValue: config.minSeconds,
                            maxValue: config.maxSeconds,
                            onMinChange: { newMin in
                                updateConfig(minSeconds: newMin)
                            },
                            onMaxChange: { newMax in
                                updateConfig(maxSeconds: newMax)
                            }
                        )
                    }
                }

                // Alarm Settings Card
                GlassCard {
                    VStack(alignment: .leading) {
                        Text("🔔 Alarm Sound Duration")
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

                        // Sound Type
                        Text("SOUND")
                            .font(.caption2)
                            .foregroundColor(.textMuted)
                            .padding(.bottom, 8)

                        HStack(spacing: 12) {
                            SoundTypeButton(
                                label: "💪 Intense",
                                selected: config.soundType == .intense,
                                onTap: {
                                    updateConfig(soundType: .intense)
                                    timerManager.previewSound()
                                }
                            )
                            SoundTypeButton(
                                label: "🌸 Gentle",
                                selected: config.soundType == .gentle,
                                onTap: {
                                    updateConfig(soundType: .gentle)
                                    timerManager.previewSound()
                                }
                            )
                        }

                        Spacer().frame(height: 16)

                        // Volume Slider
                        VolumeSliderView(
                            value: config.volume,
                            onChanged: { newVolume in
                                updateConfig(volume: newVolume)
                            },
                            onSliding: { newVolume in
                                updateConfig(volume: newVolume)
                                timerManager.updatePreviewVolume()
                            },
                            emoji: "🔊"
                        )

                        Spacer().frame(height: 16)

                        // Vibration Toggle
                        HStack {
                            Text("📳 Vibration")
                                .font(.subheadline)
                                .foregroundColor(.textSecondary)

                            Spacer()

                            Toggle("", isOn: Binding(
                                get: { config.vibrationEnabled },
                                set: { updateConfig(vibrationEnabled: $0) }
                            ))
                            .tint(.accentPrimary)
                            .labelsHidden()
                        }
                        .transaction { $0.animation = nil }
                    }
                }

                Spacer(minLength: 32)

                // Start Button
                PrimaryButton(title: "Start Timer") {
                    Task {
                        await timerManager.startTimer()
                    }
                }
                .padding(.bottom, 32)
            }
            .padding(.horizontal, 24)
        }
        .background(Color.backgroundDark.ignoresSafeArea())
        .navigationTitle("Random Timer")
        .navigationBarTitleDisplayMode(.inline)
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
}

// MARK: - Time Range Sliders

private struct TimeRangeSliders: View {
    let minValue: Int
    let maxValue: Int
    let onMinChange: (Int) -> Void
    let onMaxChange: (Int) -> Void

    var body: some View {
        VStack {
            // Display
            HStack {
                Spacer()
                Text(TimeInterval(minValue).formattedDuration)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.textPrimary)

                Text(" - ")
                    .font(.title2)
                    .foregroundColor(.textSecondary)

                Text(TimeInterval(maxValue).formattedDuration)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.textPrimary)
                Spacer()
            }

            Spacer().frame(height: 16)

            // Min slider
            Text("Minimum: \(TimeInterval(minValue).formattedDuration)")
                .font(.caption2)
                .foregroundColor(.textMuted)

            Slider(
                value: Binding(
                    get: { Double(minValue) },
                    set: { newVal in
                        let clamped = min(Int(newVal), maxValue - 30)
                        onMinChange(clamped)
                    }
                ),
                in: 0...270,
                step: 5
            )
            .tint(.accentPrimary)

            // Max slider
            Text("Maximum: \(TimeInterval(maxValue).formattedDuration)")
                .font(.caption2)
                .foregroundColor(.textMuted)

            Slider(
                value: Binding(
                    get: { Double(maxValue) },
                    set: { newVal in
                        let clamped = max(Int(newVal), minValue + 30)
                        onMaxChange(clamped)
                    }
                ),
                in: 30...300,
                step: 5
            )
            .tint(.accentPrimary)
        }
        .transaction { $0.animation = nil }
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
    }
}

// MARK: - Sound Type Button

private struct SoundTypeButton: View {
    let label: String
    let selected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            Text(label)
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
    }
}

// MARK: - Volume Slider

private struct VolumeSliderView: View {
    let value: Float
    let onChanged: (Float) -> Void
    var onSliding: ((Float) -> Void)? = nil
    var emoji: String = ""

    var body: some View {
        VStack {
            HStack {
                Text("\(emoji) Volume")
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
    }
}
