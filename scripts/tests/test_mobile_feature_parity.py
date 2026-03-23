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

IOS_TIMER_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"
IOS_PRO_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/ProManager.swift"
IOS_PAYWALL = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/PaywallSheet.swift"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_TIMER_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/TimerManager.swift"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"
IOS_ACTIVE_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/ActiveTimerScreen.swift"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_default_timer_range_is_zero_to_300_on_both_platforms():
    android_source = _read(ANDROID_TIMER_CONFIG)
    ios_source = _read(IOS_TIMER_MODELS)

    assert re.search(r"minSeconds\s*=\s*0", android_source)
    assert re.search(r"maxSeconds\s*=\s*300", android_source)
    assert re.search(r"minSeconds:\s*Int\s*=\s*0", ios_source)
    assert re.search(r"maxSeconds:\s*Int\s*=\s*300", ios_source)


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
    ios_pro_manager = _read(IOS_PRO_MANAGER)

    assert "Upgrade to Pro" in android_source and "holdForHiddenUnlock" in android_source
    assert "Upgrade to Pro" in ios_paywall and "onLongPressGesture" in ios_paywall and "8.0" in ios_paywall
    assert "unlockProForDebug" in ios_paywall


def test_paywall_single_offer_parity():
    """Enforce one visible premium offer on both platforms (monetization-roadmap)."""
    android_paywall = _read(ANDROID_PAYWALL)
    ios_paywall = _read(IOS_PAYWALL)

    assert "Elite Tactical" not in android_paywall, (
        "Android paywall must not show Elite Tactical; single-offer only per monetization roadmap"
    )
    assert "One premium plan" in android_paywall
    assert "One premium plan" in ios_paywall
    assert "Yearly auto-renewing subscription" in android_paywall
    assert "Yearly auto-renewing subscription" in ios_paywall


def test_voice_callouts_present_on_both_platforms():
    android_setup = _read(ANDROID_SETUP)
    ios_setup = _read(IOS_SETUP)
    android_timer_config = _read(ANDROID_TIMER_CONFIG)
    ios_timer_models = _read(IOS_TIMER_MODELS)

    for source in (android_setup, ios_setup):
        assert "Voice Callouts" in source or "AI Voice Callouts" in source
        assert "elapsed" in source.lower()

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

    assert "fun previewCommandCue()" in android_preview
    assert "previewCommandCue()" in android_preview_impl
    assert "fun previewCommandCue()" in android_viewmodel
    assert "onCommandCuePreview = viewModel::previewCommandCue" in android_nav

    assert "func previewCommandCue()" in ios_timer_manager
    assert "func previewCommandCue()" in ios_voice_service


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
    assert "10 alarm sounds" in android_paywall
    assert "Loop with optional round limits" in android_paywall
    assert "Loop with optional round limits" in ios_paywall
    assert "Monthly voice callout and sound arsenal refreshes" in android_paywall
    assert "Monthly voice callout and sound arsenal refreshes" in ios_paywall

    assert "const val PRO_PRODUCT_ID = ELITE_PRODUCT_ID" in android_pro_manager
    assert "suspend fun getFormattedProPrice()" in android_pro_manager or "getFormattedPrice" in android_pro_manager
    assert "suspend fun launchProPurchase(" in android_pro_manager
    assert "getFormattedPrice" in android_nav or "proPrice" in android_nav
    assert "launchProPurchase" in android_nav


def test_android_elapsed_voice_cues_short_circuit_before_command_cues():
    android_voice_manager = _read(ANDROID_VOICE_MANAGER)

    assert "runtimeVoiceCueForElapsedSecond(elapsedSeconds, lastElapsedMilestone, catalog)?.let {" in android_voice_manager
    assert re.search(r"lastElapsedMilestone = elapsedSeconds\s+return", android_voice_manager)


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
    assert 'Text("PREVIEW")' in ios_setup
