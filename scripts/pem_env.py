"""Normalize PEM and JSON-in-.env blobs from local .env / GitHub secrets.

GitHub Actions and many .env loaders store multi-line keys as a single line with
literal backslash-n sequences. Cryptography then fails with "Unable to load PEM file".

Also supports .p8 / PEM stored as **base64** (one line, no BEGIN marker) — common when
copying from GitHub Actions secrets into .env.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
from pathlib import Path
from typing import Any, Dict


def normalize_inline_pem(text: str) -> str:
    if not text:
        return text
    text = text.strip()
    if text.startswith("\ufeff"):
        text = text[1:].strip()
    # Strip one layer of wrapping quotes from .env pastes: KEY="-----BEGIN..."
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    text = text.replace("\\r\\n", "\n").replace("\\r", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if "-----BEGIN" in text and "\\n" in text:
        text = text.replace("\\n", "\n")

    # Base64-wrapped PEM (no headers visible until decoded)
    if "-----BEGIN" not in text and _looks_like_base64_pem_blob(text):
        decoded_try = _try_decode_pem_base64(text)
        if decoded_try:
            return normalize_inline_pem(decoded_try)

    return text.strip()


_B64ISH = re.compile(r"^[A-Za-z0-9+/=\s]+$")


def _looks_like_base64_pem_blob(text: str) -> bool:
    compact = "".join(text.split())
    # Short .p8 files still base64-encode to >32 chars; keep threshold low.
    return len(compact) >= 32 and bool(_B64ISH.match(compact))


def _try_decode_pem_base64(text: str) -> str:
    compact = "".join(text.split())
    for pad in ("", "=", "==", "==="):
        candidate = compact + pad
        if len(candidate) % 4 != 0:
            continue
        try:
            raw = base64.b64decode(candidate, validate=False)
        except (binascii.Error, ValueError):
            continue
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if "-----BEGIN" in decoded:
            return decoded
    return ""


def normalize_google_service_account_info(info: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(info)
    pk = out.get("private_key")
    if isinstance(pk, str):
        out["private_key"] = normalize_inline_pem(pk)
    return out


def load_google_play_service_account_dict(key_material: str) -> Dict[str, Any]:
    """Load service-account JSON from a filesystem path or raw JSON string."""
    raw = key_material.strip()
    expanded = os.path.expanduser(raw)
    if os.path.isfile(expanded):
        raw = Path(expanded).read_text(encoding="utf-8")
    elif raw and not raw.lstrip().startswith("{"):
        raise ValueError(
            f"Google Play key path is not a file (check GOOGLE_PLAY_JSON_KEY_PATH): {expanded}"
        )
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    if not raw.strip():
        raise ValueError("Google Play key material is empty")
    info = json.loads(raw)
    if not isinstance(info, dict):
        raise ValueError("Google Play key must be a JSON object")
    return normalize_google_service_account_info(info)
