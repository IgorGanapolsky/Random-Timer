from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAPTURE_SCRIPT = ROOT / "scripts/capture_ios_store_screenshots.sh"


def test_ios_store_capture_script_uses_dynamic_runtime_and_device_resolution():
    source = CAPTURE_SCRIPT.read_text(encoding="utf-8")

    assert 'RUNTIME_ID="com.apple.CoreSimulator.SimRuntime.iOS-18-6"' not in source
    assert "resolve_latest_ios_runtime()" in source
    assert "resolve_device_type()" in source
    assert "xcrun simctl list runtimes -j" in source
    assert "xcrun simctl list devicetypes -j" in source
    assert '-destination "platform=iOS Simulator,id=$IPHONE_UDID"' in source
    assert 'run_capture "platform=iOS Simulator,id=$IPAD_UDID"' in source
