#!/usr/bin/env python3
"""Complete Google Play Console App Content declarations via CDP connection to existing Chrome."""

import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

DEVELOPER_ID = "8239620436488925047"
BASE = f"https://play.google.com/console/u/0/developers/{DEVELOPER_ID}"
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / ".artifacts" / "play_console"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def safe_click(page, selector, timeout=5000):
    try:
        el = page.locator(selector).first
        el.wait_for(state="visible", timeout=timeout)
        el.click()
        time.sleep(1.5)
        return True
    except Exception:
        return False

def safe_click_text(page, text, timeout=5000):
    try:
        el = page.get_by_text(text, exact=False).first
        el.wait_for(state="visible", timeout=timeout)
        el.click()
        time.sleep(1.5)
        return True
    except Exception:
        return False

def save_page(page):
    """Click Save button if present."""
    for label in ["Save", "Submit", "Confirm"]:
        if safe_click_text(page, label, timeout=3000):
            print(f"  Clicked '{label}'")
            time.sleep(2)
            return True
    return False

def screenshot(page, name):
    path = ARTIFACTS_DIR / f"play_{name}.png"
    page.screenshot(path=path)
    print(f"  Screenshot: {path}")

def main():
    with sync_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        
        # Find the Play Console tab or open a new one
        play_page = None
        for page in context.pages:
            if "play.google.com/console" in page.url:
                play_page = page
                break
        
        if not play_page:
            play_page = context.new_page()
            play_page.goto(f"{BASE}/app-list", wait_until="networkidle", timeout=60000)
            time.sleep(3)
        
        page = play_page
        print(f"Current URL: {page.url}")
        screenshot(page, "00_start")

        # Navigate to app if on app-list
        if "app-list" in page.url:
            print("Clicking into Random Timer app...")
            if safe_click_text(page, "Random Timer"):
                time.sleep(3)
            screenshot(page, "01_app_dashboard")

        # Get current URL to extract app ID
        current_url = page.url
        print(f"App URL: {current_url}")

        # Navigate to App content
        print("\n=== Navigating to App Content ===")
        if safe_click_text(page, "App content"):
            time.sleep(3)
        elif safe_click_text(page, "Policy and programs"):
            time.sleep(2)
            safe_click_text(page, "App content")
            time.sleep(3)
        
        screenshot(page, "02_app_content")
        print(f"URL: {page.url}")

        # List all the declaration sections visible
        sections = page.locator("text=/Start|Manage|Complete/i").all()
        print(f"\nFound {len(sections)} action items on App Content page")
        for i, s in enumerate(sections):
            try:
                text = s.text_content()
                print(f"  [{i}] {text}")
            except:
                pass

        # Now let's handle each declaration that shows "Start" or similar
        declarations = [
            "Data safety",
            "Advertising ID", 
            "Government apps",
            "Financial features",
            "Health",
            "Foreground service",
            "Exact alarm",
        ]

        for decl in declarations:
            print(f"\n=== Processing: {decl} ===")
            # Try to find and click the Start/Manage button next to this section
            try:
                row = page.locator(f"text={decl}").first
                parent = row.locator("..").locator("..")
                start_btn = parent.locator("text=/Start|Manage|Update/i").first
                start_btn.click()
                time.sleep(3)
                screenshot(page, f"03_{decl.replace(' ', '_')}")
                print(f"  Opened {decl} page")
                print(f"  URL: {page.url}")
            except Exception as e:
                print(f"  Could not open {decl}: {e}")
                continue

            # Go back to app content for next declaration
            page.go_back()
            time.sleep(2)

        screenshot(page, "99_final")
        print(f"\nDone! Check screenshots in {ARTIFACTS_DIR}")
        print("Browser left open for manual completion if needed.")

if __name__ == "__main__":
    main()
