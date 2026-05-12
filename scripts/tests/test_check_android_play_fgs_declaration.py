from pathlib import Path

import pytest

from scripts.check_android_play_fgs_declaration import inspect_manifest
from scripts.check_android_play_fgs_declaration import main


def _write_manifest(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_inspect_manifest_detects_fgs_permissions_services_and_subtype(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "AndroidManifest.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />
  <application>
    <service android:name=".service.TimerForegroundService"
      android:foregroundServiceType="specialUse|mediaPlayback">
      <property
        android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
        android:value="timer" />
    </service>
  </application>
</manifest>
""",
    )

    result = inspect_manifest(manifest)

    assert result["requires_play_console_declaration"] is True
    assert result["foreground_service_permissions"] == [
        "android.permission.FOREGROUND_SERVICE",
        "android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK",
    ]
    assert result["foreground_service_services"] == [
        {
            "name": ".service.TimerForegroundService",
            "foreground_service_types": ["mediaPlayback", "specialUse"],
            "special_use_subtype": "timer",
        }
    ]


def test_main_fails_when_fgs_ack_is_required_but_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _write_manifest(
        tmp_path / "AndroidManifest.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
</manifest>
""",
    )
    monkeypatch.delenv("PLAY_FGS_DECLARATION_ACK", raising=False)

    status = main(["--manifest", str(manifest), "--require-ack-env", "PLAY_FGS_DECLARATION_ACK"])

    assert status == 1


def test_main_accepts_fgs_ack_when_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _write_manifest(
        tmp_path / "AndroidManifest.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
</manifest>
""",
    )
    monkeypatch.setenv("PLAY_FGS_DECLARATION_ACK", "2026-04-24")

    status = main(["--manifest", str(manifest), "--require-ack-env", "PLAY_FGS_DECLARATION_ACK"])

    assert status == 0
