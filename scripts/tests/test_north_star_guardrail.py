from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class NorthStarGuardrailTests(unittest.TestCase):
    def _write_paid_campaigns(
        self,
        root: Path,
        statuses: list[str],
        launched_at: list[str | None] | None = None,
    ) -> None:
        path = root / "marketing" / "data" / "paid_campaigns.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        launch_times = launched_at or [None] * len(statuses)
        payload = {
            "campaigns": [
                {
                    "platform": f"p{i}",
                    "status": status,
                    "daily_budget_usd": 10.0,
                    "launched_at": launch_times[i],
                }
                for i, status in enumerate(statuses)
            ]
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_run_missing_credentials_marks_skipped(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["draft"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "",
                    "POSTHOG_API_KEY": "",
                    "posthog_api_key": "",
                    "POSTHOG_PROJECT_ID": "",
                },
                clear=True,
            ):
                result = nsg.run(root)

            self.assertEqual(result["status"], "skipped")
            out = root / "marketing" / "data" / "north_star.json"
            self.assertTrue(out.exists())
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "skipped")
            self.assertFalse(payload["paid"]["guardrail_violated"])
            self.assertFalse(payload["paid"]["no_scale_lock"]["active"])
            self.assertEqual(payload["paid"]["no_scale_lock"]["enforceable_status"], "not_applicable")

    def test_guardrail_violates_when_active_and_zero_paid_users(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["active"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ):
                # query_scalar calls:
                # wqtu, completions_7d, completed_users_7d, paid_distinct_users_30d
                with mock.patch.object(
                    nsg,
                    "query_scalar",
                    side_effect=[0, 2, 1, 0],
                ), mock.patch.object(
                    nsg,
                    "query_rows",
                    return_value=[],
                ):
                    result = nsg.run(root)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["active_campaign_count"], 1)
            self.assertEqual(result["paid_distinct_users_30d"], 0)
            self.assertTrue(result["guardrail_violated"])
            self.assertTrue(result["no_scale_lock_active"])
            self.assertEqual(result["no_scale_lock_enforceable_status"], "enforceable")

    def test_guardrail_grace_window_skips_violation_for_new_campaign(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["active"], launched_at=["2026-02-24T16:30:00Z"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ):
                with mock.patch.object(
                    nsg,
                    "query_scalar",
                    side_effect=[0, 2, 1, 0],
                ), mock.patch.object(
                    nsg,
                    "query_rows",
                    return_value=[],
                ), mock.patch.object(
                    nsg.dt,
                    "datetime",
                    wraps=nsg.dt.datetime,
                ) as mock_datetime:
                    mock_datetime.now.return_value = nsg.dt.datetime(2026, 2, 24, 17, 0, tzinfo=nsg.dt.timezone.utc)
                    result = nsg.run(root, campaign_grace_days=7)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["active_campaign_count"], 1)
            self.assertEqual(result["paid_distinct_users_30d"], 0)
            self.assertFalse(result["guardrail_violated"])
            self.assertFalse(result["no_scale_lock_active"])
            self.assertEqual(result["no_scale_lock_enforceable_status"], "advisory")

    def test_guardrail_violates_with_apple_traffic_signal_even_in_grace(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_dir = root / "marketing" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / "apple_ads_live_metrics.json").write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "metrics_30d": {"taps": 5, "spend_usd": 2.1, "installs": 0},
                    }
                ),
                encoding="utf-8",
            )
            path = data_dir / "paid_campaigns.json"
            path.write_text(
                json.dumps(
                    {
                        "campaigns": [
                            {
                                "platform": "apple_search_ads",
                                "status": "active",
                                "daily_budget_usd": 10.0,
                                "launched_at": "2026-02-24T16:30:00Z",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ):
                with mock.patch.object(
                    nsg,
                    "query_scalar",
                    side_effect=[0, 2, 1, 0],
                ), mock.patch.object(
                    nsg,
                    "query_rows",
                    return_value=[],
                ), mock.patch.object(
                    nsg.dt,
                    "datetime",
                    wraps=nsg.dt.datetime,
                ) as mock_datetime:
                    mock_datetime.now.return_value = nsg.dt.datetime(2026, 2, 24, 17, 0, tzinfo=nsg.dt.timezone.utc)
                    result = nsg.run(root, campaign_grace_days=7)

            self.assertTrue(result["guardrail_violated"])

    def test_guardrail_passes_with_paid_users(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["active", "running"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ):
                with mock.patch.object(
                    nsg,
                    "query_scalar",
                    side_effect=[3, 12, 4, 7],
                ), mock.patch.object(
                    nsg,
                    "query_rows",
                    return_value=[["apple_ads", 20, 7]],
                ):
                    result = nsg.run(root)

            self.assertEqual(result["wqtu_7d"], 3)
            self.assertEqual(result["active_campaign_count"], 2)
            self.assertEqual(result["paid_distinct_users_30d"], 7)
            self.assertFalse(result["guardrail_violated"])
            self.assertFalse(result["no_scale_lock_active"])
            self.assertEqual(result["no_scale_lock_enforceable_status"], "not_applicable")

    def test_main_require_posthog_when_active_fails_on_missing_credentials(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["active"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "",
                    "POSTHOG_API_KEY": "",
                    "posthog_api_key": "",
                    "POSTHOG_PROJECT_ID": "",
                },
                clear=True,
            ), mock.patch.object(
                sys,
                "argv",
                [
                    "north_star_guardrail.py",
                    "--repo-root",
                    str(root),
                    "--require-posthog-when-active",
                ],
            ):
                exit_code = nsg.main()

            self.assertEqual(exit_code, 3)

    def test_main_require_posthog_when_active_allows_missing_credentials_without_active_campaigns(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["draft"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "",
                    "POSTHOG_API_KEY": "",
                    "posthog_api_key": "",
                    "POSTHOG_PROJECT_ID": "",
                },
                clear=True,
            ), mock.patch.object(
                sys,
                "argv",
                [
                    "north_star_guardrail.py",
                    "--repo-root",
                    str(root),
                    "--require-posthog-when-active",
                ],
            ):
                exit_code = nsg.main()

            self.assertEqual(exit_code, 0)

    def test_main_require_posthog_when_active_fails_on_degraded_query(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["active"])

            def degraded_scalar(_sql: str, _key: str, _project_id: str, errors: list[str]) -> int:
                errors.append("query failed")
                return 0

            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ), mock.patch.object(
                nsg,
                "query_scalar",
                side_effect=degraded_scalar,
            ), mock.patch.object(
                nsg,
                "query_rows",
                return_value=[],
            ), mock.patch.object(
                sys,
                "argv",
                [
                    "north_star_guardrail.py",
                    "--repo-root",
                    str(root),
                    "--require-posthog-when-active",
                ],
            ):
                exit_code = nsg.main()

            self.assertEqual(exit_code, 3)

    def test_main_enforce_guardrail_fails_when_no_scale_lock_enforceable(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_paid_campaigns(root, ["active"])
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ), mock.patch.object(
                nsg,
                "query_scalar",
                side_effect=[0, 2, 1, 0],
            ), mock.patch.object(
                nsg,
                "query_rows",
                return_value=[],
            ), mock.patch.object(
                sys,
                "argv",
                [
                    "north_star_guardrail.py",
                    "--repo-root",
                    str(root),
                    "--enforce-guardrail",
                ],
            ):
                exit_code = nsg.main()

            self.assertEqual(exit_code, 1)

    def test_run_preserves_previous_query_metrics_when_posthog_degrades(self):
        from scripts import north_star_guardrail as nsg

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_dir = root / "marketing" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self._write_paid_campaigns(root, ["draft"])
            (data_dir / "north_star.json").write_text(
                json.dumps(
                    {
                        "generated_at": "2026-03-15T10:00:00+00:00",
                        "status": "ok",
                        "north_star": {
                            "wqtu_7d": 5,
                            "timer_completed_7d": 18,
                            "completed_users_7d": 6,
                            "sessions_per_completed_user_7d": 3.0,
                            "targets": {"checkpoint_2026_03_31": 8, "quarter_2026_06_30": 25},
                            "on_track_checkpoint": False,
                            "on_track_quarter": False,
                        },
                        "paid": {
                            "paid_distinct_users_30d": 4,
                            "paid_events_by_source_30d": [{"source": "apple_ads", "events": 7, "users": 4}],
                        },
                        "snapshots": [{"timestamp": "2026-03-15T10:00:00+00:00", "wqtu_7d": 5}],
                    }
                ),
                encoding="utf-8",
            )

            def degraded_scalar(_sql, _key, _project_id, errors):
                errors.append("http_504")
                return 0

            def degraded_rows(_sql, _key, _project_id, errors):
                errors.append("http_504")
                return []

            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ), mock.patch.object(nsg, "query_scalar", side_effect=degraded_scalar), mock.patch.object(
                nsg, "query_rows", side_effect=degraded_rows
            ):
                result = nsg.run(root)

            self.assertEqual(result["status"], "degraded")
            self.assertTrue(result["preserved_previous_metrics"])
            payload = json.loads((data_dir / "north_star.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["north_star"]["wqtu_7d"], 5)
            self.assertEqual(payload["paid"]["paid_distinct_users_30d"], 4)
            self.assertTrue(payload["data_quality"]["is_stale"])
            self.assertEqual(payload["data_quality"]["last_good_generated_at"], "2026-03-15T10:00:00+00:00")
            self.assertEqual(len(payload["snapshots"]), 1)


if __name__ == "__main__":
    unittest.main()
