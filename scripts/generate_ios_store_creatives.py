#!/usr/bin/env python3
"""Generate App Store screenshot creatives from clean raw captures.

The generator reads raw simulator captures from the locale's ``originals/``
folder and writes the composed App Store PNGs into the locale root. This
prevents nested compositions and keeps the raw source inventory intact.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class CreativeSpec:
    source: str
    eyebrow: str
    title: str
    subtitle: str
    focus_y: float = 0.5
    crop_box: Tuple[float, float, float, float] | None = None


CREATIVE_SPECS: Dict[str, CreativeSpec] = {
    "1_setup.png": CreativeSpec(
        source="iphone_setup_raw.png",
        eyebrow="RANDOM START",
        title="SET THE WINDOW. WAIT FOR THE CUE.",
        subtitle="Choose a minimum and maximum trigger time in seconds and stop training to a predictable beep.",
        focus_y=0.44,
    ),
    "2_active.png": CreativeSpec(
        source="iphone_running_raw.png",
        eyebrow="LIVE DRILL",
        title="REACT WHEN IT HITS.",
        subtitle="No fixed countdown rhythm. Hold ready, wait for the signal, and move only when it fires.",
        focus_y=0.48,
    ),
    "3_alarm.png": CreativeSpec(
        source="iphone_sound_raw.png",
        eyebrow="AUDIO",
        title="TUNE SOUND, HAPTICS, AND VOICE PREVIEWS.",
        subtitle="Pick the alert profile, preview the cue, and set the feel before the first rep starts.",
        focus_y=0.54,
    ),
    "4_running.png": CreativeSpec(
        source="iphone_paused_raw.png",
        eyebrow="CONTROL",
        title="RESET FAST. RUN AGAIN.",
        subtitle="Pause, resume, and restart without digging through menus between honest reps.",
        focus_y=0.48,
    ),
    "5_ipad_setup.png": CreativeSpec(
        source="ipad_setup_raw.png",
        eyebrow="IPAD VIEW",
        title="COACH THE DRILL ON A BIG SCREEN.",
        subtitle="Large controls and readable status make partner work and group demos easier to run.",
        focus_y=0.42,
    ),
    "6_ipad_running.png": CreativeSpec(
        source="ipad_setup_raw.png",
        eyebrow="IPAD VIEW",
        title="SET RANGE AND LAUNCH THE NEXT REP FAST.",
        subtitle="Coaches can adjust the trigger window, confirm the output mode, and start the next drill without crowding around a phone.",
        focus_y=0.48,
        crop_box=(0.04, 0.04, 0.96, 0.82),
    ),
    "7_ipad_stopped.png": CreativeSpec(
        source="ipad_sound_raw.png",
        eyebrow="IPAD VIEW",
        title="ADJUST AUDIO AND HAPTICS BEFORE THE FIRST REP.",
        subtitle="Preview the cue, set the output level, and hand the tablet to a coach or training partner.",
        focus_y=0.56,
    ),
}


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next Condensed Heavy.ttf" if bold else "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        candidate_width = draw.textbbox((0, 0), candidate, font=font)[2]
        if candidate_width <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def _draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    spacing = max(44, width // 18)
    color = (34, 38, 46)
    for x in range(0, width, spacing):
        draw.line((x, 0, x, height), fill=color, width=1)
    for y in range(0, height, spacing):
        draw.line((0, y, width, y), fill=color, width=1)


def _apply_tactical_lighting(base: Image.Image) -> None:
    width, height = base.size
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        (-int(width * 0.15), -int(height * 0.08), int(width * 0.48), int(height * 0.36)),
        fill=(166, 29, 29, 84),
    )
    glow_draw.ellipse(
        (int(width * 0.52), -int(height * 0.18), int(width * 1.08), int(height * 0.28)),
        fill=(112, 20, 20, 64),
    )
    glow_draw.rectangle(
        (0, int(height * 0.66), width, height),
        fill=(12, 15, 20, 190),
    )
    base.alpha_composite(glow)


def _render_one(source: Image.Image, spec: CreativeSpec) -> Image.Image:
    w, h = source.size

    base = Image.new("RGBA", (w, h), (11, 13, 18, 255))
    draw = ImageDraw.Draw(base)
    _draw_grid(draw, w, h)
    _apply_tactical_lighting(base)
    draw = ImageDraw.Draw(base)

    left = int(w * 0.08)
    right_margin = int(w * 0.08)
    header_top = int(h * 0.07)
    header_width = w - left - right_margin
    accent_x = left
    draw.rounded_rectangle(
        (accent_x, header_top, accent_x + int(w * 0.012), header_top + int(h * 0.12)),
        radius=8,
        fill=(213, 45, 45, 255),
    )

    eyebrow_font = _load_font(max(26, int(h * 0.015)), bold=True)
    title_font = _load_font(max(66, int(h * 0.038)), bold=True)
    subtitle_font = _load_font(max(30, int(h * 0.018)), bold=False)

    eyebrow_x = accent_x + int(w * 0.03)
    draw.text((eyebrow_x, header_top + int(h * 0.003)), spec.eyebrow, font=eyebrow_font, fill=(224, 85, 85, 255))

    wrapped_title = _wrap_text(draw, spec.title, title_font, header_width - int(w * 0.03))
    title_y = header_top + int(h * 0.032)
    draw.multiline_text(
        (eyebrow_x, title_y),
        wrapped_title,
        font=title_font,
        fill=(247, 248, 250, 255),
        spacing=int(h * 0.007),
    )

    title_bbox = draw.multiline_textbbox((eyebrow_x, title_y), wrapped_title, font=title_font, spacing=int(h * 0.007))
    subtitle_y = title_bbox[3] + int(h * 0.018)
    wrapped_subtitle = _wrap_text(draw, spec.subtitle, subtitle_font, header_width - int(w * 0.05))
    draw.multiline_text(
        (eyebrow_x, subtitle_y),
        wrapped_subtitle,
        font=subtitle_font,
        fill=(192, 198, 208, 255),
        spacing=int(h * 0.006),
    )

    card_margin_x = int(w * 0.05)
    card_top = int(h * 0.30)
    card_bottom = h - int(h * 0.055)
    card_w = w - (card_margin_x * 2)
    card_h = card_bottom - card_top
    shadow_offset = int(w * 0.008)
    draw.rounded_rectangle(
        (card_margin_x + shadow_offset, card_top + shadow_offset, card_margin_x + card_w + shadow_offset, card_bottom + shadow_offset),
        radius=int(w * 0.03),
        fill=(0, 0, 0, 82),
    )
    draw.rounded_rectangle(
        (card_margin_x, card_top, card_margin_x + card_w, card_bottom),
        radius=int(w * 0.03),
        fill=(16, 18, 24, 255),
        outline=(56, 60, 70, 255),
        width=max(2, int(w * 0.0022)),
    )

    inner_pad = int(w * 0.018)
    target_w = card_w - inner_pad * 2
    target_h = card_h - inner_pad * 2
    if spec.crop_box is not None:
        left, top, right, bottom = spec.crop_box
        crop = (
            int(source.width * left),
            int(source.height * top),
            int(source.width * right),
            int(source.height * bottom),
        )
        source = source.crop(crop)
    ui_frame = ImageOps.fit(
        source,
        (target_w, target_h),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, spec.focus_y),
    )
    base.alpha_composite(ui_frame.convert("RGBA"), dest=(card_margin_x + inner_pad, card_top + inner_pad))

    footer_y = h - int(h * 0.04)
    draw.line((left, footer_y, w - right_margin, footer_y), fill=(42, 46, 54, 255), width=max(2, int(w * 0.0015)))

    return base.convert("RGB")


def generate(repo_root: Path, locale: str, *, source_subdir: str = "originals") -> Dict[str, object]:
    screenshots_dir = repo_root / "native-ios" / "fastlane" / "screenshots" / locale
    source_dir = screenshots_dir / source_subdir
    written: list[str] = []

    if not screenshots_dir.is_dir():
        raise FileNotFoundError(f"Screenshots directory not found: {screenshots_dir}")
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Raw source directory not found: {source_dir}")

    backup_root = screenshots_dir / "_backup"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / timestamp

    for filename, spec in CREATIVE_SPECS.items():
        source_path = source_dir / spec.source
        if not source_path.is_file():
            raise FileNotFoundError(f"Source screenshot not found: {source_path}")

        target = screenshots_dir / filename
        if target.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_dir / filename)

        source = Image.open(source_path).convert("RGB")
        out = _render_one(source, spec)
        out.save(target, format="PNG", optimize=True)
        written.append(str(target))

    report = {
        "status": "success",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "locale": locale,
        "source_dir": str(source_dir),
        "written_files": written,
        "backup_dir": str(backup_dir) if written else None,
        "report_path": str(screenshots_dir / "report.json"),
    }

    with open(report["report_path"], "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--source-subdir", default="originals")
    args = parser.parse_args()
    print(json.dumps(generate(Path(args.repo_root), args.locale, source_subdir=args.source_subdir), indent=2))
