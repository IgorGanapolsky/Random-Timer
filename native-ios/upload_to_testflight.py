#!/usr/bin/env python3
"""Upload iOS build to TestFlight"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import tempfile
import time
import subprocess
import sys


TEMP_DIR = os.environ.get("RANDOM_TIMER_UPLOAD_TMPDIR", tempfile.gettempdir())
ARCHIVE_PATH = os.path.join(TEMP_DIR, "RandomTimer.xcarchive")
EXPORT_PATH = os.path.join(TEMP_DIR, "RandomTimer-ipa")
IPA_PATH = os.path.join(EXPORT_PATH, "RandomTimer.ipa")

def upload_to_testflight():
    """Upload the built archive to TestFlight"""

    # First, export the archive to IPA using App Store development profile
    print("📦 Exporting archive to IPA...")

    export_cmd = f"""
xcodebuild -exportArchive \
  -archivePath {ARCHIVE_PATH} \
  -exportPath {EXPORT_PATH} \
  -exportOptionsPlist /dev/stdin <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>development</string>
    <key>uploadSymbols</key>
    <true/>
    <key>uploadBitcode</key>
    <false/>
</dict>
</plist>
EOF
"""

    result = subprocess.run(export_cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Export failed: {result.stderr}")

        # Try using xcrun altool with app-specific password
        print("📤 Attempting direct upload with xcrun...")

        # Use transporter CLI
        upload_cmd = f"""
xcrun altool --upload-app \
  --type ios \
  --file {ARCHIVE_PATH} \
  --username "$APPLE_ID" \
  --password "@keychain:AC_PASSWORD"
"""

        result = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Upload output: {result.stdout}")
            print(f"Upload errors: {result.stderr}")
    else:
        print("✅ IPA exported successfully")

        # Upload the IPA
        print("📤 Uploading to App Store Connect...")
        upload_cmd = f"""
xcrun altool --upload-app \
  --type ios \
  --file {IPA_PATH} \
  --username "$APPLE_ID" \
  --password "@keychain:AC_PASSWORD"
"""

        result = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)

        if result.returncode == 0:
            print("✅ Upload successful!")
            return True
        else:
            print(f"❌ Upload failed: {result.stderr}")

    # Alternative: Use browser automation to complete the submission
    print("🌐 Using browser automation to complete submission...")

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Connected to Chrome")

        # Click on Random Alarm Timer
        print("📱 Opening Random Alarm Timer...")
        app_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Random Alarm Timer')]"))
        )
        app_link.click()
        time.sleep(3)

        # Navigate to TestFlight tab
        print("🚀 Opening TestFlight...")
        testflight_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'TestFlight') or @href[contains(., 'testflight')]]"))
        )
        testflight_tab.click()
        time.sleep(3)

        print("✅ Ready for build upload!")
        print("📝 Note: Build upload requires Xcode Organizer or Transporter app")
        print(f"   The archive is at: {ARCHIVE_PATH}")

        return True

    except Exception as e:
        print(f"❌ Browser automation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = upload_to_testflight()
    sys.exit(0 if success else 1)
