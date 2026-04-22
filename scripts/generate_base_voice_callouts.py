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
    if not _SAFE_FILENAME.fullmatch(filename):
        raise ValueError(f"Unsafe cue filename rejected: {filename!r}")
    return filename

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


def _missing_male_cues(catalog: dict) -> list[tuple[str, str]]:
    return [
        (_safe_filename(cue["filename"]), cue["text"])
        for cue in catalog["commandCues"]
        if not (ANDROID_RAW_DIR / f"{_safe_filename(cue['filename'])}.mp3").is_file()
    ]


def _mirror_into(src_dir: Path, dst_dir: Path, filename: str) -> None:
    safe = _safe_filename(filename)
    src = (src_dir / f"{safe}.mp3").resolve()
    dst = (dst_dir / f"{safe}.mp3").resolve()
    if src_dir.resolve() not in src.parents or dst_dir.resolve() not in dst.parents:
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
    for filename, text in missing:
        print(f"  - {filename}: {text!r}")

    male_settings = _load_voice_settings(api_key, male_voice_id, DEFAULT_VOICE_SETTINGS)
    _generate_voice_assets(
        api_key=api_key,
        voice_id=male_voice_id,
        model_id=model_id,
        voice_settings=male_settings,
        lines=missing,
        output_dir=IOS_AUDIO_DIR,
    )
    for filename, _ in missing:
        _mirror_into(IOS_AUDIO_DIR, ANDROID_RAW_DIR, filename)

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
        for filename, _ in missing:
            safe = _safe_filename(filename)
            src = (IOS_FEMALE_AUDIO_DIR / f"{safe}.mp3").resolve()
            dst = (ANDROID_RAW_DIR / f"female_{safe}.mp3").resolve()
            if IOS_FEMALE_AUDIO_DIR.resolve() not in src.parents or ANDROID_RAW_DIR.resolve() not in dst.parents:
                raise ValueError(f"Female mirror path escaped allowed dir: {src} -> {dst}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            print(f"mirrored -> {dst}")
    else:
        print("FEMALE_VOICE_ID not set — skipping female render.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
