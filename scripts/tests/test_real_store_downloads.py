"""Tests for Play review list pagination helper."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from real_store_downloads import (  # noqa: E402
    ANDROID_REFUND_COUNT_METRIC_ID,
    ANDROID_REVIEW_COUNT_METRIC_ID,
    IOS_REFUND_COUNT_METRIC_ID,
    IOS_REVIEW_COUNT_METRIC_ID,
    _parse_asc_sales_report_rows,
    _fetch_all_android_voided_purchases,
    _fetch_all_play_reviews_list,
    _summarize_ios_refunds_from_sales_rows,
    _summarize_voided_purchases,
)


def test_review_metric_ids_are_stable_tokens() -> None:
    assert "google_play" in ANDROID_REVIEW_COUNT_METRIC_ID
    assert "voidedpurchases" in ANDROID_REFUND_COUNT_METRIC_ID
    assert "app_store_connect" in IOS_REVIEW_COUNT_METRIC_ID
    assert "sales_reports" in IOS_REFUND_COUNT_METRIC_ID


def test_fetch_all_play_reviews_list_paginates_until_no_token() -> None:
    service = MagicMock()
    list_resource = service.reviews.return_value.list
    list_resource.return_value.execute.side_effect = [
        {
            "reviews": [{"reviewId": "a"}],
            "tokenPagination": {"nextPageToken": "t1"},
        },
        {
            "reviews": [{"reviewId": "b"}, {"reviewId": "c"}],
            "tokenPagination": {},
        },
    ]

    out = _fetch_all_play_reviews_list(service, "com.example.app")

    assert len(out) == 3
    assert list_resource.call_count == 2
    first_kw = list_resource.call_args_list[0].kwargs
    assert first_kw == {"packageName": "com.example.app", "maxResults": 100}
    second_kw = list_resource.call_args_list[1].kwargs
    assert second_kw == {
        "packageName": "com.example.app",
        "maxResults": 100,
        "token": "t1",
    }


def test_fetch_all_android_voided_purchases_paginates_until_no_token() -> None:
    service = MagicMock()
    list_resource = service.purchases.return_value.voidedpurchases.return_value.list
    list_resource.return_value.execute.side_effect = [
        {
            "voidedPurchases": [{"orderId": "a"}],
            "tokenPagination": {"nextPageToken": "t1"},
        },
        {
            "voidedPurchases": [{"orderId": "b"}],
            "tokenPagination": {},
        },
    ]

    out = _fetch_all_android_voided_purchases(service, "com.example.app", 30)
    assert len(out) == 2
    assert list_resource.call_count == 2
    first_kw = list_resource.call_args_list[0].kwargs
    assert first_kw["packageName"] == "com.example.app"
    assert first_kw["maxResults"] == 1000
    second_kw = list_resource.call_args_list[1].kwargs
    assert second_kw["token"] == "t1"


def test_summarize_voided_purchases_groups_reason_codes() -> None:
    summary = _summarize_voided_purchases(
        [
            {"voidedReason": 0},
            {"voidedReason": 0},
            {"voidedReason": 1},
            {},
        ]
    )
    assert summary["refund_requests_30d"] == 4
    assert summary["voided_purchase_reason_counts"] == {
        "0": 2,
        "1": 1,
        "unknown": 1,
    }


def test_parse_asc_sales_report_rows_handles_gzip_tsv() -> None:
    import gzip

    raw_tsv = (
        "Provider\tUnits\tSKU\n"
        "ABC\t-2\tpro_monthly\n"
        "ABC\t5\tpro_yearly\n"
    ).encode("utf-8")
    rows = _parse_asc_sales_report_rows(gzip.compress(raw_tsv))
    assert len(rows) == 2
    assert rows[0]["Units"] == "-2"
    assert rows[1]["SKU"] == "pro_yearly"


def test_summarize_ios_refunds_uses_negative_units() -> None:
    summary = _summarize_ios_refunds_from_sales_rows(
        [
            {"Units": "-2"},
            {"Units": "-1.5"},
            {"Units": "4"},
            {"Units": "bad"},
        ]
    )
    assert summary["ios_refund_units_30d"] == 4
    assert summary["ios_gross_units_30d"] == 4
    assert summary["ios_net_units_30d"] == 0
