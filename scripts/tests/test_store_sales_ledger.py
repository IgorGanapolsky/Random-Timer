"""Tests for App Store sales TSV parsing helpers."""

from __future__ import annotations

import os

import pytest


def test_parse_sales_tsv_tab_separated_sums() -> None:
    from scripts.store_sales_ledger import _parse_sales_tsv_rows

    text = "Units\tDeveloper Proceeds\tApple Identifier\n2\t9.99\t6758355312\n1\t4.99\t6758355312\n"
    hdr, rows = _parse_sales_tsv_rows(text)
    assert "units" in hdr
    assert len(rows) == 2


def test_fetch_ios_sales_skipped_without_vendor(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import store_sales_ledger as ssl

    monkeypatch.delenv("APPSTORE_CONNECT_VENDOR_NUMBER", raising=False)
    out = ssl.fetch_ios_sales_daily_summary(7)
    assert out["status"] == "skipped"
    assert "VENDOR" in (out.get("reason") or "").upper()


def test_fetch_ios_sales_skipped_when_vendor_only_no_asc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import store_sales_ledger as ssl

    monkeypatch.setenv("APPSTORE_CONNECT_VENDOR_NUMBER", "12345678")
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
