#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_BASE_URL = "https://api.elevenlabs.io"


def _read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        return error.read().decode("utf-8").strip()
    except Exception:
        return ""


def _request_json(path: str, api_key: str | None) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["xi-api-key"] = api_key

    request = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = _read_error_body(error)
        detail = f" Body: {body}" if body else ""
        raise SystemExit(f"ElevenLabs request failed with HTTP {error.code} for {path}.{detail}") from error


def _request_audio(path: str, api_key: str, payload: dict) -> bytes:
    request = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        body = _read_error_body(error)
        detail = f" Body: {body}" if body else ""
        raise SystemExit(f"ElevenLabs audio request failed with HTTP {error.code} for {path}.{detail}") from error


def _load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _catalog_lines(catalog: dict) -> list[tuple[str, str]]:
    lines = [(catalog["previewElapsed"]["filename"], catalog["previewElapsed"]["text"])]
    lines.extend((cue["filename"], cue["text"]) for cue in catalog["elapsedCues"])
    lines.extend((cue["filename"], cue["text"]) for cue in catalog["commandCues"])
    return lines


def _list_voices(api_key: str | None) -> list[dict]:
    payload = _request_json("/v1/voices", api_key)
    return payload.get("voices", [])


def _resolve_voice(voices: list[dict], voice_id: str | None, voice_name_pattern: str) -> dict:
    if voice_id:
        for voice in voices:
            if voice.get("voice_id") == voice_id:
                return voice
        raise SystemExit(f"Requested voice_id {voice_id!r} was not found in ElevenLabs voice list.")

    pattern = re.compile(voice_name_pattern, re.IGNORECASE)
    candidates = [voice for voice in voices if pattern.search(voice.get("name", ""))]
    if not candidates:
        available = ", ".join(sorted(voice.get("name", "<unnamed>") for voice in voices))
        raise SystemExit(
            "Could not auto-discover an ElevenLabs voice matching "
            f"{voice_name_pattern!r}. Available voices: {available}"
        )

    def rank(voice: dict) -> tuple[int, int, str]:
        category = (voice.get("category") or "").lower()
        name = voice.get("name", "")
        is_custom = 0 if category in {"cloned", "professional", "generated"} else 1
        return (is_custom, len(name), name.lower())

    return sorted(candidates, key=rank)[0]


def _configured_voice(voice_id: str) -> dict[str, str]:
    return {
        "name": "Configured custom drill instructor voice",
        "voice_id": voice_id,
        "category": "configured",
    }


def _load_voice_settings(api_key: str, voice_id: str) -> dict:
    try:
        return _request_json(f"/v1/voices/{voice_id}/settings", api_key)
    except SystemExit:
        return {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.65,
            "use_speaker_boost": True,
            "speed": 0.95,
        }


def _generate(
    api_key: str,
    voice_id: str,
    model_id: str,
    voice_settings: dict,
    lines: list[tuple[str, str]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, text in lines:
        query = urllib.parse.urlencode({"output_format": "mp3_44100_128"})
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings,
        }
        audio = _request_audio(f"/v1/text-to-speech/{voice_id}?{query}", api_key, payload)
        destination = output_dir / f"{filename}.mp3"
        destination.write_bytes(audio)
        print(f"generated {destination}")


def _remove_stale_assets(lines: list[tuple[str, str]], output_dir: Path) -> None:
    expected_stems = {filename for filename, _ in lines}
    for asset in output_dir.glob("*.mp3"):
        if asset.stem in expected_stems:
            continue
        asset.unlink()
        print(f"removed stale {asset}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate iOS drill-instructor voice assets from ElevenLabs.")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("native-ios/RandomTimer/Resources/Audio/voice_callouts.json"),
        help="Path to the voice callout catalog JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("native-ios/RandomTimer/Resources/Audio"),
        help="Directory where generated MP3 files should be written.",
    )
    parser.add_argument("--voice-id", default="", help="Exact ElevenLabs voice ID to use.")
    parser.add_argument(
        "--voice-name-pattern",
        default="marine|drill|instructor|sergeant",
        help="Regex used to auto-discover the custom drill-instructor voice when --voice-id is omitted.",
    )
    parser.add_argument(
        "--model-id",
        default="eleven_multilingual_v2",
        help="ElevenLabs model ID used for synthesis.",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="Print available ElevenLabs voices and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_voices:
        api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip() or None
        voices = _list_voices(api_key)
        for voice in voices:
            print(
                json.dumps(
                    {
                        "name": voice.get("name"),
                        "voice_id": voice.get("voice_id"),
                        "category": voice.get("category"),
                    }
                )
            )
        return 0

    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("ELEVENLABS_API_KEY is required for voice synthesis.")

    voice_id = args.voice_id.strip()
    if voice_id:
        voice = _configured_voice(voice_id)
    else:
        voices = _list_voices(api_key)
        voice = _resolve_voice(voices, None, args.voice_name_pattern)
    voice_settings = _load_voice_settings(api_key, voice["voice_id"])
    catalog = _load_catalog(args.catalog)
    lines = _catalog_lines(catalog)

    print(
        json.dumps(
            {
                "voice_name": voice.get("name"),
                "voice_id": voice.get("voice_id"),
                "voice_category": voice.get("category"),
                "model_id": args.model_id,
                "asset_count": len(lines),
            }
        )
    )

    _generate(
        api_key=api_key,
        voice_id=voice["voice_id"],
        model_id=args.model_id,
        voice_settings=voice_settings,
        lines=lines,
        output_dir=args.output_dir,
    )
    _remove_stale_assets(lines, args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
