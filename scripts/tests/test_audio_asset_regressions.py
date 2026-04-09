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


BUNDLED_SOUNDS = {
    "airhorn": "airhorn.mp3",
    "alarm": "alarm.mp3",
    "bell": "bell.mp3",
    "buzzer": "buzzer.mp3",
    "drum_roll": "drum_roll.mp3",
    "gentle_chime": "gentle_chime.mp3",
    "gong": "gong.mp3",
    "klaxon": "klaxon.mp3",
    "siren": "siren.mp3",
    "whistle": "whistle.mp3",
}


def test_android_bundled_sound_arsenal_files_exist() -> None:
    """All Sound Arsenal sounds must exist as bundled MP3s."""
    for name, filename in BUNDLED_SOUNDS.items():
        path = ANDROID_RAW_DIR / filename
        assert path.exists(), f"Missing bundled sound: {filename}"
        assert path.stat().st_size > 5000, f"{filename} too small ({path.stat().st_size}B) — likely corrupt"


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
