import SwiftUI

/// Initial screen for configuring and starting a timer
struct TimerSetupScreen: View {
    @EnvironmentObject var timerManager: TimerManager
    @EnvironmentObject var proManager: ProManager
    @State private var showPaywall = false
    @State private var paywallEntryPoint: PaywallEntryPoint = .unknown
    @State private var showArsenal = true
    @State private var screenAppearedAt: Date?
    @AppStorage("hasCompletedFirstTimer") private var hasCompletedFirstTimer = false
    @AppStorage("timer_range_free_min") private var storedFreeMinSeconds = TimerConfig.minimumFloorSeconds
    @AppStorage("timer_range_free_max") private var storedFreeMaxSeconds = TimerConfig.maxSecondsFree
    @AppStorage("timer_range_extended_min") private var storedExtendedMinSeconds = TimerConfig.minimumFloorSeconds
    @AppStorage("timer_range_extended_max") private var storedExtendedMaxSeconds = TimerConfig.maxSecondsPro

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

                // 1. Timer Range Card
                GlassCard {
                    VStack(alignment: .leading) {
                        HStack {
                            Label("Timer Range", systemImage: "timer")
                                .font(.headline)
                                .fontWeight(.semibold)
                                .foregroundColor(.textPrimary)

                            Spacer()

                            if !proManager.isPro {
                                Text("PRO: 1H \u{1F512}")
                                    .font(.caption2)
                                    .foregroundColor(.accentPrimary)
                                    .onTapGesture {
                                        presentPaywall(entryPoint: .rangeGate)
                                    }
                                    .onLongPressGesture {
                                        proManager.unlockProForDebug()
                                    }
                            } else {
                                Button {
                                    let result = toggleExtendedRange(
                                        current: config,
                                        profiles: currentRangeProfiles
                                    )
                                    applyRangeProfiles(result.profiles)
                                    timerManager.updateConfig(result.config.clamped(isPro: proManager.isPro))
                                } label: {
                                    Text(config.useExtendedRange ? "1H" : "5m")
                                        .font(.caption2.weight(.bold))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(
                                            config.useExtendedRange
                                                ? Color.accentPrimary.opacity(0.2)
                                                : Color.glassBackground
                                        )
                                        .foregroundColor(
                                            config.useExtendedRange ? .accentPrimary : .textSecondary
                                        )
                                        .cornerRadius(6)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 6)
                                                .stroke(
                                                    config.useExtendedRange
                                                        ? Color.accentPrimary
                                                        : Color.glassBorder,
                                                    lineWidth: 1
                                                )
                                        )
                                }
                            }
                        }

                        Text("Each timer picks a random duration in your range \u{2014} stay ready for anything.")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        Spacer().frame(height: 16)

                        TimeRangeSliders(
                            minValue: config.minSeconds,
                            maxValue: config.maxSeconds,
                            maxSecondsLimit: config.useExtendedRange ? proManager.maxSecondsLimit : 300,
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

                                Text("Time checks and command cues that keep you sharp under pressure")
                                    .font(.caption2)
                                    .foregroundColor(.textMuted)
                            }

                            Spacer()

                            HStack(spacing: 8) {
                                if proManager.isPro {
                                    // Pro users see only the voice toggle
                                    Toggle("Voice Enabled", isOn: Binding(
                                        get: { config.voiceEnabled },
                                        set: { updateConfig(voiceEnabled: $0) }
                                    ))
                                    .tint(.accentPrimary)
                                    .labelsHidden()
                                } else {
                                    // Free users see PREVIEW to sell the feature, then PRO lock
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

                                    Button {
                                        presentPaywall(entryPoint: .soundGate, feature: "voice_callouts")
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

                        if config.voiceEnabled || !proManager.isPro {
                            Picker("Voice", selection: Binding(
                                get: { config.voiceGender },
                                set: { newGender in
                                    updateConfig(voiceGender: newGender)
                                    AnalyticsService.shared.track(
                                        AnalyticsEvents.voiceGenderSelected,
                                        properties: [
                                            AnalyticsProperties.gender: newGender.rawValue,
                                        ]
                                    )
                                }
                            )) {
                                Text("Male").tag(VoiceGender.male)
                                Text("Female").tag(VoiceGender.female)
                            }
                            .pickerStyle(.segmented)
                            .padding(.horizontal)
                        }

                        Spacer().frame(height: 20)

                        // Core Sounds
                        HStack(spacing: 12) {
                            SoundTypeButton(
                                label: "Fire Alarm",
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

                // 3. Loop & Rounds (Pro)
                GlassCard {
                    VStack(alignment: .leading, spacing: 16) {
                        HStack {
                            Label("Repeat Loop", systemImage: "repeat")
                                .font(.headline)
                                .fontWeight(.semibold)
                                .foregroundColor(.textPrimary)

                            Spacer()

                            Toggle("Loop Enabled", isOn: Binding(
                                get: { config.repeatEnabled },
                                set: { updateConfig(repeatEnabled: $0) }
                            ))
                            .tint(.accentPrimary)
                            .labelsHidden()
                        }

                        if config.repeatEnabled {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(repeatLoopDetailTitle(isPro: proManager.isPro))
                                        .font(.subheadline)
                                        .fontWeight(.semibold)
                                        .foregroundColor(proManager.isPro ? .textPrimary : .textMuted)

                                    Text(
                                        repeatLoopDetailSummary(
                                            isPro: proManager.isPro,
                                            repeatRounds: config.repeatRounds
                                        )
                                    )
                                        .font(.caption2)
                                        .foregroundColor(.accentPrimary)
                                }

                                Spacer()

                                if proManager.isPro {
                                    Stepper("", value: Binding(
                                        get: { config.repeatRounds },
                                        set: { updateConfig(repeatRounds: $0) }
                                    ), in: 0...100)
                                    .labelsHidden()
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
                            .padding(.top, 8)
                        }
                    }
                }

                // 4. Sound Arsenal
                HStack {
                    Text("SOUND ARSENAL")
                        .font(.caption2)
                        .fontWeight(.bold)
                        .foregroundColor(proManager.isPro ? .textPrimary : .textMuted)

                    if !proManager.isPro {
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
                        .accessibilityLabel("Unlock Sound Arsenal")
                    }

                    Spacer()

                    Button {
                        withAnimation(.spring()) {
                            showArsenal.toggle()
                        }
                    } label: {
                        let label = showArsenal ? "Hide Sound Arsenal"
                            : (proManager.isPro ? "View Sound Arsenal" : "Preview Sounds")
                        Text(label)
                            .font(.caption2)
                            .fontWeight(.bold)
                            .foregroundColor(.accentPrimary)
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
                                                    timerManager.previewSound(type: sound2)
                                                    presentPaywall(entryPoint: .soundGate)
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

                Spacer(minLength: 140)
            }
            .padding(.horizontal, 24)
        }
        .safeAreaInset(edge: .bottom) {
            PrimaryButton(title: "Start Timer") {
                Task {
                    await timerManager.startTimer()
                }
            }
            .scaleEffect(1.02)
            .padding(.horizontal, 24)
            .padding(.vertical, 8)
            .background(Color.backgroundDark)
        }
        .background(Color.backgroundDark, ignoresSafeAreaEdges: .all)
        .navigationTitle("Random Tactical Timer")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showPaywall) {
            PaywallSheet(entryPoint: paywallEntryPoint)
                .environmentObject(proManager)
                .presentationDetents([.large])
                .presentationDragIndicator(.visible)
                .interactiveDismissDisabled(false)
        }
        .onAppear {
            timerManager.applyActivationPresetForFirstCompletionIfNeeded()
            screenAppearedAt = Date()
            AnalyticsService.shared.screen(AnalyticsScreens.timerSetup)
            showArsenal = true
            persistActiveRangeProfile(
                minSeconds: config.minSeconds,
                maxSeconds: config.maxSeconds,
                useExtendedRange: config.useExtendedRange
            )
        }
        .onDisappear {
            if let appearedAt = screenAppearedAt {
                let dwellSeconds = Date().timeIntervalSince(appearedAt)
                AnalyticsService.shared.track(AnalyticsEvents.screenDwellTime, properties: [
                    AnalyticsProperties.screen: "timer_setup",
                    AnalyticsProperties.durationSeconds: round(dwellSeconds * 10) / 10,
                ])
            }
            screenAppearedAt = nil
        }
        .onChange(of: proManager.isPro) { _, isPro in
            if isPro {
                withAnimation(.spring()) {
                    showArsenal = true
                }
            }
        }
    }

    // Helper to update config with specific field changes
    private func updateConfig(
        minSeconds: Int? = nil,
        maxSeconds: Int? = nil,
        alarmDuration: Int? = nil,
        repeatEnabled: Bool? = nil,
        soundType: SoundType? = nil,
        volume: Float? = nil,
        vibrationEnabled: Bool? = nil,
        useExtendedRange: Bool? = nil,
        voiceEnabled: Bool? = nil,
        voiceGender: VoiceGender? = nil,
        repeatRounds: Int? = nil
    ) {
        let newConfig = TimerConfig(
            minSeconds: minSeconds ?? config.minSeconds,
            maxSeconds: maxSeconds ?? config.maxSeconds,
            alarmDuration: alarmDuration ?? config.alarmDuration,
            hiddenMode: false,
            repeatEnabled: repeatEnabled ?? config.repeatEnabled,
            soundType: soundType ?? config.soundType,
            volume: volume ?? config.volume,
            vibrationEnabled: vibrationEnabled ?? config.vibrationEnabled,
            useExtendedRange: useExtendedRange ?? config.useExtendedRange,
            voiceEnabled: voiceEnabled ?? config.voiceEnabled,
            voiceGender: voiceGender ?? config.voiceGender,
            repeatRounds: repeatRounds ?? config.repeatRounds
        )
        let effectiveUseExtendedRange = useExtendedRange ?? config.useExtendedRange
        persistActiveRangeProfile(
            minSeconds: newConfig.minSeconds,
            maxSeconds: newConfig.maxSeconds,
            useExtendedRange: effectiveUseExtendedRange
        )
        timerManager.updateConfig(newConfig.clamped(isPro: proManager.isPro))
    }

    private func repeatLoopDetailTitle(isPro: Bool) -> String {
        return "Round Selection"
    }

    private func repeatLoopDetailSummary(isPro: Bool, repeatRounds: Int) -> String {
        if !isPro {
            return "Infinite Loop (Pro: set 1–100 rounds)"
        }

        return repeatRounds == 0 ? "Infinite Rounds" : "\(repeatRounds) Rounds"
    }

    private func presentPaywall(entryPoint: PaywallEntryPoint, feature: String? = nil) {
        let featureName = feature ?? entryPoint.featureGateName
        AnalyticsService.shared.track(
            AnalyticsEvents.featureGateHit,
            properties: [
                AnalyticsProperties.feature: featureName,
            ]
        )
        paywallEntryPoint = entryPoint
        showPaywall = true
    }

    private var currentRangeProfiles: RangeToggleProfiles {
        RangeToggleProfiles(
            freeMinSeconds: storedFreeMinSeconds,
            freeMaxSeconds: storedFreeMaxSeconds,
            extendedMinSeconds: storedExtendedMinSeconds,
            extendedMaxSeconds: storedExtendedMaxSeconds
        )
    }

    private func applyRangeProfiles(_ profiles: RangeToggleProfiles) {
        storedFreeMinSeconds = profiles.freeMinSeconds
        storedFreeMaxSeconds = profiles.freeMaxSeconds
        storedExtendedMinSeconds = profiles.extendedMinSeconds
        storedExtendedMaxSeconds = profiles.extendedMaxSeconds
    }

    private func persistActiveRangeProfile(
        minSeconds: Int,
        maxSeconds: Int,
        useExtendedRange: Bool
    ) {
        if useExtendedRange {
            let sanitized = sanitizedStoredRange(
                minSeconds: minSeconds,
                maxSeconds: maxSeconds,
                maxSecondsLimit: TimerConfig.maxSecondsPro
            )
            storedExtendedMinSeconds = sanitized.min
            storedExtendedMaxSeconds = sanitized.max
        } else {
            let sanitized = sanitizedStoredRange(
                minSeconds: minSeconds,
                maxSeconds: maxSeconds,
                maxSecondsLimit: TimerConfig.maxSecondsFree
            )
            storedFreeMinSeconds = sanitized.min
            storedFreeMaxSeconds = sanitized.max
        }
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
        Swift.max(TimeRangeAdjuster.defaultMinSecondsLimit, maxValue - minGap)
    }

    private var maxSliderLowerBound: Int {
        Swift.min(maxSecondsLimit, minValue + minGap)
    }

    private var minSliderRange: ClosedRange<Double> {
        let lower = Double(TimeRangeAdjuster.defaultMinSecondsLimit)
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
                            get: {
                                Double(
                                    Swift.min(
                                        Swift.max(minValue, TimeRangeAdjuster.defaultMinSecondsLimit),
                                        minSliderUpperBound
                                    )
                                )
                            },
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
            newMinSeconds: Swift.max(TimeRangeAdjuster.defaultMinSecondsLimit, newValue),
            maxSecondsLimit: maxSecondsLimit
        )
    }

    private func adjustedRangeForMax(newValue: Int) -> (min: Int, max: Int) {
        TimeRangeAdjuster.adjustForMaxChange(
            currentMinSeconds: minValue,
            currentMaxSeconds: maxValue,
            newMaxSeconds: Swift.max(TimeRangeAdjuster.defaultMinSecondsLimit + minGap, newValue),
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
    var onSliding: ((Float) -> Void)?
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
