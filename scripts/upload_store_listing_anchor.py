#!/usr/bin/env python3
"""Upload App Store screenshots via Anchor Browser.

Uses ANCHOR_BROWSER_API_KEY and FASTLANE_* from .env.
"""
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCREENSHOTS = REPO / "native-ios" / "fastlane" / "screenshots" / "en-US"


def load_env():
    env_file = REPO / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and v and k not in os.environ:
                    os.environ[k] = v


def create_screenshots_zip() -> Path:
    zip_path = REPO / "scripts" / "_screenshots_anchor.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for device_dir in ["iPhone-6.9-inch", "iPad-Pro-13-inch"]:
            src = SCREENSHOTS / device_dir
            if not src.exists():
                continue
            for f in sorted(src.glob("*.png")):
                zf.write(f, f"{device_dir}/{f.name}")
    return zip_path


def main():
    load_env()
    api_key = os.environ.get("ANCHOR_BROWSER_API_KEY", "").strip()
    if not api_key:
        print("ANCHOR_BROWSER_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    zip_path = create_screenshots_zip()
    print(f"Created {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")

    # 1. Start session
    r = subprocess.run(
        [
            "curl", "-s", "-X", "POST", "https://api.anchorbrowser.io/v1/sessions",
            "-H", f"anchor-api-key: {api_key}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"session": {"initial_url": "https://appstoreconnect.apple.com"}}),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"Start session failed: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(r.stdout)
    session_id = data.get("data", {}).get("id")
    if not session_id:
        print(f"No session ID: {data}", file=sys.stderr)
        sys.exit(1)
    print(f"Session: {session_id}")

    # 2. Upload screenshots ZIP
    r2 = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            f"https://api.anchorbrowser.io/v1/sessions/{session_id}/agent/files",
            "-H", f"anchor-api-key: {api_key}",
            "-F", f"file=@{zip_path}",
        ],
        capture_output=True,
        text=True,
    )
    if r2.returncode != 0:
        print(f"Upload failed: {r2.stderr}", file=sys.stderr)
    else:
        print("Screenshots uploaded to session")

    # 3. Perform web task
    user = os.environ.get("FASTLANE_USER", "")
    password = os.environ.get("FASTLANE_PASSWORD", "")
    prompt = (
        "Sign in to App Store Connect using the APPLE_ID and APPLE_PASSWORD from secret values. "
        "Then go to My Apps > Random Tactical Timer > the current iOS version in Prepare for Submission. "
        "Open the App Store tab and the Screenshots section for en-US. "
        "Replace existing iPhone 6.9-inch and iPad Pro 13-inch screenshots with the PNG files from the uploaded agent resources "
        "(iPhone-6.9-inch/*.png and iPad-Pro-13-inch/*.png). Upload each file to the correct device class."
    )
    body = {
        "url": "https://appstoreconnect.apple.com",
        "prompt": prompt,
        "secret_values": {"APPLE_ID": user, "APPLE_PASSWORD": password},
        "human_intervention": True,
        "max_steps": 150,
    }
    r3 = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            f"https://api.anchorbrowser.io/v1/tools/perform-web-task?sessionId={session_id}",
            "-H", f"anchor-api-key: {api_key}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(body),
        ],
        capture_output=True,
        text=True,
    )
    print("Perform web task response:", r3.stdout[:500] if r3.stdout else r3.stderr)
    if r3.returncode != 0:
        sys.exit(1)
    result = json.loads(r3.stdout) if r3.stdout else {}
    print("Result:", json.dumps(result.get("data", result), indent=2)[:1000])


if __name__ == "__main__":
    main()
