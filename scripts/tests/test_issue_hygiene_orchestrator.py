from __future__ import annotations

from pathlib import Path

from scripts.issue_hygiene_orchestrator import (
    decide_ci_gate_issue,
    decide_pr_incident,
    decide_release_watch,
    parse_release_watch_version,
    parse_semver,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_parse_release_watch_version() -> None:
    assert parse_release_watch_version("Release watch: v1.3.56") == "1.3.56"
    assert parse_release_watch_version("unrelated") is None


def test_parse_semver_orders() -> None:
    assert parse_semver("1.3.56") > parse_semver("1.3.55")
    assert parse_semver("1.3.9") < parse_semver("1.3.10")


def test_release_watch_closes_when_superseded_by_live() -> None:
    decision = decide_release_watch(
        title="Release watch: v1.3.26",
        live_ios="1.3.56",
        live_play="1.3.56",
    )
    assert decision.action == "close"
    assert decision.reason == "superseded"


def test_release_watch_closes_when_both_stores_live() -> None:
    decision = decide_release_watch(
        title="Release watch: v1.3.56",
        live_ios="1.3.56",
        live_play="1.3.56",
    )
    assert decision.action == "close"
    assert decision.reason == "both_live"


def test_release_watch_keeps_in_flight_newer_than_live() -> None:
    decision = decide_release_watch(
        title="Release watch: v1.3.58",
        live_ios="1.3.56",
        live_play="1.3.56",
        created_at="2026-09-01T00:00:00Z",
        now=__import__("datetime").datetime(2026, 9, 6, tzinfo=__import__("datetime").timezone.utc),
    )
    assert decision.action == "keep"


def test_release_watch_closes_stale_in_flight() -> None:
    decision = decide_release_watch(
        title="Release watch: v1.3.58",
        live_ios="1.3.56",
        live_play="1.3.56",
        created_at="2026-07-01T00:00:00Z",
        now=__import__("datetime").datetime(2026, 9, 6, tzinfo=__import__("datetime").timezone.utc),
    )
    assert decision.action == "close"
    assert decision.reason == "stale_in_flight"


def test_pr_incident_closes_when_pr_merged() -> None:
    decision = decide_pr_incident(
        title="PR Incident: #1834 required checks failing",
        pr_state="MERGED",
    )
    assert decision.action == "close"
    assert decision.reason == "pr_merged"


def test_pr_incident_closes_when_pr_closed() -> None:
    decision = decide_pr_incident(
        title="PR Incident: #1499 required checks failing",
        pr_state="CLOSED",
    )
    assert decision.action == "close"
    assert decision.reason == "pr_closed"


def test_pr_incident_keeps_open_blocked_pr() -> None:
    decision = decide_pr_incident(
        title="PR Incident: #1840 required checks failing",
        pr_state="OPEN",
    )
    assert decision.action == "keep"


def test_ci_gate_issue_closes_when_contracts_green() -> None:
    decision = decide_ci_gate_issue(
        title="CI base gates red: voice regression contracts failing on every PR",
        voice_contracts_passing=True,
    )
    assert decision.action == "close"


def test_orchestrator_files_exist() -> None:
    assert (REPO_ROOT / "scripts" / "issue_hygiene_orchestrator.py").is_file()
    wf = REPO_ROOT / ".github" / "workflows" / "issue-hygiene-orchestrator.yml"
    assert wf.is_file()
    text = wf.read_text(encoding="utf-8")
    assert "schedule:" in text
    assert "issue_hygiene_orchestrator.py" in text
    assert "workflow_dispatch" in text
