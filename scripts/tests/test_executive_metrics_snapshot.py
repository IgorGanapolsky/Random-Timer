"""Tests for executive_metrics_snapshot.py."""

import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture()
def ems_module(tmp_path, monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    fake_rs = types.ModuleType("real_store_downloads")
    fake_rs._get_android_data = lambda days: {"status": "skipped", "reason": "stub"}
    fake_rs._get_ios_data = lambda days: {"status": "skipped", "reason": "stub"}
    monkeypatch.setitem(sys.modules, "real_store_downloads", fake_rs)
    fake_cc = types.ModuleType("check_crashlytics")
    fake_cc.collect_crashlytics_snapshot = lambda hours=168: {
        "status": "ok",
        "fatal_crash_events": 0,
        "source": "stub",
    }
    monkeypatch.setitem(sys.modules, "check_crashlytics", fake_cc)
    monkeypatch.setenv("POSTHOG_PROJECT_ID", "")
    monkeypatch.delenv("POSTHOG_PERSONAL_API_KEY", raising=False)
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)

    spec = importlib.util.spec_from_file_location(
        "executive_metrics_snapshot",
        repo_root / "scripts" / "executive_metrics_snapshot.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_writes_json_without_posthog(ems_module, tmp_path):
    ems_module.run(tmp_path, load_dotenv=False)
    out = tmp_path / "marketing" / "data" / "executive_metrics.json"
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["posthog"]["status"] == "skipped"
    assert data["store_apis"]["android"]["status"] == "skipped"
    assert data["crashlytics_bigquery"]["fatal_crash_events"] == 0


def test_posthog_section_with_mock_query(ems_module):
    repo_root = Path(__file__).resolve().parents[2]
    scripts_dir = str(repo_root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import store_downloads_snapshot as sds

    def fake_posthog_query(query, api_key, project_id, errors):
        if "event = 'Application Installed'" in query:
            return {"results": [[42]]}
        if "event = 'first_open'" in query and "distinct" in query.lower():
            return {"results": [[40]]}
        if "review_prompt_requested" in query:
            return {"results": [[3, 2]]}
        if "$screen" in query:
            return {"results": [["Timer Setup", 10, 50]]}
        return {"results": [[0]]}

    with patch.object(sds, "posthog_query", side_effect=fake_posthog_query):
        out = ems_module._posthog_section("123", "phx_test", days=7)
    assert out["status"] == "ok"
    assert out["distinct_persons_application_installed"] == 42
    assert out["distinct_persons_first_open"] == 40
