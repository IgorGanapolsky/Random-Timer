"""Unit tests for PostHog dashboard query helpers (no live API)."""

from __future__ import annotations

from unittest import mock

import pytest


def test_posthog_credentials_prefer_personal_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import posthog_dashboard as phd

    monkeypatch.setenv("POSTHOG_PERSONAL_API_KEY", " phx_a ")
    monkeypatch.setenv("POSTHOG_API_KEY", "phx_b")
    monkeypatch.setenv("POSTHOG_PROJECT_ID", " 123 ")
    key, project_id = phd._posthog_credentials()
    assert key == "phx_a"
    assert project_id == "123"


def test_scalar_parses_int_and_handles_bad_rows() -> None:
    from scripts import posthog_dashboard as phd

    errors: list[str] = []
    with mock.patch.object(phd, "posthog_query", return_value={"results": [[42]]}):
        assert phd._scalar("SELECT 1", "k", "1", errors) == 42
    with mock.patch.object(phd, "posthog_query", return_value={"results": [["x"]]}):
        assert phd._scalar("SELECT 1", "k", "1", errors) is None
    with mock.patch.object(phd, "posthog_query", return_value={"results": []}):
        assert phd._scalar("SELECT 1", "k", "1", errors) is None


def test_scalar_float_rounds() -> None:
    from scripts import posthog_dashboard as phd

    errors: list[str] = []
    with mock.patch.object(phd, "posthog_query", return_value={"results": [[1.239]]}):
        assert phd._scalar_float("SELECT 1", "k", "1", errors) == 1.24


def test_rows_returns_empty_on_missing() -> None:
    from scripts import posthog_dashboard as phd

    errors: list[str] = []
    with mock.patch.object(phd, "posthog_query", return_value=None):
        assert phd._rows("SELECT 1", "k", "1", errors) == []
    with mock.patch.object(
        phd, "posthog_query", return_value={"results": [["a", 1], ["b", 2]]}
    ):
        assert phd._rows("SELECT 1", "k", "1", errors) == [["a", 1], ["b", 2]]


def test_posthog_query_records_http_errors() -> None:
    from scripts import posthog_dashboard as phd

    class FakeResp:
        status_code = 401
        text = "unauthorized"

        def json(self):
            raise AssertionError("json should not be called")

    class FakeRequests:
        class RequestException(Exception):
            pass

        @staticmethod
        def post(*_args, **_kwargs):
            return FakeResp()

    errors: list[str] = []
    with mock.patch.object(phd, "_requests_module", return_value=FakeRequests):
        assert phd.posthog_query("SELECT 1", "k", "1", errors) is None
    assert any(e.startswith("http_401") for e in errors)


def test_build_dashboard_aggregates_mocked_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import posthog_dashboard as phd

    monkeypatch.setenv("POSTHOG_PERSONAL_API_KEY", "phx")
    monkeypatch.setenv("POSTHOG_PROJECT_ID", "9")
    with mock.patch.object(phd, "_funnel_section", return_value={"ok": True}), mock.patch.object(
        phd, "_engagement_section", return_value={"e": 1}
    ), mock.patch.object(
        phd, "_feature_popularity_section", return_value={"f": 1}
    ), mock.patch.object(
        phd, "_revenue_section", return_value={"r": 1}
    ), mock.patch.object(
        phd, "_retention_section", return_value={"t": 1}
    ):
        dash = phd.build_dashboard(load_dotenv=False)
    assert dash["status"] == "ok"
    assert dash["funnel"] == {"ok": True}
    assert dash["engagement"] == {"e": 1}


def test_build_dashboard_skips_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import posthog_dashboard as phd

    monkeypatch.delenv("POSTHOG_PERSONAL_API_KEY", raising=False)
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    monkeypatch.delenv("posthog_api_key", raising=False)
    monkeypatch.delenv("POSTHOG_PROJECT_ID", raising=False)
    dash = phd.build_dashboard(load_dotenv=False)
    assert dash["status"] == "skipped"
