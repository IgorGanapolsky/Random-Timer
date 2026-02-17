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

        self.assertEqual(len(client.calls), 1)
        call = client.calls[0]
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
                            "privacyPolicyUrl": "",
                            "supportUrl": "",
                        },
                    }
                ],
            }
        )

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                verify_app_info(client, "6758355312", "en-US")


if __name__ == "__main__":
    unittest.main()
