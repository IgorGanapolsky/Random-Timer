from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

ANDROID_TIMER_CONFIG = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt"
ANDROID_PAYWALL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/PaywallSheet.kt"
ANDROID_SETUP = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
ANDROID_VIEWMODEL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/viewmodel/TimerViewModel.kt"
ANDROID_SOUND_PREVIEW = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/SoundPreviewManager.kt"
ANDROID_SOUND_PREVIEW_IMPL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/SoundPreviewManagerImpl.kt"
ANDROID_NAV = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/navigation/Navigation.kt"
ANDROID_PRO_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/billing/ProManager.kt"
ANDROID_ACTIVE_SCREEN = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/ActiveTimerScreen.kt"
ANDROID_VOICE_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt"
ANDROID_REPOSITORY = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/repository/TimerRepositoryImpl.kt"

IOS_TIMER_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"
IOS_PRO_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/ProManager.swift"
IOS_PAYWALL = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/PaywallSheet.swift"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_TIMER_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/TimerManager.swift"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"
IOS_ACTIVE_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/ActiveTimerScreen.swift"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _android_paywall_em_dash_normalized(source: str) -> str:
    """Kotlin may use ASCII ``\\u2014`` escapes; Swift sources typically use literal em dashes."""
    return source.replace("\\u2014", "\u2014")


def test_default_timer_range_is_5_to_30_on_both_platforms():
    """Activation-first default range in TimerConfig.DEFAULT / Swift defaults (free-tier cap remains 300s)."""
    android_source = _read(ANDROID_TIMER_CONFIG)
    android_range_adjuster = _read(ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimeRangeAdjuster.kt")
    ios_source = _read(IOS_TIMER_MODELS)

    assert "const val DEFAULT_MIN_SECONDS = 5" in android_range_adjuster
    assert "minSeconds = TimeRangeAdjuster.DEFAULT_MIN_SECONDS" in android_source
    assert re.search(r"maxSeconds\s*=\s*30", android_source)
    assert "public static let minimumFloorSeconds = 5" in ios_source
    assert re.search(r"minSeconds:\s*Int\s*=\s*minimumFloorSeconds", ios_source)
    assert re.search(r"maxSeconds:\s*Int\s*=\s*30", ios_source)


def test_time_range_limits_and_gap_match_between_platforms():
    android_source = _read(ANDROID_TIMER_CONFIG)
    ios_source = _read(IOS_TIMER_MODELS)

    assert "MAX_SECONDS_PRO = 3600" in android_source
    assert "maxSecondsPro = 3600" in ios_source
    assert "defaultMaxSecondsLimit = TimerConfig.maxSecondsFree" in ios_source
    assert "defaultMinGapSeconds = 5" in ios_source


def test_paywall_hidden_unlock_is_on_title_and_unlocks_pro_not_elite():
    android_source = _read(ANDROID_PAYWALL)
    ios_paywall = _read(IOS_PAYWALL)

    assert "Stop Training With the Brakes On" in android_source and "holdForHiddenUnlock" in android_source
    assert "8_000L" in android_source
    assert "Stop Training With the Brakes On" in ios_paywall and "highPriorityGesture" in ios_paywall
    assert "LongPressGesture(minimumDuration: Self.hiddenUnlockHoldDuration" in ios_paywall
    assert "triggerDebugUnlock()" in ios_paywall
    assert "unlockProForDebug" in ios_paywall


def test_paywall_single_offer_parity():
    """Enforce outcome-focused paywall copy and plan parity on both platforms."""
    android_paywall = _read(ANDROID_PAYWALL)
    ios_paywall = _read(IOS_PAYWALL)

    assert "Elite Tactical" not in android_paywall
    assert "Stop Training With the Brakes On" in android_paywall
    assert "Stop Training With the Brakes On" in ios_paywall
    assert "Go unlimited" in android_paywall
    assert "Go unlimited" in ios_paywall
    assert "Cancel anytime" in android_paywall
    assert "Start Monthly" in android_paywall
    assert "Start Annual" in android_paywall
    assert "Start Monthly" in ios_paywall
    assert "Start Annual" in ios_paywall
    assert "Unlock Lifetime" in ios_paywall


def test_ios_paywall_uses_scrollable_large_presentation_to_avoid_clipped_actions():
    android_paywall = _read(ANDROID_PAYWALL)
    ios_paywall = _read(IOS_PAYWALL)
    ios_setup = _read(IOS_SETUP)

    assert "skipPartiallyExpanded = true" in android_paywall
    assert "ScrollView" in ios_paywall
    assert ".scrollIndicators(.hidden)" in ios_paywall
    assert ".presentationDetents([.large])" in ios_setup


def test_paywall_sticky_chrome_keeps_primary_cta_outside_scroll():
    """Sticky footer must hold CTA + restore + legal links so long content cannot strand the purchase path."""
    android_paywall = _read(ANDROID_PAYWALL)
    ios_paywall = _read(IOS_PAYWALL)

    assert "Scaffold(" in android_paywall
    assert "bottomBar = {" in android_paywall
    assert ".verticalScroll(" in android_paywall
    assert android_paywall.index("bottomBar = {") < android_paywall.index("PrimaryButton(")
    assert "ModalBottomSheet(" in android_paywall
    for label in ("Restore purchase", "Privacy Policy", "Start Monthly", "Start Annual"):
        assert label in android_paywall

    assert "paywallStickyChrome" in ios_paywall
    body_start = ios_paywall.find("var body: some View")
    assert body_start != -1
    body_region = ios_paywall[body_start:]
    scroll_at = body_region.find("ScrollView")
    chrome_at = body_region.find("paywallStickyChrome")
    assert scroll_at != -1 and chrome_at != -1 and scroll_at < chrome_at
    assert "PrimaryButton(title: ctaButtonTitle)" in ios_paywall
    for label in ("Restore purchase", "Privacy Policy", "Terms of Use (EULA)", "Start Monthly", "Start Annual"):
        assert label in ios_paywall


def test_voice_callouts_present_on_both_platforms():
    android_setup = _read(ANDROID_SETUP)
    ios_setup = _read(IOS_SETUP)
    android_timer_config = _read(ANDROID_TIMER_CONFIG)
    ios_timer_models = _read(IOS_TIMER_MODELS)

    assert "Voice Callouts" in android_setup or "AI Voice Callouts" in android_setup
    assert "Voice Callouts" in ios_setup or "AI Voice Callouts" in ios_setup
    assert "Time checks and command cues that keep you sharp under pressure" in android_setup
    assert "Time checks and command cues that keep you sharp under pressure" in ios_setup
    assert "VoiceGender.entries.forEach" in android_setup
    assert 'text = "PREVIEW"' in android_setup
    assert 'if (config.voiceEnabled || !isPro)' in android_setup
    assert android_setup.index('text = "PREVIEW"') < android_setup.index("VoiceGender.entries.forEach")
    assert 'if (gender == VoiceGender.MALE)' in android_setup
    assert '.accessibilityLabel("Preview Voice Callouts")' in ios_setup
    assert '.accessibilityLabel("Unlock Voice Callouts")' in ios_setup

    assert "voiceEnabled" in android_timer_config
    assert "voiceEnabled" in ios_timer_models


def test_voice_callouts_use_toggle_when_pro_and_runtime_respects_setting():
    android_setup = _read(ANDROID_SETUP)
    android_service = _read(ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/TimerForegroundService.kt")
    ios_setup = _read(IOS_SETUP)
    ios_timer_manager = _read(IOS_TIMER_MANAGER)

    assert "checked = config.voiceEnabled" in android_setup
    assert "updateConfig(voiceEnabled = " in android_setup
    assert "voiceEnabled" in android_service

    assert "config.voiceEnabled" in ios_setup
    assert "updateConfig(voiceEnabled:" in ios_setup
    assert "voiceEnabled" in ios_timer_manager


def test_voice_preview_supports_command_cues_on_both_platforms():
    android_preview = _read(ANDROID_SOUND_PREVIEW)
    android_preview_impl = _read(ANDROID_SOUND_PREVIEW_IMPL)
    android_viewmodel = _read(ANDROID_VIEWMODEL)
    android_nav = _read(ANDROID_NAV)
    ios_timer_manager = _read(IOS_TIMER_MANAGER)
    ios_voice_service = _read(IOS_VOICE_SERVICE)

    assert "fun previewCommandCue(gender: VoiceGender)" in android_preview
    assert "previewCommandCue(gender)" in android_preview_impl
    assert "fun previewCommandCue(gender: VoiceGender)" in android_viewmodel
    assert "onCommandCuePreview = viewModel::previewCommandCue" in android_nav

    assert "func previewCommandCue()" in ios_timer_manager
    assert "func previewCommandCue(gender: VoiceGender" in ios_voice_service


def test_android_persists_voice_gender_selection_like_ios():
    android_repository = _read(ANDROID_REPOSITORY)
    android_timer_config = _read(ANDROID_TIMER_CONFIG)
    ios_timer_models = _read(IOS_TIMER_MODELS)

    assert 'val voiceGender: VoiceGender = VoiceGender.MALE' in android_timer_config
    assert 'case male' in ios_timer_models and 'case female' in ios_timer_models
    assert 'private val KEY_VOICE_GENDER = stringPreferencesKey("voice_gender")' in android_repository
    assert 'preferences[KEY_VOICE_GENDER] = config.voiceGender.name' in android_repository
    assert 'VoiceGender.valueOf(it)' in android_repository


def test_android_repeat_loop_uses_distinct_paywall_gate_identifier():
    android_setup = _read(ANDROID_SETUP)
    repeat_loop_block = android_setup.split("text = repeatLoopDetailTitle(isPro = isPro)", 1)[1].split(
        'text = "Sound Arsenal"',
        1,
    )[0]

    assert 'onUpgradeTap("repeat_loop")' in repeat_loop_block
    assert 'onUpgradeTap("pro_sounds")' not in repeat_loop_block


def test_sound_arsenal_copy_and_purchase_path_are_normalized_for_pro():
    android_setup = _read(ANDROID_SETUP)
    android_paywall = _read(ANDROID_PAYWALL)
    android_nav = _read(ANDROID_NAV)
    android_pro_manager = _read(ANDROID_PRO_MANAGER)
    ios_setup = _read(IOS_SETUP)
    ios_paywall = _read(IOS_PAYWALL)

    assert "TACTICAL EXPANSION" not in android_setup
    assert "TACTICAL EXPANSION" not in ios_setup
    assert "Preview Sounds" in android_setup
    assert "Preview Sounds" in ios_setup
    assert 'contentDescription = "Unlock Sound Arsenal"' in android_setup
    assert "Icons.Filled.Lock" in android_setup
    assert '.accessibilityLabel("Unlock Sound Arsenal")' in ios_setup
    android_paywall_norm = _android_paywall_em_dash_normalized(android_paywall)
    for expected in (
        "Full-length sessions — up to 60 minutes, no cutoffs",
        "Live voice callouts keep you sharp under pressure",
        "Loop drills with round limits — just like competition",
        "Full sound arsenal — real bells, horns, and sirens",
        "Verified audio drops when new packs are ready",
    ):
        assert expected in android_paywall_norm
        assert expected in ios_paywall

    assert "const val PRO_PRODUCT_ID = ELITE_PRODUCT_ID" in android_pro_manager
    assert "suspend fun getFormattedProPrice()" in android_pro_manager or "getFormattedPrice" in android_pro_manager
    assert "suspend fun launchProPurchase(" in android_pro_manager
    assert "getFormattedPrice" in android_nav or "proPrice" in android_nav
    assert "launchPurchase(it, productID, paywallEntryPoint)" in android_nav


def test_free_sound_arsenal_taps_preview_without_forcing_ios_paywall():
    ios_setup = _read(IOS_SETUP)
    assert "timerManager.previewSound(type: sound)" in ios_setup
    assert "timerManager.previewSound(type: sound2)" in ios_setup
    assert (
        "timerManager.previewSound(type: sound)\n"
        "                                                presentPaywall(entryPoint: .soundGate)"
    ) not in ios_setup
    assert (
        "timerManager.previewSound(type: sound2)\n"
        "                                                    presentPaywall(entryPoint: .soundGate)"
    ) not in ios_setup


def test_android_elapsed_voice_cues_fire_on_configured_marks_and_commands_start_early():
    android_voice_manager = _read(ANDROID_VOICE_MANAGER)

    assert "runtimeVoiceCueForElapsedMark(elapsedSeconds, lastElapsedMilestone, catalog)?.let {" in android_voice_manager
    assert "else -> 15" in android_voice_manager
    assert "nextCommandCueAt = elapsedSeconds + 30" in android_voice_manager


def test_active_timer_loop_badge_shows_round_progress_on_both_platforms():
    android_active = _read(ANDROID_ACTIVE_SCREEN)
    ios_active = _read(IOS_ACTIVE_SCREEN)

    assert "repeatRounds" in android_active
    assert "roundCount" in android_active
    assert 'return "Infinite Loop"' in android_active
    assert 'return "Loop On · Round $clampedRound/$repeatRounds"' in android_active

    assert "repeatRounds" in ios_active
    assert "roundCount" in ios_active
    assert 'guard enabled else { return "Loop Off" }' in ios_active
    assert 'guard repeatRounds > 0 else { return "Infinite Loop" }' in ios_active
    assert 'return "Loop On · Round \\(clampedRound)/\\(repeatRounds)"' in ios_active


def test_active_timer_voice_badge_is_visible_and_live_toggleable_on_both_platforms():
    android_active = _read(ANDROID_ACTIVE_SCREEN)
    android_nav = _read(ANDROID_NAV)
    android_viewmodel = _read(ANDROID_VIEWMODEL)
    android_service = _read(
        ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/TimerForegroundService.kt"
    )
    android_controller = _read(
        ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/TimerServiceController.kt"
    )
    ios_active = _read(IOS_ACTIVE_SCREEN)
    ios_timer_manager = _read(IOS_TIMER_MANAGER)

    assert 'voiceBadgeText(enabled: Bool)' in ios_active
    assert 'Label(' in ios_active and 'systemImage: "waveform"' in ios_active
    assert 'updateConfig(voiceEnabled: !isEnabled)' in ios_active
    assert 'timerManager.updateConfig(newConfig)' in ios_active
    assert 'voiceEnabled: voiceEnabled ?? current.voiceEnabled' in ios_active
    assert "if var state = timerState" in ios_timer_manager

    assert "internal fun voiceBadgeText(enabled: Boolean)" in android_active
    assert "VoiceBadge(" in android_active
    assert "onVoiceToggle: (Boolean) -> Unit" in android_active
    assert "onVoiceToggle = viewModel::updateVoiceSetting" in android_nav
    assert "fun updateVoiceSetting(enabled: Boolean)" in android_viewmodel
    assert '"voice_callouts_enabled" to updatedConfig.voiceEnabled' in android_viewmodel
    assert "fun updateVoiceEnabled(enabled: Boolean)" in android_controller
    assert "ACTION_UPDATE_VOICE" in android_service
    assert "updateVoiceSetting(voiceEnabled)" in android_service


def test_android_setup_screen_has_single_start_timer_cta_and_clear_free_loop_copy():
    android_setup = _read(ANDROID_SETUP)

    start_cta_count = len(re.findall(r'PrimaryButton\(\s*text\s*=\s*"Start Timer"', android_setup, re.MULTILINE))
    assert start_cta_count == 1, "Android setup screen should expose exactly one Start Timer CTA"
    assert 'repeatLoopDetailTitle(isPro = isPro)' in android_setup
    assert 'repeatLoopDetailSummary(' in android_setup
    assert 'Infinite Loop (Pro: set 1–100 rounds)' in android_setup
    assert ".navigationBarsPadding()" in android_setup


def test_ios_setup_screen_keeps_start_timer_in_sticky_bottom_inset():
    ios_setup = _read(IOS_SETUP)

    assert ".safeAreaInset(edge: .bottom)" in ios_setup
    assert 'PrimaryButton(title: "Start Timer")' in ios_setup
    assert "Spacer(minLength: 140)" in ios_setup


def test_repeat_loop_detail_copy_matches_android_on_both_platforms():
    android_setup = _read(ANDROID_SETUP)
    ios_setup = _read(IOS_SETUP)

    assert 'repeatLoopDetailTitle(isPro = isPro)' in android_setup
    assert 'repeatLoopDetailSummary(' in android_setup
    assert 'internal fun repeatLoopDetailTitle(isPro: Boolean): String = "Round Selection"' in android_setup
    assert 'repeatLoopDetailSummary(' in android_setup
    assert '!isPro -> "Infinite Loop (Pro: set 1–100 rounds)"' in android_setup

    assert 'repeatLoopDetailTitle(isPro: proManager.isPro)' in ios_setup
    assert re.search(
        r"repeatLoopDetailSummary\(\s*isPro:\s*proManager\.isPro,\s*repeatRounds:\s*config\.repeatRounds\s*\)",
        ios_setup,
    )
    assert 'private func repeatLoopDetailTitle(isPro: Bool) -> String' in ios_setup
    assert 'return "Round Selection"' in ios_setup
    assert 'private func repeatLoopDetailSummary(isPro: Bool, repeatRounds: Int) -> String' in ios_setup
    assert 'return "Infinite Loop (Pro: set 1–100 rounds)"' in ios_setup


def test_setup_screen_pro_range_toggle_and_voice_gating_are_present_on_both_platforms():
    android_setup = _read(ANDROID_SETUP)
    ios_setup = _read(IOS_SETUP)

    assert 'text = if (config.useExtendedRange) "1H" else "5m"' in android_setup
    assert "config.useExtendedRange" in android_setup
    assert 'text = "PRO: 1H' in android_setup
    assert 'text = "PREVIEW"' in android_setup

    assert 'Text(config.useExtendedRange ? "1H" : "5m")' in ios_setup
    assert "config.useExtendedRange ? proManager.maxSecondsLimit : 300" in ios_setup
    assert "timerManager.updateConfig(newConfig.clamped(isPro: proManager.isPro))" in ios_setup
    assert 'Text("PRO: 1H' in ios_setup
    assert 'if !proManager.isPro' in ios_setup
    assert 'Text("PREVIEW")' in ios_setup
