import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

from scripts.release_context import (
    ContextError,
    _extract_build_processing_state,
    _safe_output_path,
    build_summary,
    collect_local_context,
    collect_remote_context,
    detect_ios_version,
)


PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _chunk(tag: bytes, data: bytes) -> bytes:
    return len(data).to_bytes(4, "big") + tag + data + (zlib.crc32(tag + data) & 0xFFFFFFFF).to_bytes(4, "big")


def _write_png(path: Path, width: int, height: int, rgb: tuple[int, int, int] = (0, 0, 0)) -> None:
    row = bytes([0]) + bytes(rgb) * width  # filter byte + RGB pixels
    raw = row * height
    ihdr = width.to_bytes(4, "big") + height.to_bytes(4, "big") + bytes([8, 2, 0, 0, 0])
    png = PNG_SIG + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


class ReleaseContextLocalTests(unittest.TestCase):
    def test_detect_ios_version_reads_shared_source_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ios_project = repo / "native-ios" / "RandomTimer.xcodeproj"
            android_app = repo / "native-android" / "app"
            ios_project.mkdir(parents=True)
            android_app.mkdir(parents=True)
            (ios_project / "project.pbxproj").write_text(
                "MARKETING_VERSION = 1.3.7;\nCURRENT_PROJECT_VERSION = 151;\n",
                encoding="utf-8",
            )
            (android_app / "build.gradle.kts").write_text(
                'android {\n  defaultConfig {\n    versionCode = ciVersionCode ?: 1773900000\n    versionName = "1.3.7"\n  }\n}\n',
                encoding="utf-8",
            )

            self.assertEqual(detect_ios_version(repo), "1.3.7")

    def test_collect_local_context_marks_ready_when_assets_are_complete(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots = repo / "native-ios" / "fastlane" / "screenshots" / "en-US"
            meta = repo / "native-ios" / "fastlane" / "metadata" / "en-US"
            shots.mkdir(parents=True)
            meta.mkdir(parents=True)

            # iPhone large
            _write_png(shots / "1_setup.png", 1320, 2868, (10, 20, 30))
            _write_png(shots / "2_active.png", 1320, 2868, (11, 20, 30))
            _write_png(shots / "3_alarm.png", 1320, 2868, (12, 20, 30))
            # iPad large + required file names
            _write_png(shots / "5_ipad_setup.png", 2064, 2752, (20, 20, 30))
            _write_png(shots / "6_ipad_running.png", 2064, 2752, (21, 20, 30))
            _write_png(shots / "7_ipad_stopped.png", 2064, 2752, (22, 20, 30))

            (meta / "description.txt").write_text("desc", encoding="utf-8")
            (meta / "keywords.txt").write_text("kw1,kw2", encoding="utf-8")
            (meta / "support_url.txt").write_text("https://example.com/support", encoding="utf-8")
            (meta / "privacy_url.txt").write_text("https://example.com/privacy", encoding="utf-8")

            local = collect_local_context(repo, "en-US")

            self.assertTrue(local["local_ready"])
            self.assertEqual(local["screenshots"]["iphone_large_count"], 3)
            self.assertEqual(local["screenshots"]["ipad_large_count"], 3)
            self.assertEqual(local["screenshots"]["missing_required_ipad_files"], [])
            self.assertEqual(local["metadata"]["missing_required_fields"], [])

    def test_collect_local_context_reports_missing_requirements(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            shots = repo / "native-ios" / "fastlane" / "screenshots" / "en-US"
            meta = repo / "native-ios" / "fastlane" / "metadata" / "en-US"
            shots.mkdir(parents=True)
            meta.mkdir(parents=True)

            _write_png(shots / "1_setup.png", 1320, 2868)
            _write_png(shots / "2_active.png", 1320, 2868)
            _write_png(shots / "5_ipad_setup.png", 2064, 2752)

            (meta / "description.txt").write_text("", encoding="utf-8")
            (meta / "keywords.txt").write_text("k", encoding="utf-8")

            local = collect_local_context(repo, "en-US")

            self.assertFalse(local["local_ready"])
            self.assertIn("support_url", local["metadata"]["missing_required_fields"])
            self.assertIn("privacy_url", local["metadata"]["missing_required_fields"])
            self.assertIn("7_ipad_stopped.png", local["screenshots"]["missing_required_ipad_files"])


class ReleaseContextSummaryTests(unittest.TestCase):
    def test_build_summary_includes_sla_and_remote_blockers(self):
        local = {"local_ready": True}
        remote = {
            "status": "partial_failure",
            "build_processing_state": "PROCESSING",
            "reviews_ops": {"payload": {"slaBreachCount": 2}},
        }

        summary = build_summary(local, remote)

        self.assertFalse(summary["remote_ready"])
        self.assertEqual(summary["build_processing_state"], "PROCESSING")
        self.assertEqual(summary["sla_breach_count"], 2)
        self.assertIn("remote_checks_failed", summary["blockers"])
        self.assertIn("review_sla_breaches_present", summary["blockers"])

    def test_extract_build_processing_state_from_check_evidence(self):
        payload = {
            "checks": [
                {
                    "name": "Build Attached",
                    "details": "build=11 processingState=VALID",
                    "evidence": {"buildNumber": "11", "processingState": "VALID"},
                }
            ]
        }
        self.assertEqual(_extract_build_processing_state(payload), "VALID")


class ReleaseContextRemoteTests(unittest.TestCase):
    def test_collect_remote_context_skips_when_remote_is_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            ctx = collect_remote_context(
                repo_root=Path(td),
                version="1.2.3",
                locale="en-US",
                include_remote=False,
                review_limit=200,
                sla_hours=24,
                env={},
            )
        self.assertEqual(ctx["status"], "skipped_no_remote")

    def test_collect_remote_context_skips_when_credentials_missing(self):
        with tempfile.TemporaryDirectory() as td:
            ctx = collect_remote_context(
                repo_root=Path(td),
                version="1.2.3",
                locale="en-US",
                include_remote=True,
                review_limit=200,
                sla_hours=24,
                env={},
            )
        self.assertEqual(ctx["status"], "skipped_missing_credentials")

    def test_collect_remote_context_reports_partial_failure(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            with (
                mock.patch("scripts.release_context.has_asc_credentials", return_value=True),
                mock.patch(
                    "scripts.release_context._run_json_command",
                    side_effect=[
                        {
                            "status": "success",
                            "payload": {"checks": [{"evidence": {"processingState": "VALID"}}]},
                            "exit_code": 0,
                            "command": [],
                            "stdout_tail": "",
                            "stderr_tail": "",
                        },
                        {
                            "status": "failed",
                            "payload": None,
                            "exit_code": 1,
                            "command": [],
                            "stdout_tail": "",
                            "stderr_tail": "boom",
                        },
                    ],
                ),
            ):
                ctx = collect_remote_context(
                    repo_root=repo_root,
                    version="1.2.3",
                    locale="en-US",
                    include_remote=True,
                    review_limit=200,
                    sla_hours=24,
                    env={},
                )

        self.assertEqual(ctx["status"], "partial_failure")
        self.assertEqual(ctx["build_processing_state"], "VALID")
        self.assertEqual(ctx["asc_readiness"]["status"], "success")
        self.assertEqual(ctx["reviews_ops"]["status"], "failed")

    def test_safe_output_path_rejects_paths_outside_allowed_roots(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            with self.assertRaises(ContextError):
                _safe_output_path(str(Path.home() / "release-context-outside.json"), repo_root)


if __name__ == "__main__":
    unittest.main()
