import SwiftUI

/// Initial screen for configuring and starting a timer
struct TimerSetupScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @State private var showShareSheet = false

    // Read directly from timerManager.config to avoid animation issues
    private var config: TimerConfig { timerManager.config }

    private static let shareMessage = """
        This is the timer I use for random fight drills. \
        It goes off unpredictably so you can't game it. \
        Train for chaos, not comfort.
        https://apps.apple.com/us/app/random-tactical-timer/id6758355312
        """

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Spacer().frame(height: 8)

                // Training Stats
                HStack {
                    Text("Session #\(TrainingStatsService.shared.totalSessions + 1)")
                        .font(.caption)
                        .foregroundColor(.textSecondary)
                    Spacer()
                    if TrainingStatsService.shared.currentStreak > 1 {
                        Label("\(TrainingStatsService.shared.currentStreak) day streak", systemImage: "flame.fill")
                            .font(.caption)
                            .foregroundColor(.accentPrimary)
                    }
                }

                // Time Range Card
                GlassCard {
                    VStack(alignment: .leading) {
                        Label("Goes Off In This Range", systemImage: "timer")
                            .font(.headline)
                            .fontWeight(.semibold)
                            .foregroundColor(.textPrimary)

                        Spacer().frame(height: 16)

                        TimeRangeSliders(
                            minValue: config.minSeconds,
                            maxValue: config.maxSeconds,
                            onRangeChange: { newMin, newMax in
                                updateConfig(minSeconds: newMin, maxSeconds: newMax)
                            }
                        )
                    }
                }

                // Alarm Settings Card
                GlassCard {
                    VStack(alignment: .leading) {
                        Label("Alarm Sound Duration", systemImage: "bell.fill")
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
                                systemImage: "leaf.fill",
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
                                timerManager.previewVolume()
                            },
                            systemImage: "speaker.wave.3.fill"
                        )

                        Spacer().frame(height: 16)

                        // Vibration Toggle
                        HStack {
                            Label("Vibration", systemImage: "iphone.radiowaves.left.and.right")
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
        .navigationTitle("Random Tactical Timer")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    showShareSheet = true
                } label: {
                    Image(systemName: "square.and.arrow.up")
                        .foregroundColor(.accentPrimary)
                }
                .accessibilityLabel("Share app")
            }
        }
        .sheet(isPresented: $showShareSheet) {
            ShareSheet(items: [Self.shareMessage])
        }
        .onAppear {
            AnalyticsService.shared.screen(AnalyticsScreens.timerSetup)
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
}

// MARK: - Time Range Sliders

private struct TimeRangeSliders: View {
    let minValue: Int
    let maxValue: Int
    let onRangeChange: (Int, Int) -> Void

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
                .frame(maxWidth: .infinity, alignment: .center)

            Slider(
                value: Binding(
                    get: { Double(minValue) },
                    set: { newVal in
                        let adjusted = TimeRangeAdjuster.adjustForMinChange(
                            currentMinSeconds: minValue,
                            currentMaxSeconds: maxValue,
                            newMinSeconds: Int(newVal)
                        )
                        onRangeChange(adjusted.min, adjusted.max)
                    }
                ),
                in: 0...270,
                step: 5
            )
            .tint(.accentPrimary)
            .accessibilityIdentifier("minimumTimeSlider")

            // Max slider
            Text("Maximum: \(TimeInterval(maxValue).formattedDuration)")
                .font(.caption2)
                .foregroundColor(.textMuted)
                .frame(maxWidth: .infinity, alignment: .center)

            Slider(
                value: Binding(
                    get: { Double(maxValue) },
                    set: { newVal in
                        let adjusted = TimeRangeAdjuster.adjustForMaxChange(
                            currentMinSeconds: minValue,
                            currentMaxSeconds: maxValue,
                            newMaxSeconds: Int(newVal)
                        )
                        onRangeChange(adjusted.min, adjusted.max)
                    }
                ),
                in: 30...300,
                step: 5
            )
            .tint(.accentPrimary)
            .accessibilityIdentifier("maximumTimeSlider")
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
    }
}
