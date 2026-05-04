import plistlib
import tempfile
import unittest
from pathlib import Path


from scripts.tests.router_client import RouterClient


class AscSubmitForReviewVerifyReviewDetailTests(unittest.TestCase):
    def test_verify_review_detail_reads_relationship_off_version(self):
        from scripts.asc.asc_submit_for_review import verify_review_detail

        client = RouterClient(
            {
                ("GET", "/appStoreVersions/ver1/appStoreReviewDetail"): {
                    "data": {
                        "id": "rd1",
                        "type": "appStoreReviewDetails",
                        "attributes": {"contactEmail": "dev@example.com", "contactPhone": "+15551231234"},
                    }
                }
            }
        )
        verify_review_detail(client, "ver1")
        self.assertEqual([c["path"] for c in client.calls], ["/appStoreVersions/ver1/appStoreReviewDetail"])

    def test_verify_review_detail_requires_contact_email(self):
        from scripts.asc.asc_submit_for_review import verify_review_detail

        client = RouterClient(
            {
                ("GET", "/appStoreVersions/ver1/appStoreReviewDetail"): {
                    "data": {"id": "rd1", "type": "appStoreReviewDetails", "attributes": {"contactPhone": "123"}}
                }
            }
        )
        with self.assertRaises(SystemExit):
            verify_review_detail(client, "ver1")

    def test_background_audio_review_note_patches_missing_instructions(self):
        from scripts.asc.asc_submit_for_review import (
            BACKGROUND_AUDIO_REVIEW_NOTE,
            ensure_background_audio_review_note,
        )

        with tempfile.TemporaryDirectory() as tmp:
            plist_path = Path(tmp) / "Info.plist"
            with plist_path.open("wb") as f:
                plistlib.dump({"UIBackgroundModes": ["audio"]}, f)

            client = RouterClient(
                {
                    ("GET", "/appStoreVersions/ver1/appStoreReviewDetail"): {
                        "data": {
                            "id": "rd1",
                            "type": "appStoreReviewDetails",
                            "attributes": {"notes": "Existing review notes."},
                        }
                    },
                    ("PATCH", "/appStoreReviewDetails/rd1"): {
                        "data": {"id": "rd1", "type": "appStoreReviewDetails", "attributes": {}}
                    },
                }
            )

            ensure_background_audio_review_note(client, "ver1", info_plist_path=str(plist_path))

        self.assertEqual(client.calls[1]["method"], "PATCH")
        self.assertEqual(client.calls[1]["path"], "/appStoreReviewDetails/rd1")
        notes = client.calls[1]["payload"]["data"]["attributes"]["notes"]
        self.assertIn("Existing review notes.", notes)
        self.assertIn(BACKGROUND_AUDIO_REVIEW_NOTE, notes)
        self.assertIn("UIBackgroundModes=audio", notes)
        self.assertIn("Voice Callouts", notes)

    def test_background_audio_review_note_skips_when_info_plist_has_no_audio_mode(self):
        from scripts.asc.asc_submit_for_review import ensure_background_audio_review_note

        with tempfile.TemporaryDirectory() as tmp:
            plist_path = Path(tmp) / "Info.plist"
            with plist_path.open("wb") as f:
                plistlib.dump({"UIBackgroundModes": ["location"]}, f)

            client = RouterClient({})
            ensure_background_audio_review_note(client, "ver1", info_plist_path=str(plist_path))

        self.assertEqual(client.calls, [])

    def test_background_audio_review_note_skips_when_already_present(self):
        from scripts.asc.asc_submit_for_review import ensure_background_audio_review_note

        with tempfile.TemporaryDirectory() as tmp:
            plist_path = Path(tmp) / "Info.plist"
            with plist_path.open("wb") as f:
                plistlib.dump({"UIBackgroundModes": ["audio"]}, f)

            client = RouterClient(
                {
                    ("GET", "/appStoreVersions/ver1/appStoreReviewDetail"): {
                        "data": {
                            "id": "rd1",
                            "type": "appStoreReviewDetails",
                            "attributes": {
                                "notes": "UIBackgroundModes=audio is used for Pro Voice Callouts."
                            },
                        }
                    },
                }
            )

            ensure_background_audio_review_note(client, "ver1", info_plist_path=str(plist_path))

        self.assertEqual(len(client.calls), 1)


if __name__ == "__main__":
    unittest.main()
