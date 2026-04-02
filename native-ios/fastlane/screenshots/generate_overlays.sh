#!/usr/bin/env bash
# Generate App Store marketing overlay screenshots from raw captures.
# Uses ImageMagick to add headline + subtitle text on a dark gradient background
# above the actual screenshot. Reproducible from repo.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EN_DIR="$SCRIPT_DIR/en-US"
OUT_DIR="$EN_DIR/framed"
mkdir -p "$OUT_DIR"

# Colors matching the live store purple theme
BG_COLOR="#0D0D1A"
HEADLINE_COLOR="#FFFFFF"
SUBTITLE_COLOR="#9999BB"
ACCENT_COLOR="#7B5FFF"

# Target dimensions for 6.7" display
W=1290
H=2796

# Screenshot area: leave top 15% for text overlay
TEXT_HEIGHT=420
SCREENSHOT_HEIGHT=$((H - TEXT_HEIGHT))

generate_framed() {
  local input="$1"
  local headline="$2"
  local subtitle="$3"
  local output="$4"

  echo "Generating: $(basename "$output")"

  # Resize screenshot to fit the lower portion
  magick "$input" -resize "${W}x${SCREENSHOT_HEIGHT}^" -gravity center -extent "${W}x${SCREENSHOT_HEIGHT}" /tmp/ss_resized.png

  # Create the text overlay area
  magick -size "${W}x${TEXT_HEIGHT}" "xc:${BG_COLOR}" \
    -gravity center \
    -font "/System/Library/Fonts/Helvetica.ttc" -pointsize 72 -fill "$HEADLINE_COLOR" \
    -annotate +0-30 "$headline" \
    -font "/System/Library/Fonts/Helvetica.ttc" -pointsize 40 -fill "$SUBTITLE_COLOR" \
    -annotate +0+40 "$subtitle" \
    /tmp/ss_header.png

  # Stack header + screenshot vertically
  magick /tmp/ss_header.png /tmp/ss_resized.png -append "$output"

  echo "  -> $(file "$output" | grep -o '[0-9]* x [0-9]*')"
}

# iPhone screenshots
generate_framed "$EN_DIR/1_setup.png" \
  "SET YOUR RANGE" \
  "30 sec to 10 min — you choose" \
  "$OUT_DIR/1_setup_framed.png"

generate_framed "$EN_DIR/2_running.png" \
  "RANDOM EVERY ROUND" \
  "No predictable countdown" \
  "$OUT_DIR/2_running_framed.png"

generate_framed "$EN_DIR/3_sounds.png" \
  "SOUND ARSENAL" \
  "8 Pro sounds + voice callouts" \
  "$OUT_DIR/3_sounds_framed.png"

# iPad screenshots (2048x2732)
IPAD_W=2048
IPAD_H=2732
IPAD_TEXT_HEIGHT=410
IPAD_SS_HEIGHT=$((IPAD_H - IPAD_TEXT_HEIGHT))

generate_framed_ipad() {
  local input="$1"
  local headline="$2"
  local subtitle="$3"
  local output="$4"

  echo "Generating iPad: $(basename "$output")"

  magick "$input" -resize "${IPAD_W}x${IPAD_SS_HEIGHT}^" -gravity center -extent "${IPAD_W}x${IPAD_SS_HEIGHT}" /tmp/ss_resized.png

  magick -size "${IPAD_W}x${IPAD_TEXT_HEIGHT}" "xc:${BG_COLOR}" \
    -gravity center \
    -font "/System/Library/Fonts/Helvetica.ttc" -pointsize 80 -fill "$HEADLINE_COLOR" \
    -annotate +0-30 "$headline" \
    -font "/System/Library/Fonts/Helvetica.ttc" -pointsize 44 -fill "$SUBTITLE_COLOR" \
    -annotate +0+40 "$subtitle" \
    /tmp/ss_header.png

  magick /tmp/ss_header.png /tmp/ss_resized.png -append "$output"
}

generate_framed_ipad "$EN_DIR/5_ipad_setup.png" \
  "SET YOUR RANGE" \
  "30 sec to 10 min — you choose" \
  "$OUT_DIR/5_ipad_setup_framed.png"

generate_framed_ipad "$EN_DIR/6_ipad_running.png" \
  "RANDOM EVERY ROUND" \
  "No predictable countdown" \
  "$OUT_DIR/6_ipad_running_framed.png"

generate_framed_ipad "$EN_DIR/7_ipad_stopped.png" \
  "REACT ON THE BEEP" \
  "Built for HIIT, drills & games" \
  "$OUT_DIR/7_ipad_stopped_framed.png"

echo ""
echo "All framed screenshots generated in: $OUT_DIR"
ls -la "$OUT_DIR/"
