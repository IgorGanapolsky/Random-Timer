#!/usr/bin/env python3
"""Generate polished iOS App Store screenshot creatives from base captures.

This script overwrites the canonical fastlane screenshot files with branded
headline cards while preserving the underlying app UI in a framed panel.
It keeps a timestamped backup of prior images before rewriting.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class CreativeText:
    title: str
    subtitle: str


CREATIVE_COPY: Dict[str, CreativeText] = {
    "1_setup.png": CreativeText(
        title="SET YOUR RANGE",
        subtitle="Choose any random window from 0s to 60m",
    ),
    "2_active.png": CreativeText(
        title="RANDOM EVERY ROUND",
        subtitle="No predictable countdown. Stay ready.",
    ),
    "3_alarm.png": CreativeText(
        title="REACT ON THE BEEP",
        subtitle="Built for pad work, sparring, and pressure drills",
    ),
    "4_running.png": CreativeText(
        title="LOOP YOUR DRILLS",
        subtitle="Auto-repeat rounds for conditioning blocks",
    ),
    "5_ipad_setup.png": CreativeText(
        title="IPAD COACH VIEW",
        subtitle="Bigger screen for classes and partner sessions",
    ),
    "6_ipad_running.png": CreativeText(
        title="LIVE ROUND FEEDBACK",
        subtitle="Clear status while athletes stay focused",
    ),
    "7_ipad_stopped.png": CreativeText(
        title="RESET AND GO AGAIN",
        subtitle="Fast controls between rounds",
    ),
}


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next Demi Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _blend(top: Color, bottom: Color, t: float) -> Color:
    return (
        int(top[0] * (1.0 - t) + bottom[0] * t),
        int(top[1] * (1.0 - t) + bottom[1] * t),
        int(top[2] * (1.0 - t) + bottom[2] * t),
    )


def _make_gradient(size: Tuple[int, int], top: Color, bottom: Color) -> Image.Image:
    w, h = size
    gradient = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(gradient)
    for y in range(h):
        t = y / max(h - 1, 1)
        draw.line([(0, y), (w, y)], fill=_blend(top, bottom, t))
    return gradient


def _add_glow(base: Image.Image, center: Tuple[int, int], radius: int, color: Color, alpha: int) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy = center
    for ring in range(6, 0, -1):
        rr = int(radius * ring / 6)
        a = int(alpha * (ring / 6) ** 2)
        draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(color[0], color[1], color[2], a))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(8, radius // 8)))
    base.alpha_composite(layer)


def _rounded_mask(size: Tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _panel_rect(size: Tuple[int, int]) -> Tuple[int, int, int, int]:
    w, h = size
    ratio = w / h
    if ratio < 0.6:  # iPhone portrait
        return (int(w * 0.145), int(h * 0.225), int(w * 0.855), int(h * 0.94))
    return (int(w * 0.155), int(h * 0.225), int(w * 0.845), int(h * 0.93))  # iPad portrait


def _render_one(source: Image.Image, text: CreativeText) -> Image.Image:
    base = _make_gradient(source.size, (246, 249, 255), (226, 236, 255)).convert("RGBA")
    w, h = source.size

    _add_glow(base, (int(w * 0.22), int(h * 0.1)), int(min(w, h) * 0.24), (38, 105, 255), 55)
    _add_glow(base, (int(w * 0.82), int(h * 0.18)), int(min(w, h) * 0.26), (255, 154, 76), 40)

    left, top, right, bottom = _panel_rect(source.size)
    panel_w = right - left
    panel_h = bottom - top

    shadow_layer = Image.new("RGBA", source.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rounded_rectangle(
        (left + 10, top + 16, right + 10, bottom + 16),
        radius=max(24, int(panel_w * 0.035)),
        fill=(3, 6, 16, 160),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=14))
    base.alpha_composite(shadow_layer)

    panel_layer = Image.new("RGBA", source.size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel_layer)
    panel_draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=max(24, int(panel_w * 0.035)),
        fill=(255, 255, 255, 245),
        outline=(95, 129, 214, 220),
        width=max(3, int(panel_w * 0.0055)),
    )
    base.alpha_composite(panel_layer)

    inset = max(10, int(panel_w * 0.015))
    target_w = panel_w - 2 * inset
    target_h = panel_h - 2 * inset
    framed = ImageOps.fit(source.convert("RGB"), (target_w, target_h), method=Image.Resampling.LANCZOS)
    framed_rgba = framed.convert("RGBA")
    mask = _rounded_mask((target_w, target_h), radius=max(18, int(panel_w * 0.022)))
    base.paste(framed_rgba, (left + inset, top + inset), mask)
    text_overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_overlay)
    title_font = _load_font(max(58, int(h * 0.036)), bold=True)
    subtitle_font = _load_font(max(30, int(h * 0.017)), bold=False)

    title_bbox = text_draw.textbbox((0, 0), text.title, font=title_font)
    subtitle_bbox = text_draw.textbbox((0, 0), text.subtitle, font=subtitle_font)
    title_w = title_bbox[2] - title_bbox[0]
    subtitle_w = subtitle_bbox[2] - subtitle_bbox[0]
    text_draw.text(((w - title_w) // 2, int(h * 0.07)), text.title, font=title_font, fill=(26, 41, 78, 255))
    text_draw.text(((w - subtitle_w) // 2, int(h * 0.145)), text.subtitle, font=subtitle_font, fill=(65, 87, 136, 255))
    base.alpha_composite(text_overlay)

    return base.convert("RGB")


def generate(repo_root: Path, locale: str) -> Dict[str, object]:
    screenshots_dir = repo_root / "native-ios" / "fastlane" / "screenshots" / locale
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir = screenshots_dir / "_backup" / f"creative-{now}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    backed_up: list[str] = []
    for filename, text in CREATIVE_COPY.items():
        target = screenshots_dir / filename
        if not target.is_file():
            raise FileNotFoundError(f"Missing source screenshot: {target}")

        backup_file = backup_dir / filename
        backup_file.write_bytes(target.read_bytes())
        backed_up.append(str(backup_file))

        source = Image.open(target)
        out = _render_one(source, text)
        out.save(target, format="PNG", optimize=True)
        written.append(str(target))

    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "locale": locale,
        "backup_dir": str(backup_dir),
        "written_files": written,
    }
    report_path = screenshots_dir / "creative-refresh-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(report_path)
    report["backed_up_files"] = backed_up
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate iOS App Store screenshot creatives")
    parser.add_argument("--repo-root", default=".", help="Path to repository root")
    parser.add_argument("--locale", default="en-US", help="Fastlane locale directory")
    args = parser.parse_args()

    report = generate(Path(args.repo_root).resolve(), args.locale)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
