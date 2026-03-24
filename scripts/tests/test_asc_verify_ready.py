import unittest
from unittest import mock


class _FakeAscClient:
    def __init__(self, app_screenshots_by_set, *, include_build=True):
        self.app_screenshots_by_set = app_screenshots_by_set
        self.include_build = include_build
        self.calls = []

    def get(self, path, params=None):
        self.calls.append({"path": path, "params": params or {}})

        if path == "/apps":
            return {"data": [{"id": "app1", "type": "apps"}]}

        if path == "/apps/app1/appStoreVersions":
            build_rel = {"data": {"id": "b1", "type": "builds"}} if self.include_build else {"data": None}
            included = [
                {
                    "id": "loc1",
                    "type": "appStoreVersionLocalizations",
                    "attributes": {
                        "locale": "en-US",
                        "description": "desc",
                        "keywords": "a,b",
                        "supportUrl": "https://example.com/support",
                    },
                },
            ]
            if self.include_build:
                included.insert(
                    0,
                    {
                        "id": "b1",
                        "type": "builds",
                        "attributes": {"processingState": "VALID", "version": "19"},
                    },
                )
            return {
                "data": [
                    {
                        "id": "v1",
                        "type": "appStoreVersions",
                        "attributes": {"versionString": "1.1.1", "appStoreState": "READY_FOR_SALE"},
                        "relationships": {
                            "build": build_rel,
                            "appStoreVersionLocalizations": {
                                "data": [{"id": "loc1", "type": "appStoreVersionLocalizations"}]
                            },
                        },
                    }
                ],
                "included": included,
            }

        if path == "/apps/app1/appInfos":
            return {
                "data": [{"id": "info1", "type": "appInfos", "attributes": {"appStoreState": "READY_FOR_SALE"}}],
                "included": [
                    {
                        "id": "infoLoc1",
                        "type": "appInfoLocalizations",
                        "attributes": {"locale": "en-US", "privacyPolicyUrl": "https://example.com/privacy"},
                    }
                ],
            }

        if path == "/appStoreVersions/v1/appStoreReviewDetail":
            return {
                "data": {
                    "id": "rd1",
                    "type": "appStoreReviewDetails",
                    "attributes": {
                        "contactFirstName": "Igor",
                        "contactLastName": "G",
                        "contactEmail": "igor@example.com",
                        "contactPhone": "+10000000000",
                    },
                }
            }

        if path == "/apps/app1/appPriceSchedules":
            return {"data": [{"id": "price1", "type": "appPriceSchedules"}]}

        if path == "/appInfos/info1/ageRatingDeclaration":
            return {"data": {"id": "age1", "type": "appStoreAgeRatingDeclarations"}}

        if path == "/appStoreVersionLocalizations/loc1/appScreenshotSets":
            return {
                "data": [
                    {
                        "id": "set_iphone",
                        "type": "appScreenshotSets",
                        "attributes": {"screenshotDisplayType": "APP_IPHONE_67"},
                    },
                    {
                        "id": "set_ipad",
                        "type": "appScreenshotSets",
                        "attributes": {"screenshotDisplayType": "APP_IPAD_PRO_3GEN_129"},
                    },
                ]
            }

        if path.startswith("/appScreenshotSets/") and path.endswith("/appScreenshots"):
            set_id = path.split("/")[2]
            return {"data": self.app_screenshots_by_set.get(set_id, [])}

        raise AssertionError(f"Unhandled path: {path}")


class AscVerifyReadyScreenshotStateTests(unittest.TestCase):
    @staticmethod
    def _shots(states, prefix):
        return [
            {
                "id": f"{prefix}{i}",
                "type": "appScreenshots",
                "attributes": {"fileName": f"{prefix}{i}.png", "assetDeliveryState": {"state": state}},
            }
            for i, state in enumerate(states, start=1)
        ]

    def _run_verify(self, iphone_states, ipad_states, *, require_build=True, include_build=True):
        from scripts import asc_verify_ready

        fake = _FakeAscClient(
            app_screenshots_by_set={
                "set_iphone": self._shots(iphone_states, "ph"),
                "set_ipad": self._shots(ipad_states, "pd"),
            },
            include_build=include_build,
        )
        with mock.patch("scripts.asc_verify_ready.AscClient", return_value=fake):
            return asc_verify_ready.verify_ready(
                bundle_id="com.igorganapolsky.randomtimer",
                version="1.1.1",
                locale="en-US",
                min_iphone=3,
                min_ipad=3,
                require_build=require_build,
            )

    def test_verify_ready_fails_when_screenshots_are_not_complete(self):
        passed, report = self._run_verify(
            iphone_states=["AWAITING_UPLOAD", "AWAITING_UPLOAD", "AWAITING_UPLOAD"],
            ipad_states=["COMPLETE", "COMPLETE", "COMPLETE"],
        )
        self.assertFalse(passed)
        self.assertEqual(report["screenshot_counts"]["APP_IPHONE_67"], 0)
        self.assertEqual(report["screenshot_total_counts"]["APP_IPHONE_67"], 3)
        self.assertEqual(report["screenshot_asset_states"]["APP_IPHONE_67"]["AWAITING_UPLOAD"], 3)

    def test_verify_ready_passes_when_required_complete_counts_exist(self):
        passed, report = self._run_verify(
            iphone_states=["COMPLETE", "COMPLETE", "COMPLETE"],
            ipad_states=["COMPLETE", "COMPLETE", "COMPLETE"],
        )
        self.assertTrue(passed)
        self.assertEqual(report["screenshot_counts"]["APP_IPHONE_67"], 3)
        self.assertEqual(report["screenshot_counts"]["APP_IPAD_PRO_3GEN_129"], 3)

    def test_verify_ready_can_skip_build_requirement(self):
        passed, report = self._run_verify(
            iphone_states=["COMPLETE", "COMPLETE", "COMPLETE"],
            ipad_states=["COMPLETE", "COMPLETE", "COMPLETE"],
            require_build=False,
            include_build=False,
        )
        self.assertTrue(passed)
        build_check = next(c for c in report["checks"] if c["name"] == "Build Attached")
        self.assertTrue(build_check["passed"])
        self.assertTrue(build_check["evidence"]["skipped"])


if __name__ == "__main__":
    unittest.main()
