from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_LATEST = ROOT / "content/pro_audio/runtime/latest.json"
ANDROID_RAW_DIR = ROOT / "native-android/app/src/main/res/raw"
IOS_SETUP = ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
ANDROID_SETUP = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
IOS_VOICE_SERVICE = ROOT / "native-ios/RandomTimer/Sources/Services/AIVoiceCalloutService.swift"
ANDROID_VOICE_MANAGER = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/service/AIVoiceCalloutManager.kt"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runtime_sound_asset_map() -> dict[str, dict]:
    manifest = json.loads(RUNTIME_LATEST.read_text(encoding="utf-8"))
    return {asset["filename"]: asset for asset in manifest["assets"] if asset["kind"] == "sound"}


def test_android_bundled_sound_arsenal_matches_canonical_runtime_pack() -> None:
    runtime_assets = _runtime_sound_asset_map()
    checks = {
        "airhorn": ANDROID_RAW_DIR / "airhorn.mp3",
        "alarm": ANDROID_RAW_DIR / "alarm.mp3",
        "bell": ANDROID_RAW_DIR / "bell.mp3",
        "buzzer": ANDROID_RAW_DIR / "buzzer.mp3",
        "drum_roll": ANDROID_RAW_DIR / "drum_roll.mp3",
        "gentle-chime": ANDROID_RAW_DIR / "gentle_chime.mp3",
        "gong": ANDROID_RAW_DIR / "gong.mp3",
        "klaxon": ANDROID_RAW_DIR / "klaxon.mp3",
        "siren": ANDROID_RAW_DIR / "siren.mp3",
        "whistle": ANDROID_RAW_DIR / "whistle.mp3",
    }

    for runtime_name, local_path in checks.items():
        runtime_asset = runtime_assets[runtime_name]
        assert local_path.exists(), f"Missing bundled Android sound asset: {local_path.name}"
        assert local_path.stat().st_size == runtime_asset["bytes"], f"Unexpected byte size for {local_path.name}"
        assert _sha256(local_path) == runtime_asset["sha256"], f"Checksum drift for {local_path.name}"


def test_gentle_iconography_uses_water_not_lightning() -> None:
    ios_setup = _read(IOS_SETUP)
    android_setup = _read(ANDROID_SETUP)

    assert 'systemImage: "drop.fill"' in ios_setup
    assert 'systemImage: "bolt.fill"' not in ios_setup
    assert 'label = "\\uD83D\\uDCA7 Gentle"' in android_setup
    assert 'label = "\\u26A1 Gentle"' not in android_setup


def test_session_voice_playback_routes_to_gendered_assets() -> None:
    ios_voice_service = _read(IOS_VOICE_SERVICE)
    android_voice_manager = _read(ANDROID_VOICE_MANAGER)

    assert "genderedVoiceFilename(baseFilename, gender: currentGender)" in ios_voice_service
    assert 'return "female/\\(filename)"' in ios_voice_service
    assert "val filename = genderedVoiceFilename(baseFilename, currentGender)" in android_voice_manager
    assert 'VoiceGender.FEMALE -> if (filename.startsWith("female_")) filename else "female_$filename"' in android_voice_manager
