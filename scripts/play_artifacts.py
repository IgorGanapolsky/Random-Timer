#!/usr/bin/env python3
"""Shared artifact-path helpers for Play Console automation scripts."""

from __future__ import annotations

from pathlib import Path

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / ".artifacts" / "play_console"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def screenshot_path(name: str) -> str:
    return str(ARTIFACTS_DIR / name)

