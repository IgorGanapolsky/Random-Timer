#!/usr/bin/env python3
"""Monthly Pro audio pack generator using Freesound.org CC0 sounds.

Searches Freesound for CC0-licensed sound effects, downloads preview MP3s,
normalises them to -14 LUFS with ffmpeg, and updates the runtime manifest.

Usage:
    python scripts/generate_monthly_audio_pack.py [--month YYYY-MM] [--dry-run]

Environment variables:
    FREESOUND_API_TOKEN  – Freesound OAuth2 client-credentials token
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FREESOUND_API_BASE = "https://freesound.org/apiv2"
REPO_ROOT = Path(__file__).resolve().parents[1]
CONTENT_BASE = REPO_ROOT / "content" / "pro_audio"
RUNTIME_BASE = CONTENT_BASE / "runtime"
RUNTIME_MANIFEST = RUNTIME_BASE / "latest.json"
PACKS_DIR = RUNTIME_BASE / "packs"
MONTHLY_PACKS_JSON = CONTENT_BASE / "monthly_pro_audio_packs.json"
RAW_GITHUB_BASE = (
    "https://raw.githubusercontent.com/IgorGanapolsky/Random-Timer/develop"
    "/content/pro_audio/runtime"
)

# Rotating category schedule: index = (month_number - 1) % len(CATEGORIES)
CATEGORIES: list[dict[str, Any]] = [
    {
        "name": "sirens",
        "query": "siren alarm emergency",
        "soundType": "siren",
        "count": 2,
    },
    {
        "name": "bells",
        "query": "bell ring chime",
        "soundType": "bell",
        "count": 2,
    },
    {
        "name": "horns",
        "query": "horn blast signal",
        "soundType": "horn",
        "count": 2,
    },
    {
        "name": "drums",
        "query": "drum hit percussion",
        "soundType": "drum",
        "count": 2,
    },
    {
        "name": "whistles",
        "query": "whistle blow sport",
        "soundType": "whistle",
        "count": 2,
    },
    {
        "name": "buzzers",
        "query": "buzzer alert signal",
        "soundType": "buzzer",
        "count": 2,
    },
    {
        "name": "gongs",
        "query": "gong strike metallic",
        "soundType": "gong",
        "count": 2,
    },
    {
        "name": "airhorns",
        "query": "airhorn compressed loud",
        "soundType": "airhorn",
        "count": 2,
    },
    {
        "name": "klaxons",
        "query": "klaxon naval alert",
        "soundType": "klaxon",
        "count": 2,
    },
    {
        "name": "chimes",
        "query": "chime gentle notification",
        "soundType": "gentle",
        "count": 2,
    },
    {
        "name": "claxons",
        "query": "claxon loud alarm training",
        "soundType": "intense",
        "count": 2,
    },
    {
        "name": "snares",
        "query": "snare roll military",
        "soundType": "drumRoll",
        "count": 2,
    },
]

TARGET_LUFS = -14.0


# ---------------------------------------------------------------------------
# Freesound API helpers
# ---------------------------------------------------------------------------

def _api_token() -> str:
    token = os.environ.get("FREESOUND_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("ERROR: FREESOUND_API_TOKEN environment variable not set.")
    return token


def _freesound_get(path: str, params: dict[str, str]) -> dict[str, Any]:
    """Perform a GET request against the Freesound v2 API."""
    token = _api_token()
    params["token"] = token
    url = f"{FREESOUND_API_BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            pass
        raise RuntimeError(
            f"Freesound API error {exc.code} for {url}: {body}"
        ) from exc


def search_cc0_sounds(
    query: str,
    count: int,
    already_used: set[int],
) -> list[dict[str, Any]]:
    """Return up to `count` CC0 sounds from Freesound not in `already_used`."""
    params = {
        "query": query,
        "filter": "license:\"Creative Commons 0\"",
        "fields": "id,name,duration,previews,license,description",
        "page_size": str(min(count * 5, 50)),  # over-fetch to allow dedup
        "sort": "rating_desc",
    }
    data = _freesound_get("/search/text/", params)
    results: list[dict[str, Any]] = []
    for item in data.get("results", []):
        if item["id"] in already_used:
            continue
        if item.get("duration", 9999) > 10:
            # Skip sounds longer than 10 s — we want short alert stings
            continue
        results.append(item)
        if len(results) >= count:
            break
    return results


# ---------------------------------------------------------------------------
# Download + normalise
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_preview(sound: dict[str, Any], dest: Path) -> Path:
    """Download the HQ preview MP3 for a Freesound result."""
    previews = sound.get("previews", {})
    url = (
        previews.get("preview-hq-mp3")
        or previews.get("preview-lq-mp3")
        or previews.get("preview-hq-ogg")
    )
    if not url:
        raise ValueError(f"No preview URL found for sound id={sound['id']}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {sound['name']} ({sound['id']}) → {dest.name}")
    req = urllib.request.Request(url, headers={"User-Agent": "RandomTimer/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())
    return dest


def normalise_lufs(src: Path, dst: Path, target_lufs: float = TARGET_LUFS) -> Path:
    """Normalise audio to `target_lufs` LUFS using ffmpeg loudnorm filter."""
    if not shutil.which("ffmpeg"):
        print("  WARNING: ffmpeg not found — skipping normalisation, copying as-is.")
        shutil.copy2(src, dst)
        return dst

    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
        "-ar", "44100",
        "-ab", "128k",
        "-f", "mp3",
        str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  WARNING: ffmpeg normalisation failed:\n{result.stderr[-500:]}")
        shutil.copy2(src, dst)
    else:
        print(f"  Normalised → {dst.name}")
    return dst


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Any:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _collect_used_ids(manifest: dict[str, Any]) -> set[int]:
    """Gather all Freesound sound IDs that already appear in the manifest."""
    used: set[int] = set()
    for asset in manifest.get("assets", []):
        fid = asset.get("freesound_id")
        if fid:
            used.add(int(fid))
    return used


def build_asset_entry(
    sound: dict[str, Any],
    normalised_path: Path,
    pack_id: str,
    sound_type: str,
    relative_to: Path,
) -> dict[str, Any]:
    rel_path = normalised_path.relative_to(relative_to)
    sha = _sha256(normalised_path)
    size = normalised_path.stat().st_size
    url = f"{RAW_GITHUB_BASE}/{rel_path.as_posix()}"
    return {
        "kind": "sound",
        "freesound_id": sound["id"],
        "freesound_name": sound["name"],
        "soundType": sound_type,
        "filename": normalised_path.stem,
        "relativePath": str(rel_path),
        "url": url,
        "license": "CC0",
        "sha256": sha,
        "bytes": size,
        "pack": pack_id,
    }


def update_manifest(
    pack_id: str,
    month: str,
    new_assets: list[dict[str, Any]],
    new_sounds: list[dict[str, Any]],
) -> None:
    """Merge new Freesound assets into runtime/latest.json."""
    manifest = _load_json(RUNTIME_MANIFEST) or {
        "schemaVersion": 1,
        "packId": pack_id,
        "releaseMonth": month,
        "entitlement": "pro",
        "generatedAt": "",
        "voiceCatalog": {},
        "soundCatalog": {"packId": pack_id, "releaseMonth": month, "entitlement": "pro", "sounds": []},
        "assets": [],
    }

    manifest["generatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Merge sound catalog entries (avoid duplicates by soundType+filename)
    existing_filenames = {s["filename"] for s in manifest["soundCatalog"].get("sounds", [])}
    for s in new_sounds:
        if s["filename"] not in existing_filenames:
            manifest["soundCatalog"]["sounds"].append(s)
            existing_filenames.add(s["filename"])

    # Merge asset entries (avoid duplicates by freesound_id)
    existing_ids = {a.get("freesound_id") for a in manifest.get("assets", [])}
    for a in new_assets:
        if a.get("freesound_id") not in existing_ids:
            manifest["assets"].append(a)
            existing_ids.add(a.get("freesound_id"))

    _save_json(RUNTIME_MANIFEST, manifest)
    print(f"  Updated manifest → {RUNTIME_MANIFEST.relative_to(REPO_ROOT)}")


def update_pack_index(pack_id: str, month: str, sound_entries: list[dict[str, Any]]) -> None:
    """Append / update the monthly-packs index JSON."""
    index = _load_json(MONTHLY_PACKS_JSON) or {"activePackId": pack_id, "packs": []}

    existing_ids = {p["id"] for p in index.get("packs", [])}
    if pack_id not in existing_ids:
        theme = _month_category(month)["name"].title()
        index["packs"].append({
            "id": pack_id,
            "releaseMonth": month,
            "theme": f"Freesound — {theme}",
            "soundArsenal": sound_entries,
        })

    _save_json(MONTHLY_PACKS_JSON, index)
    print(f"  Updated pack index → {MONTHLY_PACKS_JSON.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# Category rotation
# ---------------------------------------------------------------------------

def _month_category(month: str) -> dict[str, Any]:
    """Deterministically select a category based on the month."""
    year, mon = map(int, month.split("-"))
    # Rotate: January = index 0, February = 1, …
    idx = (mon - 1) % len(CATEGORIES)
    return CATEGORIES[idx]


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(month: str, dry_run: bool) -> None:
    category = _month_category(month)
    pack_id = f"{month}_freesound_{category['name']}"
    pack_dir = PACKS_DIR / pack_id / "sounds"
    tmp_dir = Path("/tmp") / f"freesound_raw_{month}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Monthly Pro Audio Pack: {month} ===")
    print(f"Category : {category['name']}")
    print(f"Query    : {category['query']}")
    print(f"Pack ID  : {pack_id}")
    print(f"Dry run  : {dry_run}")
    print()

    # Load existing manifest to avoid re-downloading known sounds
    manifest = _load_json(RUNTIME_MANIFEST) or {}
    used_ids = _collect_used_ids(manifest)

    print(f"Searching Freesound for '{category['query']}' (CC0, ≤10 s) …")
    sounds = search_cc0_sounds(category["query"], category["count"], used_ids)

    if not sounds:
        print("No new CC0 sounds found for this category. Pack skipped.")
        return

    print(f"Found {len(sounds)} sound(s):")
    for s in sounds:
        print(f"  [{s['id']}] {s['name']} ({s.get('duration', '?'):.1f}s) — {s.get('license')}")

    if dry_run:
        print("Dry run — stopping before download/write.")
        return

    new_assets: list[dict[str, Any]] = []
    new_sounds: list[dict[str, Any]] = []

    for i, sound in enumerate(sounds):
        safe_name = (
            sound["name"]
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )
        # Trim to 40 chars max
        safe_name = safe_name[:40].rstrip("_")
        filename = f"{category['name']}_{i+1:02d}_{safe_name}"

        raw_mp3 = tmp_dir / f"{filename}_raw.mp3"
        final_mp3 = pack_dir / f"{filename}.mp3"

        download_preview(sound, raw_mp3)
        normalise_lufs(raw_mp3, final_mp3)

        asset_entry = build_asset_entry(
            sound=sound,
            normalised_path=final_mp3,
            pack_id=pack_id,
            sound_type=category["soundType"],
            relative_to=RUNTIME_BASE,
        )
        new_assets.append(asset_entry)

        new_sounds.append({
            "soundType": category["soundType"],
            "filename": filename,
            "durationSeconds": round(sound.get("duration", 0.0), 2),
            "freesound_id": sound["id"],
        })

    update_manifest(pack_id, month, new_assets, new_sounds)
    update_pack_index(pack_id, month, new_sounds)

    # Write a per-pack metadata sidecar
    sidecar = PACKS_DIR / pack_id / "pack_meta.json"
    _save_json(sidecar, {
        "packId": pack_id,
        "month": month,
        "category": category["name"],
        "soundType": category["soundType"],
        "query": category["query"],
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "license": "CC0",
        "source": "freesound.org",
        "sounds": new_sounds,
    })

    # Clean up temp files
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print()
    print(f"Pack written to content/pro_audio/runtime/packs/{pack_id}/")
    print(f"  {len(new_assets)} sound(s) downloaded and normalised to {TARGET_LUFS} LUFS")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate monthly Pro audio pack from Freesound CC0 sounds."
    )
    parser.add_argument(
        "--month",
        default=datetime.now(timezone.utc).strftime("%Y-%m"),
        help="Target month in YYYY-MM format (default: current UTC month).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and log results without downloading or writing any files.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    # Validate month format
    try:
        datetime.strptime(args.month, "%Y-%m")
    except ValueError:
        sys.exit(f"ERROR: --month must be YYYY-MM, got: {args.month!r}")
    run(args.month, args.dry_run)
