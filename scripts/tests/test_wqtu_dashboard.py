import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class WqtuDashboardTests(unittest.TestCase):
    def test_missing_credentials_writes_skipped(self):
        from scripts import wqtu_dashboard as wd

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.dict(
                "os.environ",
                {"POSTHOG_PERSONAL_API_KEY": "", "POSTHOG_API_KEY": "", "posthog_api_key": "", "POSTHOG_PROJECT_ID": ""},
                clear=True,
            ):
                result = wd.run(root)

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["wqtu"], 0)
            out = root / "marketing" / "data" / "wqtu_health.json"
            self.assertTrue(out.exists())

    def test_wqtu_computed_from_mock_posthog(self):
        from scripts import wqtu_dashboard as wd

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.dict(
                "os.environ",
                {"POSTHOG_PERSONAL_API_KEY": "phx_test", "POSTHOG_PROJECT_ID": "12345"},
                clear=True,
            ):
                with mock.patch.object(
                    wd, "posthog_query", return_value={"results": [[42]]}
                ), mock.patch.object(
                    wd, "query_scalar", return_value=10
                ), mock.patch.object(
                    wd, "query_rows", return_value=[]
                ):
                    result = wd.run(root, alert_threshold=0)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["nsm"]["wqtu"], 42)
            out = root / "marketing" / "data" / "wqtu_health.json"
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["nsm"]["wqtu"], 42)

    def test_alert_fires_when_below_threshold(self):
        from scripts import wqtu_dashboard as wd

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.dict(
                "os.environ",
                {"POSTHOG_PERSONAL_API_KEY": "phx_test", "POSTHOG_PROJECT_ID": "12345"},
                clear=True,
            ):
                with mock.patch.object(
                    wd, "posthog_query", return_value={"results": [[2]]}
                ), mock.patch.object(
                    wd, "query_scalar", return_value=0
                ), mock.patch.object(
                    wd, "query_rows", return_value=[]
                ):
                    result = wd.run(root, alert_threshold=5)

            self.assertEqual(result["status"], "alert")
            self.assertTrue(result["nsm"]["alert_fired"])

    def test_history_appended_across_runs(self):
        from scripts import wqtu_dashboard as wd

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.dict(
                "os.environ",
                {"POSTHOG_PERSONAL_API_KEY": "phx_test", "POSTHOG_PROJECT_ID": "12345"},
                clear=True,
            ):
                with mock.patch.object(
                    wd, "posthog_query", return_value={"results": [[5]]}
                ), mock.patch.object(
                    wd, "query_scalar", return_value=1
                ), mock.patch.object(
                    wd, "query_rows", return_value=[]
                ):
                    wd.run(root)
                    wd.run(root)

            out = root / "marketing" / "data" / "wqtu_health.json"
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["history"]), 2)


class ReleaseReadinessGateTests(unittest.TestCase):
    def _make_repo(self, td: str, platform: str = "both") -> Path:
        """Create a minimal repo structure that passes all checks."""
        root = Path(td)
        (root / "PRIVACY_POLICY.md").write_text("# Privacy\nWe respect your privacy.", encoding="utf-8")

        if platform in ("android", "both"):
            meta = root / "native-android" / "fastlane" / "metadata" / "android" / "en-US"
            meta.mkdir(parents=True)
            (meta / "title.txt").write_text("Random Timer", encoding="utf-8")
            (meta / "short_description.txt").write_text("Tactical random timer", encoding="utf-8")
            (meta / "full_description.txt").write_text("Full description here.", encoding="utf-8")
            shots = meta / "images" / "phoneScreenshots"
            shots.mkdir(parents=True)
            for i in range(4):
                (shots / f"{i+1}_shot.png").write_bytes(b"\x89PNG" + b"\x00" * 10)

        if platform in ("ios", "both"):
            meta = root / "native-ios" / "fastlane" / "metadata" / "en-US"
            meta.mkdir(parents=True)
            (meta / "name.txt").write_text("Random Timer", encoding="utf-8")
            (meta / "subtitle.txt").write_text("Tactical Timer", encoding="utf-8")
            (meta / "description.txt").write_text(
                "Description.\n\nTerms of Use (EULA): https://example.com/eula/", encoding="utf-8"
            )
            (meta / "keywords.txt").write_text("timer,random,tactical", encoding="utf-8")
            (meta / "release_notes.txt").write_text("Bug fixes.", encoding="utf-8")
            (meta / "privacy_url.txt").write_text("https://example.com/privacy", encoding="utf-8")
            (meta / "support_url.txt").write_text("https://example.com/support", encoding="utf-8")

        return root

    def test_all_checks_pass_with_complete_metadata(self):
        from scripts.release_readiness_gate import Gate

        with tempfile.TemporaryDirectory() as td:
            root = self._make_repo(td)
            gate = Gate(root, "both")
            result = gate.run_all()

        self.assertTrue(result["ready"])
        self.assertEqual(len(result["errors"]), 0)

    def test_missing_privacy_policy_fails(self):
        from scripts.release_readiness_gate import Gate

        with tempfile.TemporaryDirectory() as td:
            root = self._make_repo(td)
            (root / "PRIVACY_POLICY.md").unlink()
            gate = Gate(root, "both")
            result = gate.run_all()

        self.assertFalse(result["ready"])
        self.assertTrue(any("privacy_policy" in e for e in result["errors"]))

    def test_missing_android_title_fails(self):
        from scripts.release_readiness_gate import Gate

        with tempfile.TemporaryDirectory() as td:
            root = self._make_repo(td, "android")
            (root / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "title.txt").unlink()
            gate = Gate(root, "android")
            result = gate.run_all()

        self.assertFalse(result["ready"])
        self.assertTrue(any("android_title" in e for e in result["errors"]))

    def test_missing_ios_keywords_fails(self):
        from scripts.release_readiness_gate import Gate

        with tempfile.TemporaryDirectory() as td:
            root = self._make_repo(td, "ios")
            (root / "native-ios" / "fastlane" / "metadata" / "en-US" / "keywords.txt").unlink()
            gate = Gate(root, "ios")
            result = gate.run_all()

        self.assertFalse(result["ready"])
        self.assertTrue(any("ios_keywords" in e for e in result["errors"]))

    def test_insufficient_screenshots_fails(self):
        from scripts.release_readiness_gate import Gate

        with tempfile.TemporaryDirectory() as td:
            root = self._make_repo(td, "android")
            shots = root / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "images" / "phoneScreenshots"
            for f in list(shots.glob("*.png"))[2:]:
                f.unlink()
            gate = Gate(root, "android")
            result = gate.run_all()

        self.assertFalse(result["ready"])
        self.assertTrue(any("screenshot" in e for e in result["errors"]))

    def test_ios_bad_privacy_url_fails(self):
        from scripts.release_readiness_gate import Gate

        with tempfile.TemporaryDirectory() as td:
            root = self._make_repo(td, "ios")
            (root / "native-ios" / "fastlane" / "metadata" / "en-US" / "privacy_url.txt").write_text(
                "insecure.example/privacy", encoding="utf-8"
            )
            gate = Gate(root, "ios")
            result = gate.run_all()

        self.assertFalse(result["ready"])
        self.assertTrue(any("privacy_url" in e for e in result["errors"]))

    def test_ios_missing_terms_link_fails(self):
        from scripts.release_readiness_gate import Gate

        with tempfile.TemporaryDirectory() as td:
            root = self._make_repo(td, "ios")
            (root / "native-ios" / "fastlane" / "metadata" / "en-US" / "description.txt").write_text(
                "Description only.", encoding="utf-8"
            )
            gate = Gate(root, "ios")
            result = gate.run_all()

        self.assertFalse(result["ready"])
        self.assertTrue(any("ios_terms_link" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
