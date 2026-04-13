"""Tests for Play Data Safety API upload helper."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts import play_data_safety_upload as pdsu


def test_upload_data_safety_csv_rejects_empty() -> None:
    out = pdsu.upload_data_safety_csv("com.example.app", "", dry_run=False)
    assert out["status"] == "error"
    assert "empty" in str(out.get("reason", "")).lower()


def test_upload_data_safety_dry_run_skips_api() -> None:
    out = pdsu.upload_data_safety_csv("com.example.app", "a,b\n1,2", dry_run=True)
    assert out["status"] == "dry_run"
    assert out["safety_labels_bytes"] > 0


def test_upload_data_safety_calls_data_safety_method(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _Req:
        def execute(self) -> dict:
            return {}

    class _Apps:
        def dataSafety(self, packageName: str, body: dict) -> _Req:
            captured["packageName"] = packageName
            captured["body"] = body
            return _Req()

    fake_service = MagicMock()
    fake_service.applications.return_value = _Apps()

    monkeypatch.setattr(pdsu, "_credentials_and_service", lambda: (fake_service, None))

    out = pdsu.upload_data_safety_csv("com.test.app", "header\nrow", dry_run=False)
    assert out["status"] == "ok"
    assert captured["packageName"] == "com.test.app"
    assert captured["body"] == {"safetyLabels": "header\nrow"}


def test_main_exits_nonzero_for_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.csv"
    with patch("sys.argv", ["play_data_safety_upload.py", "--csv-path", str(missing)]):
        assert pdsu.main() == 1
