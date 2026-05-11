import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "check_android_play_fgs_declaration.py"
SPEC = importlib.util.spec_from_file_location("check_android_play_fgs_declaration", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_manifest_requires_special_use_declaration_from_permission() -> None:
    assert mod.manifest_requires_special_use_declaration(ROOT / "native-android/app/src/main/AndroidManifest.xml")


def test_manifest_without_special_use_does_not_require_ack(tmp_path: Path) -> None:
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(
        """<manifest xmlns:android="http://schemas.android.com/apk/res/android">
            <application>
                <service android:name=".TimerService" android:foregroundServiceType="mediaPlayback" />
            </application>
        </manifest>""",
        encoding="utf-8",
    )

    assert not mod.manifest_requires_special_use_declaration(manifest)
