"""CLI coverage for upload_store_listing_anchor.main()."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import upload_store_listing_anchor as usa


def _fake_anchor_curl(cmd, **_kwargs):
    cmd_str = " ".join(cmd)
    if "perform-web-task" in cmd_str:
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"data": {"status": "ok"}}),
            stderr="",
        )
    if "agent/files" in cmd_str:
        return SimpleNamespace(returncode=0, stdout="{}", stderr="")
    if "sessions" in cmd_str:
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"data": {"id": "sess-123"}}),
            stderr="",
        )
    return SimpleNamespace(returncode=1, stdout="", stderr="curl failed")


def test_main_exits_when_api_key_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(usa, "REPO", tmp_path)
    monkeypatch.delenv("ANCHOR_BROWSER_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        usa.main()
    assert exc.value.code == 1


def test_main_happy_path(monkeypatch, tmp_path):
    monkeypatch.setattr(usa, "REPO", tmp_path)
    (tmp_path / ".env").write_text(
        "ANCHOR_BROWSER_API_KEY=test-key\nFASTLANE_USER=ceo@example.com\nFASTLANE_PASSWORD=secret\n",
        encoding="utf-8",
    )
    zip_path = tmp_path / "scripts" / "_screenshots_anchor.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    zip_path.write_bytes(b"PK\x03\x04")
    monkeypatch.setattr(usa, "create_screenshots_zip", lambda: zip_path)
    monkeypatch.setattr(usa.subprocess, "run", _fake_anchor_curl)
    usa.main()


def test_main_exits_when_session_start_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(usa, "REPO", tmp_path)
    (tmp_path / ".env").write_text("ANCHOR_BROWSER_API_KEY=test-key\n", encoding="utf-8")
    zip_path = tmp_path / "scripts" / "_screenshots_anchor.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    zip_path.write_bytes(b"zip")
    monkeypatch.setattr(usa, "create_screenshots_zip", lambda: zip_path)
    monkeypatch.setattr(
        usa.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=1, stdout="", stderr="network"),
    )
    with pytest.raises(SystemExit) as exc:
        usa.main()
    assert exc.value.code == 1
