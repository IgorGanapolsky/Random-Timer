#!/usr/bin/env python3
"""Create App Store Connect API Key for automated uploads"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import sys

def create_api_key():
    """Create API Key in App Store Connect"""

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Connected to Chrome")

        # Navigate to App Store Connect Users and Access
        print("🔑 Opening App Store Connect Users and Access...")
        driver.get("https://appstoreconnect.apple.com/access/integrations/api")
        time.sleep(5)

        print("⏳ Waiting for page to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Click "Generate API Key" or "+" button
        print("➕ Looking for 'Generate API Key' button...")
        try:
            # Try finding the generate/add button
            add_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Generate') or contains(., 'Key') or contains(@aria-label, 'add')]"))
            )
            add_button.click()
            print("✅ Clicked 'Generate API Key'")
        except:
            # Try alternative selectors
            try:
                add_button = driver.find_element(By.XPATH, "//button[@aria-label='Add']")
                add_button.click()
                print("✅ Clicked Add button")
            except:
                # Try the + button
                add_button = driver.find_element(By.CSS_SELECTOR, "button[class*='add'], button[aria-label*='Add']")
                add_button.click()
                print("✅ Clicked + button")

        time.sleep(3)

        # Fill in API Key Name
        print("📝 Entering API Key details...")
        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='name'], input[placeholder*='name']"))
        )
        name_input.clear()
        name_input.send_keys("Random Timer CLI Upload Key")

        time.sleep(1)

        # Select Access level - need "Admin" or "App Manager"
        print("🔐 Setting access level to Admin...")
        try:
            # Try clicking Access dropdown
            access_select = driver.find_element(By.XPATH, "//select[contains(@name, 'access') or contains(@name, 'role')] | //div[contains(@class, 'select')]")
            access_select.click()
            time.sleep(1)

            # Select Admin or App Manager
            admin_option = driver.find_element(By.XPATH, "//option[contains(., 'Admin')] | //div[contains(., 'Admin')]")
            admin_option.click()
            print("✅ Selected Admin access")
        except:
            print("⚠️  Could not set access level - may need manual selection")

        time.sleep(2)

        # Click Generate/Create button
        print("🚀 Generating API Key...")
        generate_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Generate') or contains(., 'Create')]"))
        )
        generate_button.click()

        time.sleep(5)

        print("✅ API Key generated!")
        print("\n📥 IMPORTANT: Download the API Key file (.p8)")
        print("   1. Click 'Download API Key'")
        print("   2. Save it to ~/.appstoreconnect/private_keys/")
        print("   3. Note the Issuer ID and Key ID from the page")
        print("\n⏳ Waiting 10 seconds for you to download...")

        time.sleep(10)

        # Try to extract the Key ID and Issuer ID
        print("\n🔍 Extracting Key details...")
        try:
            page_text = driver.page_source
            if "Key ID" in page_text:
                print("✅ API Key created successfully!")
                print("   Check the page for Key ID and Issuer ID")
        except:
            pass

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_api_key()
    sys.exit(0 if success else 1)
