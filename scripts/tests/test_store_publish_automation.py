"""Contract and unit tests for hands-off iOS store publish automation."""

from __future__ import annotations

import io
import json
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]

from scripts.asc import asc_set_release_type as set_release_type_mod
from scripts.asc import asc_resolve_watcher_target as watcher_target


class StorePublishAutomationContracts(unittest.TestCase):
    def test_fastfile_uses_automatic_release_true(self):
        fastfile = (ROOT / "native-ios/fastlane/Fastfile").read_text(encoding="utf-8")
        self.assertIn("automatic_release: true", fastfile)
        self.assertNotIn("automatic_release: false", fastfile)

    def test_store_release_watcher_prefers_in_flight_target_resolution(self):
        watcher = (ROOT / ".github/workflows/store-release-watcher.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("asc_resolve_watcher_target.py", watcher)
        self.assertIn("WAITING_FOR_REVIEW", watcher)
        self.assertIn("PENDING_DEVELOPER_RELEASE", watcher)

    def test_store_release_watcher_auto_releases_pending_developer_release(self):
        watcher = (ROOT / ".github/workflows/store-release-watcher.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("asc_release_version.py", watcher)
        self.assertRegex(
            watcher,
            re.compile(
                r"if:\s*steps\.asc\.outputs\.state\s*==\s*'PENDING_DEVELOPER_RELEASE'",
                re.MULTILINE,
            ),
        )

    def test_autonomous_operations_documents_after_approval(self):
        doc = (ROOT / "docs/AUTONOMOUS_OPERATIONS.md").read_text(encoding="utf-8")
        self.assertIn("AFTER_APPROVAL", doc)
        self.assertIn("automatic_release", doc.lower())


class AscWatcherTargetTests(unittest.TestCase):
    def test_prefers_highest_in_flight_over_develop_tip(self):
        versions = [
            {
                "attributes": {
                    "versionString": "1.3.60",
                    "appStoreState": "WAITING_FOR_REVIEW",
                }
            },
            {
                "attributes": {
                    "versionString": "1.3.59",
                    "appStoreState": "IN_REVIEW",
                }
            },
        ]
        result = watcher_target.pick_watcher_target(
            versions=versions, develop_tip="1.3.61"
        )
        self.assertEqual(result["target_version"], "1.3.60")
        self.assertEqual(result["reason"], "in_flight_highest")

    def test_falls_back_to_develop_tip_when_no_in_flight(self):
        versions = [
            {
                "attributes": {
                    "versionString": "1.3.58",
                    "appStoreState": "READY_FOR_SALE",
                }
            }
        ]
        result = watcher_target.pick_watcher_target(
            versions=versions, develop_tip="1.3.61"
        )
        self.assertEqual(result["target_version"], "1.3.61")
        self.assertEqual(result["reason"], "develop_tip_fallback")


class AscSetReleaseTypeTests(unittest.TestCase):
    def test_already_after_approval_is_idempotent(self):
        client = Mock()
        client.get.return_value = {
            "data": {
                "id": "ver1",
                "attributes": {"releaseType": "AFTER_APPROVAL", "versionString": "1.3.60"},
            }
        }
        payload = set_release_type_mod.apply_release_type(
            client, version_id="ver1", release_type="AFTER_APPROVAL"
        )
        self.assertFalse(payload["changed"])
        client.request.assert_not_called()

    def test_patches_manual_release_to_after_approval(self):
        client = Mock()
        client.get.return_value = {
            "data": {
                "id": "ver1",
                "attributes": {"releaseType": "MANUAL", "versionString": "1.3.60"},
            }
        }
        client.request.return_value = {
            "data": {
                "id": "ver1",
                "attributes": {"releaseType": "AFTER_APPROVAL"},
            }
        }
        payload = set_release_type_mod.apply_release_type(
            client, version_id="ver1", release_type="AFTER_APPROVAL"
        )
        self.assertTrue(payload["changed"])
        client.request.assert_called_once()
        patch_payload = client.request.call_args.kwargs["payload"]
        self.assertEqual(
            patch_payload["data"]["attributes"]["releaseType"], "AFTER_APPROVAL"
        )

    def test_main_emits_json_for_version(self):
        client = Mock()
        with patch.object(set_release_type_mod, "ASCClient") as asc_client:
            asc_client.from_env.return_value = client
            with patch.object(set_release_type_mod, "get_app", return_value={"id": "app1"}):
                with patch.object(
                    set_release_type_mod,
                    "find_app_store_version_id",
                    return_value=("ver1", "WAITING_FOR_REVIEW"),
                ):
                    with patch.object(
                        set_release_type_mod,
                        "apply_release_type",
                        return_value={
                            "version_id": "ver1",
                            "prior_release_type": "MANUAL",
                            "release_type": "AFTER_APPROVAL",
                            "changed": True,
                        },
                    ):
                        with patch(
                            "sys.argv",
                            [
                                "asc_set_release_type.py",
                                "--version",
                                "1.3.60",
                                "--json",
                            ],
                        ):
                            buffer = io.StringIO()
                            with redirect_stdout(buffer):
                                code = set_release_type_mod.main()
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue().strip())
        self.assertEqual(payload["version"], "1.3.60")
        self.assertTrue(payload["changed"])


if __name__ == "__main__":
    unittest.main()
