import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from scripts.asc import asc_list_versions


class _FakeClient:
    pass


class AscListVersionsTests(unittest.TestCase):
    def test_normalize_versions(self):
        normalized = asc_list_versions._normalize_versions(
            [
                {
                    "id": "ver1",
                    "attributes": {
                        "versionString": "1.2.3",
                        "appStoreState": "PREPARE_FOR_SUBMISSION",
                        "createdDate": "2026-03-12T19:00:00Z",
                    },
                }
            ]
        )
        self.assertEqual(
            normalized,
            [
                {
                    "id": "ver1",
                    "version": "1.2.3",
                    "state": "PREPARE_FOR_SUBMISSION",
                    "createdDate": "2026-03-12T19:00:00Z",
                }
            ],
        )

    def test_main_writes_json_inventory(self):
        fake_versions = [
            {
                "id": "ver1",
                "attributes": {
                    "versionString": "1.2.3",
                    "appStoreState": "READY_FOR_SALE",
                    "createdDate": "2026-03-12T19:00:00Z",
                },
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "asc_versions.json"
            stdout = io.StringIO()
            with mock.patch("scripts.asc.asc_list_versions.ASCClient.from_env", return_value=_FakeClient()), mock.patch(
                "scripts.asc.asc_list_versions.get_app", return_value={"id": "app123"}
            ), mock.patch("scripts.asc.asc_list_versions._list_ios_versions", return_value=fake_versions), mock.patch(
                "sys.argv",
                ["asc_list_versions.py", "--json-out", str(out_path)],
            ), redirect_stdout(stdout):
                rc = asc_list_versions.main()
            payload = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(payload["app_id"], "app123")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["versions"][0]["version"], "1.2.3")
        self.assertIn("Versions: 1", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
