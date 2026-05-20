from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock
from unittest.mock import patch

from scripts import asc_release_version as release


class AscReleaseVersionTests(unittest.TestCase):
    def test_already_ready_for_sale_emits_json_without_post(self):
        client = Mock()
        with patch.object(release, "ASCClient") as asc_client:
            asc_client.from_env.return_value = client
            with patch.object(release, "get_app", return_value={"id": "app1"}):
                with patch.object(
                    release,
                    "find_app_store_version_id",
                    return_value=("ver1", "READY_FOR_SALE"),
                ):
                    with patch.object(release, "release_version") as post_release:
                        with patch(
                            "sys.argv",
                            [
                                "asc_release_version.py",
                                "--version",
                                "1.3.35",
                                "--json",
                            ],
                        ):
                            buffer = io.StringIO()
                            with redirect_stdout(buffer):
                                code = release.main()
        self.assertEqual(code, 0)
        post_release.assert_not_called()
        payload = json.loads(buffer.getvalue().strip())
        self.assertEqual(payload["reason"], "already_ready_for_sale")

    def test_pending_developer_release_posts_release_request(self):
        client = Mock()
        with patch.object(release, "ASCClient") as asc_client:
            asc_client.from_env.return_value = client
            with patch.object(release, "get_app", return_value={"id": "app1"}):
                with patch.object(
                    release,
                    "find_app_store_version_id",
                    return_value=("ver1", "PENDING_DEVELOPER_RELEASE"),
                ):
                    with patch.object(
                        release,
                        "release_version",
                        return_value={"data": {"id": "req1"}},
                    ) as post_release:
                        with patch.object(
                            release, "get_version_state", return_value="READY_FOR_SALE"
                        ):
                            with patch(
                                "sys.argv",
                                [
                                    "asc_release_version.py",
                                    "--version",
                                    "1.3.35",
                                    "--json",
                                ],
                            ):
                                code = release.main()
        self.assertEqual(code, 0)
        post_release.assert_called_once()


if __name__ == "__main__":
    unittest.main()
