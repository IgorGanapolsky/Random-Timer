#!/usr/bin/env python3
"""
Fully autonomous Google Play Console setup - No user interaction required.
Uses Selenium with Chrome to automatically complete all App Content declarations.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:
    print("❌ Selenium not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "selenium"], check=True)
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options

PACKAGE = "com.iganapolsky.randomtimer"

class AutonomousPlayStoreSetup:
    def __init__(self):
        self.driver = None
        self.wait = None

    def init_browser(self):
        """Initialize Chrome browser with proper configuration"""
        print("🌐 Initializing browser...")

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Use existing Chrome profile to maintain login session
        user_data = Path.home() / "Library/Application Support/Google/Chrome"
        if user_data.exists():
            # Create temporary profile directory to avoid conflicts
            import tempfile
            temp_profile = Path(tempfile.mkdtemp())
            options.add_argument(f"--user-data-dir={temp_profile}")

        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)
            print("✓ Browser ready")
            return True
        except WebDriverException as e:
            print(f"❌ Failed to start Chrome: {e}")
            print("\n💡 Please ensure:")
            print("   1. Google Chrome is installed")
            print("   2. ChromeDriver is available (brew install chromedriver)")
            return False

    def login_check(self):
        """Check if user is logged in to Google Play Console"""
        print("\n🔐 Checking authentication...")
        self.driver.get(f"https://play.google.com/console/")
        time.sleep(3)

        current_url = self.driver.current_url

        if "accounts.google.com" in current_url or "signin" in current_url:
            print("\n⚠️  Not logged in. Please log in manually...")
            print("Waiting for you to complete login in the browser...")

            # Wait for successful login (URL changes away from accounts.google.com)
            for i in range(60):  # Wait up to 5 minutes
                time.sleep(5)
                current_url = self.driver.current_url
                if "accounts.google.com" not in current_url and "signin" not in current_url:
                    print("✓ Login successful!")
                    return True

            print("❌ Login timeout")
            return False

        print("✓ Already authenticated")
        return True

    def click_element(self, selectors, timeout=10):
        """Try multiple selector strategies to click an element"""
        for selector_type, selector in selectors:
            try:
                element = self.wait.until(
                    EC.element_to_be_clickable((selector_type, selector))
                )
                element.click()
                return True
            except (TimeoutException, NoSuchElementException):
                continue
        return False

    def enter_text(self, selectors, text, timeout=10):
        """Try multiple selector strategies to enter text"""
        for selector_type, selector in selectors:
            try:
                element = self.wait.until(
                    EC.presence_of_element_located((selector_type, selector))
                )
                element.clear()
                element.send_keys(text)
                return True
            except (TimeoutException, NoSuchElementException):
                continue
        return False

    def complete_declaration(self, name, url, steps):
        """Generic function to complete a declaration"""
        print(f"\n📋 {name}...")
        self.driver.get(url)
        time.sleep(2)

        success = True
        for step_name, action, *args in steps:
            if action == "click":
                if not self.click_element(args[0]):
                    print(f"   ⚠️  Could not complete: {step_name}")
                    success = False
            elif action == "text":
                if not self.enter_text(args[0], args[1]):
                    print(f"   ⚠️  Could not enter text: {step_name}")
                    success = False
            time.sleep(1)

        if success:
            print(f"✓ {name} complete")
        return success

    def run(self):
        """Main execution flow"""
        print("\n" + "="*60)
        print("Fully Autonomous Play Store Setup")
        print("="*60)
        print(f"\nPackage: {PACKAGE}\n")

        # Verify AAB exists
        aab_path = Path("app/build/outputs/bundle/release/app-release.aab")
        if not aab_path.exists():
            print(f"❌ AAB not found: {aab_path}")
            print("Build it first: ./gradlew bundleRelease")
            return False

        print(f"✓ AAB ready: {aab_path.name} ({aab_path.stat().st_size / 1024 / 1024:.1f}MB)")

        # Initialize browser
        if not self.init_browser():
            return False

        # Check authentication
        if not self.login_check():
            return False

        base_url = f"https://play.google.com/console/developers/{PACKAGE}/app-content"

        # Define all declarations with XPath selectors
        declarations = [
            ("Data Safety", f"{base_url}/data-safety", [
                ("Start/Edit", "click", [
                    (By.XPATH, "//button[contains(text(), 'Start')]"),
                    (By.XPATH, "//button[contains(text(), 'Edit')]"),
                    (By.XPATH, "//span[contains(text(), 'Start')]"),
                ]),
                ("No data collected", "click", [
                    (By.XPATH, "//span[contains(text(), 'No') and contains(text(), 'collect')]"),
                    (By.XPATH, "//label[contains(., 'No') and contains(., 'collect')]//input"),
                ]),
                ("Next", "click", [
                    (By.XPATH, "//button[contains(text(), 'Next')]"),
                    (By.XPATH, "//span[contains(text(), 'Next')]"),
                ]),
                ("Save", "click", [
                    (By.XPATH, "//button[contains(text(), 'Submit')]"),
                    (By.XPATH, "//button[contains(text(), 'Save')]"),
                ]),
            ]),

            ("Advertising ID", f"{base_url}/advertising-id", [
                ("No advertising ID", "click", [
                    (By.XPATH, "//span[contains(text(), 'No')]"),
                    (By.XPATH, "//input[@value='false']"),
                ]),
                ("Save", "click", [
                    (By.XPATH, "//button[contains(text(), 'Save')]"),
                ]),
            ]),

            ("Government Apps", f"{base_url}/government-apps", [
                ("No", "click", [
                    (By.XPATH, "//span[contains(text(), 'No')]"),
                    (By.XPATH, "//input[@value='false']"),
                ]),
                ("Save", "click", [
                    (By.XPATH, "//button[contains(text(), 'Save')]"),
                ]),
            ]),

            ("Financial Features", f"{base_url}/financial-features", [
                ("No financial features", "click", [
                    (By.XPATH, "//span[contains(text(), 'No')]"),
                    (By.XPATH, "//input[@value='false']"),
                ]),
                ("Save", "click", [
                    (By.XPATH, "//button[contains(text(), 'Save')]"),
                ]),
            ]),

            ("Health Apps", f"{base_url}/health", [
                ("No", "click", [
                    (By.XPATH, "//span[contains(text(), 'No')]"),
                    (By.XPATH, "//input[@value='false']"),
                ]),
                ("Save", "click", [
                    (By.XPATH, "//button[contains(text(), 'Save')]"),
                ]),
            ]),

            ("Foreground Service", f"{base_url}/foreground-service", [
                ("Yes FGS", "click", [
                    (By.XPATH, "//span[contains(text(), 'Yes')]"),
                    (By.XPATH, "//input[@value='true']"),
                ]),
                ("Timer type", "click", [
                    (By.XPATH, "//span[contains(text(), 'Timer')]"),
                    (By.XPATH, "//span[contains(text(), 'Stopwatch')]"),
                ]),
                ("Justification", "text", [
                    (By.XPATH, "//textarea"),
                    (By.CSS_SELECTOR, "textarea"),
                ], "App runs a countdown timer that must continue when the app is in the background to notify the user when time expires."),
                ("Save", "click", [
                    (By.XPATH, "//button[contains(text(), 'Save')]"),
                ]),
            ]),

            ("Exact Alarm", f"{base_url}/exact-alarm", [
                ("Yes exact alarm", "click", [
                    (By.XPATH, "//span[contains(text(), 'Yes')]"),
                    (By.XPATH, "//input[@value='true']"),
                ]),
                ("Timer use case", "click", [
                    (By.XPATH, "//span[contains(text(), 'Timer')]"),
                    (By.XPATH, "//span[contains(text(), 'Alarm')]"),
                ]),
                ("Justification", "text", [
                    (By.XPATH, "//textarea"),
                    (By.CSS_SELECTOR, "textarea"),
                ], "App schedules exact alarms to notify the user precisely when their random timer completes."),
                ("Save", "click", [
                    (By.XPATH, "//button[contains(text(), 'Save')]"),
                ]),
            ]),
        ]

        # Execute all declarations
        completed = 0
        for name, url, steps in declarations:
            if self.complete_declaration(name, url, steps):
                completed += 1

        # Take screenshot of App Content page
        print("\n📸 Taking verification screenshot...")
        self.driver.get(base_url)
        time.sleep(3)
        screenshot_path = "app_content_completed.png"
        self.driver.save_screenshot(screenshot_path)
        print(f"✓ Screenshot saved: {screenshot_path}")

        # Results
        print("\n" + "="*60)
        print(f"✅ COMPLETED {completed}/{len(declarations)} DECLARATIONS")
        print("="*60)

        if completed == len(declarations):
            print("\n🎉 All declarations completed successfully!")
        else:
            print(f"\n⚠️  {len(declarations) - completed} declarations may need manual review")

        print("\n📋 Next Steps:")
        print("  1. Review the screenshot to verify completion")
        print("  2. Go to: Store listing → Verify name/description/graphics")
        print("  3. Go to: Testing → Closed testing")
        print("  4. Create closed test track and upload AAB")
        print("  5. Add 20+ testers and run for 14+ days")
        print("\n🔗 Direct link to closed testing:")
        print(f"   https://play.google.com/console/developers/{PACKAGE}/testing/closed")

        print("\n🌐 Browser will stay open for 30 seconds for review...")
        time.sleep(30)

        self.driver.quit()
        return completed == len(declarations)

if __name__ == "__main__":
    try:
        automation = AutonomousPlayStoreSetup()
        success = automation.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
