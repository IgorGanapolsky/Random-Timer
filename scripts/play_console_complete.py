#!/usr/bin/env python3
"""Automate completing Google Play Console App Content declarations via Playwright."""

import time
from playwright.sync_api import sync_playwright
from play_artifacts import ARTIFACTS_DIR, screenshot_path

DEVELOPER_ID = "8239620436488925047"
PACKAGE = "com.iganapolsky.randomtimer"
BASE_URL = f"https://play.google.com/console/u/0/developers/{DEVELOPER_ID}/app"

def wait_and_click(page, selector, timeout=10000):
    """Wait for element and click it."""
    el = page.wait_for_selector(selector, timeout=timeout)
    if el:
        el.click()
        time.sleep(1)
    return el

def wait_and_click_text(page, text, timeout=10000):
    """Click element containing specific text."""
    el = page.get_by_text(text, exact=False).first
    el.wait_for(timeout=timeout)
    el.click()
    time.sleep(1)
    return el

def handle_dialog(page):
    """Dismiss any modal dialogs."""
    page.on("dialog", lambda d: d.accept())

def main():
    with sync_playwright() as p:
        # Connect to existing Chrome session or launch persistent
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
        )
        context = browser.new_context(
            storage_state=None,
            viewport={"width": 1400, "height": 900}
        )
        page = context.new_page()
        handle_dialog(page)

        # Navigate to app dashboard
        print("Navigating to Play Console...")
        page.goto(f"{BASE_URL}/list", wait_until="networkidle", timeout=60000)
        time.sleep(3)
        page.screenshot(path=screenshot_path("play_console_01_home.png"))

        # Click on Random Timer app
        print("Clicking Random Timer app...")
        try:
            page.get_by_text("Random Timer").first.click()
            time.sleep(3)
        except Exception as e:
            print(f"Could not find app: {e}")
            page.screenshot(path=screenshot_path("play_console_error.png"))
            browser.close()
            return

        page.screenshot(path=screenshot_path("play_console_02_app.png"))
        print("On app dashboard")

        # Navigate to App content / Policy
        print("Navigating to App content...")
        try:
            page.get_by_text("App content", exact=False).first.click()
            time.sleep(3)
        except Exception:
            # Try via URL
            app_id_match = page.url
            print(f"Current URL: {app_id_match}")
            # Try sidebar navigation
            try:
                page.locator("text=Policy").first.click()
                time.sleep(2)
                page.get_by_text("App content").first.click()
                time.sleep(3)
            except Exception as e2:
                print(f"Navigation failed: {e2}")

        page.screenshot(path=screenshot_path("play_console_03_content.png"))
        print(f"Screenshot saved. Check {screenshot_path('play_console_03_content.png')}")

        # Take final screenshot and close
        browser.close()
        print(f"Done. Check screenshots in {ARTIFACTS_DIR}")

if __name__ == "__main__":
    main()
