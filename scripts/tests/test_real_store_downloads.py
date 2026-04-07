"""Tests for Play review list pagination helper."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from real_store_downloads import (  # noqa: E402
    ANDROID_REVIEW_COUNT_METRIC_ID,
    IOS_REVIEW_COUNT_METRIC_ID,
    _fetch_all_play_reviews_list,
)


def test_review_metric_ids_are_stable_tokens() -> None:
    assert "google_play" in ANDROID_REVIEW_COUNT_METRIC_ID
    assert "app_store_connect" in IOS_REVIEW_COUNT_METRIC_ID


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
