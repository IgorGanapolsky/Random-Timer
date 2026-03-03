#!/usr/bin/env python3
"""Generate professional App Store marketing screenshots.

Extracts device content from existing framed screenshots and reframes
them with a dark gradient background, bold headline text, and consistent
styling across iPhone and iPad variants.

Usage:
    python scripts/generate_marketing_screenshots.py
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

# --- Config ---

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "native-ios" / "fastlane" / "screenshots" / "en-US"

# Font paths (macOS)
FONT_BOLD = "/System/Library/Fonts/Avenir Next.ttc"
FONT_BOLD_INDEX = 0  # Avenir Next Bold
FONT_MEDIUM = "/System/Library/Fonts/Avenir Next.ttc"
FONT_MEDIUM_INDEX = 5  # Avenir Next Medium

# Colors
BG_TOP = (12, 10, 32)       # Deep dark purple
BG_BOTTOM = (18, 14, 48)    # Slightly lighter dark purple
ACCENT = (120, 80, 220)     # Purple accent (matches app theme)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (180, 180, 200)
GLOW_COLOR = (100, 60, 200, 40)  # Purple glow around device

# Device content crop regions - adjusted for raw 1320x2868 captures from simulator/device.
# We crop to skip the status bar (top ~120px) and home indicator (bottom ~100px).
IPHONE_DEVICE_CROP = (0, 120, 1320, 2750)  # Full width, skip status/home
IPAD_DEVICE_CROP = (0, 0, 2048, 2732)       # iPad is usually captured full-screen

# Output dimensions (App Store requirements)
IPHONE_SIZE = (1290, 2796)
IPAD_SIZE = (2048, 2732)

# Screenshot definitions: (filename, headline, subtitle, is_ipad)
SCREENSHOTS = [
    ("1_setup.png", "YOUR DRILL, YOUR RULES", "Customize timing from 30s to 10 min", False),
    ("2_active.png", "UNPREDICTABLE BY DESIGN", "You never know when it fires", False),
    ("3_alarm.png", "REACT ON THE BEEP", "Built for pad work, sparring & HIIT", False),
    ("4_running.png", "NON-STOP CONDITIONING", "Auto-loop for continuous rounds", False),
    ("5_ipad_setup.png", "COACH VIEW", "Big screen for classes & partners", True),
    ("6_ipad_running.png", "VISIBLE ACROSS THE GYM", "Full-screen timer for group drills", True),
    ("7_ipad_stopped.png", "ROUND COMPLETE", "Clear feedback after every drill", True),
]


def create_gradient(size: tuple[int, int], top_color: tuple, bottom_color: tuple) -> Image.Image:
    """Create a vertical gradient background."""
    w, h = size
    img = Image.new("RGB", size)
    pixels = img.load()
    for y in range(h):
        ratio = y / h
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        for x in range(w):
            pixels[x, y] = (r, g, b)
    return img


def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
    """Add rounded corners to an image, returning RGBA."""
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)
    result = img.convert("RGBA")
    result.putalpha(mask)
    return result


def add_device_glow(canvas: Image.Image, device_box: tuple[int, int, int, int], radius: int = 30) -> None:
    """Add a subtle purple glow around the device frame."""
    left, top, right, bottom = device_box
    glow_expand = 8
    glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow_layer)
    draw.rounded_rectangle(
        [(left - glow_expand, top - glow_expand),
         (right + glow_expand, bottom + glow_expand)],
        radius=radius + glow_expand,
        fill=GLOW_COLOR,
    )
    # Blur the glow
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=15))
    canvas.paste(Image.alpha_composite(Image.new("RGBA", canvas.size, (0, 0, 0, 0)), glow_layer))


def generate_screenshot(
    source_path: Path,
    output_path: Path,
    headline: str,
    subtitle: str,
    is_ipad: bool,
) -> None:
    """Generate a single marketing screenshot."""
    target_size = IPAD_SIZE if is_ipad else IPHONE_SIZE
    crop_box = IPAD_DEVICE_CROP if is_ipad else IPHONE_DEVICE_CROP
    tw, th = target_size

    # Load and crop device content from raw screenshot
    source = Image.open(source_path)
    # Ensure crop box is within source bounds
    sw, sh = source.size
    actual_crop = (
        max(0, crop_box[0]),
        max(0, crop_box[1]),
        min(sw, crop_box[2]),
        min(sh, crop_box[3])
    )
    device_content = source.crop(actual_crop)

    # Create dark gradient canvas
    canvas = create_gradient(target_size, BG_TOP, BG_BOTTOM).convert("RGBA")

    # Layout calculations
    headline_area_height = int(th * 0.16)  # Top 16% for text
    device_area_top = headline_area_height
    device_area_height = th - device_area_top - int(th * 0.04)  # 4% bottom padding
    margin_x = int(tw * 0.08)  # 8% horizontal margin
    device_area_width = tw - (margin_x * 2)

    # Scale device content to fit the device area while preserving aspect ratio
    dw, dh = device_content.size
    scale = min(device_area_width / dw, device_area_height / dh)
    new_dw = int(dw * scale)
    new_dh = int(dh * scale)
    device_content = device_content.resize((new_dw, new_dh), Image.Resampling.LANCZOS)

    # Add rounded corners to device content
    corner_radius = int(new_dw * 0.04)  # 4% of width
    device_content = add_rounded_corners(device_content, corner_radius)

    # Center device content horizontally
    device_x = (tw - new_dw) // 2
    device_y = device_area_top + (device_area_height - new_dh) // 2

    # Add glow effect around device
    add_device_glow(canvas, (device_x, device_y, device_x + new_dw, device_y + new_dh), corner_radius)

    # Add thin border around device
    border_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_layer)
    border_draw.rounded_rectangle(
        [(device_x - 2, device_y - 2), (device_x + new_dw + 1, device_y + new_dh + 1)],
        radius=corner_radius + 2,
        outline=(*ACCENT, 100),
        width=2,
    )
    canvas = Image.alpha_composite(canvas, border_layer)

    # Paste device content
    canvas.paste(device_content, (device_x, device_y), device_content)

    # Add headline text — auto-scaled to fit within 90% width
    max_text_width = int(tw * 0.90)
    headline_font_size = int(th * 0.042)
    subtitle_font_size = int(th * 0.020)

    # Auto-scale headline font to fit width
    while headline_font_size > 40:
        headline_font = ImageFont.truetype(FONT_BOLD, headline_font_size, index=FONT_BOLD_INDEX)
        test_draw = ImageDraw.Draw(canvas)
        bbox = test_draw.textbbox((0, 0), headline, font=headline_font)
        if (bbox[2] - bbox[0]) <= max_text_width:
            break
        headline_font_size -= 2

    subtitle_font = ImageFont.truetype(FONT_MEDIUM, subtitle_font_size, index=FONT_MEDIUM_INDEX)
    text_draw = ImageDraw.Draw(canvas)

    # Headline - centered, bold white
    h_bbox = text_draw.textbbox((0, 0), headline, font=headline_font)
    h_w = h_bbox[2] - h_bbox[0]
    h_h = h_bbox[3] - h_bbox[1]
    headline_y = int(th * 0.04)  # 4% from top
    text_draw.text(
        ((tw - h_w) // 2, headline_y),
        headline,
        fill=TEXT_WHITE,
        font=headline_font,
    )

    # Subtitle - centered, light gray
    s_bbox = text_draw.textbbox((0, 0), subtitle, font=subtitle_font)
    s_w = s_bbox[2] - s_bbox[0]
    subtitle_y = headline_y + h_h + int(th * 0.015)
    text_draw.text(
        ((tw - s_w) // 2, subtitle_y),
        subtitle,
        fill=TEXT_GRAY,
        font=subtitle_font,
    )

    # Convert to RGB and save
    final = canvas.convert("RGB")
    final.save(output_path, "PNG", optimize=True)
    print(f"  Generated: {output_path.name} ({final.size[0]}x{final.size[1]})")


def main() -> int:
    print("Generating marketing screenshots from raw originals...")
    print(f"Source dir: {SCREENSHOT_DIR}/originals")

    # Use the originals directory we just populated
    raw_dir = SCREENSHOT_DIR / "originals"
    if not raw_dir.exists():
        print(f"  ERROR: {raw_dir} not found. Please restore raw screenshots first.")
        return 1

    for filename, headline, subtitle, is_ipad in SCREENSHOTS:
        source_path = raw_dir / filename
        if not source_path.exists():
            print(f"  SKIP: {filename} not found in originals")
            continue

        output_path = SCREENSHOT_DIR / filename
        
        # Generate new marketing screenshot
        generate_screenshot(
            source_path=source_path,
            output_path=output_path,
            headline=headline,
            subtitle=subtitle,
            is_ipad=is_ipad,
        )

    print("\nDone! Screenshots regenerated in:")
    print(f"  {SCREENSHOT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
