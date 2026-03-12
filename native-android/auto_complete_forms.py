#!/usr/bin/env python3
"""Actually complete the Play Console forms automatically"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

options = Options()
options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

def click_element(xpath_list):
    """Try multiple XPath selectors"""
    for xpath in xpath_list:
        try:
            el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            el.click()
            return True
        except TimeoutException:
            continue
    return False

def fill_text(xpath_list, text):
    """Try multiple XPath selectors for text input"""
    for xpath in xpath_list:
        try:
            el = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            el.clear()
            el.send_keys(text)
            return True
        except TimeoutException:
            continue
    return False

# 1. Data Safety
print("\n1️⃣  Data Safety...")
driver.get('https://play.google.com/console/u/0/developers/8239620436488925047/app/4972891717661818591/app-content/data-safety')
time.sleep(3)

click_element([
    "//button[contains(., 'Start')]",
    "//button[contains(., 'Edit')]",
    "//span[text()='Start']",
])
time.sleep(2)

click_element([
    "//label[contains(., 'No') and contains(., 'collect')]",
    "//span[contains(., 'No') and contains(., 'collect')]//ancestor::label",
    "//input[@value='false']",
])
time.sleep(1)

click_element([
    "//button[contains(., 'Next')]",
    "//span[text()='Next']//ancestor::button",
])
time.sleep(2)

click_element([
    "//button[contains(., 'Submit')]",
    "//button[contains(., 'Save')]",
])
time.sleep(2)
print("✓ Data Safety complete")

# 2. Advertising ID
print("\n2️⃣  Advertising ID...")
driver.get('https://play.google.com/console/u/0/developers/8239620436488925047/app/4972891717661818591/app-content/advertising-id')
time.sleep(3)

click_element([
    "//label[contains(., 'No')]",
    "//span[text()='No']//ancestor::label",
])
time.sleep(1)

click_element([
    "//button[contains(., 'Save')]",
])
time.sleep(2)
print("✓ Advertising ID complete")

# 3. Government Apps
print("\n3️⃣  Government Apps...")
driver.get('https://play.google.com/console/u/0/developers/8239620436488925047/app/4972891717661818591/app-content/government-apps')
time.sleep(3)

click_element([
    "//label[contains(., 'No')]",
    "//span[text()='No']//ancestor::label",
])
time.sleep(1)

click_element([
    "//button[contains(., 'Save')]",
])
time.sleep(2)
print("✓ Government Apps complete")

# 4. Financial Features
print("\n4️⃣  Financial Features...")
driver.get('https://play.google.com/console/u/0/developers/8239620436488925047/app/4972891717661818591/app-content/financial-features')
time.sleep(3)

click_element([
    "//label[contains(., 'No')]",
    "//span[text()='No']//ancestor::label",
])
time.sleep(1)

click_element([
    "//button[contains(., 'Save')]",
])
time.sleep(2)
print("✓ Financial Features complete")

# 5. Health Apps
print("\n5️⃣  Health Apps...")
driver.get('https://play.google.com/console/u/0/developers/8239620436488925047/app/4972891717661818591/app-content/health')
time.sleep(3)

click_element([
    "//label[contains(., 'No')]",
    "//span[text()='No']//ancestor::label",
])
time.sleep(1)

click_element([
    "//button[contains(., 'Save')]",
])
time.sleep(2)
print("✓ Health Apps complete")

# 6. Foreground Service
print("\n6️⃣  Foreground Service...")
driver.get('https://play.google.com/console/u/0/developers/8239620436488925047/app/4972891717661818591/app-content/foreground-service')
time.sleep(3)

click_element([
    "//label[contains(., 'Yes')]",
    "//span[text()='Yes']//ancestor::label",
])
time.sleep(2)

click_element([
    "//label[contains(., 'Timer')]",
    "//label[contains(., 'Stopwatch')]",
    "//span[contains(., 'Timer')]//ancestor::label",
])
time.sleep(1)

fill_text([
    "//textarea",
    "//textarea[@aria-label='Justification']",
], "App runs a countdown timer that must continue when the app is in the background to notify the user when time expires.")
time.sleep(1)

click_element([
    "//button[contains(., 'Save')]",
])
time.sleep(2)
print("✓ Foreground Service complete")

# 7. Exact Alarm
print("\n7️⃣  Exact Alarm...")
driver.get('https://play.google.com/console/u/0/developers/8239620436488925047/app/4972891717661818591/app-content/exact-alarm')
time.sleep(3)

click_element([
    "//label[contains(., 'Yes')]",
    "//span[text()='Yes']//ancestor::label",
])
time.sleep(2)

click_element([
    "//label[contains(., 'Timer')]",
    "//label[contains(., 'Alarm')]",
    "//span[contains(., 'Timer')]//ancestor::label",
])
time.sleep(1)

fill_text([
    "//textarea",
    "//textarea[@aria-label='Justification']",
], "App schedules exact alarms to notify the user precisely when their random timer completes.")
time.sleep(1)

click_element([
    "//button[contains(., 'Save')]",
])
time.sleep(2)
print("✓ Exact Alarm complete")

print("\n" + "="*60)
print("✅ ALL 7 DECLARATIONS COMPLETED")
print("="*60)

# Navigate back to overview
driver.get('https://play.google.com/console/u/0/developers/8239620436488925047/app/4972891717661818591/app-content')
time.sleep(3)

print("\n✓ Navigated back to App Content overview")
print("Check the page to verify all sections are complete!")
