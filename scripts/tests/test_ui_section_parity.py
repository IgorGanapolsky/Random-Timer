"""UI section regression guard for TimerSetupScreen on both platforms.

Ensures required UI sections are never accidentally removed.
Run with: pytest scripts/tests/test_ui_section_parity.py
"""

import pathlib

REPO_ROOT = pathlib.Path(__file__).parents[2]

IOS_FILE = REPO_ROOT / "native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
ANDROID_FILE = REPO_ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"

IOS_REQUIRED_SECTIONS = [
    "Timer Range",
    "Alarm Sound",
    "Repeat Loop",
    "Start Timer",
    "Sound Arsenal",
]

ANDROID_REQUIRED_SECTIONS = [
    "Timer Range",
    "Alarm Sound",
    "Start Timer",
    "Sound Arsenal",
]


def _read(path: pathlib.Path) -> str:
    assert path.exists(), f"File not found: {path}"
    return path.read_text(encoding="utf-8")


def test_ios_required_sections_present():
    content = _read(IOS_FILE)
    missing = [s for s in IOS_REQUIRED_SECTIONS if s not in content]
    assert not missing, (
        f"TimerSetupScreen.swift is missing required UI sections: {missing}\n"
        f"File: {IOS_FILE}"
    )


def test_android_required_sections_present():
    content = _read(ANDROID_FILE)
    missing = [s for s in ANDROID_REQUIRED_SECTIONS if s not in content]
    assert not missing, (
        f"TimerSetupScreen.kt is missing required UI sections: {missing}\n"
        f"File: {ANDROID_FILE}"
    )
