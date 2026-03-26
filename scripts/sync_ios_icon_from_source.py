#!/usr/bin/env python3
"""Regenerate iOS AppIcon.appiconset PNGs from a single square source icon."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"Pillow is required: {exc}")


def _parse_pixels(entry: Dict[str, Any]) -> int:
    size_text = str(entry.get("size", "0x0")).strip().lower()
    scale_text = str(entry.get("scale", "1x")).strip().lower()
    base = float(size_text.split("x")[0])
    scale = float(scale_text.replace("x", ""))
    return int(round(base * scale))


def _background_rgba(image: Image.Image) -> Tuple[int, int, int, int]:
    width, height = image.size
    corners = [
        image.getpixel((0, 0)),
        image.getpixel((width - 1, 0)),
        image.getpixel((0, height - 1)),
        image.getpixel((width - 1, height - 1)),
    ]
    for r, g, b, a in corners:
        if a == 255:
            return (r, g, b, 255)

    r, g, b, _a = corners[0]
    return (r, g, b, 255)


def _flatten_to_opaque_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, _background_rgba(rgba))
    return Image.alpha_composite(background, rgba).convert("RGB")


def run(source: Path, appiconset: Path) -> Dict[str, Any]:
    contents_path = appiconset / "Contents.json"
    if not source.exists():
        return {"status": "error", "reason": f"source icon missing: {source}"}
    if not contents_path.exists():
        return {"status": "error", "reason": f"Contents.json missing: {contents_path}"}

    try:
        payload = json.loads(contents_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"status": "error", "reason": f"invalid Contents.json: {exc}"}

    images = payload.get("images", [])
    if not isinstance(images, list):
        return {"status": "error", "reason": "Contents.json has invalid images list"}

    src = Image.open(source).convert("RGBA")
    written = []
    for image in images:
        if not isinstance(image, dict):
            continue
        filename = image.get("filename")
        if not filename:
            continue
        pixels = _parse_pixels(image)
        if pixels <= 0:
            continue
        out = appiconset / str(filename)
        resized = src.resize((pixels, pixels), Image.Resampling.LANCZOS)
        flattened = _flatten_to_opaque_rgb(resized)
        flattened.save(out, format="PNG")
        written.append({"file": str(out), "pixels": pixels})

    return {"status": "ok", "written_count": len(written), "files": written}


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate iOS iconset from source PNG")
    parser.add_argument(
        "--source",
        default="branding/app-icon-source.png",
        help="Source icon PNG",
    )
    parser.add_argument(
        "--appiconset",
        default="native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset",
        help="Path to AppIcon.appiconset",
    )
    args = parser.parse_args()

    result = run(Path(args.source), Path(args.appiconset))
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
