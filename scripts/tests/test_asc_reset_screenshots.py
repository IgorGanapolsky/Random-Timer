import json
import unittest
from types import SimpleNamespace
from unittest import mock

from scripts.asc import asc_reset_screenshots


class _FakeClient:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params or {}))
        if path == "/appStoreVersionLocalizations/loc1/appScreenshotSets":
            return {
                "data": [
                    {
                        "id": "set_iphone",
                        "attributes": {"screenshotDisplayType": "APP_IPHONE_67"},
                    },
                    {
                        "id": "set_ipad",
                        "attributes": {"screenshotDisplayType": "APP_IPAD_PRO_3GEN_129"},
                    },
                ]
            }
        if path == "/appScreenshotSets/set_iphone/appScreenshots":
            return {
                "data": [
                    {
                        "id": "shot_a",
                        "attributes": {
                            "fileName": "1_setup.png",
                            "assetDeliveryState": {"state": "COMPLETE"},
                        },
                    },
                    {
                        "id": "shot_b",
                        "attributes": {
                            "fileName": "2_active.png",
                            "assetDeliveryState": {"state": "COMPLETE"},
                        },
                    },
                ]
            }
        if path == "/appScreenshotSets/set_ipad/appScreenshots":
            return {
                "data": [
                    {
                        "id": "shot_c",
                        "attributes": {
                            "fileName": "5_ipad_setup.png",
                            "assetDeliveryState": {"state": "COMPLETE"},
                        },
                    }
                ]
            }
        return {"data": []}


class AscResetScreenshotsTests(unittest.TestCase):
    def test_list_screenshot_assets_reads_all_sets(self):
        client = _FakeClient()
        assets = asc_reset_screenshots.list_screenshot_assets(client, "loc1")
        self.assertEqual(len(assets), 3)
        self.assertEqual([a["screenshot_id"] for a in assets], ["shot_a", "shot_b", "shot_c"])
        self.assertEqual(assets[0]["display_type"], "APP_IPHONE_67")
        self.assertEqual(assets[-1]["display_type"], "APP_IPAD_PRO_3GEN_129")

    def test_reset_screenshots_dry_run_counts_only_assets_with_ids(self):
        fake_client = SimpleNamespace(
            get=lambda _path, params=None: {"data": [{"id": "loc1", "attributes": {"locale": "en-US"}}]}
        )
        fake_version = {
            "id": "v1",
            "relationships": {"appStoreVersionLocalizations": {"data": [{"id": "loc1"}]}},
        }
        fake_assets = [
            {"screenshot_id": "shot_a"},
            {"screenshot_id": ""},
            {"screenshot_id": "shot_b"},
        ]

        with (
            mock.patch("scripts.asc.asc_reset_screenshots.AscClient.from_env", return_value=fake_client),
            mock.patch("scripts.asc.asc_reset_screenshots._get_app_id", return_value="app1"),
            mock.patch("scripts.asc.asc_reset_screenshots._list_app_store_versions", return_value=({}, fake_version)),
            mock.patch("scripts.asc.asc_reset_screenshots._pick_localization", return_value={"id": "loc1"}),
            mock.patch("scripts.asc.asc_reset_screenshots.list_screenshot_assets", return_value=fake_assets),
            mock.patch("scripts.asc.asc_reset_screenshots._api_delete") as delete_mock,
        ):
            summary = asc_reset_screenshots.reset_screenshots(
                version="1.2.3",
                locale="en-US",
                bundle_id="com.example.app",
                dry_run=True,
            )

        self.assertEqual(summary["found_assets"], 3)
        self.assertEqual(summary["deleted_assets"], 2)
        self.assertTrue(summary["dry_run"])
        delete_mock.assert_not_called()

    def test_reset_screenshots_deletes_each_asset_when_not_dry_run(self):
        fake_client = SimpleNamespace(
            get=lambda _path, params=None: {"data": [{"id": "loc1", "attributes": {"locale": "en-US"}}]}
        )
        fake_version = {
            "id": "v1",
            "relationships": {"appStoreVersionLocalizations": {"data": [{"id": "loc1"}]}},
        }
        fake_assets = [
            {"screenshot_id": "shot_a"},
            {"screenshot_id": "shot_b"},
        ]

        with (
            mock.patch("scripts.asc.asc_reset_screenshots.AscClient.from_env", return_value=fake_client),
            mock.patch("scripts.asc.asc_reset_screenshots._get_app_id", return_value="app1"),
            mock.patch("scripts.asc.asc_reset_screenshots._list_app_store_versions", return_value=({}, fake_version)),
            mock.patch("scripts.asc.asc_reset_screenshots._pick_localization", return_value={"id": "loc1"}),
            mock.patch("scripts.asc.asc_reset_screenshots.list_screenshot_assets", return_value=fake_assets),
            mock.patch("scripts.asc.asc_reset_screenshots._api_delete", return_value=True) as delete_mock,
        ):
            summary = asc_reset_screenshots.reset_screenshots(
                version="1.2.3",
                locale="en-US",
                bundle_id="com.example.app",
                dry_run=False,
            )

        self.assertEqual(summary["deleted_assets"], 2)
        self.assertEqual(summary["skipped_locked_assets"], 0)
        self.assertEqual(delete_mock.call_count, 2)
        delete_mock.assert_any_call(fake_client, "/appScreenshots/shot_a")
        delete_mock.assert_any_call(fake_client, "/appScreenshots/shot_b")

    def test_api_delete_dies_on_http_error(self):
        response = SimpleNamespace(status_code=500, text="server exploded")
        fake_requests = SimpleNamespace(delete=lambda *_args, **_kwargs: response)
        fake_client = SimpleNamespace(token_value=lambda: "token")

        with mock.patch.dict("sys.modules", {"requests": fake_requests}):
            with self.assertRaises(SystemExit):
                asc_reset_screenshots._api_delete(fake_client, "/appScreenshots/shot_a")

    def test_api_delete_ignores_submit_lock_state_error(self):
        response_body = json.dumps(
            {
                "errors": [
                    {
                        "status": "409",
                        "code": "STATE_ERROR",
                        "detail": "Can't Delete Screenshot After Submit for review appScreenshots",
                    }
                ]
            }
        )
        response = SimpleNamespace(status_code=409, text=response_body)
        fake_requests = SimpleNamespace(delete=lambda *_args, **_kwargs: response)
        fake_client = SimpleNamespace(token_value=lambda: "token")

        with mock.patch.dict("sys.modules", {"requests": fake_requests}):
            deleted = asc_reset_screenshots._api_delete(fake_client, "/appScreenshots/shot_locked")

        self.assertFalse(deleted)

    def test_reset_screenshots_counts_locked_delete_skips(self):
        fake_client = SimpleNamespace(
            get=lambda _path, params=None: {"data": [{"id": "loc1", "attributes": {"locale": "en-US"}}]}
        )
        fake_version = {
            "id": "v1",
            "relationships": {"appStoreVersionLocalizations": {"data": [{"id": "loc1"}]}},
        }
        fake_assets = [{"screenshot_id": "shot_locked"}, {"screenshot_id": "shot_ok"}]

        with (
            mock.patch("scripts.asc.asc_reset_screenshots.AscClient.from_env", return_value=fake_client),
            mock.patch("scripts.asc.asc_reset_screenshots._get_app_id", return_value="app1"),
            mock.patch("scripts.asc.asc_reset_screenshots._list_app_store_versions", return_value=({}, fake_version)),
            mock.patch("scripts.asc.asc_reset_screenshots._pick_localization", return_value={"id": "loc1"}),
            mock.patch("scripts.asc.asc_reset_screenshots.list_screenshot_assets", return_value=fake_assets),
            mock.patch("scripts.asc.asc_reset_screenshots._api_delete", side_effect=[False, True]) as delete_mock,
        ):
            summary = asc_reset_screenshots.reset_screenshots(
                version="1.2.3",
                locale="en-US",
                bundle_id="com.example.app",
                dry_run=False,
            )

        self.assertEqual(delete_mock.call_count, 2)
        self.assertEqual(summary["deleted_assets"], 1)
        self.assertEqual(summary["skipped_locked_assets"], 1)


if __name__ == "__main__":
    unittest.main()
