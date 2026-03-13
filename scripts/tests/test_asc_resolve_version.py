import unittest

from scripts.asc_client import AscClientError
from scripts.asc_resolve_version import (
    _bump_patch,
    _is_editable_state,
    _list_ios_versions,
    _parse_semver,
    resolve_version,
)


class _FakeClient:
    def __init__(self, versions):
        self.versions = list(versions)
        self.created = []
        self.create_error = None

    def get_all(self, path, params=None):
        if path.endswith("/appStoreVersions"):
            return list(self.versions)
        raise AssertionError(f"Unhandled get_all path: {path}")

    def request(self, method, path, payload=None, params=None):
        if method == "POST" and path == "/appStoreVersions":
            if self.create_error is not None:
                raise self.create_error
            data = payload["data"]
            created = {
                "id": f"new-{len(self.created) + 1}",
                "type": "appStoreVersions",
                "attributes": {
                    "versionString": data["attributes"]["versionString"],
                    "appStoreState": "PREPARE_FOR_SUBMISSION",
                },
            }
            self.created.append(created)
            self.versions.insert(0, created)
            return {"data": created}
        raise AssertionError(f"Unhandled request: {method} {path}")


def _version(version, state, vid=None):
    return {
        "id": vid or f"id-{version}",
        "type": "appStoreVersions",
        "attributes": {"versionString": version, "appStoreState": state},
    }


class AscResolveVersionUnitTests(unittest.TestCase):
    def test_semver_parse_and_bump(self):
        self.assertEqual(_parse_semver("1.2.3"), (1, 2, 3))
        self.assertEqual(_bump_patch("1.2.3"), "1.2.4")

    def test_editable_state_filter(self):
        self.assertTrue(_is_editable_state("PREPARE_FOR_SUBMISSION"))
        self.assertFalse(_is_editable_state("READY_FOR_SALE"))
        self.assertFalse(_is_editable_state("WAITING_FOR_REVIEW"))

    def test_reuses_preferred_when_editable(self):
        client = _FakeClient([_version("1.1.2", "PREPARE_FOR_SUBMISSION")])
        result = resolve_version(
            client=client,
            app_id="app1",
            preferred_version="1.1.2",
            create_if_needed=True,
            auto_next_patch=True,
        )
        self.assertEqual(result.selected_version, "1.1.2")
        self.assertFalse(result.created)
        self.assertEqual(result.reason, "preferred_version_editable")

    def test_creates_next_patch_when_preferred_is_live(self):
        client = _FakeClient([_version("1.1.1", "READY_FOR_SALE")])
        result = resolve_version(
            client=client,
            app_id="app1",
            preferred_version="1.1.1",
            create_if_needed=True,
            auto_next_patch=True,
        )
        self.assertEqual(result.selected_version, "1.1.2")
        self.assertTrue(result.created)
        self.assertIn("created_next_patch", result.reason)

    def test_reuses_existing_next_patch_when_editable(self):
        client = _FakeClient(
            [
                _version("1.1.1", "READY_FOR_SALE"),
                _version("1.1.2", "PREPARE_FOR_SUBMISSION"),
            ]
        )
        result = resolve_version(
            client=client,
            app_id="app1",
            preferred_version="1.1.1",
            create_if_needed=True,
            auto_next_patch=True,
        )
        self.assertEqual(result.selected_version, "1.1.2")
        self.assertFalse(result.created)
        self.assertIn("reused", result.reason)

    def test_reuses_highest_existing_editable_even_when_not_next_patch(self):
        client = _FakeClient(
            [
                _version("1.1.1", "READY_FOR_SALE"),
                _version("1.2.0", "PREPARE_FOR_SUBMISSION"),
            ]
        )
        result = resolve_version(
            client=client,
            app_id="app1",
            preferred_version="1.1.1",
            create_if_needed=True,
            auto_next_patch=True,
        )
        self.assertEqual(result.selected_version, "1.2.0")
        self.assertFalse(result.created)
        self.assertIn("reused_highest_editable", result.reason)

    def test_reuses_existing_editable_when_preferred_missing_and_auto_next_patch(self):
        client = _FakeClient([_version("1.2.0", "PREPARE_FOR_SUBMISSION")])
        result = resolve_version(
            client=client,
            app_id="app1",
            preferred_version="1.1.2",
            create_if_needed=True,
            auto_next_patch=True,
        )
        self.assertEqual(result.selected_version, "1.2.0")
        self.assertFalse(result.created)
        self.assertEqual(result.reason, "preferred_missing_reused_highest_editable")

    def test_creates_preferred_when_missing(self):
        client = _FakeClient([])
        result = resolve_version(
            client=client,
            app_id="app1",
            preferred_version="1.1.2",
            create_if_needed=True,
            auto_next_patch=False,
        )
        self.assertEqual(result.selected_version, "1.1.2")
        self.assertTrue(result.created)
        self.assertEqual(result.reason, "preferred_missing_created")

    def test_reuses_preferred_when_next_patch_create_blocked_by_409(self):
        client = _FakeClient([_version("1.1.1", "WAITING_FOR_REVIEW")])
        client.create_error = AscClientError("POST /appStoreVersions failed: HTTP 409 {'errors': []}")
        result = resolve_version(
            client=client,
            app_id="app1",
            preferred_version="1.1.1",
            create_if_needed=True,
            auto_next_patch=True,
        )
        self.assertEqual(result.selected_version, "1.1.1")
        self.assertFalse(result.created)
        self.assertEqual(result.selected_state, "WAITING_FOR_REVIEW")
        self.assertIn("create_blocked_409", result.reason)

    def test_reuses_highest_existing_when_preferred_missing_create_blocked_by_409(self):
        client = _FakeClient(
            [
                _version("1.2.6", "WAITING_FOR_REVIEW"),
                _version("1.2.5", "READY_FOR_SALE"),
            ]
        )
        client.create_error = AscClientError("POST /appStoreVersions failed: HTTP 409 {'errors': []}")
        result = resolve_version(
            client=client,
            app_id="app1",
            preferred_version="1.2.2",
            create_if_needed=True,
            auto_next_patch=True,
        )
        self.assertEqual(result.selected_version, "1.2.6")
        self.assertFalse(result.created)
        self.assertEqual(result.selected_state, "WAITING_FOR_REVIEW")
        self.assertEqual(result.reason, "preferred_missing_create_blocked_409_reused_highest_existing")

    def test_list_ios_versions_does_not_send_disallowed_sort_param(self):
        captured = {}

        class _CaptureClient:
            def get_all(self, path, params=None):
                captured["path"] = path
                captured["params"] = dict(params or {})
                return []

        _list_ios_versions(_CaptureClient(), "app123")
        self.assertEqual(captured["path"], "/apps/app123/appStoreVersions")
        self.assertNotIn("sort", captured["params"])
        self.assertEqual(captured["params"].get("filter[platform]"), "IOS")


if __name__ == "__main__":
    unittest.main()
