#!/usr/bin/env python3
"""Shared App Store Connect API auth + HTTP helpers."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

_SCRIPTS_ROOT = str(Path(__file__).resolve().parent.parent)
if _SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, _SCRIPTS_ROOT)

from pem_env import normalize_inline_pem
from repo_dotenv import load_repo_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_repo_dotenv(REPO_ROOT)

APP_STORE_CONNECT_API = "https://api.appstoreconnect.apple.com/v1"


class AscClientError(RuntimeError):
    """Raised for auth, dependency, and HTTP/API failures."""


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_private_key_material(key_id: str) -> str:
    """Resolve .p8 material from env, path, base64 secret, or Fastlane default path."""
    for env_name in ("APPSTORE_PRIVATE_KEY", "APPSTORE_PRIVATE_KEY_PATH"):
        raw = (os.environ.get(env_name) or "").strip()
        if not raw:
            continue
        expanded = os.path.expanduser(raw)
        if os.path.isfile(expanded):
            return normalize_inline_pem(_read_file(expanded))
        return normalize_inline_pem(raw)

    b64 = (os.environ.get("APP_STORE_CONNECT_KEY_B64") or "").strip()
    if b64:
        try:
            import base64

            decoded = base64.b64decode("".join(b64.split()), validate=False).decode(
                "utf-8"
            )
            return normalize_inline_pem(decoded)
        except Exception:
            pass

    github_key = (os.environ.get("APPSTORE_PRIVATE_KEY_GITHUB") or "").strip()
    if github_key:
        return normalize_inline_pem(github_key)

    default_path = os.path.expanduser(
        f"~/.appstoreconnect/private_keys/AuthKey_{key_id}.p8"
    )
    if os.path.isfile(default_path):
        return normalize_inline_pem(_read_file(default_path))

    return ""


def safe_json_response(resp: Any) -> dict[str, Any]:
    if not getattr(resp, "content", None):
        return {}
    try:
        parsed = resp.json()
    except Exception:
        return {"raw": (resp.text or "")[:2000]}
    if isinstance(parsed, dict):
        return parsed
    return {"data": parsed}


@dataclass
class ASCAuth:
    key_id: str
    issuer_id: str
    private_key: str  # raw key contents

    @classmethod
    def from_env(cls) -> "ASCAuth":
        key_id = (os.environ.get("APPSTORE_KEY_ID") or "").strip()
        issuer_id = (os.environ.get("APPSTORE_ISSUER_ID") or "").strip()
        private_key = read_private_key_material(key_id)
        missing: list[str] = []
        if not key_id:
            missing.append("APPSTORE_KEY_ID")
        if not issuer_id:
            missing.append("APPSTORE_ISSUER_ID")
        if not private_key:
            missing.append("APPSTORE_PRIVATE_KEY (or APPSTORE_PRIVATE_KEY_PATH)")
        if missing:
            raise AscClientError(f"Missing env vars: {', '.join(missing)}")
        return cls(key_id=key_id, issuer_id=issuer_id, private_key=private_key)

    def jwt(self) -> str:
        try:
            import jwt  # PyJWT
            from cryptography.hazmat.primitives import serialization
        except ImportError as exc:
            raise AscClientError(
                "Missing PyJWT/cryptography. Install: pip install pyjwt cryptography"
            ) from exc

        try:
            signing_key = serialization.load_pem_private_key(
                self.private_key.encode("utf-8"),
                password=None,
            )
        except Exception as exc:
            raise AscClientError(
                "Could not parse App Store Connect API private key as PEM (.p8). "
                "Re-download the key from App Store Connect (Users and Access → Keys) or set "
                "APPSTORE_PRIVATE_KEY, APP_STORE_CONNECT_KEY_B64, or APPSTORE_PRIVATE_KEY_PATH. "
                f"If using the Fastlane default file, verify "
                f"~/.appstoreconnect/private_keys/AuthKey_{self.key_id}.p8 is intact. Details: {exc}"
            ) from exc

        now = int(time.time())
        exp = now + 20 * 60
        payload = {"iss": self.issuer_id, "iat": now, "exp": exp, "aud": "appstoreconnect-v1"}
        headers = {"alg": "ES256", "kid": self.key_id, "typ": "JWT"}
        return jwt.encode(payload, signing_key, algorithm="ES256", headers=headers)


class ASCClient:
    def __init__(self, auth: Optional[ASCAuth] = None, *, timeout: int = 30):
        self._auth = auth or ASCAuth.from_env()
        self._token: Optional[str] = None
        self._token_expiry = 0.0
        self._timeout = timeout

    @classmethod
    def from_env(cls, *, timeout: int = 30) -> "ASCClient":
        return cls(ASCAuth.from_env(), timeout=timeout)

    def token_value(self) -> str:
        now = time.time()
        if self._token and now < self._token_expiry - 30:
            return self._token
        token = self._auth.jwt()
        self._token = token
        self._token_expiry = now + (20 * 60)
        return token

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        try:
            import requests
        except ImportError as exc:
            raise AscClientError("Missing requests. Install: pip install requests") from exc

        url = path if path.startswith("https://") else f"{APP_STORE_CONNECT_API}{path}"
        resp = requests.request(
            method.upper(),
            url,
            headers={
                "Authorization": f"Bearer {self.token_value()}",
                "Content-Type": "application/json",
            },
            params=params or {},
            json=payload,
            timeout=self._timeout,
        )
        if resp.status_code >= 400:
            body = safe_json_response(resp)
            raise AscClientError(f"{method.upper()} {path} failed: HTTP {resp.status_code} {body}")
        return safe_json_response(resp)

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return self.request("GET", path, params=params)

    def get_all(self, path: str, *, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        next_path = path
        next_params = dict(params or {})

        while True:
            data = self.get(next_path, params=next_params)
            chunk = data.get("data", [])
            if isinstance(chunk, list):
                items.extend(chunk)

            next_url = (data.get("links") or {}).get("next")
            if not next_url:
                break
            if next_url.startswith(APP_STORE_CONNECT_API):
                next_url = next_url[len(APP_STORE_CONNECT_API) :]
            if "?" in next_url:
                next_path, query = next_url.split("?", 1)
                next_path = f"{next_path}?{query}"
                next_params = {}
            else:
                next_path = next_url
                next_params = {}
        return items


AscAuth = ASCAuth
AscClient = ASCClient
