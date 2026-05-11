"""Tests for Zernio orchestration helpers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

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


def test_parse_publish_accounts_rejects_replace_me_placeholder() -> None:
    raw = json.dumps([{"platform": "youtube", "accountId": "REPLACE_ME"}])
    parsed, err = zo._parse_publish_accounts(raw)
    assert parsed is None
    assert err and "placeholder" in err.lower()


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


def test_recent_zernio_publish_ignores_stale_entries(tmp_path: Path) -> None:
    log = tmp_path / "zernio_orchestration.jsonl"
    log.write_text(
        json.dumps(
            {
                "timestamp": "2000-01-01T00:00:00+00:00",
                "slug": "old",
                "channel": "zernio",
                "status": "published",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert zo._recent_zernio_publish_for_slug(log, "old", hours=36) is False


def test_zernio_headers_shape() -> None:
    h = zo.zernio_headers("sk_test")
    assert h["Authorization"] == "Bearer sk_test"
    assert "json" in h["Content-Type"].lower()


def test_zernio_list_accounts_success() -> None:
    mock_r = MagicMock()
    mock_r.status_code = 200
    mock_r.json.return_value = {"accounts": [{"platform": "twitter", "id": "1"}]}

    with patch.object(zo.requests, "get", return_value=mock_r) as mget:
        accounts, err = zo.zernio_list_accounts("key")

    assert err is None
    assert accounts == [{"platform": "twitter", "id": "1"}]
    mget.assert_called_once()
    assert zo.ZERNIO_BASE in mget.call_args[0][0]


def test_zernio_list_accounts_http_error() -> None:
    mock_r = MagicMock()
    mock_r.status_code = 502
    mock_r.text = "bad gateway"

    with patch.object(zo.requests, "get", return_value=mock_r):
        accounts, err = zo.zernio_list_accounts("key")

    assert accounts is None
    assert err and "http_502" in err


def test_zernio_list_accounts_request_exception() -> None:
    with patch.object(zo.requests, "get", side_effect=requests.RequestException("timeout")):
        accounts, err = zo.zernio_list_accounts("key")

    assert accounts is None
    assert err and "request_error" in err


def test_zernio_list_accounts_unexpected_payload() -> None:
    mock_r = MagicMock()
    mock_r.status_code = 200
    mock_r.json.return_value = {"not_accounts": []}

    with patch.object(zo.requests, "get", return_value=mock_r):
        accounts, err = zo.zernio_list_accounts("key")

    assert accounts is None
    assert err == "unexpected_payload"


def test_zernio_create_post_publish_now() -> None:
    mock_r = MagicMock()
    mock_r.status_code = 201
    mock_r.json.return_value = {"id": "post_1"}

    with patch.object(zo.requests, "post", return_value=mock_r) as mpost:
        payload, err = zo.zernio_create_post(
            "key",
            "hello",
            [{"platform": "twitter", "accountId": "acc"}],
            publish_now=True,
        )

    assert err is None
    assert payload == {"id": "post_1"}
    body = mpost.call_args.kwargs["json"]
    assert body["publishNow"] is True
    assert body["content"] == "hello"


def test_zernio_create_post_scheduled() -> None:
    mock_r = MagicMock()
    mock_r.status_code = 200
    mock_r.json.return_value = {"ok": True}

    with patch.object(zo.requests, "post", return_value=mock_r) as mpost:
        _, err = zo.zernio_create_post(
            "key",
            "x",
            [{"platform": "li", "accountId": "a"}],
            publish_now=False,
            scheduled_for="2026-04-04T12:00:00",
            timezone="America/New_York",
        )

    assert err is None
    body = mpost.call_args.kwargs["json"]
    assert "publishNow" not in body
    assert body["scheduledFor"] == "2026-04-04T12:00:00"
    assert body["timezone"] == "America/New_York"


def test_append_jsonl_creates_parent(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "log.jsonl"
    zo._append_jsonl(path, {"a": 1})
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8").strip()) == {"a": 1}


def test_parse_publish_accounts_platform_id_alias() -> None:
    raw = json.dumps([{"platformId": "linkedin", "accountId": "acc_x"}])
    parsed, err = zo._parse_publish_accounts(raw)
    assert err is None
    assert parsed == [{"platform": "linkedin", "accountId": "acc_x"}]


def test_publish_accounts_from_current_accounts_filters_text_accounts() -> None:
    accounts = [
        {"platform": "twitter", "_id": "tw_1"},
        {"platform": "instagram", "id": "ig_1"},
        {"platformId": "threads", "accountId": "th_1"},
        {"platform": "youtube", "id": "yt_1"},
        {"platform": "twitter", "id": "tw_1"},
    ]

    assert zo._publish_accounts_from_current_accounts(accounts) == [
        {"platform": "twitter", "accountId": "tw_1"},
        {"platform": "threads", "accountId": "th_1"},
    ]


def test_stale_account_error_detects_zernio_403() -> None:
    assert zo._stale_account_error('http_403:{"error":"One or more accounts do not belong to this user"}')
    assert not zo._stale_account_error("http_500:bad gateway")


def test_cmd_health_skipped_without_key(capsys: pytest.CaptureFixture[str]) -> None:
    args = MagicMock()
    with patch.object(zo, "zernio_api_key", return_value=""):
        code = zo.cmd_health(args)
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "skipped"


def test_cmd_health_error_on_list_failure(capsys: pytest.CaptureFixture[str]) -> None:
    args = MagicMock()
    with patch.object(zo, "zernio_api_key", return_value="sk"):
        with patch.object(zo, "zernio_list_accounts", return_value=(None, "http_500:x")):
            code = zo.cmd_health(args)
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "error"


def test_cmd_health_ok_counts_platforms(capsys: pytest.CaptureFixture[str]) -> None:
    args = MagicMock()
    accounts = [
        {"platform": "twitter"},
        {"platform": "twitter"},
        {"platform": "linkedin"},
    ]
    with patch.object(zo, "zernio_api_key", return_value="sk"):
        with patch.object(zo, "zernio_list_accounts", return_value=(accounts, None)):
            code = zo.cmd_health(args)
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert out["account_count"] == 3
    assert out["platforms"]["twitter"] == 2


def test_build_parser_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        zo.build_parser().parse_args([])


def test_main_routes_health(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(zo, "cmd_health", lambda _a: 42)
    monkeypatch.setattr(zo, "load_repo_dotenv", lambda _p: None)
    monkeypatch.setattr("sys.argv", ["zernio", "health"])
    assert zo.main() == 42
