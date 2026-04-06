"""Tests for executive_metrics_snapshot PostHog wiring."""

from __future__ import annotations

import pytest


def test_posthog_section_skipped_without_credentials() -> None:
    from scripts import executive_metrics_snapshot as ems

    out = ems._posthog_section("299775", "", 30)
    assert out["status"] == "skipped"


def test_posthog_section_includes_wqtu_7d_from_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import executive_metrics_snapshot as ems

    import store_downloads_snapshot as sds

    def fake_posthog_query(
        query: str,
        api_key: str,
        project_id: str,
        errors: list,
        **kwargs: object,
    ):
        if "interval 7 day" in query and "HAVING count() >= 3" in query:
            return {"results": [[99]]}
        if "review_prompt_requested" in query:
            return {"results": [[1, 1]]}
        if "$screen" in query:
            return {"results": [["Timer Setup", 2, 3]]}
        return {"results": [[0]]}

    monkeypatch.setattr(sds, "posthog_query", fake_posthog_query)

    out = ems._posthog_section("299775", "test-key", 30)
    assert out["status"] == "ok"
    assert out["wqtu_7d_distinct_persons"] == 99
    assert out["window_days"] == 30
