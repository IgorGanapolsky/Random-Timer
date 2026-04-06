"""Tests for repo-root .env loading (empty env placeholders must not block .env)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from repo_dotenv import load_repo_dotenv  # noqa: E402


class RepoDotenvTests(unittest.TestCase):
    def test_overwrites_empty_env_var_from_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / ".env").write_text("FOO_FROM_ENV=hello\n", encoding="utf-8")
            old = os.environ.get("FOO_FROM_ENV")
            os.environ["FOO_FROM_ENV"] = ""
            try:
                load_repo_dotenv(tmp)
                self.assertEqual(os.environ.get("FOO_FROM_ENV"), "hello")
            finally:
                if old is None:
                    os.environ.pop("FOO_FROM_ENV", None)
                else:
                    os.environ["FOO_FROM_ENV"] = old

    def test_skips_when_env_already_non_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / ".env").write_text("BAR=from_file\n", encoding="utf-8")
            old = os.environ.get("BAR")
            os.environ["BAR"] = "keep_me"
            try:
                load_repo_dotenv(tmp)
                self.assertEqual(os.environ.get("BAR"), "keep_me")
            finally:
                if old is None:
                    os.environ.pop("BAR", None)
                else:
                    os.environ["BAR"] = old


    def test_multiline_quoted_value(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / ".env").write_text(
                'SINGLE=one\n'
                'MULTI="-----BEGIN TEST BLOCK-----\n'  # gitleaks:allow
                'AAAA\n'
                'BBBB\n'
                '-----END TEST BLOCK-----"\n'
                'AFTER=two\n',
                encoding="utf-8",
            )
            env_keys = ("SINGLE", "MULTI", "AFTER")
            saved = {k: os.environ.pop(k, None) for k in env_keys}
            try:
                load_repo_dotenv(tmp)
                self.assertEqual(os.environ.get("SINGLE"), "one")
                self.assertIn("-----BEGIN TEST BLOCK-----", os.environ.get("MULTI", ""))
                self.assertIn("BBBB", os.environ.get("MULTI", ""))
                self.assertIn("-----END TEST BLOCK-----", os.environ.get("MULTI", ""))
                self.assertEqual(os.environ.get("AFTER"), "two")
            finally:
                for k in env_keys:
                    if saved[k] is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = saved[k]


if __name__ == "__main__":
    unittest.main()
