#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


API_BASE_URL = "https://api.elevenlabs.io"
VOICE_OUTPUT_FORMAT = "mp3_44100_128"
SOUND_OUTPUT_FORMAT = "mp3_44100_128"
DEFAULT_RUNTIME_BASE_URL = "https://raw.githubusercontent.com/IgorGanapolsky/Random-Timer/develop/content/pro_audio/runtime"
REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MANIFEST_PATH = REPO_ROOT / "content/pro_audio/monthly_pro_audio_packs.json"
IOS_VOICE_CATALOG_PATH = REPO_ROOT / "native-ios/RandomTimer/Resources/Audio/voice_callouts.json"
ANDROID_VOICE_CATALOG_PATH = REPO_ROOT / "native-android/app/src/main/assets/voice_callouts.json"
IOS_SOUND_CATALOG_PATH = REPO_ROOT / "native-ios/RandomTimer/Resources/Audio/sound_arsenal.json"
ANDROID_SOUND_CATALOG_PATH = REPO_ROOT / "native-android/app/src/main/assets/sound_arsenal.json"
RUNTIME_MANIFEST_PATH = REPO_ROOT / "content/pro_audio/runtime/latest.json"
VOICE_MODEL_RATES = {
    "eleven_multilingual_v2": 1.0,
    "eleven_multilingual_v3": 1.0,
    "eleven_v3": 1.0,
    "eleven_flash_v2_5": 0.5,
    "eleven_turbo_v2_5": 0.5,
}


class ElevenLabsRequestError(RuntimeError):
    pass


def _read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        return error.read().decode("utf-8").strip()
    except Exception:
        return ""


def _request_json(path: str, api_key: str | None) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["xi-api-key"] = api_key

    request = urllib.request.Request(f"{API_BASE_URL}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = _read_error_body(error)
        detail = f" Body: {body}" if body else ""
        raise ElevenLabsRequestError(
            f"ElevenLabs request failed with HTTP {error.code} for {path}.{detail}"
        ) from error


def _request_binary(path: str, api_key: str, payload: dict, accept: str) -> bytes:
    request = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": accept,
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        body = _read_error_body(error)
        detail = f" Body: {body}" if body else ""
        raise ElevenLabsRequestError(
            f"ElevenLabs binary request failed with HTTP {error.code} for {path}.{detail}"
        ) from error


def _resolve_repo_path(path: Path, *, must_exist: bool = False) -> Path:
    resolved = path.expanduser().resolve(strict=must_exist)
    if resolved != REPO_ROOT and REPO_ROOT not in resolved.parents:
        raise SystemExit(f"Refusing to access path outside repository: {path}")
    return resolved


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(_resolve_repo_path(path, must_exist=True).read_text(encoding="utf-8"))


def _select_pack(manifest: dict[str, Any], pack_id: str | None) -> dict[str, Any]:
    resolved_id = pack_id or manifest["activePackId"]
    for pack in manifest["packs"]:
        if pack["id"] == resolved_id:
            return pack
    raise SystemExit(f"Could not find audio pack {resolved_id!r}.")


def _voice_catalog(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "previewElapsed": pack["previewElapsed"],
        "fallbackCommandFilename": pack["fallbackCommandFilename"],
        "elapsedCues": pack["elapsedCues"],
        "commandCues": pack["commandCues"],
    }


def _sound_catalog(pack: dict[str, Any], entitlement: str) -> dict[str, Any]:
    return {
        "packId": pack["id"],
        "releaseMonth": pack["releaseMonth"],
        "entitlement": entitlement,
        "sounds": [
            {
                "soundType": sound["soundType"],
                "filename": sound["filename"],
                "durationSeconds": sound["durationSeconds"],
            }
            for sound in pack["soundArsenal"]
        ],
    }


def _voice_lines(catalog: dict[str, Any]) -> list[tuple[str, str]]:
    lines = [(catalog["previewElapsed"]["filename"], catalog["previewElapsed"]["text"])]
    lines.extend((cue["filename"], cue["text"]) for cue in catalog["elapsedCues"])
    lines.extend((cue["filename"], cue["text"]) for cue in catalog["commandCues"])
    return lines


def _sound_entries(pack: dict[str, Any]) -> list[tuple[str, str, float]]:
    return [
        (
            sound["filename"],
            sound["prompt"],
            float(sound["durationSeconds"]),
        )
        for sound in pack["soundArsenal"]
    ]


def _remove_stale_assets(expected_stems: set[str], output_dir: Path) -> None:
    if not output_dir.exists():
        return
    for asset in output_dir.glob("*.mp3"):
        if asset.stem in expected_stems:
            continue
        asset.unlink()
        print(f"removed stale {asset}")


def _android_safe_stem(stem: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]", "_", stem.lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        raise SystemExit(f"Could not normalize Android resource stem from {stem!r}.")
    return normalized


def _list_voices(api_key: str | None) -> list[dict[str, Any]]:
    payload = _request_json("/v1/voices", api_key)
    return payload.get("voices", [])


def _resolve_voice(voices: list[dict[str, Any]], voice_id: str | None, voice_name_query: str) -> dict[str, Any]:
    if voice_id:
        for voice in voices:
            if voice.get("voice_id") == voice_id:
                return voice
        raise SystemExit(f"Requested voice_id {voice_id!r} was not found in ElevenLabs voice list.")

    normalized_query = voice_name_query.strip().casefold()
    candidates = [
        voice for voice in voices if normalized_query and normalized_query in voice.get("name", "").casefold()
    ]
    if not candidates:
        available = ", ".join(sorted(voice.get("name", "<unnamed>") for voice in voices))
        raise SystemExit(
            "Could not auto-discover an ElevenLabs voice matching "
            f"{voice_name_query!r}. Available voices: {available}"
        )

    def rank(voice: dict[str, Any]) -> tuple[int, int, str]:
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


def _load_voice_settings(api_key: str, voice_id: str, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        return _request_json(f"/v1/voices/{voice_id}/settings", api_key)
    except ElevenLabsRequestError:
        return fallback


def _resolve_output_paths(args: argparse.Namespace) -> argparse.Namespace:
    path_fields = (
        "manifest",
        "ios_audio_dir",
        "ios_sounds_dir",
        "android_raw_dir",
        "runtime_assets_dir",
    )
    for field in path_fields:
        setattr(args, field, _resolve_repo_path(getattr(args, field), must_exist=(field == "manifest")))
    return args


def _print_available_voices(api_key: str | None) -> None:
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


def _write_catalogs(voice_catalog: dict[str, Any], sound_catalog: dict[str, Any]) -> None:
    serialized_voice_catalog = json.dumps(voice_catalog, indent=2) + "\n"
    serialized_sound_catalog = json.dumps(sound_catalog, indent=2) + "\n"

    ios_voice_catalog_path = IOS_VOICE_CATALOG_PATH.resolve()
    ios_voice_catalog_path.relative_to(REPO_ROOT)
    ios_voice_catalog_path.parent.mkdir(parents=True, exist_ok=True)
    ios_voice_catalog_path.write_text(serialized_voice_catalog, encoding="utf-8")

    android_voice_catalog_path = ANDROID_VOICE_CATALOG_PATH.resolve()
    android_voice_catalog_path.relative_to(REPO_ROOT)
    android_voice_catalog_path.parent.mkdir(parents=True, exist_ok=True)
    android_voice_catalog_path.write_text(serialized_voice_catalog, encoding="utf-8")

    ios_sound_catalog_path = IOS_SOUND_CATALOG_PATH.resolve()
    ios_sound_catalog_path.relative_to(REPO_ROOT)
    ios_sound_catalog_path.parent.mkdir(parents=True, exist_ok=True)
    ios_sound_catalog_path.write_text(serialized_sound_catalog, encoding="utf-8")

    android_sound_catalog_path = ANDROID_SOUND_CATALOG_PATH.resolve()
    android_sound_catalog_path.relative_to(REPO_ROOT)
    android_sound_catalog_path.parent.mkdir(parents=True, exist_ok=True)
    android_sound_catalog_path.write_text(serialized_sound_catalog, encoding="utf-8")


def _resolve_generation_api_key(args: argparse.Namespace) -> str:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if (args.generate_voice_assets or args.generate_sound_assets) and not api_key:
        raise SystemExit("ELEVENLABS_API_KEY is required when generating audio assets.")
    return api_key


def _generate_voice_assets_if_requested(
    args: argparse.Namespace,
    api_key: str,
    defaults: dict[str, Any],
    voice_lines: list[tuple[str, str]],
    expected_voice_stems: set[str],
    model_id: str,
    voice_name_query: str,
) -> None:
    if not args.generate_voice_assets:
        return

    voice_id = args.voice_id.strip()
    if voice_id:
        voice = _configured_voice(voice_id)
    else:
        voices = _list_voices(api_key)
        voice = _resolve_voice(voices, None, voice_name_query)

    voice_settings = _load_voice_settings(api_key, voice["voice_id"], defaults["voiceSettings"])
    _generate_voice_assets(
        api_key=api_key,
        voice_id=voice["voice_id"],
        model_id=model_id,
        voice_settings=voice_settings,
        lines=voice_lines,
        output_dir=args.ios_audio_dir,
    )
    _remove_stale_assets(expected_voice_stems, args.ios_audio_dir)


def _generate_sound_assets_if_requested(
    args: argparse.Namespace,
    api_key: str,
    sound_lines: list[tuple[str, str, float]],
    expected_sound_stems: set[str],
) -> None:
    if not args.generate_sound_assets:
        return

    _generate_sound_assets(
        api_key=api_key,
        sounds=sound_lines,
        output_dir=args.ios_sounds_dir,
    )
    _remove_stale_assets(expected_sound_stems, args.ios_sounds_dir)


def _sync_android_assets_if_requested(
    args: argparse.Namespace,
    expected_voice_stems: set[str],
    expected_sound_stems: set[str],
) -> None:
    if not args.sync_android_assets:
        return

    android_voice_stems = _copy_assets(args.ios_audio_dir, args.android_raw_dir, expected_voice_stems)
    android_sound_stems = _copy_assets(
        args.ios_sounds_dir,
        args.android_raw_dir,
        expected_sound_stems,
        stem_transform=_android_safe_stem,
    )
    _remove_stale_assets(android_voice_stems | android_sound_stems, args.android_raw_dir)


def _generate_voice_assets(
    api_key: str,
    voice_id: str,
    model_id: str,
    voice_settings: dict[str, Any],
    lines: list[tuple[str, str]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, text in lines:
        query = urllib.parse.urlencode({"output_format": VOICE_OUTPUT_FORMAT})
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings,
        }
        audio = _request_binary(
            f"/v1/text-to-speech/{voice_id}?{query}",
            api_key,
            payload,
            accept="audio/mpeg",
        )
        destination = output_dir / f"{filename}.mp3"
        destination.write_bytes(audio)
        print(f"generated voice {destination}")


def _generate_sound_assets(
    api_key: str,
    sounds: list[tuple[str, str, float]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, prompt, duration_seconds in sounds:
        query = urllib.parse.urlencode({"output_format": SOUND_OUTPUT_FORMAT})
        payload = {
            "text": prompt,
            "duration_seconds": duration_seconds,
        }
        audio = _request_binary(
            f"/v1/sound-generation?{query}",
            api_key,
            payload,
            accept="audio/mpeg",
        )
        destination = output_dir / f"{filename}.mp3"
        destination.write_bytes(audio)
        print(f"generated sound {destination}")


def _copy_assets(
    source_dir: Path,
    destination_dir: Path,
    stems: set[str],
    *,
    stem_transform: Callable[[str], str] | None = None,
) -> set[str]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    copied_stems: set[str] = set()

    for stem in stems:
        source = source_dir / f"{stem}.mp3"
        if not source.exists():
            raise SystemExit(f"Cannot sync missing source asset: {source}")
        destination_stem = stem_transform(stem) if stem_transform else stem
        copied_stems.add(destination_stem)
        shutil.copy2(source, destination_dir / f"{destination_stem}.mp3")

    return copied_stems


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _runtime_manifest(
    pack: dict[str, Any],
    entitlement: str,
    voice_catalog: dict[str, Any],
    sound_catalog: dict[str, Any],
    *,
    runtime_base_url: str,
    runtime_assets_dir: Path,
) -> dict[str, Any]:
    voice_dir = runtime_assets_dir / "packs" / pack["id"] / "voice"
    sound_dir = runtime_assets_dir / "packs" / pack["id"] / "sounds"
    assets: list[dict[str, Any]] = []

    for kind, directory in (("voice", voice_dir), ("sound", sound_dir)):
        for asset in sorted(directory.glob("*.mp3")):
            relative_path = asset.relative_to(runtime_assets_dir).as_posix()
            assets.append(
                {
                    "kind": kind,
                    "filename": asset.stem,
                    "relativePath": relative_path,
                    "url": f"{runtime_base_url.rstrip('/')}/{relative_path}",
                    "sha256": _sha256_hex(asset),
                    "bytes": asset.stat().st_size,
                }
            )

    return {
        "schemaVersion": 1,
        "packId": pack["id"],
        "releaseMonth": pack["releaseMonth"],
        "entitlement": entitlement,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "voiceCatalog": voice_catalog,
        "soundCatalog": sound_catalog,
        "assets": assets,
    }


def _stage_runtime_assets(
    pack_id: str,
    *,
    ios_audio_dir: Path,
    ios_sounds_dir: Path,
    runtime_assets_dir: Path,
    voice_stems: set[str],
    sound_stems: set[str],
) -> None:
    voice_destination = runtime_assets_dir / "packs" / pack_id / "voice"
    sound_destination = runtime_assets_dir / "packs" / pack_id / "sounds"

    _copy_assets(ios_audio_dir, voice_destination, voice_stems)
    _copy_assets(ios_sounds_dir, sound_destination, sound_stems)
    _remove_stale_assets(voice_stems, voice_destination)
    _remove_stale_assets(sound_stems, sound_destination)

    packs_dir = runtime_assets_dir / "packs"
    if packs_dir.exists():
        for sibling in packs_dir.iterdir():
            if sibling.is_dir() and sibling.name != pack_id:
                shutil.rmtree(sibling)
                print(f"removed stale runtime pack {sibling}")


def _estimate_voice_credits(lines: list[tuple[str, str]], model_id: str) -> int:
    multiplier = VOICE_MODEL_RATES.get(model_id, 1.0)
    characters = sum(len(text) for _, text in lines)
    return int(round(characters * multiplier))


def _estimate_sound_credits(sounds: list[tuple[str, str, float]]) -> int:
    return int(round(sum(duration * 40 for _, _, duration in sounds)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and sync monthly Pro audio content from ElevenLabs.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=CANONICAL_MANIFEST_PATH,
        help="Canonical monthly Pro audio manifest.",
    )
    parser.add_argument("--pack-id", default="", help="Optional explicit pack ID. Defaults to the active pack.")
    parser.add_argument(
        "--ios-audio-dir",
        type=Path,
        default=Path("native-ios/RandomTimer/Resources/Audio"),
        help="Directory for iOS voice MP3 files.",
    )
    parser.add_argument(
        "--ios-sounds-dir",
        type=Path,
        default=Path("native-ios/RandomTimer/Resources/Sounds"),
        help="Directory for iOS alarm sound MP3 files.",
    )
    parser.add_argument(
        "--android-raw-dir",
        type=Path,
        default=Path("native-android/app/src/main/res/raw"),
        help="Directory for Android raw audio files.",
    )
    parser.add_argument(
        "--runtime-assets-dir",
        type=Path,
        default=Path("content/pro_audio/runtime"),
        help="Directory for hosted runtime manifest and audio pack assets.",
    )
    parser.add_argument(
        "--runtime-base-url",
        default=DEFAULT_RUNTIME_BASE_URL,
        help="Public base URL used by mobile clients to download the hosted runtime manifest and assets.",
    )
    parser.add_argument("--voice-id", default="", help="Exact ElevenLabs voice ID to use.")
    parser.add_argument(
        "--voice-name-pattern",
        default="",
        help="Regex used to auto-discover the drill instructor voice when --voice-id is omitted.",
    )
    parser.add_argument(
        "--model-id",
        default="",
        help="ElevenLabs model ID used for speech synthesis.",
    )
    parser.add_argument("--list-voices", action="store_true", help="Print available ElevenLabs voices and exit.")
    parser.add_argument("--generate-voice-assets", action="store_true", help="Generate voice callout MP3 files.")
    parser.add_argument("--generate-sound-assets", action="store_true", help="Generate alarm sound MP3 files.")
    parser.add_argument(
        "--sync-android-assets",
        action="store_true",
        help="Sync managed iOS audio assets into Android raw resources.",
    )
    parser.add_argument(
        "--estimate-only",
        action="store_true",
        help="Only print the monthly credit estimate; do not write files or generate assets.",
    )
    return parser.parse_args()


def main() -> None:
    args = _resolve_output_paths(parse_args())
    manifest = _load_manifest(args.manifest)
    pack = _select_pack(manifest, args.pack_id.strip() or None)
    defaults = manifest["defaults"]
    entitlement = defaults["entitlement"]
    voice_catalog = _voice_catalog(pack)
    sound_catalog = _sound_catalog(pack, entitlement)
    voice_lines = _voice_lines(voice_catalog)
    sound_lines = _sound_entries(pack)
    model_id = args.model_id.strip() or defaults["voiceModelId"]
    voice_name_pattern = args.voice_name_pattern.strip() or defaults["voiceNamePattern"]

    estimate = {
        "pack_id": pack["id"],
        "release_month": pack["releaseMonth"],
        "voice_line_count": len(voice_lines),
        "sound_count": len(sound_lines),
        "voice_credit_estimate": _estimate_voice_credits(voice_lines, model_id),
        "sound_credit_estimate": _estimate_sound_credits(sound_lines),
        "voice_model_id": model_id,
    }

    if args.list_voices:
        _print_available_voices(os.environ.get("ELEVENLABS_API_KEY", "").strip() or None)
        return

    print(json.dumps(estimate))
    if args.estimate_only:
        return

    _write_catalogs(voice_catalog, sound_catalog)

    expected_voice_stems = {filename for filename, _ in voice_lines}
    expected_sound_stems = {filename for filename, _, _ in sound_lines}

    api_key = _resolve_generation_api_key(args)
    _generate_voice_assets_if_requested(
        args=args,
        api_key=api_key,
        defaults=defaults,
        voice_lines=voice_lines,
        expected_voice_stems=expected_voice_stems,
        model_id=model_id,
        voice_name_query=voice_name_pattern,
    )
    _generate_sound_assets_if_requested(args, api_key, sound_lines, expected_sound_stems)
    _sync_android_assets_if_requested(args, expected_voice_stems, expected_sound_stems)

    _stage_runtime_assets(
        pack["id"],
        ios_audio_dir=args.ios_audio_dir,
        ios_sounds_dir=args.ios_sounds_dir,
        runtime_assets_dir=args.runtime_assets_dir,
        voice_stems=expected_voice_stems,
        sound_stems=expected_sound_stems,
    )
    runtime_payload = json.dumps(
        _runtime_manifest(
            pack,
            entitlement,
            voice_catalog,
            sound_catalog,
            runtime_base_url=args.runtime_base_url,
            runtime_assets_dir=args.runtime_assets_dir,
        ),
        indent=2,
    ) + "\n"
    runtime_manifest_path = RUNTIME_MANIFEST_PATH.resolve()
    runtime_manifest_path.relative_to(REPO_ROOT)
    runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.write_text(runtime_payload, encoding="utf-8")

if __name__ == "__main__":
    main()
