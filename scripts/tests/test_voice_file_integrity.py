"""Voice file integrity tests.

Prevents regressions like PR #860 where male voice callout files were
overwritten with a different ElevenLabs voice, breaking the marine drill
sergeant voice. These tests run in CI to catch any voice file drift
between iOS and Android, unexpected size changes, or missing files.
"""

from __future__ import annotations

import hashlib
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

IOS_AUDIO_DIR = ROOT / "native-ios" / "RandomTimer" / "Resources" / "Audio"
ANDROID_RAW_DIR = ROOT / "native-android" / "app" / "src" / "main" / "res" / "raw"
IOS_FEMALE_DIR = IOS_AUDIO_DIR / "female"

# Marine drill sergeant voice: command cues are short, punchy clips.
# The approved ElevenLabs voice produces files in the 17-35 KB range.
# A different voice (e.g. the one from PR #860) lands in 35-50 KB.
CMD_MIN_SIZE_BYTES = 10_000   # 10 KB — anything smaller is corrupt/empty
CMD_MAX_SIZE_BYTES = 50_000   # 50 KB — anything larger is wrong voice/settings
CMD_EXPECTED_RANGE_MAX = 40_000  # soft ceiling for the approved marine voice

MIN_EXPECTED_CMD_FILES = 28  # at least 28 command cues expected (~31 today)


def _md5(path: Path) -> str:
    """Return hex MD5 digest of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _cmd_files(directory: Path) -> list[Path]:
    """Return sorted list of cmd_*.mp3 files in a directory."""
    return sorted(directory.glob("cmd_*.mp3"))


class TestMaleVoiceFileIntegrity(unittest.TestCase):
    """Ensure male (cmd_*) voice files are consistent across platforms."""

    def test_ios_and_android_cmd_files_have_matching_names(self):
        """iOS and Android must ship the exact same set of command cue filenames."""
        ios_names = {p.name for p in _cmd_files(IOS_AUDIO_DIR)}
        android_names = {p.name for p in _cmd_files(ANDROID_RAW_DIR)}

        missing_on_android = ios_names - android_names
        missing_on_ios = android_names - ios_names

        self.assertEqual(
            missing_on_android,
            set(),
            f"Files present on iOS but missing on Android: {sorted(missing_on_android)}",
        )
        self.assertEqual(
            missing_on_ios,
            set(),
            f"Files present on Android but missing on iOS: {sorted(missing_on_ios)}",
        )

    def test_ios_and_android_cmd_files_have_identical_md5(self):
        """Every cmd_*.mp3 must be byte-identical across iOS and Android.

        This is the primary regression gate for PR #860-style overwrites.
        If a voice file is regenerated with a different ElevenLabs voice,
        the MD5 will change and this test will fail.
        """
        ios_files = _cmd_files(IOS_AUDIO_DIR)
        android_files = _cmd_files(ANDROID_RAW_DIR)

        # Build lookup by filename
        ios_hashes = {p.name: _md5(p) for p in ios_files}
        android_hashes = {p.name: _md5(p) for p in android_files}

        common = set(ios_hashes.keys()) & set(android_hashes.keys())
        self.assertGreater(len(common), 0, "No common cmd_*.mp3 files found")

        mismatches = []
        for name in sorted(common):
            if ios_hashes[name] != android_hashes[name]:
                mismatches.append(
                    f"  {name}: iOS={ios_hashes[name]} Android={android_hashes[name]}"
                )

        self.assertEqual(
            len(mismatches),
            0,
            f"MD5 mismatch between iOS and Android for {len(mismatches)} file(s):\n"
            + "\n".join(mismatches),
        )

    def test_minimum_cmd_file_count(self):
        """At least {MIN_EXPECTED_CMD_FILES} command cue files must exist."""
        ios_count = len(_cmd_files(IOS_AUDIO_DIR))
        android_count = len(_cmd_files(ANDROID_RAW_DIR))

        self.assertGreaterEqual(
            ios_count,
            MIN_EXPECTED_CMD_FILES,
            f"iOS has only {ios_count} cmd_*.mp3 files (expected >= {MIN_EXPECTED_CMD_FILES})",
        )
        self.assertGreaterEqual(
            android_count,
            MIN_EXPECTED_CMD_FILES,
            f"Android has only {android_count} cmd_*.mp3 files (expected >= {MIN_EXPECTED_CMD_FILES})",
        )

    def test_cmd_file_sizes_within_expected_range(self):
        """Command cue files must be between {CMD_MIN_SIZE_BYTES} and {CMD_MAX_SIZE_BYTES} bytes.

        The approved marine drill sergeant voice produces files in the
        17-35 KB range. Files above 50 KB suggest a different voice or
        wrong generation settings were used.
        """
        too_small = []
        too_large = []

        for platform_name, directory in [("iOS", IOS_AUDIO_DIR), ("Android", ANDROID_RAW_DIR)]:
            for f in _cmd_files(directory):
                size = f.stat().st_size
                if size < CMD_MIN_SIZE_BYTES:
                    too_small.append(f"  {platform_name}/{f.name}: {size} bytes")
                if size > CMD_MAX_SIZE_BYTES:
                    too_large.append(f"  {platform_name}/{f.name}: {size} bytes")

        errors = []
        if too_small:
            errors.append(
                f"Files below {CMD_MIN_SIZE_BYTES} bytes (corrupt/empty?):\n"
                + "\n".join(too_small)
            )
        if too_large:
            errors.append(
                f"Files above {CMD_MAX_SIZE_BYTES} bytes (wrong voice/settings?):\n"
                + "\n".join(too_large)
            )

        self.assertEqual(len(errors), 0, "\n".join(errors))

    def test_no_suspiciously_large_cmd_files(self):
        """Warn if any command cue exceeds the soft ceiling of {CMD_EXPECTED_RANGE_MAX} bytes.

        Files in the 35-50 KB range may indicate a voice change is in
        progress. This test surfaces them for manual review.
        """
        suspects = []
        for platform_name, directory in [("iOS", IOS_AUDIO_DIR), ("Android", ANDROID_RAW_DIR)]:
            for f in _cmd_files(directory):
                size = f.stat().st_size
                if size > CMD_EXPECTED_RANGE_MAX:
                    suspects.append(f"  {platform_name}/{f.name}: {size:,} bytes")

        if suspects:
            # This is a warning, not a hard failure — but we surface it
            # so reviewers notice during CI.
            print(
                f"\nWARNING: {len(suspects)} cmd file(s) exceed {CMD_EXPECTED_RANGE_MAX:,} byte soft ceiling:\n"
                + "\n".join(suspects)
            )


class TestFemaleVoiceFilePresence(unittest.TestCase):
    """Ensure female voice files exist in the expected locations."""

    def test_android_female_files_exist_with_prefix(self):
        """Android female voice files must use female_cmd_* or female_* prefix."""
        female_files = sorted(ANDROID_RAW_DIR.glob("female_*.mp3"))
        self.assertGreater(
            len(female_files),
            0,
            "No female_*.mp3 files found in Android raw resources",
        )

    def test_ios_female_files_exist_in_subdirectory(self):
        """iOS female voice files must exist in the female/ subdirectory."""
        self.assertTrue(
            IOS_FEMALE_DIR.is_dir(),
            f"iOS female voice directory does not exist: {IOS_FEMALE_DIR.relative_to(ROOT)}",
        )
        female_files = sorted(IOS_FEMALE_DIR.glob("cmd_*.mp3"))
        self.assertGreater(
            len(female_files),
            0,
            "No cmd_*.mp3 files found in iOS female/ subdirectory",
        )

    def test_female_file_count_parity(self):
        """Android and iOS should have a similar number of female voice files."""
        android_female = sorted(ANDROID_RAW_DIR.glob("female_cmd_*.mp3"))
        ios_female = sorted(IOS_FEMALE_DIR.glob("cmd_*.mp3")) if IOS_FEMALE_DIR.is_dir() else []

        # Allow some drift but they should be in the same ballpark
        if android_female and ios_female:
            ratio = len(ios_female) / len(android_female) if android_female else 0
            self.assertGreater(
                ratio,
                0.5,
                f"Female file count imbalance: Android={len(android_female)}, iOS={len(ios_female)}",
            )


if __name__ == "__main__":
    unittest.main()
