import os
import tempfile
import unittest


class _FakeClient:
    def __init__(self, *, patch_error=None, refreshed_whats_new="Hello"):
        self.calls = []
        self._patch_error = patch_error
        self._refreshed_whats_new = refreshed_whats_new

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
            if self._patch_error is not None:
                raise self._patch_error
            return {}
        if method == "GET" and path == "/appStoreVersionLocalizations/loc1":
            return {
                "data": {
                    "id": "loc1",
                    "type": "appStoreVersionLocalizations",
                    "attributes": {"description": "desc", "keywords": "kw", "whatsNew": self._refreshed_whats_new},
                }
            }
        raise RuntimeError(f"unhandled {method} {path}")

_WHATS_NEW_STATE_ERROR = RuntimeError(
    "PATCH /appStoreVersionLocalizations/loc1 failed: HTTP 409 "
    "{'errors': [{'status': '409', 'code': 'STATE_ERROR', 'detail': \"Attribute 'whatsNew' cannot be edited at this time\"}]}"
)


class AscSubmitForReviewVersionLocalizationAutofillTests(unittest.TestCase):
    def test_get_version_localization_autofills_whats_new_from_fastlane(self):
        import scripts.asc.asc_submit_for_review as asc

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

    def test_get_version_localization_ignores_whats_new_state_error(self):
        import scripts.asc.asc_submit_for_review as asc

        client = _FakeClient(patch_error=_WHATS_NEW_STATE_ERROR, refreshed_whats_new="")

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

        # Should not raise, and should not require whatsNew to be present.
        self.assertEqual((loc.get("attributes") or {}).get("description"), "desc")
        self.assertEqual((loc.get("attributes") or {}).get("keywords"), "kw")
        self.assertEqual((loc.get("attributes") or {}).get("whatsNew"), "")


if __name__ == "__main__":
    unittest.main()
