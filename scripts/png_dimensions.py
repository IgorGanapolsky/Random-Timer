#!/usr/bin/env python3
"""Return PNG dimensions as WIDTHxHEIGHT.

Used by release preflight so screenshot validation works on Linux runners
without relying on macOS-only tooling (e.g. `sips`).
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path


PNG_SIG = b"\x89PNG\r\n\x1a\n"


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != PNG_SIG:
        raise ValueError("not a PNG")
    # IHDR chunk starts at byte 8. Width/height are at bytes 16-24.
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: png_dimensions.py <file.png>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        w, h = png_dimensions(path)
    except Exception as exc:
        print(f"error: {path}: {exc}", file=sys.stderr)
        return 1
    print(f"{w}x{h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

