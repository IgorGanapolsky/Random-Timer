from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICE_TEST = (
    ROOT
    / "native-android/app/src/androidTest/java/com/iganapolsky/randomtimer/service/TimerForegroundServiceResetTest.kt"
)


def test_after_class_does_not_force_stop_during_instrumentation():
    """@AfterClass force-stop kills the instrumentation process after tests pass (API 30 CI)."""
    source = SERVICE_TEST.read_text(encoding="utf-8")

    after_class_block = source.split("@AfterClass", 1)[1].split("fun ", 1)[0]
    assert "prepareColdStart" not in after_class_block
    assert "forceStopApp" not in after_class_block
