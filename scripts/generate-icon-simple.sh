#!/bin/bash

# Create a simple colored square as placeholder icons
# Purple gradient colors: #667eea to #764ba2

echo "Generating placeholder app icons..."

# Create assets directory if it doesn't exist
mkdir -p assets

# Check if ImageMagick is installed
if command -v convert &> /dev/null
then
    echo "Using ImageMagick to generate icons..."
    
    # Generate main icon (1024x1024)
    convert -size 1024x1024 \
        gradient:'#667eea-#764ba2' \
        -gravity center \
        -fill white \
        -font Helvetica-Bold \
        -pointsize 200 \
        -annotate +0+0 'RT' \
        assets/icon.png
    
    # Copy for adaptive icon
    cp assets/icon.png assets/adaptive-icon.png
    
    # Generate splash screen
    convert -size 1242x2436 \
        gradient:'#667eea-#764ba2' \
        -gravity center \
        -fill white \
        -font Helvetica-Bold \
        -pointsize 150 \
        -annotate +0-300 'Random Timer' \
        -pointsize 60 \
        -annotate +0-100 'Chaotic intervals' \
        assets/splash.png
    
    echo "✅ Icons generated with ImageMagick"
else
    echo "ImageMagick not found. Creating solid color placeholders..."
    
    # Use Python to create simple colored squares
    python3 << 'EOF'
import os

# Create a simple PNG with solid color
def create_png(filename, width, height, color=(102, 126, 234)):
    """Create a simple colored PNG file"""
    import struct
    import zlib
    
    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return struct.pack("!I", len(data)) + chunk_head + struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head))
    
    # PNG header
    png_data = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0)
    png_data += png_pack(b'IHDR', ihdr_data)
    
    # IDAT chunk (simple colored rectangle)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter type
        for x in range(width):
            # Gradient effect
            t = y / height
            r = int(color[0] * (1-t) + 118 * t)
            g = int(color[1] * (1-t) + 75 * t)
            b = int(color[2] * (1-t) + 162 * t)
            raw_data += struct.pack("BBB", r, g, b)
    
    png_data += png_pack(b'IDAT', zlib.compress(raw_data, 9))
    
    # IEND chunk
    png_data += png_pack(b'IEND', b'')
    
    # Write file
    with open(filename, 'wb') as f:
        f.write(png_data)
    print(f"Created {filename}")

# Ensure assets directory exists
os.makedirs('assets', exist_ok=True)

# Create icons
create_png('assets/icon.png', 1024, 1024)
create_png('assets/adaptive-icon.png', 1024, 1024)
create_png('assets/splash.png', 1242, 2436)
create_png('assets/favicon.png', 48, 48)

print("✅ Basic placeholder icons created")
EOF
fi

echo "
Note: These are placeholder icons. For production, you should create proper icons with:
1. A professional design tool (Figma, Sketch, etc.)
2. Or use an online icon generator
3. Or install ImageMagick: brew install imagemagick
"
