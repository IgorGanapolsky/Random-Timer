#!/usr/bin/env python3
"""Refresh iOS App Store screenshots with cleaner ASO overlays.

Keeps original pixel dimensions and file names so fastlane upload paths stay stable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont


CAPTIONS: Dict[str, Tuple[str, str]] = {
    "1_setup.png": ("Random Interval Training", "Set a range. Start in one tap."),
    "2_active.png": ("No Predictable Countdown", "Alarm triggers at an unpredictable moment."),
    "3_alarm.png": ("React Under Pressure", "Train focus, timing, and composure."),
    "5_ipad_setup.png": ("Coach-Ready on iPad", "Large-screen setup for team drills."),
    "6_ipad_running.png": ("Live Random Rounds", "Run sessions without timing patterns."),
    "7_ipad_stopped.png": ("Reset Fast", "Repeat quality reps with one tap."),
}

PRIMARY_COLOR = (9, 26, 48)
ACCENT_COLOR = (86, 207, 255)
TEXT_COLOR = (244, 250, 255)
SUBTEXT_COLOR = (198, 224, 244)


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/SFNS.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/HelveticaNeue.ttc",
            ]
        )
    else:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Helvetica.ttc",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
            ]
        )

    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> str:
    words = text.split()
    if not words:
        return ""

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        w, _ = _measure_text(draw, candidate, font)
        if w <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return "\n".join(lines)


def apply_overlay(image_path: Path, title: str, subtitle: str) -> None:
    base = Image.open(image_path).convert("RGBA")
    width, height = base.size

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    top_h = int(height * 0.26)
    for y in range(top_h):
        alpha = int(232 - 170 * (y / max(1, top_h)))
        draw.line([(0, y), (width, y)], fill=(*PRIMARY_COLOR, alpha), width=1)

    for y in range(int(height * 0.18)):
        real_y = height - y - 1
        alpha = int(145 * (y / max(1, int(height * 0.18))))
        draw.line([(0, real_y), (width, real_y)], fill=(6, 16, 30, alpha), width=1)

    left = int(width * 0.05)
    right = width - left
    box_top = int(height * 0.04)
    box_bottom = int(height * 0.22)
    draw.rounded_rectangle(
        [(left, box_top), (right, box_bottom)],
        radius=int(width * 0.02),
        fill=(8, 24, 44, 184),
        outline=(*ACCENT_COLOR, 178),
        width=max(2, width // 480),
    )

    pill_w = int(width * 0.21)
    pill_h = int(height * 0.043)
    pill_left = left + int(width * 0.02)
    pill_top = box_top + int(height * 0.018)
    draw.rounded_rectangle(
        [(pill_left, pill_top), (pill_left + pill_w, pill_top + pill_h)],
        radius=int(pill_h / 2),
        fill=(18, 43, 70, 220),
    )

    tag_font = _load_font(max(20, width // 54), bold=True)
    title_font = _load_font(max(44, width // 25), bold=True)
    subtitle_font = _load_font(max(26, width // 44), bold=False)

    draw.text(
        (pill_left + int(width * 0.016), pill_top + int(height * 0.006)),
        "RANDOM TACTICAL TIMER",
        fill=ACCENT_COLOR,
        font=tag_font,
    )

    text_x = left + int(width * 0.02)
    max_text_w = int(width * 0.86)
    wrapped_title = _wrap_text(draw, title, title_font, max_text_w)
    wrapped_subtitle = _wrap_text(draw, subtitle, subtitle_font, max_text_w)

    title_y = pill_top + pill_h + int(height * 0.014)
    draw.multiline_text(
        (text_x, title_y),
        wrapped_title,
        font=title_font,
        fill=TEXT_COLOR,
        spacing=int(height * 0.008),
    )

    _, title_height = _measure_text(draw, wrapped_title.split("\n")[0], title_font)
    subtitle_y = title_y + title_height + int(height * 0.032)
    draw.multiline_text(
        (text_x, subtitle_y),
        wrapped_subtitle,
        font=subtitle_font,
        fill=SUBTEXT_COLOR,
        spacing=int(height * 0.006),
    )

    result = Image.alpha_composite(base, overlay).convert("RGB")
    result.save(image_path, format="PNG", optimize=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    screenshots_dir = root / "native-ios" / "fastlane" / "screenshots" / "en-US"

    missing = [name for name in CAPTIONS if not (screenshots_dir / name).is_file()]
    if missing:
        print("Missing screenshot files:")
        for name in missing:
            print(f"- {screenshots_dir / name}")
        return 1

    for name, (title, subtitle) in CAPTIONS.items():
        path = screenshots_dir / name
        apply_overlay(path, title, subtitle)
        print(f"updated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
