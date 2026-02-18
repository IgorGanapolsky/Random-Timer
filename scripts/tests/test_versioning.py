import tempfile
import unittest
from pathlib import Path

from scripts.versioning import (
    SEMVER_RE,
    bump_semver,
    parse_android_build_gradle_kts,
    parse_ios_pbxproj,
    update_android_build_gradle_kts,
    update_ios_pbxproj,
)


class TestVersioning(unittest.TestCase):
    def test_semver_regex_accepts_basic(self):
        self.assertTrue(SEMVER_RE.match("1.2.3"))
        self.assertTrue(SEMVER_RE.match("0.0.1"))
        self.assertTrue(SEMVER_RE.match("1.2.3-beta.1"))
        self.assertTrue(SEMVER_RE.match("1.2.3+build.5"))

    def test_bump_semver(self):
        self.assertEqual(bump_semver("1.2.3", "patch"), "1.2.4")
        self.assertEqual(bump_semver("1.2.3", "minor"), "1.3.0")
        self.assertEqual(bump_semver("1.2.3", "major"), "2.0.0")

    def test_android_parse_and_update(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "build.gradle.kts"
            p.write_text(
                """
                android {
                  defaultConfig {
                    versionCode = 5
                    versionName = "1.1.1"
                  }
                }
                """.strip(),
                encoding="utf-8",
            )
            v, c = parse_android_build_gradle_kts(p)
            self.assertEqual(v, "1.1.1")
            self.assertEqual(c, 5)

            update_android_build_gradle_kts(p, version="1.2.0", version_code=6)
            v2, c2 = parse_android_build_gradle_kts(p)
            self.assertEqual(v2, "1.2.0")
            self.assertEqual(c2, 6)

    def test_ios_parse_and_update(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "project.pbxproj"
            p.write_text(
                """
                MARKETING_VERSION = 1.1.1;
                CURRENT_PROJECT_VERSION = 11;
                OTHER = x;
                MARKETING_VERSION = 1.1.1;
                CURRENT_PROJECT_VERSION = 11;
                """.strip(),
                encoding="utf-8",
            )
            v, b = parse_ios_pbxproj(p)
            self.assertEqual(v, "1.1.1")
            self.assertEqual(b, 11)

            update_ios_pbxproj(p, version="1.2.0", build_number=12)
            v2, b2 = parse_ios_pbxproj(p)
            self.assertEqual(v2, "1.2.0")
            self.assertEqual(b2, 12)


if __name__ == "__main__":
    unittest.main()

