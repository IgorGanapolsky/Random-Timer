import unittest
import io
import contextlib


class _FakeClient:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def request(self, method, path, *, params=None, payload=None):
        self.calls.append({"method": method, "path": path, "params": params, "payload": payload})
        return self._response


class AscSubmitForReviewVerifyAppInfoTests(unittest.TestCase):
    def test_verify_app_info_uses_conservative_query_params(self):
        from scripts.asc_submit_for_review import verify_app_info

        client = _FakeClient(
            {
                "data": [
                    {
                        "id": "info1",
                        "type": "appInfos",
                        "attributes": {},
                        "relationships": {
                            "primaryCategory": {"data": {"type": "appCategories", "id": "cat1"}},
                            "appInfoLocalizations": {"data": [{"type": "appInfoLocalizations", "id": "loc1"}]},
                        },
                    }
                ],
                "included": [
                    {
                        "id": "loc1",
                        "type": "appInfoLocalizations",
                        "attributes": {
                            "locale": "en-US",
                            "privacyPolicyUrl": "https://example.com/privacy",
                            "supportUrl": "https://example.com/support",
                        },
                    }
                ],
            }
        )

        verify_app_info(client, "6758355312", "en-US")

        try:
            call = next(iter(client.calls))
        except StopIteration:
            self.fail("Expected verify_app_info() to make exactly one ASC request")
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["path"], "/apps/6758355312/appInfos")
        params = call["params"] or {}
        # No schema-fragile filters/fields.
        self.assertNotIn("filter[platform]", params)
        self.assertNotIn("fields[appInfoLocalizations]", params)
        self.assertNotIn("fields[appInfos]", params)
        # Still request localizations (and category relationship) to validate required fields.
        self.assertEqual(params.get("include"), "appInfoLocalizations,primaryCategory")

    def test_verify_app_info_requires_support_and_privacy_urls(self):
        import scripts.asc_submit_for_review as asc
        verify_app_info = asc.verify_app_info

        client = _FakeClient(
            {
                "data": [
                    {
                        "id": "info1",
                        "type": "appInfos",
                        "attributes": {},
                        "relationships": {
                            "primaryCategory": {"data": {"type": "appCategories", "id": "cat1"}},
                            "appInfoLocalizations": {"data": [{"type": "appInfoLocalizations", "id": "loc1"}]},
                        },
                    }
                ],
                "included": [
                    {
                        "id": "loc1",
                        "type": "appInfoLocalizations",
                        "attributes": {
                            "locale": "en-US",
                            "privacyPolicyUrl": "",
                            "supportUrl": "",
                        },
                    }
                ],
            }
        )

        prev_dir = asc.FASTLANE_METADATA_DIR
        asc.FASTLANE_METADATA_DIR = "/__missing_fastlane_metadata__"
        try:
            with self.assertRaises(SystemExit):
                with contextlib.redirect_stdout(io.StringIO()):
                    with contextlib.redirect_stderr(io.StringIO()):
                        verify_app_info(client, "6758355312", "en-US")
        finally:
            asc.FASTLANE_METADATA_DIR = prev_dir

    def test_verify_app_info_autofills_support_url_when_missing(self):
        import os
        import io as _io
        import contextlib as _contextlib
        from scripts.asc_submit_for_review import verify_app_info

        class _RouterClient:
            def __init__(self):
                self.calls = []

            def request(self, method, path, *, params=None, payload=None):
                self.calls.append({"method": method, "path": path, "params": params, "payload": payload})
                if method == "GET" and path == "/apps/app1/appInfos":
                    return {
                        "data": [
                            {
                                "id": "info1",
                                "type": "appInfos",
                                "attributes": {},
                                "relationships": {
                                    "primaryCategory": {"data": {"type": "appCategories", "id": "cat1"}},
                                    "appInfoLocalizations": {"data": [{"type": "appInfoLocalizations", "id": "loc1"}]},
                                },
                            }
                        ],
                        "included": [
                            {
                                "id": "loc1",
                                "type": "appInfoLocalizations",
                                "attributes": {
                                    "locale": "en-US",
                                    "privacyPolicyUrl": "https://example.com/privacy",
                                    "supportURL": "",
                                },
                            }
                        ],
                    }
                if method == "PATCH" and path == "/appInfoLocalizations/loc1":
                    # Newer schema uses supportURL.
                    if "supportURL" not in (payload or {}).get("data", {}).get("attributes", {}):
                        raise RuntimeError("expected supportURL patch")
                    return {}
                if method == "GET" and path == "/appInfoLocalizations/loc1":
                    # Return the updated object
                    return {
                        "data": {
                            "id": "loc1",
                            "type": "appInfoLocalizations",
                            "attributes": {
                                "locale": "en-US",
                                "privacyPolicyUrl": "https://example.com/privacy",
                                "supportURL": os.environ.get("ASC_SUPPORT_URL"),
                            },
                        }
                    }
                raise RuntimeError(f"unhandled {method} {path}")

        prev = os.environ.get("ASC_SUPPORT_URL")
        os.environ["ASC_SUPPORT_URL"] = "https://example.com/support"
        try:
            client = _RouterClient()
            with _contextlib.redirect_stdout(_io.StringIO()):
                verify_app_info(client, "app1", "en-US")
            self.assertTrue(any(c["method"] == "PATCH" and c["path"] == "/appInfoLocalizations/loc1" for c in client.calls))
        finally:
            if prev is None:
                os.environ.pop("ASC_SUPPORT_URL", None)
            else:
                os.environ["ASC_SUPPORT_URL"] = prev


if __name__ == "__main__":
    unittest.main()
