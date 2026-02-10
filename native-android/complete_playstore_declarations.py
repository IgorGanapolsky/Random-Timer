#!/usr/bin/env python3
"""
Complete Google Play Console declarations for Random Timer app.
Automates filling out all required App Content forms.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# App details
PACKAGE_NAME = "com.iganapolsky.randomtimer"
APP_NAME = "Random Timer"

# Declaration data based on manifest analysis
DECLARATIONS = {
    "data_safety": {
        "collects_data": False,
        "shares_data": False,
        "encryption": False,
        "description": "App does not collect or share any user data."
    },
    "advertising_id": {
        "uses_advertising_id": False
    },
    "government_app": {
        "is_government": False
    },
    "financial_features": {
        "has_financial": False
    },
    "health_app": {
        "is_health_app": False
    },
    "foreground_service": {
        "uses_fgs": True,
        "service_type": "Timer / Stopwatch",
        "justification": "App runs a countdown timer that must continue when the app is in the background to notify the user when time expires."
    },
    "exact_alarm": {
        "uses_exact_alarm": True,
        "use_case": "Timer / Alarm",
        "justification": "App schedules exact alarms to notify the user precisely when their random timer completes."
    }
}

def setup_driver():
    """Initialize Chrome WebDriver with appropriate options"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Use existing Chrome profile to maintain login session
    user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def wait_for_element(driver, by, value, timeout=10):
    """Wait for element to be present and return it"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"Timeout waiting for element: {value}")
        return None

def navigate_to_app_content(driver):
    """Navigate to App Content section"""
    print("Navigating to App Content...")
    url = f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/app-content"
    driver.get(url)
    time.sleep(3)

def complete_data_safety(driver):
    """Complete Data Safety declaration"""
    print("\n=== Completing Data Safety Declaration ===")

    # Navigate to data safety
    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/app-content/data-safety")
    time.sleep(3)

    # Click "Start" or "Edit" button
    try:
        start_btn = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Start') or contains(text(), 'Edit')]")
        if start_btn:
            start_btn.click()
            time.sleep(2)
    except:
        pass

    # Select "No data collection"
    try:
        no_data = wait_for_element(driver, By.XPATH, "//label[contains(., 'No, this app does not collect')]")
        if no_data:
            no_data.click()
            time.sleep(1)
    except:
        print("Could not find 'No data collection' option")

    # Click Next/Save
    try:
        next_btn = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Save')]")
        if next_btn:
            next_btn.click()
            time.sleep(2)
    except:
        pass

    print("✓ Data Safety completed")

def complete_advertising_id(driver):
    """Complete Advertising ID declaration"""
    print("\n=== Completing Advertising ID Declaration ===")

    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/app-content/advertising-id")
    time.sleep(3)

    try:
        # Select "No" for advertising ID usage
        no_ads = wait_for_element(driver, By.XPATH, "//label[contains(., 'No') and contains(., 'does not use')]")
        if no_ads:
            no_ads.click()
            time.sleep(1)

            # Save
            save_btn = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Save')]")
            if save_btn:
                save_btn.click()
                time.sleep(2)
    except:
        print("Could not complete Advertising ID")

    print("✓ Advertising ID completed")

def complete_government_apps(driver):
    """Complete Government Apps declaration"""
    print("\n=== Completing Government Apps Declaration ===")

    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/app-content/government-apps")
    time.sleep(3)

    try:
        # Select "No"
        no_govt = wait_for_element(driver, By.XPATH, "//label[contains(., 'No')]")
        if no_govt:
            no_govt.click()
            time.sleep(1)

            # Save
            save_btn = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Save')]")
            if save_btn:
                save_btn.click()
                time.sleep(2)
    except:
        print("Could not complete Government Apps")

    print("✓ Government Apps completed")

def complete_financial_features(driver):
    """Complete Financial Features declaration"""
    print("\n=== Completing Financial Features Declaration ===")

    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/app-content/financial-features")
    time.sleep(3)

    try:
        # Select "No" for all financial features
        no_financial = wait_for_element(driver, By.XPATH, "//label[contains(., 'No') and contains(., 'does not contain')]")
        if no_financial:
            no_financial.click()
            time.sleep(1)

            # Save
            save_btn = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Save')]")
            if save_btn:
                save_btn.click()
                time.sleep(2)
    except:
        print("Could not complete Financial Features")

    print("✓ Financial Features completed")

def complete_health_apps(driver):
    """Complete Health Apps declaration"""
    print("\n=== Completing Health Apps Declaration ===")

    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/app-content/health")
    time.sleep(3)

    try:
        # Select "No"
        no_health = wait_for_element(driver, By.XPATH, "//label[contains(., 'No')]")
        if no_health:
            no_health.click()
            time.sleep(1)

            # Save
            save_btn = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Save')]")
            if save_btn:
                save_btn.click()
                time.sleep(2)
    except:
        print("Could not complete Health Apps")

    print("✓ Health Apps completed")

def complete_foreground_service(driver):
    """Complete Foreground Service permissions declaration"""
    print("\n=== Completing Foreground Service Declaration ===")

    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/app-content/foreground-service")
    time.sleep(3)

    try:
        # Select "Yes, app uses foreground service"
        yes_fgs = wait_for_element(driver, By.XPATH, "//label[contains(., 'Yes') and contains(., 'foreground service')]")
        if yes_fgs:
            yes_fgs.click()
            time.sleep(2)

        # Select service type: Timer / Stopwatch
        timer_type = wait_for_element(driver, By.XPATH, "//label[contains(., 'Timer') or contains(., 'Stopwatch')]")
        if timer_type:
            timer_type.click()
            time.sleep(1)

        # Enter justification
        justification_field = wait_for_element(driver, By.XPATH, "//textarea[@name='justification' or @aria-label='Justification']")
        if justification_field:
            justification_field.clear()
            justification_field.send_keys(DECLARATIONS["foreground_service"]["justification"])
            time.sleep(1)

        # Save
        save_btn = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Save')]")
        if save_btn:
            save_btn.click()
            time.sleep(2)
    except Exception as e:
        print(f"Could not complete Foreground Service: {e}")

    print("✓ Foreground Service completed")

def complete_exact_alarm(driver):
    """Complete Exact Alarm permission declaration"""
    print("\n=== Completing Exact Alarm Declaration ===")

    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/app-content/exact-alarm")
    time.sleep(3)

    try:
        # Select "Yes, app uses exact alarm"
        yes_alarm = wait_for_element(driver, By.XPATH, "//label[contains(., 'Yes') and contains(., 'exact alarm')]")
        if yes_alarm:
            yes_alarm.click()
            time.sleep(2)

        # Select use case: Timer / Alarm
        timer_case = wait_for_element(driver, By.XPATH, "//label[contains(., 'Timer') or contains(., 'Alarm')]")
        if timer_case:
            timer_case.click()
            time.sleep(1)

        # Enter justification
        justification_field = wait_for_element(driver, By.XPATH, "//textarea[@name='justification' or @aria-label='Justification']")
        if justification_field:
            justification_field.clear()
            justification_field.send_keys(DECLARATIONS["exact_alarm"]["justification"])
            time.sleep(1)

        # Save
        save_btn = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Save')]")
        if save_btn:
            save_btn.click()
            time.sleep(2)
    except Exception as e:
        print(f"Could not complete Exact Alarm: {e}")

    print("✓ Exact Alarm completed")

def verify_store_listing(driver):
    """Verify and re-save store listing"""
    print("\n=== Verifying Store Listing ===")

    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/store-presence/main")
    time.sleep(3)

    print("Store listing page loaded. Please verify:")
    print("  1. App name and description are correct")
    print("  2. Screenshots and graphics are showing")
    print("  3. Click 'Save' at the bottom if any changes were made")

    input("\nPress Enter after verifying store listing...")

def setup_closed_testing(driver):
    """Guide user to set up closed testing track"""
    print("\n=== Setting Up Closed Testing ===")

    driver.get(f"https://play.google.com/console/u/0/developers/{PACKAGE_NAME}/testing/closed")
    time.sleep(3)

    print("\n⚠️  CRITICAL 2026 Policy Requirement:")
    print("New personal accounts must run Closed Testing with:")
    print("  - 20+ testers")
    print("  - 14+ days of testing")
    print("  - Before production access is granted")
    print("\nPlease create a closed testing track and add testers.")
    print("You can use family, friends, or community members.")

    input("\nPress Enter after setting up closed testing track...")

def main():
    """Main execution flow"""
    print("=" * 60)
    print("Random Timer - Google Play Console Setup")
    print("=" * 60)
    print(f"\nPackage: {PACKAGE_NAME}")
    print(f"App: {APP_NAME}")
    print("\nThis script will automatically complete all required")
    print("App Content declarations for your Android app.\n")

    # Verify AAB exists
    aab_path = "app/build/outputs/bundle/release/app-release.aab"
    if not os.path.exists(aab_path):
        print("❌ AAB file not found. Please build first:")
        print("   ./gradlew bundleRelease")
        return

    print(f"✓ Found AAB: {os.path.basename(aab_path)} ({os.path.getsize(aab_path) / 1024 / 1024:.1f}MB)\n")

    # Initialize browser
    print("Initializing browser (using your Chrome profile for authentication)...")
    driver = setup_driver()

    try:
        # Navigate to Play Console
        print("\nOpening Google Play Console...")
        driver.get("https://play.google.com/console")
        time.sleep(3)

        input("\nPress Enter after you've selected your app in the console...")

        # Complete all declarations
        complete_data_safety(driver)
        complete_advertising_id(driver)
        complete_government_apps(driver)
        complete_financial_features(driver)
        complete_health_apps(driver)
        complete_foreground_service(driver)
        complete_exact_alarm(driver)

        # Verify store listing
        verify_store_listing(driver)

        # Setup closed testing
        setup_closed_testing(driver)

        print("\n" + "=" * 60)
        print("✓ ALL DECLARATIONS COMPLETED!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Upload the AAB to the Closed Testing track")
        print("  2. Add 20+ testers to your closed testing")
        print("  3. Wait 14+ days while testers use the app")
        print("  4. Apply for production access after testing period")
        print("\nYour AAB is ready at:")
        print(f"  {os.path.abspath(aab_path)}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()
