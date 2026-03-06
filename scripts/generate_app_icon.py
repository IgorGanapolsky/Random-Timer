#!/usr/bin/env python3
"""Tactical App Icon Generator.

Generates a high-fidelity 1024x1024 App Store icon with:
- Deep background depth
- Tactical Red (#EF4444) glowing timer ring
- Precise geometric center-mark
"""

from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def generate_icon(output_path: Path):
    size = 1024
    # Create base with deep tactical gradient
    icon = Image.new("RGB", (size, size), (10, 12, 18))
    draw = ImageDraw.Draw(icon)
    
    # Outer glow
    glow_size = int(size * 0.8)
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Draw a soft red glow behind the ring
    glow_color = (239, 68, 68, 40) # EF4444 with low alpha
    center = size // 2
    glow_draw.ellipse(
        (center - glow_size // 2, center - glow_size // 2, center + glow_size // 2, center + glow_size // 2),
        fill=glow_color
    )
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    icon.paste(glow, (0, 0), glow)
    
    # Draw the main timer ring (track)
    ring_margin = int(size * 0.15)
    ring_width = int(size * 0.08)
    draw.ellipse(
        (ring_margin, ring_margin, size - ring_margin, size - ring_margin),
        outline=(40, 45, 60),
        width=ring_width
    )
    
    # Draw the active segment (Tactical Red)
    # We draw an arc from -90 (top) to 45 degrees
    draw.arc(
        (ring_margin, ring_margin, size - ring_margin, size - ring_margin),
        start=-90,
        end=60,
        fill=(239, 68, 68),
        width=ring_width
    )
    
    # Draw the tip of the active segment with a small highlight
    # (Calculated roughly)
    
    # Center Mark (Tactical Crosshair/Timer symbol)
    mark_size = int(size * 0.12)
    draw.ellipse(
        (center - mark_size, center - mark_size, center + mark_size, center + mark_size),
        outline=(255, 255, 255),
        width=int(size * 0.02)
    )
    
    # Small inner dot
    dot_size = int(size * 0.02)
    draw.ellipse(
        (center - dot_size, center - dot_size, center + dot_size, center + dot_size),
        fill=(239, 68, 68)
    )

    # Save
    icon.save(output_path, format="PNG")
    print(f"Generated tactical icon at {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png")
    args = parser.parse_args()
    generate_icon(Path(args.output))
