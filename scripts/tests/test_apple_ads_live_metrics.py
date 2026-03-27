from __future__ import annotations

import json
from pathlib import Path

import pytest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import apple_ads_live_metrics as aam


class _Resp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def test_run_skips_without_oauth(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    (repo_root / "marketing" / "data").mkdir(parents=True)
    monkeypatch.setattr(aam, "load_env", lambda _: None)
    monkeypatch.setattr(aam, "_oauth_access_token", lambda: ("", "missing creds"))

    result = aam.run(repo_root, window_days=30, adam_id=6758355312)

    assert result["status"] == "skipped"
    output = repo_root / "marketing" / "data" / "apple_ads_live_metrics.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "skipped"
    assert "missing creds" in payload["status_reason"]


def test_run_writes_metrics_snapshot(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    (repo_root / "marketing" / "data").mkdir(parents=True)
    monkeypatch.setattr(aam, "load_env", lambda _: None)
    monkeypatch.setattr(aam, "_oauth_access_token", lambda: ("token", ""))
    monkeypatch.setattr(
        aam,
        "_ads_headers",
        lambda _: ({"Authorization": "Bearer token", "X-AP-Context": "orgId=1"}, ""),
    )

    campaigns_payload = {
        "data": [
            {
                "id": 101,
                "name": "Random Tactical Timer - Search v1",
                "status": "ENABLED",
                "servingStatus": "RUNNING",
                "dailyBudgetAmount": {"amount": "10", "currency": "USD"},
            }
        ]
    }
    report_payload = {
        "data": {
            "reportingDataResponse": {
                "row": [
                    {
                        "metadata": {
                            "campaignId": 101,
                            "campaignName": "Random Tactical Timer - Search v1",
                            "campaignStatus": "ENABLED",
                            "servingStatus": "RUNNING",
                        },
                        "total": {
                            "impressions": 100,
                            "taps": 10,
                            "localSpend": {"amount": "12.34", "currency": "USD"},
                            "totalInstalls": 4,
                            "tapInstalls": 3,
                        },
                    }
                ]
            }
        }
    }

    monkeypatch.setattr(aam, "_api_get", lambda _p, _h: _Resp(200, campaigns_payload))
    monkeypatch.setattr(aam, "_api_post", lambda _p, _h, _q: _Resp(200, report_payload))

    result = aam.run(repo_root, window_days=30, adam_id=6758355312)
    assert result["status"] == "ok"
    assert result["campaign_count"] == 1
    assert result["active_campaign_count"] == 1
    assert result["taps_30d"] == 10

    output = repo_root / "marketing" / "data" / "apple_ads_live_metrics.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["metrics_30d"]["impressions"] == 100
    assert payload["metrics_30d"]["spend_usd"] == pytest.approx(12.34)
    assert payload["metrics_30d"]["installs"] == 4
    assert payload["metrics_30d"]["tap_install_cpi_usd"] > 0


def test_ads_headers_requires_org_id(monkeypatch) -> None:
    monkeypatch.delenv("APPLE_ADS_ORG_ID", raising=False)
    headers, err = aam._ads_headers("token")
    assert headers == {}
    assert "missing APPLE_ADS_ORG_ID" in err


def test_read_private_key_from_relative_path(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "keys" / "ads.p8"
    key_path.parent.mkdir(parents=True)
    key_path.write_text("line1\nline2\n", encoding="utf-8")
    monkeypatch.setenv("APPLE_ADS_PRIVATE_KEY_PATH", str(Path("keys") / "ads.p8"))
    monkeypatch.delenv("APPLE_ADS_PRIVATE_KEY", raising=False)

    key = aam._read_private_key(tmp_path)
    assert key == "line1\nline2\n"


def test_run_degraded_when_campaign_list_fails(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    (repo_root / "marketing" / "data").mkdir(parents=True)
    monkeypatch.setattr(aam, "load_env", lambda _: None)
    monkeypatch.setattr(aam, "_oauth_access_token", lambda: ("token", ""))
    monkeypatch.setattr(
        aam,
        "_ads_headers",
        lambda _: ({"Authorization": "Bearer token", "X-AP-Context": "orgId=1"}, ""),
    )
    monkeypatch.setattr(aam, "_api_get", lambda _p, _h: _Resp(503, {}))

    result = aam.run(repo_root, window_days=30, adam_id=6758355312)

    assert result["status"] == "degraded"
    assert "campaign list failed" in result["reason"]
    output = repo_root / "marketing" / "data" / "apple_ads_live_metrics.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "degraded"
    assert payload["campaign_count"] == 0


def test_run_trims_snapshots_to_120_entries(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    output = repo_root / "marketing" / "data" / "apple_ads_live_metrics.json"
    output.parent.mkdir(parents=True)
    output.write_text(
        json.dumps({"snapshots": [{"timestamp": f"t{i}"} for i in range(130)]}),
        encoding="utf-8",
    )

    monkeypatch.setattr(aam, "load_env", lambda _: None)
    monkeypatch.setattr(aam, "_oauth_access_token", lambda: ("token", ""))
    monkeypatch.setattr(
        aam,
        "_ads_headers",
        lambda _: ({"Authorization": "Bearer token", "X-AP-Context": "orgId=1"}, ""),
    )
    monkeypatch.setattr(
        aam,
        "_api_get",
        lambda _p, _h: _Resp(200, {"data": [{"id": 1, "status": "ENABLED", "servingStatus": "RUNNING"}]}),
    )
    monkeypatch.setattr(
        aam,
        "_api_post",
        lambda _p, _h, _q: _Resp(200, {"data": {"reportingDataResponse": {"row": []}}}),
    )

    aam.run(repo_root, window_days=30, adam_id=6758355312)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload["snapshots"]) == 120
