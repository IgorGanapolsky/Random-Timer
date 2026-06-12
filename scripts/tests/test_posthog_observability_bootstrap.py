"""Tests for posthog_observability_bootstrap (no live PostHog required)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "marketing" / "data" / "posthog_observability.json"


def test_observability_config_has_unique_query_ids() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    ids = [q["id"] for q in config["saved_queries"]]
    assert len(ids) == len(set(ids))


def test_observability_config_queries_are_non_empty() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for item in config["saved_queries"]:
        assert item["hogql"].strip()
        assert "FROM events" in item["hogql"]


def test_bootstrap_module_loads_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import posthog_observability_bootstrap as bootstrap

    monkeypatch.setattr(bootstrap, "CONFIG_PATH", CONFIG_PATH)
    monkeypatch.setattr(bootstrap, "STATUS_PATH", tmp_path / "status.json")
    config = bootstrap.load_config()
    results = bootstrap.verify_saved_queries(config)
    assert len(results) == len(config["saved_queries"])
    assert all("skipped" in r for r in results)
