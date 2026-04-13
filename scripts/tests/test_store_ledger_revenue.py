"""Tests for store ledger revenue (ASC daily sales TSV) helpers."""

from __future__ import annotations

import gzip
from unittest import mock

import pytest


def test_parse_sales_summary_tsv_sums_matched_rows() -> None:
    from scripts import store_ledger_revenue as slr

    tsv = (
        "Provider\tSKU\tApple Identifier\tParent Identifier\tUnits\t"
        "Developer Proceeds (per unit)\tCurrency of Proceeds\n"
        "APPLE\tother_sku\t999\t\t1\t1.00\tUSD\n"
        f"APPLE\t{slr.DEFAULT_APP_SKU}\t{slr.IOS_APP_ID}\t\t10\t0.70\tUSD\n"
        "APPLE\tiap1\t888\t"
        + slr.DEFAULT_APP_SKU
        + "\t2\t0.50\tEUR\n"
    )
    out = slr.parse_sales_summary_tsv(tsv, app_apple_id=slr.IOS_APP_ID, app_sku=slr.DEFAULT_APP_SKU)
    assert out["rows_total"] == 3
    assert out["rows_matched"] == 2
    assert out["proceeds_by_currency"]["USD"] == pytest.approx(7.0)
    assert out["proceeds_by_currency"]["EUR"] == pytest.approx(1.0)
    assert out["units_sum_matched"] == pytest.approx(12.0)


def test_parse_sales_summary_tsv_parent_identifier_iap() -> None:
    from scripts import store_ledger_revenue as slr

    tsv = (
        "SKU\tApple Identifier\tParent Identifier\tUnits\t"
        "Developer Proceeds (per unit)\tCurrency of Proceeds\n"
        "pro_base\t111111\t"
        + slr.DEFAULT_APP_SKU
        + "\t1\t4.00\tUSD\n"
    )
    out = slr.parse_sales_summary_tsv(tsv, app_apple_id=slr.IOS_APP_ID, app_sku=slr.DEFAULT_APP_SKU)
    assert out["rows_matched"] == 1
    assert out["proceeds_by_currency"]["USD"] == pytest.approx(4.0)


def test_collect_ios_ledger_skipped_without_vendor(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import store_ledger_revenue as slr

    monkeypatch.delenv("APPSTORE_VENDOR_NUMBER", raising=False)
    out = slr.collect_ios_ledger_revenue(7)
    assert out["status"] == "skipped"
    assert "APPSTORE_VENDOR_NUMBER" in (out.get("reason") or "")


def test_collect_ios_ledger_fetches_and_aggregates(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import store_ledger_revenue as slr

    monkeypatch.setenv("APPSTORE_VENDOR_NUMBER", "12345678")
    monkeypatch.setenv("APPSTORE_KEY_ID", "kid")
    monkeypatch.setenv("APPSTORE_ISSUER_ID", "iss")
    monkeypatch.setenv("APPSTORE_PRIVATE_KEY", "not-a-real-key")

    tsv = (
        "SKU\tApple Identifier\tUnits\tDeveloper Proceeds (per unit)\tCurrency of Proceeds\n"
        f"{slr.DEFAULT_APP_SKU}\t{slr.IOS_APP_ID}\t2\t1.00\tUSD\n"
    )
    gz = gzip.compress(tsv.encode("utf-8"))

    class Resp:
        def __init__(self, code: int, body: bytes) -> None:
            self.status_code = code
            self.content = body
            self.headers = {"Content-Type": "application/a-gzip"}
            self.text = ""

        def json(self) -> dict:
            return {}

    calls: list[int] = []

    def fake_gw(requests_mod, url, headers, params, **kwargs):
        calls.append(1)
        return Resp(200, gz)

    with mock.patch("asc_client.ASCAuth.from_env") as fe:
        fe.return_value = mock.Mock(jwt=lambda: "jwt")
        out = slr.collect_ios_ledger_revenue(1, report_lag_days=3, get_with_retries=fake_gw)

    assert out["status"] == "ok"
    assert out["days_fetched_ok"] == 1
    assert out["proceeds_by_currency"].get("USD") == pytest.approx(2.0)
    assert len(calls) == 1


def test_collect_android_ledger_is_skipped() -> None:
    from scripts import store_ledger_revenue as slr

    out = slr.collect_android_ledger_revenue(30)
    assert out["status"] == "skipped"
    assert "androidpublisher" in out["reason"]


def test_collect_store_ledger_revenue_shape() -> None:
    from scripts import store_ledger_revenue as slr

    bundle = slr.collect_store_ledger_revenue(30)
    assert bundle["metric_bundle_id"] == slr.STORE_LEDGER_METRIC_BUNDLE_ID
    assert "ios" in bundle and "android" in bundle
