import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class AscWatchStatusTests(unittest.TestCase):
    def test_append_if_changed_first_write_and_noop_second(self):
        from scripts.asc_watch_status import append_if_changed

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "status.jsonl"
            rec = {
                "iso": "2026-02-21T00:00:00Z",
                "bundle_id": "com.example.app",
                "app_id": "123",
                "version": "1.1.2",
                "version_id": "ver1",
                "state": "WAITING_FOR_REVIEW",
            }
            changed_1 = append_if_changed(p, rec)
            changed_2 = append_if_changed(p, rec)

            self.assertTrue(changed_1)
            self.assertFalse(changed_2)
            lines = p.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0])["state"], "WAITING_FOR_REVIEW")

    def test_append_if_changed_writes_on_state_transition(self):
        from scripts.asc_watch_status import append_if_changed

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "status.jsonl"
            rec_1 = {
                "iso": "2026-02-21T00:00:00Z",
                "bundle_id": "com.example.app",
                "app_id": "123",
                "version": "1.1.2",
                "version_id": "ver1",
                "state": "WAITING_FOR_REVIEW",
            }
            rec_2 = dict(rec_1)
            rec_2["iso"] = "2026-02-21T01:00:00Z"
            rec_2["state"] = "IN_REVIEW"

            self.assertTrue(append_if_changed(p, rec_1))
            self.assertTrue(append_if_changed(p, rec_2))
            lines = p.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[-1])["state"], "IN_REVIEW")

    def test_append_if_changed_writes_when_version_id_changes(self):
        from scripts.asc_watch_status import append_if_changed

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "status.jsonl"
            rec_1 = {
                "iso": "2026-02-21T00:00:00Z",
                "bundle_id": "com.example.app",
                "app_id": "123",
                "version": "1.1.2",
                "version_id": "ver1",
                "state": "WAITING_FOR_REVIEW",
            }
            rec_2 = dict(rec_1)
            rec_2["iso"] = "2026-02-21T00:10:00Z"
            rec_2["version_id"] = "ver2"

            self.assertTrue(append_if_changed(p, rec_1))
            self.assertTrue(append_if_changed(p, rec_2))
            lines = p.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)

    def test_read_last_jsonl_returns_none_for_invalid_last_line(self):
        from scripts.asc_watch_status import _read_last_jsonl

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "status.jsonl"
            p.write_text('{"state":"WAITING_FOR_REVIEW"}\nnot-json\n', encoding="utf-8")
            self.assertIsNone(_read_last_jsonl(p))

    def test_main_rejects_non_positive_max_polls(self):
        from scripts import asc_watch_status

        fake_args = mock.Mock(
            max_polls=0,
            jsonl="status.jsonl",
            bundle_id="com.example.app",
            version="1.0.0",
            print_json=False,
            interval=1,
        )
        with mock.patch("scripts.asc_watch_status.parse_args", return_value=fake_args):
            with self.assertRaises(SystemExit):
                asc_watch_status.main()


if __name__ == "__main__":
    unittest.main()
