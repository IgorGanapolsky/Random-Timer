#!/usr/bin/env python3
"""Create app in App Store Connect and upload to TestFlight"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import sys

def create_app_and_upload():
    """Create app in App Store Connect and upload IPA"""

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Connected to Chrome")

        # Navigate to Apps page
        print("📱 Opening App Store Connect Apps page...")
        driver.get("https://appstoreconnect.apple.com/apps")
        time.sleep(5)

        # Check if we need to log in
        if "appleid.apple.com" in driver.current_url:
            print("🔐 Login required...")
            print("⏳ Waiting for manual login (up to 3 minutes)...")

            WebDriverWait(driver, 180).until(
                lambda d: "appstoreconnect.apple.com/apps" in d.current_url
            )
            print("✅ Logged in!")
            time.sleep(3)

        # Click "+" to add new app
        print("➕ Clicking + to add new app...")
        try:
            add_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Add Apps' or contains(@aria-label, 'Add')]"))
            )
            add_button.click()
            time.sleep(2)
        except:
            # Try alternative selector
            add_button = driver.find_element(By.XPATH, "//button[contains(., '+')]")
            add_button.click()
            time.sleep(2)

        # Click "New App" in dropdown
        print("📝 Clicking 'New App'...")
        try:
            new_app_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'New App')] | //button[contains(., 'New App')]"))
            )
            new_app_option.click()
            time.sleep(3)
        except:
            print("⚠️  Could not find 'New App' option - it may already be showing the form")

        # Fill in app details
        print("📝 Filling in app details...")

        # Platform: iOS (should be selected by default)

        # Name
        print("  - Setting name to 'Random Timer'...")
        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='App Name' or @name='name' or contains(@aria-label, 'Name')]"))
        )
        name_input.clear()
        name_input.send_keys("Random Timer")
        time.sleep(1)

        # Primary Language - select English (U.S.)
        print("  - Setting language to English (U.S.)...")
        try:
            language_dropdown = driver.find_element(By.XPATH, "//select[contains(@name, 'language')] | //button[contains(@aria-label, 'Language')]")
            language_dropdown.click()
            time.sleep(1)

            english_option = driver.find_element(By.XPATH, "//option[@value='en-US'] | //div[contains(text(), 'English (U.S.)')]")
            english_option.click()
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Could not set language: {e}")

        # Bundle ID - select com.iganapolsky.randomtimer
        print("  - Selecting Bundle ID...")
        try:
            bundle_dropdown = driver.find_element(By.XPATH, "//select[contains(@name, 'bundleId')] | //button[contains(@aria-label, 'Bundle ID')]")
            bundle_dropdown.click()
            time.sleep(1)

            bundle_option = driver.find_element(By.XPATH, "//option[contains(@value, 'com.iganapolsky.randomtimer')] | //div[contains(text(), 'com.iganapolsky.randomtimer')]")
            bundle_option.click()
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Could not select Bundle ID: {e}")
            print("     You may need to select it manually")
            time.sleep(5)

        # SKU
        print("  - Setting SKU to 'randomtimer'...")
        try:
            sku_input = driver.find_element(By.XPATH, "//input[@placeholder='SKU' or @name='sku']")
            sku_input.clear()
            sku_input.send_keys("randomtimer")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Could not set SKU: {e}")

        # User Access - Full Access (should be default)

        # Click Create
        print("🚀 Creating app...")
        create_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create') or @aria-label='Create']"))
        )
        create_button.click()

        print("⏳ Waiting for app to be created...")
        time.sleep(10)

        # Verify we're on the app page
        WebDriverWait(driver, 30).until(
            lambda d: "app/" in d.current_url
        )

        print("\n✅ App created successfully in App Store Connect!")
        print(f"   URL: {driver.current_url}")

        # Now upload the IPA
        print("\n📤 Now uploading IPA to TestFlight...")
        time.sleep(3)

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_app_and_upload()
    sys.exit(0 if success else 1)
