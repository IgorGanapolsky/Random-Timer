"""Tests for PEM / service-account normalization from .env-style secrets."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pem_env import (  # noqa: E402
    load_google_play_service_account_dict,
    normalize_google_service_account_info,
    normalize_inline_pem,
)


class PemEnvTests(unittest.TestCase):
    def test_normalize_literal_backslash_n_in_pem(self) -> None:
        one_line = (  # gitleaks:allow
            "-----BEGIN PRIVATE KEY-----\\nABC\\n-----END PRIVATE KEY-----"
        )
        out = normalize_inline_pem(one_line)
        self.assertIn("\nABC\n", out)
        self.assertNotIn("\\n", out)

    def test_strip_wrapping_quotes(self) -> None:
        inner = "-----BEGIN PRIVATE KEY-----\\nX\\n-----END PRIVATE KEY-----"  # gitleaks:allow
        out = normalize_inline_pem(f'"{inner}"')
        self.assertTrue(out.startswith("-----BEGIN"))

    def test_base64_wrapped_pem(self) -> None:
        pem = "-----BEGIN PRIVATE KEY-----\nMII\n-----END PRIVATE KEY-----"  # gitleaks:allow
        b64 = __import__("base64").b64encode(pem.encode()).decode()
        out = normalize_inline_pem(b64)
        self.assertIn("-----BEGIN PRIVATE KEY-----", out)
        self.assertIn("MII", out)

    def test_normalize_google_service_account_private_key(self) -> None:
        info = {
            "type": "service_account",
            "private_key": "-----BEGIN PRIVATE KEY-----\\nLINE\\n-----END PRIVATE KEY-----",  # gitleaks:allow
        }
        fixed = normalize_google_service_account_info(info)
        self.assertNotIn("\\n", fixed["private_key"])
        self.assertIn("\nLINE\n", fixed["private_key"])

    def test_load_google_play_rejects_missing_path(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            load_google_play_service_account_dict("/nonexistent/path/google-play-ci-missing.json")
        self.assertIn("not a file", str(ctx.exception).lower())

    def test_load_google_play_dict_from_minimal_json_string(self) -> None:
        inner = {
            "type": "service_account",
            "project_id": "x",
            "private_key_id": "kid",
            "private_key": "-----BEGIN PRIVATE KEY-----\\nMII\\n-----END PRIVATE KEY-----",  # gitleaks:allow
            "client_email": "x@x.iam.gserviceaccount.com",
            "client_id": "1",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        raw = json.dumps(inner)
        loaded = load_google_play_service_account_dict(raw)
        self.assertEqual(loaded["client_email"], inner["client_email"])
        self.assertNotIn("\\n", loaded["private_key"])


if __name__ == "__main__":
    unittest.main()
