#!/usr/bin/env python3
"""Normalize PEM key file for App Store Connect API compatibility.

Fixes common issues when storing PEM in CI secrets:
  - UTF-8 BOM
  - CRLF line endings
  - Trailing/leading whitespace
  - Literal \\n in content

Usage:
  python scripts/normalize_pem.py <path_to.p8>
"""

import os
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: normalize_pem.py <path_to.p8>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    with open(path, "rb") as f:
        data = f.read()

    # Strip UTF-8 BOM
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]

    # Decode as UTF-8
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        print(f"Invalid UTF-8 in {path}", file=sys.stderr)
        return 1

    # Replace CRLF and CR with LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace literal \n with real newlines (common when pasting into secrets)
    if "\\n" in text and "-----BEGIN" in text:
        text = text.replace("\\n", "\n")

    # Trim
    text = text.strip()

    if "-----BEGIN PRIVATE KEY-----" not in text or "-----END PRIVATE KEY-----" not in text:
        print(f"Invalid PEM structure in {path}", file=sys.stderr)
        return 1

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
