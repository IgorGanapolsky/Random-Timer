#!/usr/bin/env python3
"""
Monthly audio pack generator — fetches CC0 sounds from Freesound and optionally
generates voice callouts via ElevenLabs.

Usage
-----
    python scripts/generate_monthly_audio_pack.py [--skip-voice]

Environment variables
---------------------
FREESOUND_API_TOKEN   (required) Freesound OAuth client-credentials token.
ELEVENLABS_API_KEY    (optional) ElevenLabs API key for voice callouts. When absent
                      or when the account has no credits left the voice generation step
                      is skipped gracefully without failing the script.
REPO_ROOT             (optional) Override for the repository root path.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[1]))
IOS_SOUND_DIR = REPO_ROOT / "native-ios" / "RandomTimer" / "Resources" / "Sounds"
ANDROID_RAW_DIR = REPO_ROOT / "native-android" / "app" / "src" / "main" / "res" / "raw"
IOS_AUDIO_DIR = REPO_ROOT / "native-ios" / "RandomTimer" / "Resources" / "Audio"
ANDROID_ASSETS_DIR = REPO_ROOT / "native-android" / "app" / "src" / "main" / "assets"

# ---------------------------------------------------------------------------
# Freesound helpers
# ---------------------------------------------------------------------------

FREESOUND_SEARCH_URL = "https://freesound.org/apiv2/search/text/"
FREESOUND_DOWNLOAD_TMPL = "https://freesound.org/apiv2/sounds/{sound_id}/download/"

# Curated CC0 search queries for workout / timer sound effects
SOUND_QUERIES: list[dict[str, Any]] = [
    {"query": "timer beep short", "filename": "timer_beep_monthly", "max_duration": 3.0},
    {"query": "whistle sport start", "filename": "whistle_monthly", "max_duration": 4.0},
    {"query": "bell ding alert", "filename": "bell_monthly", "max_duration": 3.0},
    {"query": "countdown beep", "filename": "countdown_monthly", "max_duration": 5.0},
]


def _freesound_get(url: str, token: str, params: dict[str, str] | None = None) -> Any:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            pass
        raise RuntimeError(f"Freesound API {exc.code}: {body[:300]}") from exc


def _freesound_download(sound_id: int, token: str) -> bytes | None:
    """Download Freesound audio bytes. Returns None on failure."""
    url = f"https://freesound.org/apiv2/sounds/{sound_id}/download/"
    req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as exc:
        print(f"  ⚠️  Download failed for sound {sound_id}: {exc}", file=sys.stderr)
        return None


def _search_freesound(query: str, max_duration: float, token: str) -> list[dict[str, Any]]:
    result = _freesound_get(
        FREESOUND_SEARCH_URL,
        token,
        params={
            "query": query,
            "filter": f"license:\"Creative Commons 0\" duration:[0 TO {max_duration}]",
            "fields": "id,name,duration,license,previews",
            "page_size": "5",
            "format": "json",
        },
    )
    return result.get("results", [])


def _preview_url(sound: dict[str, Any]) -> str | None:
    previews = sound.get("previews", {})
    return previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")


def _write_preview_pair(
    preview_url: str,
    ios_dest: Path,
    android_dest: Path,
    token: str,
) -> bool:
    req = urllib.request.Request(preview_url, headers={"Authorization": f"Token {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        ios_dest.write_bytes(data)
        android_dest.write_bytes(data)
        return True
    except Exception as exc:
        print(f"  ⚠️  Preview download failed: {exc}; falling back to download endpoint")
        return False


def _download_sound_pair(
    sound: dict[str, Any],
    ios_dest: Path,
    android_dest: Path,
    token: str,
) -> bool:
    preview_url = _preview_url(sound)
    if preview_url and _write_preview_pair(preview_url, ios_dest, android_dest, token):
        print(f"  ✅ Wrote {ios_dest.name} via preview URL")
        return True

    sound_id = sound["id"]
    audio_bytes = _freesound_download(sound_id, token)
    if audio_bytes is None:
        return False

    ios_dest.write_bytes(audio_bytes)
    android_dest.write_bytes(audio_bytes)
    print(f"  ✅ Wrote {ios_dest.name} via download endpoint")
    return True


def fetch_freesound_pack(token: str, dry_run: bool = False) -> list[Path]:
    """Fetch CC0 sounds from Freesound and write them to both platform dirs.
    Returns list of written paths."""

    IOS_SOUND_DIR.mkdir(parents=True, exist_ok=True)
    ANDROID_RAW_DIR.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    month_tag = datetime.now(tz=timezone.utc).strftime("%Y%m")

    for query_cfg in SOUND_QUERIES:
        query = query_cfg["query"]
        base_filename = f"{query_cfg['filename']}_{month_tag}"
        max_dur = query_cfg.get("max_duration", 5.0)

        print(f"Searching Freesound: {query!r} …")
        try:
            sounds = _search_freesound(query, max_dur, token)
        except RuntimeError as exc:
            print(f"  ⚠️  Skipping {query!r}: {exc}", file=sys.stderr)
            continue

        if not sounds:
            print(f"  ℹ  No results for {query!r}")
            continue

        sound = sounds[0]
        sound_id = sound["id"]
        print(f"  Found: id={sound_id} name={sound['name']!r} dur={sound['duration']:.1f}s")

        ios_dest = IOS_SOUND_DIR / f"{base_filename}.mp3"
        android_dest = ANDROID_RAW_DIR / f"{base_filename}.mp3"

        if dry_run:
            print(f"  [dry-run] Would write {ios_dest} and {android_dest}")
            continue

        if _download_sound_pair(sound, ios_dest, android_dest, token):
            written.extend([ios_dest, android_dest])

        time.sleep(0.5)  # be polite to Freesound rate limits

    return written


# ---------------------------------------------------------------------------
# ElevenLabs helpers
# ---------------------------------------------------------------------------

ELEVENLABS_BASE = "https://api.elevenlabs.io"
VOICE_MODEL = "eleven_turbo_v2_5"
# Default: Ivanna — warrior drill instructor voice
DEFAULT_VOICE_ID = "cgSgspJ2msm6clMCkdW9"

MONTHLY_CALLOUT_SCRIPTS: list[dict[str, str]] = [
    {"name": "cmd_go_monthly", "text": "Go! Push harder!"},
    {"name": "cmd_rest_monthly", "text": "Rest. Recover. Stay focused."},
    {"name": "elapsed_30s_monthly", "text": "Thirty seconds in. Keep moving!"},
    {"name": "elapsed_1m_monthly", "text": "One minute. Stay strong!"},
    {"name": "elapsed_halfway_monthly", "text": "Halfway there. Don't stop now!"},
]


def _check_elevenlabs_credits(api_key: str) -> int:
    """Return remaining character credits. Returns 0 on any error."""
    url = f"{ELEVENLABS_BASE}/v1/user/subscription"
    req = urllib.request.Request(
        url,
        headers={"xi-api-key": api_key, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        limit = data.get("character_limit", 0)
        used = data.get("character_count", 0)
        remaining = limit - used
        print(f"ElevenLabs credits: {remaining:,} remaining of {limit:,}")
        return max(0, remaining)
    except Exception as exc:
        print(f"  ⚠️  Could not check ElevenLabs credits: {exc}", file=sys.stderr)
        return 0


def _elevenlabs_tts(text: str, voice_id: str, api_key: str) -> bytes:
    url = f"{ELEVENLABS_BASE}/v1/text-to-speech/{voice_id}"
    payload = json.dumps(
        {
            "text": text,
            "model_id": VOICE_MODEL,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def generate_voice_callouts(api_key: str, dry_run: bool = False) -> list[Path]:
    """Generate new monthly voice callouts via ElevenLabs.
    Returns list of written paths. Never raises — all errors are warnings."""

    available_credits = _check_elevenlabs_credits(api_key)
    total_chars = sum(len(c["text"]) for c in MONTHLY_CALLOUT_SCRIPTS)
    if available_credits < total_chars:
        print(
            f"  ℹ  Not enough ElevenLabs credits ({available_credits} < {total_chars} needed). "
            "Skipping voice callout generation.",
            file=sys.stderr,
        )
        return []

    IOS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ANDROID_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    month_tag = datetime.now(tz=timezone.utc).strftime("%Y%m")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)

    for callout in MONTHLY_CALLOUT_SCRIPTS:
        key = f"{callout['name']}_{month_tag}"
        text = callout["text"]
        ios_dest = IOS_AUDIO_DIR / f"{key}.mp3"
        android_dest = ANDROID_ASSETS_DIR / f"{key}.mp3"

        if dry_run:
            print(f"  [dry-run] Would generate {key}.mp3: {text!r}")
            continue

        print(f"  Generating {key}.mp3 …")
        try:
            audio_bytes = _elevenlabs_tts(text, voice_id, api_key)
            ios_dest.write_bytes(audio_bytes)
            android_dest.write_bytes(audio_bytes)
            written.extend([ios_dest, android_dest])
            print(f"  ✅ Wrote {key}.mp3")
        except Exception as exc:
            print(f"  ⚠️  Voice generation failed for {key}: {exc}", file=sys.stderr)

        time.sleep(0.3)  # avoid rate-limit

    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate monthly Pro audio pack (CC0 sounds + voice callouts)."
    )
    parser.add_argument(
        "--skip-voice",
        action="store_true",
        help="Skip ElevenLabs voice generation (sounds only).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing any files.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    freesound_token = os.environ.get("FREESOUND_API_TOKEN", "").strip()
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()

    if not freesound_token:
        print(
            "❌ FREESOUND_API_TOKEN is not set. Cannot fetch CC0 sounds.",
            file=sys.stderr,
        )
        return 1

    print("=== Step 1: Fetch CC0 sounds from Freesound ===")
    sound_paths = fetch_freesound_pack(freesound_token, dry_run=args.dry_run)
    print(f"Fetched {len(sound_paths)} sound file(s).")

    voice_paths: list[Path] = []
    if not args.skip_voice:
        if elevenlabs_key:
            print("\n=== Step 2: Generate voice callouts via ElevenLabs ===")
            voice_paths = generate_voice_callouts(elevenlabs_key, dry_run=args.dry_run)
            print(f"Generated {len(voice_paths)} voice file(s).")
        else:
            print(
                "\n=== Step 2: Voice callouts — SKIPPED (ELEVENLABS_API_KEY not set) ===",
                file=sys.stderr,
            )
    else:
        print("\n=== Step 2: Voice callouts — SKIPPED (--skip-voice flag) ===")

    all_files = sound_paths + voice_paths
    print(f"\nDone. Total files written: {len(all_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
