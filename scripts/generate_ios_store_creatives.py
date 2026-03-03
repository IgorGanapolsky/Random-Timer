#!/usr/bin/env python3
"""Generate conversion-focused iOS App Store screenshot creatives.

This script rewrites canonical fastlane screenshots with tactical-styled
headline overlays while preserving the app UI in a framed panel.
It keeps a timestamped backup before rewriting.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class CreativeText:
    title: str
    subtitle: str
    badge: str


CREATIVE_COPY: Dict[str, CreativeText] = {
    "1_setup.png": CreativeText(
        title="TRAINING ON YOUR TERMS",
        subtitle="Set a random trigger window from seconds to minutes.",
        badge="SET RANGE",
    ),
    "2_active.png": CreativeText(
        title="UNPREDICTABLE BY DESIGN",
        subtitle="No fixed countdown, so your reaction stays honest.",
        badge="START ROUND",
    ),
    "3_alarm.png": CreativeText(
        title="REACT THE INSTANT IT HITS",
        subtitle="Sharp beep cues explosive first movement under pressure.",
        badge="HIT NOW",
    ),
    "4_running.png": CreativeText(
        title="RUN NON-STOP ROUNDS",
        subtitle="Auto-loop sessions for conditioning and sparring blocks.",
        badge="ENABLE LOOP",
    ),
    "5_ipad_setup.png": CreativeText(
        title="COACH VIEW ON IPAD",
        subtitle="Dial in range, sound, and vibration for group sessions.",
        badge="SET CLASS",
    ),
    "6_ipad_running.png": CreativeText(
        title="VISIBLE ACROSS THE GYM",
        subtitle="Large live timer keeps every athlete synchronized.",
        badge="RUN SESSION",
    ),
    "7_ipad_stopped.png": CreativeText(
        title="RESET BETWEEN ROUNDS",
        subtitle="Adjust fast and launch the next drill in seconds.",
        badge="GO AGAIN",
    ),
}

# Safe source mapping avoids known bad/PII-prone captures in canonical files.
SOURCE_MAP: Dict[str, str] = {
    "1_setup.png": "2_active.png",
    "2_active.png": "4_running.png",
    "3_alarm.png": "4_running.png",
    "4_running.png": "2_active.png",
    # Use 13-inch originals to preserve 2064x2752 iPad class dimensions.
    "5_ipad_setup.png": "originals/5_ipad_setup.png",
    "6_ipad_running.png": "originals/6_ipad_running.png",
    "7_ipad_stopped.png": "originals/7_ipad_stopped.png",
}


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next Condensed Heavy.ttf" if bold else "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
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
    for ring in range(7, 0, -1):
        rr = int(radius * ring / 7)
        a = int(alpha * (ring / 7) ** 2)
        draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(color[0], color[1], color[2], a))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(10, radius // 8)))
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
        return (int(w * 0.08), int(h * 0.24), int(w * 0.92), int(h * 0.95))
    return (int(w * 0.09), int(h * 0.23), int(w * 0.91), int(h * 0.94))  # iPad portrait


def _source_image(screenshots_dir: Path, target_filename: str) -> Image.Image:
    source_rel = SOURCE_MAP.get(target_filename, target_filename)
    source_path = screenshots_dir / source_rel
    if not source_path.is_file():
        fallback_path = screenshots_dir / target_filename
        if source_rel != target_filename and fallback_path.is_file():
            source_path = fallback_path
        else:
            raise FileNotFoundError(
                f"Missing source screenshot for {target_filename}: {source_path}"
            )
    return Image.open(source_path).convert("RGB")


def _render_one(source: Image.Image, text: CreativeText) -> Image.Image:
    base = _make_gradient(source.size, (8, 12, 22), (18, 26, 45)).convert("RGBA")
    w, h = source.size

    _add_glow(base, (int(w * 0.20), int(h * 0.10)), int(min(w, h) * 0.25), (244, 73, 58), 75)
    _add_glow(base, (int(w * 0.84), int(h * 0.14)), int(min(w, h) * 0.22), (255, 148, 58), 65)

    left, top, right, bottom = _panel_rect(source.size)
    panel_w = right - left
    panel_h = bottom - top

    shadow_layer = Image.new("RGBA", source.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rounded_rectangle(
        (left + 10, top + 12, right + 10, bottom + 12),
        radius=max(28, int(panel_w * 0.035)),
        fill=(0, 0, 0, 165),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=16))
    base.alpha_composite(shadow_layer)

    panel_layer = Image.new("RGBA", source.size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel_layer)
    panel_draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=max(28, int(panel_w * 0.035)),
        fill=(12, 18, 30, 238),
        outline=(255, 112, 72, 238),
        width=max(4, int(panel_w * 0.006)),
    )
    base.alpha_composite(panel_layer)

    inset = max(12, int(panel_w * 0.016))
    target_w = panel_w - 2 * inset
    target_h = panel_h - 2 * inset
    framed = ImageOps.fit(source, (target_w, target_h), method=Image.Resampling.LANCZOS)
    framed_rgba = framed.convert("RGBA")
    mask = _rounded_mask((target_w, target_h), radius=max(20, int(panel_w * 0.022)))
    base.paste(framed_rgba, (left + inset, top + inset), mask)

    text_overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_overlay)

    title_font = _load_font(max(54, int(h * 0.034)), bold=True)
    subtitle_font = _load_font(max(28, int(h * 0.016)), bold=False)
    badge_font = _load_font(max(24, int(h * 0.014)), bold=True)

    title_bbox = text_draw.textbbox((0, 0), text.title, font=title_font)
    subtitle_bbox = text_draw.textbbox((0, 0), text.subtitle, font=subtitle_font)
    title_w = title_bbox[2] - title_bbox[0]
    subtitle_w = subtitle_bbox[2] - subtitle_bbox[0]

    text_draw.text(((w - title_w) // 2, int(h * 0.065)), text.title, font=title_font, fill=(244, 248, 255, 255))
    text_draw.text(((w - subtitle_w) // 2, int(h * 0.132)), text.subtitle, font=subtitle_font, fill=(192, 208, 230, 255))

    badge_w = int(w * 0.26)
    badge_h = int(h * 0.048)
    badge_x = (w - badge_w) // 2
    badge_y = int(h * 0.175)
    text_draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        radius=max(16, int(badge_h * 0.45)),
        fill=(244, 73, 58, 245),
        outline=(255, 171, 96, 245),
        width=max(2, int(badge_h * 0.07)),
    )
    badge_bbox = text_draw.textbbox((0, 0), text.badge, font=badge_font)
    badge_text_w = badge_bbox[2] - badge_bbox[0]
    badge_text_h = badge_bbox[3] - badge_bbox[1]
    text_draw.text(
        (badge_x + (badge_w - badge_text_w) // 2, badge_y + (badge_h - badge_text_h) // 2 - 1),
        text.badge,
        font=badge_font,
        fill=(255, 250, 248, 255),
    )

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
            raise FileNotFoundError(f"Missing target screenshot to overwrite: {target}")

        backup_file = backup_dir / filename
        backup_file.write_bytes(target.read_bytes())
        backed_up.append(str(backup_file))

        source = _source_image(screenshots_dir, filename)
        out = _render_one(source, text)
        out.save(target, format="PNG", optimize=True)
        written.append(str(target))

    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "locale": locale,
        "backup_dir": str(backup_dir),
        "written_files": written,
        "backed_up_files": backed_up,
        "source_map": SOURCE_MAP,
    }
    report_path = screenshots_dir / "creative-refresh-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(report_path)
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
