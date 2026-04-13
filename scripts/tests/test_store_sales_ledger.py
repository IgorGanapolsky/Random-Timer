"""Tests for App Store sales TSV parsing helpers."""

from __future__ import annotations

import gzip
import sys
import types

import pytest


class _FakeResponse:
    def __init__(self, status_code: int, content: bytes = b"") -> None:
        self.status_code = status_code
        self.content = content


def test_parse_sales_tsv_tab_separated_sums() -> None:
    from scripts.store_sales_ledger import _parse_sales_tsv_rows

    text = "Units\tDeveloper Proceeds\tApple Identifier\n2\t9.99\t6758355312\n1\t4.99\t6758355312\n"
    hdr, rows = _parse_sales_tsv_rows(text)
    assert "units" in hdr
    assert len(rows) == 2


def test_find_col_prefers_exact_match_and_rejects_ambiguous_substrings() -> None:
    from scripts.store_sales_ledger import _find_col

    assert _find_col(["gross proceeds", "developer proceeds"], "developer proceeds", "proceeds") == 1
    assert _find_col(["developer proceeds usd"], "developer proceeds") == 0
    assert _find_col(["gross proceeds"], "proceeds") is None
    assert _find_col(["net units"], "units") is None


def test_fetch_ios_sales_skipped_without_vendor(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import store_sales_ledger as ssl

    monkeypatch.delenv("APPSTORE_VENDOR_NUMBER", raising=False)
    monkeypatch.delenv("APPSTORE_CONNECT_VENDOR_NUMBER", raising=False)
    out = ssl.fetch_ios_sales_daily_summary(7)
    assert out["status"] == "skipped"
    assert "VENDOR" in (out.get("reason") or "").upper()


def test_fetch_ios_sales_skipped_when_vendor_only_no_asc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import store_sales_ledger as ssl

    monkeypatch.setenv("APPSTORE_VENDOR_NUMBER", "12345678")
    for k in (
        "APPSTORE_KEY_ID",
        "APPSTORE_ISSUER_ID",
        "APPSTORE_PRIVATE_KEY",
        "APP_STORE_CONNECT_KEY_B64",
    ):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("APPSTORE_PRIVATE_KEY_PATH", raising=False)
    out = ssl.fetch_ios_sales_daily_summary(1)
    assert out["status"] in {"skipped", "error"}


def test_fetch_ios_sales_parses_direct_gzip_report_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import store_sales_ledger as ssl

    auth_calls: list[str] = []

    class FakeASCAuth:
        @classmethod
        def from_env(cls) -> types.SimpleNamespace:
            return types.SimpleNamespace(jwt=lambda: auth_calls.append("jwt") or "token")

    def fake_get(url: str, **kwargs: object) -> _FakeResponse:
        assert url.endswith("/salesReports")
        assert kwargs["headers"] == {
            "Authorization": "Bearer token",
            "Accept": "application/a-gzip",
        }
        body = (
            "Units\tDeveloper Proceeds\tCustomer Price\tApple Identifier\n"
            "2\t1.50\t3.00\t6758355312\n"
            "9\t7.00\t8.00\t1111111111\n"
        )
        return _FakeResponse(200, gzip.compress(body.encode("utf-8")))

    monkeypatch.setenv("APPSTORE_VENDOR_NUMBER", "12345678")
    monkeypatch.setitem(
        sys.modules,
        "asc_client",
        types.SimpleNamespace(
            APP_STORE_CONNECT_API="https://api.appstoreconnect.apple.com/v1",
            ASCAuth=FakeASCAuth,
        ),
    )
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(get=fake_get))

    out = ssl.fetch_ios_sales_daily_summary(1)

    assert out["status"] == "ok"
    assert out["days_with_nonzero_rows"] == 1
    assert out["sum_units"] == 2
    assert out["sum_developer_proceeds_or_partner_share"] == pytest.approx(1.5)
    assert out["sum_customer_price"] == pytest.approx(3.0)
    assert auth_calls == ["jwt"]


def test_fetch_ios_sales_accepts_legacy_connect_vendor_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import store_sales_ledger as ssl

    monkeypatch.delenv("APPSTORE_VENDOR_NUMBER", raising=False)
    monkeypatch.setenv("APPSTORE_CONNECT_VENDOR_NUMBER", "12345678")

    vendor, env_name = ssl._vendor_number_from_env()

    assert vendor == "12345678"
    assert env_name == "APPSTORE_CONNECT_VENDOR_NUMBER"


def test_fetch_ios_sales_all_failures_return_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import store_sales_ledger as ssl

    class FakeASCAuth:
        @classmethod
        def from_env(cls) -> types.SimpleNamespace:
            return types.SimpleNamespace(jwt=lambda: "token")

    monkeypatch.setenv("APPSTORE_VENDOR_NUMBER", "12345678")
    monkeypatch.setitem(
        sys.modules,
        "asc_client",
        types.SimpleNamespace(
            APP_STORE_CONNECT_API="https://api.appstoreconnect.apple.com/v1",
            ASCAuth=FakeASCAuth,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "requests",
        types.SimpleNamespace(get=lambda *_args, **_kwargs: _FakeResponse(500, b"error")),
    )

    out = ssl.fetch_ios_sales_daily_summary(2)

    assert out["status"] == "error"
    assert out["days_with_nonzero_rows"] == 0
    assert len(out["http_errors_sample"]) == 2
    assert all("HTTP 500" in err for err in out["http_errors_sample"])


def test_fetch_ios_sales_some_failures_return_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import store_sales_ledger as ssl

    class FakeASCAuth:
        @classmethod
        def from_env(cls) -> types.SimpleNamespace:
            return types.SimpleNamespace(jwt=lambda: "token")

    calls = 0

    def fake_get(_url: str, **_kwargs: object) -> _FakeResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            body = (
                "Units\tDeveloper Proceeds\tCustomer Price\tApple Identifier\n"
                "1\t0.75\t1.99\t6758355312\n"
            )
            return _FakeResponse(200, gzip.compress(body.encode("utf-8")))
        return _FakeResponse(503, b"unavailable")

    monkeypatch.setenv("APPSTORE_VENDOR_NUMBER", "12345678")
    monkeypatch.setitem(
        sys.modules,
        "asc_client",
        types.SimpleNamespace(
            APP_STORE_CONNECT_API="https://api.appstoreconnect.apple.com/v1",
            ASCAuth=FakeASCAuth,
        ),
    )
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(get=fake_get))

    out = ssl.fetch_ios_sales_daily_summary(2)

    assert out["status"] == "partial"
    assert out["days_with_nonzero_rows"] == 1
    assert out["sum_units"] == 1
    assert out["http_errors_sample"] and "HTTP 503" in out["http_errors_sample"][0]
