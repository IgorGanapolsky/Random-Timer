import os
import tempfile
import unittest


class _FakeClient:
    def __init__(self):
        self.calls = []

    def get_all(self, path, *, params=None):
        self.calls.append({"method": "GET_ALL", "path": path, "params": params})
        return [
            {
                "id": "loc1",
                "type": "appStoreVersionLocalizations",
                "attributes": {"description": "desc", "keywords": "kw", "whatsNew": ""},
            }
        ]

    def request(self, method, path, *, params=None, payload=None):
        self.calls.append({"method": method, "path": path, "params": params, "payload": payload})
        if method == "PATCH" and path == "/appStoreVersionLocalizations/loc1":
            return {}
        if method == "GET" and path == "/appStoreVersionLocalizations/loc1":
            return {
                "data": {
                    "id": "loc1",
                    "type": "appStoreVersionLocalizations",
                    "attributes": {"description": "desc", "keywords": "kw", "whatsNew": "Hello"},
                }
            }
        raise RuntimeError(f"unhandled {method} {path}")


class AscSubmitForReviewVersionLocalizationAutofillTests(unittest.TestCase):
    def test_get_version_localization_autofills_whats_new_from_fastlane(self):
        import scripts.asc_submit_for_review as asc

        client = _FakeClient()

        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "en-US"), exist_ok=True)
            with open(os.path.join(td, "en-US", "release_notes.txt"), "w", encoding="utf-8") as f:
                f.write("Hello")

            prev = asc.FASTLANE_METADATA_DIR
            asc.FASTLANE_METADATA_DIR = td
            try:
                loc = asc.get_version_localization(client, "ver1", "en-US")
            finally:
                asc.FASTLANE_METADATA_DIR = prev

        patch = next((c for c in client.calls if c["method"] == "PATCH"), None)
        self.assertIsNotNone(patch)
        attrs = (((patch or {}).get("payload") or {}).get("data") or {}).get("attributes") or {}
        self.assertEqual(attrs, {"whatsNew": "Hello"})
        self.assertEqual((loc.get("attributes") or {}).get("whatsNew"), "Hello")


if __name__ == "__main__":
    unittest.main()

