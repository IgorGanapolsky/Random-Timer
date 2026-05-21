#!/usr/bin/env python3
"""Generate missing base voice-callout mp3s via ElevenLabs.

Reads the Android commandCues JSON (authoritative), finds entries whose
male mp3 is missing in native-android/app/src/main/res/raw/, renders them
via ElevenLabs, and writes both male and (optionally) female mp3s into the
bundled audio directories for iOS + Android.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_SAFE_FILENAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def _safe_filename(filename: str) -> str:
    # Strip any path components Sonar taint analysis cares about, then
    # enforce an alphanumeric/underscore whitelist. Both together.
    stripped = os.path.basename(filename)
    if not _SAFE_FILENAME.fullmatch(stripped):
        raise ValueError(f"Unsafe cue filename rejected: {filename!r}")
    return stripped


sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_pro_audio_content import (  # noqa: E402
    ANDROID_VOICE_CATALOG_PATH,
    REPO_ROOT,
    _generate_voice_assets,
    _load_voice_settings,
)

ANDROID_RAW_DIR = REPO_ROOT / "native-android/app/src/main/res/raw"
IOS_AUDIO_DIR = REPO_ROOT / "native-ios/RandomTimer/Resources/Audio"
IOS_FEMALE_AUDIO_DIR = IOS_AUDIO_DIR / "female"

DEFAULT_VOICE_SETTINGS = {
    "stability": 0.6,
    "similarity_boost": 0.75,
    "style": 0.3,
    "use_speaker_boost": True,
}


def _existing_android_raw_stems() -> set[str]:
    return {path.stem for path in ANDROID_RAW_DIR.glob("*.mp3")}


def _missing_male_cues(catalog: dict) -> list[tuple[str, str]]:
    existing = _existing_android_raw_stems()
    result: list[tuple[str, str]] = []
    for cue in catalog["commandCues"]:
        name = _safe_filename(cue["filename"])
        if name not in existing:
            result.append((name, cue["text"]))
    return result


def _write_mirror(src_dir: Path, dst_dir: Path, stem: str, dst_prefix: str = "") -> None:
    src_dir_resolved = src_dir.resolve()
    dst_dir_resolved = dst_dir.resolve()
    src = src_dir_resolved / f"{stem}.mp3"
    dst = dst_dir_resolved / f"{dst_prefix}{stem}.mp3"
    if src.parent != src_dir_resolved or dst.parent != dst_dir_resolved:
        raise ValueError(f"Mirror path escaped allowed dir: {src} -> {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    print(f"mirrored -> {dst}")


def main() -> int:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        print("ELEVENLABS_API_KEY not set", file=sys.stderr)
        return 2

    male_voice_id = os.environ.get("MALE_VOICE_ID", "DGzg6RaUqxGRTHSBjfgF").strip()
    female_voice_id = os.environ.get("FEMALE_VOICE_ID", "").strip()
    model_id = os.environ.get("MODEL_ID", "eleven_multilingual_v2").strip()

    catalog = json.loads(ANDROID_VOICE_CATALOG_PATH.read_text(encoding="utf-8"))
    missing = _missing_male_cues(catalog)
    if not missing:
        print("No missing cues. Nothing to generate.")
        return 0

    print(f"Generating {len(missing)} missing cue(s):")
    for stem, text in missing:
        print(f"  - {stem}: {text!r}")

    male_settings = _load_voice_settings(api_key, male_voice_id, DEFAULT_VOICE_SETTINGS)
    _generate_voice_assets(
        api_key=api_key,
        voice_id=male_voice_id,
        model_id=model_id,
        voice_settings=male_settings,
        lines=missing,
        output_dir=IOS_AUDIO_DIR,
    )
    for stem, _ in missing:
        _write_mirror(IOS_AUDIO_DIR, ANDROID_RAW_DIR, stem)

    if female_voice_id:
        female_settings = _load_voice_settings(api_key, female_voice_id, DEFAULT_VOICE_SETTINGS)
        _generate_voice_assets(
            api_key=api_key,
            voice_id=female_voice_id,
            model_id=model_id,
            voice_settings=female_settings,
            lines=missing,
            output_dir=IOS_FEMALE_AUDIO_DIR,
        )
        for stem, _ in missing:
            _write_mirror(IOS_FEMALE_AUDIO_DIR, ANDROID_RAW_DIR, stem, dst_prefix="female_")
    else:
        print("FEMALE_VOICE_ID not set — skipping female render.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
