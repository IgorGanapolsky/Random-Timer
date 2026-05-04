from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_RAW_DIR = ROOT / "native-android/app/src/main/res/raw"
IOS_SOUND_DIR = ROOT / "native-ios/RandomTimer/Resources/Sounds"
RUNTIME_LATEST = ROOT / "content/pro_audio/runtime/latest.json"
RUNTIME_SOUND_DIR = ROOT / "content/pro_audio/runtime/packs/2026-05_combatives_corner/sounds"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
ANDROID_SETUP = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"
ANDROID_VOICE_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


SOUND_ARSENAL_FILES = {
    "airhorn": ("airhorn.mp3", "airhorn.mp3"),
    "bell": ("bell.mp3", "bell.mp3"),
    "buzzer": ("buzzer.mp3", "buzzer.mp3"),
    "drum_roll": ("drum_roll.mp3", "drum_roll.mp3"),
    "gong": ("gong.mp3", "gong.mp3"),
    "klaxon": ("klaxon.mp3", "klaxon.mp3"),
    "siren": ("siren.mp3", "siren.mp3"),
    "whistle": ("whistle.mp3", "whistle.mp3"),
}

def test_sound_arsenal_files_exist_across_ios_android_and_runtime_pack() -> None:
    for runtime_name, (ios_filename, android_filename) in SOUND_ARSENAL_FILES.items():
        ios_path = IOS_SOUND_DIR / ios_filename
        android_path = ANDROID_RAW_DIR / android_filename
        runtime_path = RUNTIME_SOUND_DIR / f"{runtime_name}.mp3"
        for path in (ios_path, android_path, runtime_path):
            assert path.exists(), f"Missing Sound Arsenal asset: {path}"
            assert path.stat().st_size > 5000, f"{path.name} too small ({path.stat().st_size}B)"


def test_sound_arsenal_checksums_match_across_ios_android_and_runtime_pack() -> None:
    for runtime_name, (ios_filename, android_filename) in SOUND_ARSENAL_FILES.items():
        ios_path = IOS_SOUND_DIR / ios_filename
        android_path = ANDROID_RAW_DIR / android_filename
        runtime_path = RUNTIME_SOUND_DIR / f"{runtime_name}.mp3"
        ios_hash = _sha256(ios_path)
        android_hash = _sha256(android_path)
        runtime_hash = _sha256(runtime_path)

        assert android_hash == ios_hash, f"Android drift for {android_filename}"
        assert runtime_hash == ios_hash, f"Runtime pack drift for {runtime_name}.mp3"


def test_gentle_iconography_uses_water_not_lightning() -> None:
    ios_setup = _read(IOS_SETUP)
    android_setup = _read(ANDROID_SETUP)

    assert 'systemImage: "drop.fill"' in ios_setup
    assert 'systemImage: "bolt.fill"' not in ios_setup
    assert 'label = "\\uD83D\\uDCA7 Gentle"' in android_setup
    assert 'label = "\\u26A1 Gentle"' not in android_setup


def test_sound_arsenal_selection_is_visible_after_tap() -> None:
    ios_setup = _read(IOS_SETUP)
    android_setup = _read(ANDROID_SETUP)

    assert 'Image(systemName: "checkmark.circle.fill")' in ios_setup
    assert 'Text("Selected")' in ios_setup
    assert 'text = "✓"' in android_setup
    assert 'text = "Selected"' in android_setup


def test_session_voice_playback_routes_to_gendered_assets() -> None:
    ios_voice_service = _read(IOS_VOICE_SERVICE)
    android_voice_manager = _read(ANDROID_VOICE_MANAGER)

    assert "genderedVoiceFilename(baseFilename, gender: currentGender)" in ios_voice_service
    assert 'return "female/\\(filename)"' in ios_voice_service
    assert "private fun speak(cue: VoiceCue)" in android_voice_manager
    assert "val filename = genderedVoiceFilename(cue.filename, currentGender)" in android_voice_manager
    assert 'VoiceGender.FEMALE -> if (filename.startsWith("female_")) filename else "female_$filename"' in android_voice_manager
