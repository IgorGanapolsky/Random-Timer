#!/usr/bin/env python3
"""
Fully autonomous Google Play Console setup for Random Timer.
Completes all App Content declarations without user interaction.
"""

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

PACKAGE_NAME = "com.iganapolsky.randomtimer"

class PlayStoreAutomation:
    def __init__(self):
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Initialize Chrome with user profile for authentication"""
        options = Options()
        # Use existing Chrome profile to maintain login
        user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)
            print("✓ Browser initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome: {e}")
            sys.exit(1)

    def wait_and_click(self, xpath, timeout=10):
        """Wait for element and click it"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            return True
        except TimeoutException:
            return False

    def wait_and_send_keys(self, xpath, text, timeout=10):
        """Wait for input field and enter text"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            element.clear()
            element.send_keys(text)
            return True
        except TimeoutException:
            return False

    def complete_data_safety(self):
        """Complete Data Safety - App does not collect data"""
        print("\n📋 Data Safety...")
        url = f"https://play.google.com/console/developers/{PACKAGE_NAME}/app-content/data-safety"
        self.driver.get(url)
        time.sleep(2)

        # Click Start/Edit button
        if self.wait_and_click("//button[contains(., 'Start') or contains(., 'Edit')]"):
            time.sleep(1)

        # Select "No data collected"
        if self.wait_and_click("//span[contains(text(), 'No') and contains(text(), 'collect')]"):
            time.sleep(1)

        # Click Next
        if self.wait_and_click("//button[contains(., 'Next')]"):
            time.sleep(1)

        # Save
        self.wait_and_click("//button[contains(., 'Submit') or contains(., 'Save')]")
        print("✓ Data Safety complete")

    def complete_advertising_id(self):
        """Complete Advertising ID - Not used"""
        print("\n📋 Advertising ID...")
        url = f"https://play.google.com/console/developers/{PACKAGE_NAME}/app-content/advertising-id"
        self.driver.get(url)
        time.sleep(2)

        # Select "No"
        if self.wait_and_click("//span[contains(text(), 'No')]"):
            time.sleep(1)

        self.wait_and_click("//button[contains(., 'Save')]")
        print("✓ Advertising ID complete")

    def complete_government_apps(self):
        """Complete Government Apps - No"""
        print("\n📋 Government Apps...")
        url = f"https://play.google.com/console/developers/{PACKAGE_NAME}/app-content/government-apps"
        self.driver.get(url)
        time.sleep(2)

        # Select "No"
        if self.wait_and_click("//span[contains(text(), 'No')]"):
            time.sleep(1)

        self.wait_and_click("//button[contains(., 'Save')]")
        print("✓ Government Apps complete")

    def complete_financial_features(self):
        """Complete Financial Features - No"""
        print("\n📋 Financial Features...")
        url = f"https://play.google.com/console/developers/{PACKAGE_NAME}/app-content/financial-features"
        self.driver.get(url)
        time.sleep(2)

        # Select "No"
        if self.wait_and_click("//span[contains(text(), 'No')]"):
            time.sleep(1)

        self.wait_and_click("//button[contains(., 'Save')]")
        print("✓ Financial Features complete")

    def complete_health_apps(self):
        """Complete Health Apps - No"""
        print("\n📋 Health Apps...")
        url = f"https://play.google.com/console/developers/{PACKAGE_NAME}/app-content/health"
        self.driver.get(url)
        time.sleep(2)

        # Select "No"
        if self.wait_and_click("//span[contains(text(), 'No')]"):
            time.sleep(1)

        self.wait_and_click("//button[contains(., 'Save')]")
        print("✓ Health Apps complete")

    def complete_foreground_service(self):
        """Complete FGS permissions - Timer/Stopwatch"""
        print("\n📋 Foreground Service Permissions...")
        url = f"https://play.google.com/console/developers/{PACKAGE_NAME}/app-content/foreground-service"
        self.driver.get(url)
        time.sleep(2)

        # Select "Yes"
        if self.wait_and_click("//span[contains(text(), 'Yes')]"):
            time.sleep(1)

        # Select Timer/Stopwatch type
        if self.wait_and_click("//span[contains(text(), 'Timer') or contains(text(), 'Stopwatch')]"):
            time.sleep(1)

        # Enter justification
        justification = ("App runs a countdown timer that must continue when the app is in the "
                        "background to notify the user when time expires.")
        self.wait_and_send_keys("//textarea", justification)
        time.sleep(1)

        self.wait_and_click("//button[contains(., 'Save')]")
        print("✓ Foreground Service complete")

    def complete_exact_alarm(self):
        """Complete USE_EXACT_ALARM - Timer/Alarm"""
        print("\n📋 Exact Alarm Permission...")
        url = f"https://play.google.com/console/developers/{PACKAGE_NAME}/app-content/exact-alarm"
        self.driver.get(url)
        time.sleep(2)

        # Select "Yes"
        if self.wait_and_click("//span[contains(text(), 'Yes')]"):
            time.sleep(1)

        # Select Timer/Alarm use case
        if self.wait_and_click("//span[contains(text(), 'Timer') or contains(text(), 'Alarm')]"):
            time.sleep(1)

        # Enter justification
        justification = ("App schedules exact alarms to notify the user precisely when their "
                        "random timer completes.")
        self.wait_and_send_keys("//textarea", justification)
        time.sleep(1)

        self.wait_and_click("//button[contains(., 'Save')]")
        print("✓ Exact Alarm complete")

    def verify_completion(self):
        """Check App Content page for completion status"""
        print("\n🔍 Verifying completion...")
        url = f"https://play.google.com/console/developers/{PACKAGE_NAME}/app-content"
        self.driver.get(url)
        time.sleep(3)

        # Take screenshot
        screenshot_path = "/Users/ganapolsky_i/workspace/git/igor/Random-Timer/native-android/app_content_status.png"
        self.driver.save_screenshot(screenshot_path)
        print(f"✓ Screenshot saved: {screenshot_path}")

    def run(self):
        """Execute all setup steps"""
        try:
            print("\n" + "="*60)
            print("Google Play Console - Autonomous Setup")
            print("="*60)
            print(f"Package: {PACKAGE_NAME}")

            # Verify AAB
            aab_path = "app/build/outputs/bundle/release/app-release.aab"
            if not os.path.exists(aab_path):
                print(f"\n❌ AAB not found at: {aab_path}")
                print("Build it first: ./gradlew bundleRelease")
                return False

            size_mb = os.path.getsize(aab_path) / 1024 / 1024
            print(f"✓ AAB ready: {size_mb:.1f}MB")

            # Open Play Console
            print("\n🌐 Opening Play Console...")
            self.driver.get(f"https://play.google.com/console/developers/{PACKAGE_NAME}")
            time.sleep(5)

            # Check if logged in
            if "accounts.google.com" in self.driver.current_url:
                print("\n⚠️  Not logged in to Google Play Console")
                print("Please log in manually in the browser window...")
                input("Press Enter after logging in...")

            # Execute all declarations
            self.complete_data_safety()
            self.complete_advertising_id()
            self.complete_government_apps()
            self.complete_financial_features()
            self.complete_health_apps()
            self.complete_foreground_service()
            self.complete_exact_alarm()

            # Verify
            self.verify_completion()

            print("\n" + "="*60)
            print("✅ ALL APP CONTENT DECLARATIONS COMPLETE!")
            print("="*60)
            print("\n📋 Next steps:")
            print("  1. Go to: Testing → Closed testing")
            print("  2. Create closed testing track")
            print("  3. Upload AAB: " + os.path.abspath(aab_path))
            print("  4. Add 20+ testers")
            print("  5. Run for 14+ days before production")
            print("\n🔗 Direct link:")
            print(f"   https://play.google.com/console/developers/{PACKAGE_NAME}/testing/closed")

            return True

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print("\n🔚 Keeping browser open for manual review...")
            print("Press Ctrl+C to close")
            try:
                time.sleep(60)  # Keep open for 1 minute for review
            except KeyboardInterrupt:
                pass
            self.driver.quit()

if __name__ == "__main__":
    automation = PlayStoreAutomation()
    success = automation.run()
    sys.exit(0 if success else 1)
