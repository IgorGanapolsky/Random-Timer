import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class StoreDownloadsSnapshotTests(unittest.TestCase):
    def test_run_missing_credentials_writes_placeholder(self):
        from scripts import store_downloads_snapshot as sds

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
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
                result = sds.run(root, days=30)

            self.assertEqual(result["status"], "skipped")
            out = root / "marketing" / "data" / "store_downloads.json"
            self.assertTrue(out.exists())
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "skipped")
            self.assertEqual(payload["combined"]["downloads_30d"], 0)

    def test_run_with_mock_queries_generates_metrics(self):
        from scripts import store_downloads_snapshot as sds

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ):
                with mock.patch.object(
                    sds,
                    "query_rows",
                    return_value=[["iOS", 5], ["Android", 7]],
                ), mock.patch.object(
                    sds,
                    "query_scalar",
                    side_effect=[11, 3, 9, 20],
                ):
                    result = sds.run(root, days=30)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["ios_downloads_30d"], 5)
            self.assertEqual(result["android_downloads_30d"], 7)
            self.assertEqual(result["combined_downloads_30d"], 12)
            self.assertEqual(result["dau"], 3)
            self.assertEqual(result["wau"], 9)
            self.assertEqual(result["mau"], 20)

            out = root / "marketing" / "data" / "store_downloads.json"
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["android"]["active_installs"], 11)
            self.assertEqual(len(payload["snapshots"]), 1)

    def test_run_preserves_previous_metrics_when_query_degrades(self):
        from scripts import store_downloads_snapshot as sds

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = root / "marketing" / "data" / "store_downloads.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-03-15T10:00:00+00:00",
                        "status": "ok",
                        "ios": {"downloads_30d": 4},
                        "android": {"downloads_30d": 10, "active_installs": 9},
                        "combined": {"downloads_30d": 14},
                        "active_users": {"dau": 2, "wau": 6, "mau": 15},
                        "snapshots": [{"timestamp": "2026-03-15T10:00:00+00:00", "combined_downloads_30d": 14}],
                    }
                ),
                encoding="utf-8",
            )

            def degraded_rows(_sql, _key, _project_id, errors):
                errors.append("http_504")
                return []

            def degraded_scalar(_sql, _key, _project_id, errors):
                errors.append("http_504")
                return 0

            with mock.patch.dict(
                "os.environ",
                {
                    "POSTHOG_PERSONAL_API_KEY": "phx_test",
                    "POSTHOG_PROJECT_ID": "299775",
                },
                clear=True,
            ), mock.patch.object(sds, "query_rows", side_effect=degraded_rows), mock.patch.object(
                sds, "query_scalar", side_effect=degraded_scalar
            ):
                result = sds.run(root, days=30)

            self.assertEqual(result["status"], "degraded")
            self.assertTrue(result["preserved_previous_metrics"])
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["combined"]["downloads_30d"], 14)
            self.assertTrue(payload["data_quality"]["is_stale"])
            self.assertEqual(payload["data_quality"]["last_good_generated_at"], "2026-03-15T10:00:00+00:00")
            self.assertEqual(len(payload["snapshots"]), 1)

    @mock.patch("scripts.store_downloads_snapshot.time.sleep", autospec=True)
    def test_posthog_query_retries_on_transient_http_then_succeeds(self, _sleep):
        from scripts import store_downloads_snapshot as sds

        errors: list[str] = []
        bad = mock.Mock()
        bad.status_code = 504
        good = mock.Mock()
        good.status_code = 200
        good.json.return_value = {"results": [[7]]}

        fake_requests = mock.Mock()
        fake_requests.RequestException = Exception
        fake_requests.post.side_effect = [bad, good]

        with mock.patch.object(sds, "_requests_module", return_value=fake_requests):
            out = sds.posthog_query("SELECT 1", "k", "123", errors)

        self.assertEqual(out, {"results": [[7]]})
        self.assertEqual(errors, [])
        self.assertEqual(fake_requests.post.call_count, 2)

    @mock.patch("scripts.store_downloads_snapshot.time.sleep", autospec=True)
    def test_posthog_query_appends_error_after_exhausting_retries(self, _sleep):
        from scripts import store_downloads_snapshot as sds

        errors: list[str] = []
        bad = mock.Mock()
        bad.status_code = 504

        fake_requests = mock.Mock()
        fake_requests.RequestException = Exception
        fake_requests.post.return_value = bad

        with mock.patch.object(sds, "_requests_module", return_value=fake_requests):
            out = sds.posthog_query("SELECT 1", "k", "123", errors, max_retries=2)

        self.assertIsNone(out)
        self.assertEqual(errors, ["http_504"])
        self.assertEqual(fake_requests.post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
