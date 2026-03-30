from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts import verify_play_public_listing as vpl


class _Resp:
    def __init__(self, status_code: int, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.headers = headers or {}


def test_verify_public_listing_returns_pass_on_http_200(monkeypatch):
    monkeypatch.setattr(
        vpl.requests,
        "get",
        lambda *_args, **_kwargs: _Resp(200, {"date": "Fri, 27 Mar 2026 17:31:57 GMT"}),
    )

    result = vpl.verify_public_listing("https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer")

    assert result.passed is True
    assert result.status == "PUBLIC"
    assert "HTTP 200" in result.details


def test_verify_public_listing_reports_http_404(monkeypatch):
    monkeypatch.setattr(
        vpl.requests,
        "get",
        lambda *_args, **_kwargs: _Resp(404, {"date": "Fri, 27 Mar 2026 17:31:57 GMT"}),
    )

    result = vpl.verify_public_listing("https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer")

    assert result.passed is False
    assert result.status == "HTTP_404"
    assert "Fri, 27 Mar 2026 17:31:57 GMT" in result.details


def test_poll_until_visible_returns_first_success(monkeypatch):
    calls = {"count": 0}

    def fake_verify(_url: str):
        calls["count"] += 1
        if calls["count"] == 3:
            return vpl.PublicListingResult(True, "PUBLIC", "HTTP 200")
        return vpl.PublicListingResult(False, "HTTP_404", "HTTP 404")

    monkeypatch.setattr(vpl, "verify_public_listing", fake_verify)
    monkeypatch.setattr(vpl.time, "sleep", lambda *_args, **_kwargs: None)

    result = vpl.poll_until_visible("https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer", timeout=5, poll_interval=1)

    assert result.passed is True
    assert calls["count"] == 3


def test_poll_until_visible_times_out(monkeypatch):
    monkeypatch.setattr(
        vpl,
        "verify_public_listing",
        lambda _url: vpl.PublicListingResult(False, "HTTP_404", "HTTP 404"),
    )
    monkeypatch.setattr(vpl.time, "sleep", lambda *_args, **_kwargs: None)

    result = vpl.poll_until_visible(
        "https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer",
        timeout=0,
        poll_interval=1,
    )

    assert result.passed is False
    assert result.status == "TIMEOUT"
    assert "timed out" in result.details


def test_parse_args_defaults_to_us_store_url(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "verify_play_public_listing.py",
            "--package",
            "com.iganapolsky.randomtimer",
        ],
    )

    args = vpl.parse_args()

    assert args.package == "com.iganapolsky.randomtimer"
    assert args.country == "US"
