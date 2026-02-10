#!/bin/bash
set -e

echo "🚀 Complete Play Store Upload Solution"
echo "======================================"

# 1. Navigate to the Random Timer app
echo "📱 Step 1: Opening Random Timer app in Play Console..."
osascript <<'APPLESCRIPT'
tell application "Google Chrome"
    activate
    set targetURL to "https://play.google.com/console/u/0/developers/8239620436488925047/app/4976249162120849673/tracks/4701359468888052130"

    -- Find the Play Console tab
    set found to false
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "play.google.com/console" then
                set URL of t to targetURL
                set active tab index of w to index of t
                set index of w to 1
                set found to true
                exit repeat
            end if
        end repeat
        if found then exit repeat
    end repeat

    -- If no existing tab, open in current tab
    if not found then
        set URL of active tab of front window to targetURL
    end if
end tell
APPLESCRIPT

echo "⏳ Waiting for page to load..."
sleep 5

# 2. Use Python + Selenium for the actual upload automation
echo "📦 Step 2: Installing Selenium if needed..."
python3 -m pip install --user --break-system-packages selenium webdriver-manager 2>&1 | grep -v "Requirement already satisfied" || true

# 3. Create Python automation script
echo "🤖 Step 3: Creating automation script..."
cat > /tmp/playstore_upload.py << 'PYTHON_SCRIPT'
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import sys

# Connect to existing Chrome instance
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

try:
    driver = webdriver.Chrome(options=chrome_options)
    print(f"✅ Connected to Chrome. Current URL: {driver.current_url}")

    # Navigate to Random Timer internal testing track
    target_url = "https://play.google.com/console/u/0/developers/8239620436488925047/app/4976249162120849673/tracks/4701359468888052130"
    if driver.current_url != target_url:
        print(f"📍 Navigating to: {target_url}")
        driver.get(target_url)
        time.sleep(3)

    # Wait for page load
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Click "Create new release" button
    print("🔘 Looking for 'Create new release' button...")
    create_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Create new release') or contains(., 'Create release')]"))
    )
    create_button.click()
    print("✅ Clicked 'Create new release'")
    time.sleep(3)

    # Upload AAB file
    print("📦 Uploading AAB file...")
    file_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
    )
    aab_path = "/Users/ganapolsky_i/workspace/git/igor/Random-Timer/native-android/app/build/outputs/bundle/release/app-release.aab"
    file_input.send_keys(aab_path)
    print("✅ AAB file selected, waiting for upload...")

    # Wait for upload to complete (Save button becomes enabled)
    print("⏳ Waiting for upload to complete (this can take 1-2 minutes)...")
    save_button = WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Save') and not(@disabled)]"))
    )
    print("✅ Upload complete!")

    # Add release notes
    print("📝 Adding release notes...")
    textarea = driver.find_element(By.CSS_SELECTOR, "textarea")
    textarea.send_keys("Initial release\n\n• Random timer with customizable range\n• Dark glassmorphism UI\n• Persistent settings\n• Alarm sounds with volume control")
    time.sleep(2)

    # Click Save
    print("💾 Saving release...")
    save_button.click()
    time.sleep(5)

    # Click "Review release"
    print("👀 Clicking 'Review release'...")
    review_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Review release')]"))
    )
    review_button.click()
    time.sleep(3)

    # Click "Start rollout to Internal testing"
    print("🚢 Starting rollout to internal testing...")
    rollout_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Start rollout')]"))
    )
    rollout_button.click()

    print("\n🎉 SUCCESS! App published to Internal Testing track!")
    print("📱 Testers can now download the app from the Play Console")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Current URL: {driver.current_url if 'driver' in locals() else 'N/A'}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo "🚀 Step 4: Running automation..."
python3 /tmp/playstore_upload.py

echo ""
echo "✅ Upload complete! Check the Play Console for confirmation."
