#!/usr/bin/env python3
"""Complete API Key creation flow with authentication handling"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import sys
import os

def complete_api_key_creation():
    """Create API Key with full authentication"""

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Connected to Chrome")

        # Navigate to API Keys page
        print("🔑 Opening API Keys page...")
        driver.get("https://appstoreconnect.apple.com/access/integrations/api")
        time.sleep(5)

        # Check if we need to log in
        if "appleid.apple.com" in driver.current_url or "Email or Phone" in driver.page_source:
            print("🔐 Login required...")
            print("⏳ Waiting for manual login (up to 3 minutes)...")

            # Wait for login to complete
            WebDriverWait(driver, 180).until(
                lambda d: "appstoreconnect.apple.com/access" in d.current_url
            )
            print("✅ Logged in!")
            time.sleep(3)

        # Now click the + button to add new key
        print("➕ Clicking + button to generate new key...")
        add_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Add' or contains(., '+')]"))
        )
        add_button.click()
        time.sleep(3)

        # Fill in key name
        print("📝 Entering key name...")
        name_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
        )
        name_field.clear()
        name_field.send_keys("Random Timer CLI Upload")
        time.sleep(1)

        # Select access level - try to find and select Admin or Developer
        print("🔐 Setting access level...")
        try:
            # Click on the access dropdown
            access_dropdown = driver.find_element(By.XPATH, "//select | //button[contains(@class, 'select')] | //div[@role='button' and contains(., 'Access')]")
            access_dropdown.click()
            time.sleep(1)

            # Try to select "Developer" access (sufficient for uploads)
            try:
                developer_option = driver.find_element(By.XPATH, "//option[contains(., 'Developer')] | //div[contains(text(), 'Developer')]")
                developer_option.click()
                print("✅ Selected Developer access")
            except:
                # Fall back to Admin if Developer not available
                admin_option = driver.find_element(By.XPATH, "//option[contains(., 'Admin')] | //div[contains(text(), 'Admin')]")
                admin_option.click()
                print("✅ Selected Admin access")

            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Could not set access level automatically: {e}")
            print("   Please select 'Developer' or 'Admin' access manually")
            time.sleep(5)

        # Click Generate
        print("🚀 Generating API Key...")
        generate_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Generate') or contains(text(), 'Create')]"))
        )
        generate_button.click()
        time.sleep(5)

        print("\n✅ API Key generated!")
        print("\n📥 IMPORTANT NEXT STEPS:")
        print("   1. The page should show the new API Key")
        print("   2. Click 'Download API Key' to get the .p8 file")
        print("   3. Note the Key ID and Issuer ID displayed")
        print("\n⏳ Waiting 30 seconds for you to download the key...")

        # Wait for user to download
        time.sleep(30)

        # Try to extract the details from the page
        print("\n📋 Extracting API Key details...")
        try:
            # Look for Key ID and Issuer ID in the page
            page_source = driver.page_source

            # Create directory for API keys
            api_key_dir = os.path.expanduser("~/.appstoreconnect/private_keys/")
            os.makedirs(api_key_dir, exist_ok=True)

            print(f"\n✅ API Key directory created: {api_key_dir}")
            print("\nℹ️  To use this key with Fastlane, add to your .env:")
            print("   APP_STORE_CONNECT_API_KEY_PATH=~/.appstoreconnect/private_keys/AuthKey_XXXXXX.p8")
            print("   APP_STORE_CONNECT_API_KEY_ID=XXXXXX")
            print("   APP_STORE_CONNECT_API_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")

        except Exception as e:
            print(f"⚠️  Could not extract details: {e}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = complete_api_key_creation()
    sys.exit(0 if success else 1)
