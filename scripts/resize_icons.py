#!/usr/bin/env python3
"""App Icon Resizer.

Takes a 1024x1024 icon and generates all required sizes for iOS.
"""

import json
from pathlib import Path
from PIL import Image

def resize_icons(icon_1024: Path, appiconset_dir: Path):
    with open(appiconset_dir / "Contents.json") as f:
        contents = json.load(f)
    
    base_img = Image.open(icon_1024).convert("RGBA")
    
    for entry in contents["images"]:
        size_str = entry["size"].split("x")
        base_size = float(size_str[0])
        scale = float(entry["scale"].replace("x", ""))
        target_size = int(base_size * scale)
        
        filename = entry["filename"]
        target_path = appiconset_dir / filename
        
        resized = base_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        resized.save(target_path, format="PNG")
        print(f"Generated {filename} ({target_size}x{target_size})")

if __name__ == "__main__":
    resize_icons(
        Path("native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png"),
        Path("native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset")
    )
