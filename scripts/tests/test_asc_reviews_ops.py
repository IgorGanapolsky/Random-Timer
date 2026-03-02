from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

import pytest

from scripts import asc_reviews_ops as aro


def test_parse_review_extracts_expected_fields():
    item = {
        "id": "r1",
        "attributes": {
            "rating": "5",
            "title": " Great ",
            "body": " Works ",
            "territory": "US",
            "createdDate": "2026-02-20T10:00:00Z",
        },
        "relationships": {"response": {"data": {"id": "x"}}},
    }
    parsed = aro._parse_review(item)
    assert parsed.id == "r1"
    assert parsed.rating == 5
    assert parsed.title == "Great"
    assert parsed.body == "Works"
    assert parsed.has_response is True


def test_hours_since_handles_zulu_timestamp():
    now = dt.datetime(2026, 2, 25, 12, 0, 0, tzinfo=dt.timezone.utc)
    hours = aro._hours_since("2026-02-25T06:00:00Z", now)
    assert hours == pytest.approx(6.0)


def test_slack_post_raises_on_http_error(monkeypatch):
    class _Resp:
        status_code = 500
        text = "boom"

    monkeypatch.setitem(__import__("sys").modules, "requests", SimpleNamespace(post=lambda *_a, **_k: _Resp()))
    with pytest.raises(SystemExit):
        aro._slack_post("https://example.invalid", "msg")


def test_render_markdown_includes_summary_fields():
    report = {
        "generatedAt": "2026-02-25T00:00:00Z",
        "bundleId": "com.example",
        "appId": "123",
        "totalReviews": 2,
        "averageRating": 4.0,
        "ratings": {"1": 0, "2": 0, "3": 0, "4": 1, "5": 1},
        "unresolvedLowStarCount": 1,
        "slaHours": 24,
        "slaBreachCount": 1,
        "slaBreaches": [
            {"id": "r1", "rating": 1, "territory": "US", "ageHours": 30.5, "title": "Needs work"}
        ],
    }
    text = aro._render_markdown(report)
    assert "ASC Reviews Ops Report" in text
    assert "SLA breaches" in text
