#!/usr/bin/env python3
"""Generate voice callout packs using Chatterbox TTS.

Usage:
    source .venv-chatterbox/bin/activate
    python scripts/generate_voice_pack.py --manifest packs/april-2026.json
    python scripts/generate_voice_pack.py --manifest packs/april-2026.json --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
import torch
import torchaudio

# Monkey-patch Perth watermarker for Apple Silicon compatibility
import perth
if perth.PerthImplicitWatermarker is None:
    perth.PerthImplicitWatermarker = perth.DummyWatermarker

from chatterbox.tts import ChatterboxTTS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IOS_AUDIO = PROJECT_ROOT / "native-ios" / "RandomTimer" / "Resources" / "Audio"
ANDROID_AUDIO = PROJECT_ROOT / "native-android" / "app" / "src" / "main" / "res" / "raw"
TARGET_LUFS = -14.0
SAMPLE_RATE = 24000
BITRATE = "128k"


def load_manifest(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def generate_utterance(model, text: str, seed: int, ref_audio: str | None = None) -> torch.Tensor:
    """Generate a single utterance with deterministic seed."""
    torch.manual_seed(seed)
    kwargs = {}
    if ref_audio:
        kwargs["audio_prompt_path"] = ref_audio
    return model.generate(text, **kwargs)


def normalize_lufs(wav_path: str, target_lufs: float = TARGET_LUFS) -> None:
    """Normalize audio to target LUFS in-place."""
    data, rate = sf.read(wav_path)
    meter = pyln.Meter(rate)
    loudness = meter.integrated_loudness(data)
    if loudness == float("-inf"):
        print(f"  WARNING: Silent audio, skipping normalization")
        return
    normalized = pyln.normalize.loudness(data, loudness, target_lufs)
    sf.write(wav_path, normalized, rate)


def wav_to_mp3(wav_path: str, mp3_path: str) -> None:
    """Convert WAV to MP3 with target encoding settings."""
    subprocess.run([
        "ffmpeg", "-i", wav_path,
        "-ac", "1", "-ar", str(SAMPLE_RATE), "-b:a", BITRATE,
        mp3_path, "-y"
    ], check=True, capture_output=True)


def validate_mp3(mp3_path: str) -> dict:
    """Validate MP3 meets quality requirements."""
    data, rate = sf.read(mp3_path)
    meter = pyln.Meter(rate)
    loudness = meter.integrated_loudness(data)
    duration = len(data) / rate
    channels = 1 if data.ndim == 1 else data.shape[1]
    return {
        "lufs": loudness,
        "duration": duration,
        "channels": channels,
        "sample_rate": rate,
        "valid": -15.5 <= loudness <= -12.5 and 0.5 <= duration <= 10.0 and channels == 1,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate voice packs with Chatterbox TTS")
    parser.add_argument("--manifest", required=True, help="JSON manifest file")
    parser.add_argument("--ref-audio", help="Reference audio for voice cloning")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--device", default="auto", choices=["auto", "mps", "cpu"])
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    print(f"Manifest: {len(manifest)} utterances")

    if args.dry_run:
        for entry in manifest:
            print(f"  [{entry['category']}] {entry['filename']}: {entry['text']}")
        return

    device = args.device
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}")

    print("Loading Chatterbox model...")
    model = ChatterboxTTS.from_pretrained(device=device)
    print("Model ready.\n")

    os.makedirs(IOS_AUDIO, exist_ok=True)
    os.makedirs(ANDROID_AUDIO, exist_ok=True)
    tmp_dir = Path("/tmp/voice_pack_gen")
    tmp_dir.mkdir(exist_ok=True)

    results = []
    for i, entry in enumerate(manifest):
        filename = entry["filename"]
        text = entry["text"]
        seed = entry.get("seed", hash(filename) % 2**32)
        category = entry.get("category", "command")

        print(f"[{i+1}/{len(manifest)}] {filename}: {text[:60]}...")

        # Generate
        wav = generate_utterance(model, text, seed, args.ref_audio)
        wav_path = str(tmp_dir / f"{filename}.wav")
        torchaudio.save(wav_path, wav.cpu(), model.sr)

        # Normalize
        normalize_lufs(wav_path)

        # Convert to MP3
        ios_mp3 = str(IOS_AUDIO / f"{filename}.mp3")
        wav_to_mp3(wav_path, ios_mp3)

        # Copy to Android (stem normalization: hyphens to underscores)
        android_filename = filename.replace("-", "_")
        android_mp3 = str(ANDROID_AUDIO / f"{android_filename}.mp3")
        wav_to_mp3(wav_path, android_mp3)

        # Validate
        v = validate_mp3(ios_mp3)
        status = "OK" if v["valid"] else "FAIL"
        print(f"  → {status} | LUFS: {v['lufs']:.1f} | {v['duration']:.1f}s | {v['channels']}ch | {v['sample_rate']}Hz")
        results.append({"filename": filename, **v})

    # Summary
    passed = sum(1 for r in results if r["valid"])
    print(f"\n{'='*50}")
    print(f"Generated: {len(results)} | Passed: {passed} | Failed: {len(results) - passed}")
    if passed < len(results):
        print("FAILED entries:")
        for r in results:
            if not r["valid"]:
                print(f"  {r['filename']}: LUFS={r['lufs']:.1f} dur={r['duration']:.1f}s")
        sys.exit(1)


if __name__ == "__main__":
    main()
