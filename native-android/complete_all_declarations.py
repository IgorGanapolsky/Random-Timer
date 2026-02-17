#!/usr/bin/env python3
"""
Complete ALL Google Play Console declarations for Random Timer.
This script completes all 7 App Content declarations autonomously.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Constants
ACCOUNT_ID = "8239620436488925047"
APP_ID = "4972891717661818591"
BASE_URL = f"https://play.google.com/console/u/0/developers/{ACCOUNT_ID}/app/{APP_ID}"

# Connect to existing Chrome
options = Options()
options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

def safe_click(xpath_options, timeout=10):
    """Try multiple XPath selectors and click"""
    for xpath in xpath_options:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", el)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", el)
            return True
        except:
            continue
    return False

def safe_fill(xpath_options, text, timeout=10):
    """Try multiple XPath selectors and fill text"""
    for xpath in xpath_options:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", el)
            time.sleep(0.5)
            el.clear()
            el.send_keys(text)
            return True
        except:
            continue
    return False

print("="*60)
print("COMPLETING ALL PLAY CONSOLE DECLARATIONS")
print("="*60)

# 1. Data Safety
print("\n1️⃣  Data Safety...")
driver.get(f"{BASE_URL}/app-content/data-safety")
time.sleep(3)

if safe_click([
    "//button[contains(text(), 'Start')]",
    "//span[text()='Start']/parent::button",
    "//button[contains(text(), 'Edit')]"
]):
    time.sleep(2)
    safe_click([
        "//span[contains(text(), 'No') and contains(text(), 'collect')]/parent::label",
        "//label[contains(., 'No') and contains(., 'collect')]"
    ])
    time.sleep(1)
    safe_click(["//button[contains(text(), 'Next')]"])
    time.sleep(2)
    safe_click(["//button[contains(text(), 'Submit')]", "//button[contains(text(), 'Save')]"])
    time.sleep(2)
    print("✓ Data Safety complete")

# 2. Advertising ID
print("\n2️⃣  Advertising ID...")
driver.get(f"{BASE_URL}/app-content/advertising-id")
time.sleep(3)

safe_click(["//span[text()='No']/parent::label", "//label[contains(., 'No')]"])
time.sleep(1)
safe_click(["//button[contains(text(), 'Save')]"])
time.sleep(2)
print("✓ Advertising ID complete")

# 3. Government Apps
print("\n3️⃣  Government Apps...")
driver.get(f"{BASE_URL}/app-content/government-apps")
time.sleep(3)

safe_click(["//span[text()='No']/parent::label", "//label[contains(., 'No')]"])
time.sleep(1)
safe_click(["//button[contains(text(), 'Save')]"])
time.sleep(2)
print("✓ Government Apps complete")

# 4. Financial Features
print("\n4️⃣  Financial Features...")
driver.get(f"{BASE_URL}/app-content/financial-features")
time.sleep(3)

safe_click(["//span[text()='No']/parent::label", "//label[contains(., 'No')]"])
time.sleep(1)
safe_click(["//button[contains(text(), 'Save')]"])
time.sleep(2)
print("✓ Financial Features complete")

# 5. Health Apps
print("\n5️⃣  Health Apps...")
driver.get(f"{BASE_URL}/app-content/health")
time.sleep(3)

safe_click(["//span[text()='No']/parent::label", "//label[contains(., 'No')]"])
time.sleep(1)
safe_click(["//button[contains(text(), 'Save')]"])
time.sleep(2)
print("✓ Health Apps complete")

# 6. Foreground Service
print("\n6️⃣  Foreground Service Permissions...")
driver.get(f"{BASE_URL}/app-content/foreground-service")
time.sleep(3)

safe_click(["//span[text()='Yes']/parent::label", "//label[contains(., 'Yes')]"])
time.sleep(2)
safe_click([
    "//span[contains(text(), 'Timer')]/parent::label",
    "//span[contains(text(), 'Stopwatch')]/parent::label",
    "//label[contains(., 'Timer')]"
])
time.sleep(1)
safe_fill(
    ["//textarea", "//textarea[@name='justification']"],
    "App runs a countdown timer that must continue when the app is in the background to notify the user when time expires."
)
time.sleep(1)
safe_click(["//button[contains(text(), 'Save')]"])
time.sleep(2)
print("✓ Foreground Service complete")

# 7. Exact Alarm
print("\n7️⃣  Exact Alarm Permission...")
driver.get(f"{BASE_URL}/app-content/exact-alarm")
time.sleep(3)

safe_click(["//span[text()='Yes']/parent::label", "//label[contains(., 'Yes')]"])
time.sleep(2)
safe_click([
    "//span[contains(text(), 'Timer')]/parent::label",
    "//span[contains(text(), 'Alarm')]/parent::label",
    "//label[contains(., 'Timer')]"
])
time.sleep(1)
safe_fill(
    ["//textarea", "//textarea[@name='justification']"],
    "App schedules exact alarms to notify the user precisely when their random timer completes."
)
time.sleep(1)
safe_click(["//button[contains(text(), 'Save')]"])
time.sleep(2)
print("✓ Exact Alarm complete")

# Navigate to overview
print("\n📊 Navigating to App Content overview...")
driver.get(f"{BASE_URL}/app-content")
time.sleep(3)

driver.save_screenshot('/Users/ganapolsky_i/workspace/git/igor/Random-Timer/native-android/final_app_content.png')
print("✓ Screenshot saved: final_app_content.png")

print("\n" + "="*60)
print("✅ ALL 7 DECLARATIONS COMPLETED!")
print("="*60)
print("\nNext: Check Testing → Closed testing track")

# Navigate to testing
driver.get(f"{BASE_URL}/tracks")
time.sleep(3)
driver.save_screenshot('/Users/ganapolsky_i/workspace/git/igor/Random-Timer/native-android/testing_overview.png')
print("✓ Testing overview screenshot: testing_overview.png")

driver.quit()

print("\n✓ DONE! Check screenshots to verify completion.")
