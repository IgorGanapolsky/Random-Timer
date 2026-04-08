"""Tests for Zernio orchestration helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import zernio_orchestrate as zo


def test_zernio_api_key_prefers_explicit_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZERNIO_API_KEY", "sk_primary")
    monkeypatch.setenv("ZERNIO_TOKEN", "sk_fallback")
    assert zo.zernio_api_key() == "sk_primary"


def test_zernio_api_key_falls_back_to_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    monkeypatch.setenv("ZERNIO_TOKEN", "sk_from_token")
    assert zo.zernio_api_key() == "sk_from_token"


def test_parse_publish_accounts_valid() -> None:
    raw = json.dumps([{"platform": "twitter", "accountId": "acc_1"}])
    parsed, err = zo._parse_publish_accounts(raw)
    assert err is None
    assert parsed == [{"platform": "twitter", "accountId": "acc_1"}]


def test_parse_publish_accounts_rejects_empty() -> None:
    parsed, err = zo._parse_publish_accounts("")
    assert parsed is None
    assert err is not None


def test_recent_zernio_publish_for_slug(tmp_path: Path) -> None:
    log = tmp_path / "zernio_orchestration.jsonl"
    log.write_text(
        json.dumps(
            {
                "timestamp": "2099-01-01T00:00:00+00:00",
                "slug": "same-slug",
                "channel": "zernio",
                "status": "published",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert zo._recent_zernio_publish_for_slug(log, "same-slug", hours=36) is True
    assert zo._recent_zernio_publish_for_slug(log, "other-slug", hours=36) is False
