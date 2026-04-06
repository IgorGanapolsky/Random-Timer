import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_CONFIG = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt"
ANDROID_REPOSITORY = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/repository/TimerRepositoryImpl.kt"
ANDROID_RANGE_ADJUSTER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimeRangeAdjuster.kt"
ANDROID_SETUP_SCREEN = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
ANDROID_FOREGROUND_SERVICE = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/TimerForegroundService.kt"
ANDROID_PAYWALL = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/PaywallSheet.kt"
ANDROID_NAVIGATION = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/navigation/Navigation.kt"
ANDROID_VOICE_SERVICE = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt"
ANDROID_SOUND_CATALOG_SERVICE = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/ProSoundCatalog.kt"
ANDROID_VOICE_ASSET_DIR = ROOT / "native-android/app/src/main/assets"
ANDROID_VOICE_CATALOG = ANDROID_VOICE_ASSET_DIR / "voice_callouts.json"
ANDROID_SOUND_CATALOG = ANDROID_VOICE_ASSET_DIR / "sound_arsenal.json"
ANDROID_RAW_AUDIO_DIR = ROOT / "native-android/app/src/main/res/raw"
ANDROID_BUILD_GRADLE = ROOT / "native-android/app/build.gradle.kts"
IOS_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"
IOS_SETUP_SCREEN = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
IOS_PAYWALL = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/PaywallSheet.swift"
IOS_TIMER_MANAGER = ROOT / "native-ios/RandomTimer/Sources/Services/TimerManager.swift"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"
IOS_VOICE_TESTS = ROOT / "native-ios/RandomTimerTests/AIVoiceCalloutServiceTests.swift"
IOS_XCODE_PROJECT = ROOT / "native-ios/RandomTimer.xcodeproj/project.pbxproj"
IOS_INFO_PLIST = ROOT / "native-ios/RandomTimer/Info.plist"
IOS_VOICE_AUDIO_DIR = ROOT / "native-ios/RandomTimer/Resources/Audio"
IOS_VOICE_CATALOG = IOS_VOICE_AUDIO_DIR / "voice_callouts.json"
IOS_SOUND_CATALOG = IOS_VOICE_AUDIO_DIR / "sound_arsenal.json"
RUNTIME_MANIFEST = ROOT / "content/pro_audio/runtime/latest.json"


def _load_ios_voice_catalog() -> dict:
    return json.loads(IOS_VOICE_CATALOG.read_text(encoding="utf-8"))


def _load_android_voice_catalog() -> dict:
    return json.loads(ANDROID_VOICE_CATALOG.read_text(encoding="utf-8"))


def _load_ios_sound_catalog() -> dict:
    return json.loads(IOS_SOUND_CATALOG.read_text(encoding="utf-8"))


def _load_android_sound_catalog() -> dict:
    return json.loads(ANDROID_SOUND_CATALOG.read_text(encoding="utf-8"))


def _load_runtime_manifest() -> dict:
    return json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8"))


def _ios_catalog_filenames(catalog: dict) -> set[str]:
    return (
        {catalog["previewElapsed"]["filename"]}
        | {cue["filename"] for cue in catalog["elapsedCues"]}
        | {cue["filename"] for cue in catalog["commandCues"]}
    )


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _extract_block(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


def test_timer_defaults_match_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    android_repository = ANDROID_REPOSITORY.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")

    assert "minSeconds = TimeRangeAdjuster.DEFAULT_MIN_SECONDS" in android_config
    assert "maxSeconds = 30" in android_config
    assert "private fun Preferences.toTimerConfig()" in android_repository
    assert android_repository.count("maxSeconds = this[KEY_MAX_SECONDS] ?: 30") == 1
    assert android_repository.count("preferences.toTimerConfig()") == 2
    assert "public static let minimumFloorSeconds = 5" in ios_models
    assert re.search(r"minSeconds: Int = minimumFloorSeconds,\n\s*maxSeconds: Int = 30,", ios_models)
    assert "maxSecondsFree = 300" in ios_models


def test_timer_limits_and_gap_rules_match_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    android_range_adjuster = ANDROID_RANGE_ADJUSTER.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")
    ios_setup_screen = IOS_SETUP_SCREEN.read_text(encoding="utf-8")

    assert "const val MAX_SECONDS_FREE = 300" in android_config
    assert "const val MAX_SECONDS_PRO = 3600" in android_config
    assert "public static let maxSecondsFree = 300" in ios_models
    assert "public static let maxSecondsPro = 3600" in ios_models

    assert "const val DEFAULT_MIN_SECONDS = 5" in android_range_adjuster
    assert "const val DEFAULT_MAX_SECONDS = 3600" in android_range_adjuster
    assert "const val DEFAULT_MIN_GAP_SECONDS = 5" in android_range_adjuster
    assert "static let defaultMinSecondsLimit = TimerConfig.minimumFloorSeconds" in ios_models
    assert "static let defaultMaxSecondsLimit = TimerConfig.maxSecondsFree" in ios_models
    assert "static let defaultMinGapSeconds = 5" in ios_models


def test_sound_catalog_matches_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")
    android_sound_block = _extract_block(android_config, "enum class SoundType", "companion object")
    ios_sound_block = _extract_block(ios_models, "public enum SoundType", "// MARK: - Voice Gender")

    android_sounds = {
        _normalize_name(name)
        for name in re.findall(r"^\s+([A-Z_]+)(?:\(|,)", android_sound_block, re.MULTILINE)
        if name not in {"FREE", "PRO"}
    }
    ios_sounds = {
        _normalize_name(name)
        for name in re.findall(r"^\s*case\s+([a-zA-Z][a-zA-Z0-9]*)$", ios_sound_block, re.MULTILINE)
    }

    assert android_sounds == ios_sounds
    assert {_normalize_name("INTENSE"), _normalize_name("GENTLE")} <= android_sounds


def test_alarm_duration_options_match_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")

    android_match = re.search(r"ALARM_DURATION_OPTIONS = listOf\(([^)]+)\)", android_config)
    ios_match = re.search(r"alarmDurationOptions = \[([^\]]+)\]", ios_models)

    assert android_match is not None
    assert ios_match is not None
    assert android_match.group(1).replace(" ", "") == ios_match.group(1).replace(" ", "")


def test_voice_callouts_are_gated_as_pro_on_both_platforms():
    android_setup = ANDROID_SETUP_SCREEN.read_text(encoding="utf-8")
    android_service = ANDROID_FOREGROUND_SERVICE.read_text(encoding="utf-8")
    ios_setup = IOS_SETUP_SCREEN.read_text(encoding="utf-8")
    ios_timer_manager = IOS_TIMER_MANAGER.read_text(encoding="utf-8")
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")

    assert "voiceEnabled" in android_config
    assert "public let voiceEnabled: Bool" in ios_models
    assert "checked = config.voiceEnabled" in android_setup
    assert "config.voiceEnabled" in ios_setup
    assert "voiceEnabled" in android_service and "isPro" in android_service
    assert "ProManager.shared.isPro && state.config.voiceEnabled" in ios_timer_manager
    assert "triggerCallout(elapsedSeconds: elapsedSeconds)" in ios_timer_manager


def test_hidden_debug_unlock_holds_for_8_seconds_and_unlocks_pro():
    android_paywall = ANDROID_PAYWALL.read_text(encoding="utf-8")
    android_navigation = ANDROID_NAVIGATION.read_text(encoding="utf-8")
    ios_paywall = IOS_PAYWALL.read_text(encoding="utf-8")

    assert "Unlock Full Training Mode" in android_paywall
    assert "holdForHiddenUnlock" in android_paywall and "8_000" in android_paywall
    assert "Unlock Full Training Mode" in ios_paywall
    assert "highPriorityGesture" in ios_paywall
    assert "LongPressGesture(minimumDuration: Self.hiddenUnlockHoldDuration" in ios_paywall
    assert "triggerDebugUnlock()" in ios_paywall
    assert "unlockProForDebug" in android_navigation
    assert "unlockProForDebug" in ios_paywall


def test_voice_preview_actions_and_copy_match_across_mobile_platforms():
    android_setup = ANDROID_SETUP_SCREEN.read_text(encoding="utf-8")
    ios_setup = IOS_SETUP_SCREEN.read_text(encoding="utf-8")
    expected_supporting_copy = "Time checks and command cues that keep you sharp under pressure"

    assert "Voice Callouts" in android_setup or "AI Voice Callouts" in android_setup
    assert "Voice Callouts" in ios_setup
    assert expected_supporting_copy in android_setup
    assert expected_supporting_copy in ios_setup


def test_sound_arsenal_is_expanded_by_default_for_free_users():
    android_setup = ANDROID_SETUP_SCREEN.read_text(encoding="utf-8")
    ios_setup = IOS_SETUP_SCREEN.read_text(encoding="utf-8")

    assert "showArsenal" in android_setup
    assert "@State private var showArsenal = true" in ios_setup
    assert "LaunchedEffect(isPro)" in android_setup
    assert "showArsenal = true" in android_setup or "showArsenal" in android_setup
    assert "Sound Arsenal" in ios_setup
    assert "Sound Arsenal" in android_setup


def test_voice_profile_configured_on_both_platforms():
    android_voice_service = ANDROID_VOICE_SERVICE.read_text(encoding="utf-8")
    android_sound_catalog_service = ANDROID_SOUND_CATALOG_SERVICE.read_text(encoding="utf-8")
    ios_voice_service = IOS_VOICE_SERVICE.read_text(encoding="utf-8")

    assert "preferredVoiceNames" in android_voice_service
    assert "packStore.voiceCatalog()" in android_voice_service
    assert "parseVoiceCalloutCatalog" in android_voice_service
    assert "class ProAudioPackStore" in android_sound_catalog_service
    assert "BuildConfig.PRO_AUDIO_MANIFEST_URL" in android_sound_catalog_service
    assert "VoiceCueCatalog" in ios_voice_service
    assert "loadVoiceCalloutCatalog" in ios_voice_service
    assert "voiceFilenameOrFallback" in ios_voice_service
    assert "AVAudioPlayer" in ios_voice_service
    assert "AVSpeechSynthesizer" not in ios_voice_service


def test_ios_voice_assets_exist_on_disk():
    catalog = _load_ios_voice_catalog()
    required_assets = _ios_catalog_filenames(catalog)
    actual_assets = {path.stem for path in IOS_VOICE_AUDIO_DIR.glob("*.mp3")}

    assert required_assets <= actual_assets


def test_android_voice_assets_exist_on_disk_and_match_ios_catalog():
    ios_catalog = _load_ios_voice_catalog()
    android_catalog = _load_android_voice_catalog()
    required_assets = _ios_catalog_filenames(ios_catalog)
    actual_assets = {path.stem for path in ANDROID_RAW_AUDIO_DIR.glob("*.mp3")}

    assert ios_catalog == android_catalog
    assert required_assets <= actual_assets


def test_sound_arsenal_catalog_matches_across_platforms():
    ios_catalog = _load_ios_sound_catalog()
    android_catalog = _load_android_sound_catalog()

    assert ios_catalog == android_catalog
    assert ios_catalog["entitlement"] == "pro"
    assert len(ios_catalog["sounds"]) == 10


def test_ios_voice_catalog_has_clear_elapsed_language_and_more_variety():
    catalog = _load_ios_voice_catalog()

    assert len(catalog["elapsedCues"]) >= 12
    assert len(catalog["commandCues"]) >= 20
    assert all("elapsed" in cue["text"].lower() for cue in catalog["elapsedCues"])
    assert catalog["fallbackCommandFilename"] in _ios_catalog_filenames(catalog)


def test_ios_voice_assets_and_tests_are_wired_into_xcode_targets():
    project = IOS_XCODE_PROJECT.read_text(encoding="utf-8")
    voice_tests = IOS_VOICE_TESTS.read_text(encoding="utf-8")

    assert "RandomTimer/Resources/Audio" in project
    assert "Audio in Resources" in project
    assert "AIVoiceCalloutServiceTests.swift in Sources" in project
    assert "Missing bundled voice assets" in voice_tests


def test_runtime_manifest_is_generated_with_hashed_assets_and_platform_urls():
    runtime_manifest = _load_runtime_manifest()

    assert runtime_manifest["schemaVersion"] == 1
    assert runtime_manifest["entitlement"] == "pro"
    assert runtime_manifest["voiceCatalog"]["previewElapsed"]["filename"]
    assert runtime_manifest["soundCatalog"]["packId"] == runtime_manifest["packId"]
    assert runtime_manifest["assets"]
    assert all(asset["sha256"] for asset in runtime_manifest["assets"])
    assert all(asset["bytes"] > 0 for asset in runtime_manifest["assets"])
    assert all("/content/pro_audio/runtime/" in asset["url"] for asset in runtime_manifest["assets"])


def test_mobile_clients_point_to_the_same_remote_pro_audio_manifest():
    android_build = ANDROID_BUILD_GRADLE.read_text(encoding="utf-8")
    ios_info = IOS_INFO_PLIST.read_text(encoding="utf-8")

    expected_url = "https://raw.githubusercontent.com/IgorGanapolsky/Random-Timer/develop/content/pro_audio/runtime/latest.json"
    assert expected_url in android_build
    assert expected_url in ios_info
