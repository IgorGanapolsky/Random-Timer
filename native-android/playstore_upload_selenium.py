from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
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
    if target_url not in driver.current_url:
        print(f"📍 Navigating to: {target_url}")
        driver.get(target_url)
        time.sleep(5)

    # Wait for page load
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    print(f"📄 Page loaded: {driver.title}")

    # Click "Create new release" button
    print("🔘 Looking for 'Create new release' button...")
    try:
        # Try different possible button texts
        create_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create new release')]"))
        )
    except:
        try:
            create_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create release')]"))
            )
        except:
            create_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Create') and contains(text(), 'release')]/ancestor::button"))
            )

    create_button.click()
    print("✅ Clicked 'Create new release'")
    time.sleep(4)

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
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save') and not(@disabled)]"))
    )
    print("✅ Upload complete!")

    # Add release notes
    print("📝 Adding release notes...")
    time.sleep(2)
    textareas = driver.find_elements(By.CSS_SELECTOR, "textarea")
    if textareas:
        textareas[0].send_keys("Initial release\\n\\n• Random timer with customizable range\\n• Dark glassmorphism UI\\n• Persistent settings\\n• Alarm sounds with volume control")

    time.sleep(2)

    # Click Save
    print("💾 Saving release...")
    save_button.click()
    time.sleep(5)

    # Click "Review release"
    print("👀 Clicking 'Review release'...")
    review_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Review')]"))
    )
    review_button.click()
    time.sleep(3)

    # Click "Start rollout to Internal testing"
    print("🚢 Starting rollout to internal testing...")
    rollout_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Start rollout') or contains(text(), 'Roll out')]"))
    )
    rollout_button.click()
    time.sleep(3)

    print("\\n🎉 SUCCESS! App published to Internal Testing track!")
    print("📱 Testers can now download the app from the Play Console")

except Exception as e:
    print(f"\\n❌ Error: {e}")
    if 'driver' in locals():
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
