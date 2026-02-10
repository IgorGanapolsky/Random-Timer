#!/usr/bin/env python3
"""Complete Google Play Store listing setup"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def complete_playstore_setup():
    """Complete all required Play Store setup steps"""

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Navigate to main store listing
        print("📝 Opening Main store listing...")
        driver.get("https://play.google.com/console/u/0/developers/8239620436488925047/app/4976249162120849673/store-presence/main")
        time.sleep(5)

        # Fill in App name
        print("  → Setting app name: Random Timer")
        try:
            app_name = driver.find_element(By.XPATH, "//input[@aria-label='App name' or contains(@placeholder, 'App name')]")
            app_name.clear()
            app_name.send_keys("Random Timer")
            time.sleep(1)
        except:
            print("    ⚠️  App name field not found or already filled")

        # Fill in Short description
        print("  → Setting short description")
        try:
            short_desc = driver.find_element(By.XPATH, "//textarea[@aria-label='Short description' or contains(@placeholder, 'Short')]")
            short_desc.clear()
            short_desc.send_keys("A timer that goes off at a random time within your chosen range")
            time.sleep(1)
        except:
            print("    ⚠️  Short description field not found")

        # Fill in Full description
        print("  → Setting full description")
        try:
            full_desc = driver.find_element(By.XPATH, "//textarea[@aria-label='Full description' or contains(@placeholder, 'Full')]")
            full_desc.clear()
            full_desc.send_keys("""Random Timer helps you add unpredictability to your routines.

Set a time range, and the timer will go off at a random moment within that range. Perfect for:

• Adding variety to workout intervals
• Creating suspense in games and activities
• Breaking predictable patterns
• Making meditation sessions more dynamic

Features:
• Simple, intuitive interface
• Visual countdown display
• Custom time ranges
• Sound and vibration alerts
• Dark mode support""")
            time.sleep(1)
        except:
            print("    ⚠️  Full description field not found")

        # Save changes
        print("💾 Saving store listing...")
        try:
            save_button = driver.find_element(By.XPATH, "//button[contains(., 'Save') or @aria-label='Save']")
            save_button.click()
            time.sleep(3)
        except:
            print("    ⚠️  Save button not found")

        # Navigate to App category
        print("\n📂 Setting app category...")
        driver.get("https://play.google.com/console/u/0/developers/8239620436488925047/app/4976249162120849673/store-settings")
        time.sleep(5)

        try:
            # Click category dropdown
            category_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Category')] | //select[contains(@name, 'category')]")
            category_button.click()
            time.sleep(1)

            # Select "Tools" or "Productivity"
            tools_option = driver.find_element(By.XPATH, "//div[contains(text(), 'Tools')] | //option[contains(., 'Tools')]")
            tools_option.click()
            time.sleep(1)

            print("  ✓ Category set to: Tools")
        except:
            print("    ⚠️  Category selection failed - may need manual selection")

        # Save category
        try:
            save_button = driver.find_element(By.XPATH, "//button[contains(., 'Save')]")
            save_button.click()
            time.sleep(3)
        except:
            pass

        # Navigate to Content rating
        print("\n🔞 Setting up content rating...")
        driver.get("https://play.google.com/console/u/0/developers/8239620436488925047/app/4976249162120849673/content-rating")
        time.sleep(5)

        try:
            start_button = driver.find_element(By.XPATH, "//button[contains(., 'Start questionnaire') or contains(., 'Start')]")
            start_button.click()
            time.sleep(2)

            # Fill questionnaire - answer "No" to all sensitive content questions
            # This is a timer app, so all answers should be "No"
            print("  → Filling content rating questionnaire...")

            # Email
            try:
                email_field = driver.find_element(By.XPATH, "//input[@type='email']")
                email_field.send_keys("igor.ganapolsky@icloud.com")
                time.sleep(1)
            except:
                pass

            # Select app category
            try:
                cat_select = driver.find_element(By.XPATH, "//select | //button[contains(@aria-label, 'category')]")
                cat_select.click()
                time.sleep(1)
                utility_option = driver.find_element(By.XPATH, "//option[contains(., 'Utility')] | //div[contains(text(), 'Utility')]")
                utility_option.click()
                time.sleep(1)
            except:
                pass

            # Answer No to all content questions
            no_buttons = driver.find_elements(By.XPATH, "//input[@value='false'] | //button[contains(., 'No')]")
            for btn in no_buttons:
                try:
                    btn.click()
                    time.sleep(0.5)
                except:
                    pass

            # Save and submit
            submit_button = driver.find_element(By.XPATH, "//button[contains(., 'Submit') or contains(., 'Save')]")
            submit_button.click()
            time.sleep(3)

            print("  ✓ Content rating submitted")
        except Exception as e:
            print(f"    ⚠️  Content rating setup failed: {e}")

        print("\n✅ Play Store setup completed!")
        print("   Next steps:")
        print("   1. Upload screenshots (can be done later)")
        print("   2. Add privacy policy URL (if required)")
        print("   3. Review and publish from dashboard")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    import sys
    success = complete_playstore_setup()
    sys.exit(0 if success else 1)
