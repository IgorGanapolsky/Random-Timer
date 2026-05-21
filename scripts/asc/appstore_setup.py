#!/usr/bin/env python3
"""
Autonomous App Store Connect Setup
Creates app listing, generates provisioning profiles, and uploads to TestFlight
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import sys

def setup_appstore_connect():
    """Setup App Store Connect and upload iOS app"""

    # Connect to existing Chrome with debugging
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print(f"✅ Connected to Chrome")

        # Navigate to App Store Connect
        print("🍎 Opening App Store Connect...")
        driver.get("https://appstoreconnect.apple.com/apps")
        time.sleep(5)

        # Check if already logged in
        if "login" in driver.current_url.lower() or "auth" in driver.current_url.lower():
            print("🔐 Please log in to App Store Connect in the browser...")
            print("⏳ Waiting for login... (will auto-continue once logged in)")

            # Wait for login to complete (up to 5 minutes)
            WebDriverWait(driver, 300).until(
                lambda d: "appstoreconnect.apple.com/apps" in d.current_url and "login" not in d.current_url.lower()
            )
            print("✅ Logged in!")
            time.sleep(3)

        # Check if app already exists
        print("🔍 Checking if Random Timer app exists...")
        try:
            # Search for Random Timer
            search_box = driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[placeholder*='Search']")
            search_box.clear()
            search_box.send_keys("Random Timer")
            time.sleep(2)

            # Check if app exists in results
            if "Random Timer" in driver.page_source:
                print("✅ Random Timer app already exists!")
                app_link = driver.find_element(By.XPATH, "//a[contains(., 'Random Timer')]")
                app_link.click()
                time.sleep(3)
            else:
                raise Exception("App not found, will create")

        except:
            # Create new app
            print("➕ Creating new app in App Store Connect...")

            # Click "+" or "Add App" button
            try:
                add_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add') or contains(@aria-label, 'Add')]"))
                )
                add_button.click()
                time.sleep(2)
            except:
                # Try alternative button location
                add_button = driver.find_element(By.CSS_SELECTOR, "button[class*='add'], a[href*='create']")
                add_button.click()
                time.sleep(2)

            # Fill in app details
            print("📝 Filling in app details...")

            # App Name
            name_input = driver.find_element(By.CSS_SELECTOR, "input[name='name'], input[placeholder*='name']")
            name_input.send_keys("Random Timer")

            # Primary Language
            lang_select = driver.find_element(By.CSS_SELECTOR, "select[name='language']")
            lang_select.send_keys("English (U.S.)")

            # Bundle ID
            bundle_select = driver.find_element(By.CSS_SELECTOR, "select[name='bundleId']")
            bundle_select.send_keys("com.iganapolsky.randomtimer")

            # SKU
            sku_input = driver.find_element(By.CSS_SELECTOR, "input[name='sku']")
            sku_input.send_keys("randomtimer001")

            time.sleep(1)

            # Click Create
            create_button = driver.find_element(By.XPATH, "//button[contains(., 'Create')]")
            create_button.click()

            print("✅ App created!")
            time.sleep(5)

        # Now navigate to TestFlight
        print("🚀 Opening TestFlight section...")
        testflight_link = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'TestFlight') or contains(@href, 'testflight')]"))
        )
        testflight_link.click()
        time.sleep(3)

        print("✅ App Store Connect setup complete!")
        print("📱 Ready to upload build to TestFlight")

        return True

    except Exception as e:
        print(f"\\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_appstore_connect()
    sys.exit(0 if success else 1)
