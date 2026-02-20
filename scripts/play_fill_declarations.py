#!/usr/bin/env python3
"""Fill Google Play Console declarations by navigating directly to URLs."""

import time
from playwright.sync_api import sync_playwright
from play_artifacts import ARTIFACTS_DIR, screenshot_path

DEV = "8239620436488925047"
APP = "4976249162120849673"
BASE = f"https://play.google.com/console/u/0/developers/{DEV}/app/{APP}"

def screenshot(page, name):
    path = screenshot_path(f"play_{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")

def click_text(page, text, timeout=5000):
    try:
        loc = page.get_by_text(text, exact=False).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        loc.click()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"  Could not click '{text}': {e}")
        return False

def click_role(page, role, name, timeout=5000):
    try:
        loc = page.get_by_role(role, name=name).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.click()
        time.sleep(2)
        return True
    except:
        return False

def select_no_radio(page):
    """Select 'No' radio button on declaration pages."""
    try:
        radios = page.get_by_role("radio", name="No").all()
        for r in radios:
            if r.is_visible():
                r.click()
                time.sleep(0.5)
        return True
    except:
        return False

def click_save(page):
    for label in ["Save", "Submit", "Next", "Confirm"]:
        if click_role(page, "button", label):
            print(f"  Clicked '{label}'")
            time.sleep(2)
            return True
    return False

def main():
    with sync_playwright() as p:
        print("Connecting to Chrome...")
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        
        # Find or create Play Console tab
        play_page = None
        for pg in context.pages:
            if "play.google.com/console" in pg.url:
                play_page = pg
                break
        if not play_page:
            play_page = context.new_page()
        page = play_page

        # Go directly to App Content page
        content_url = f"{BASE}/app-content"
        print(f"Navigating to: {content_url}")
        page.goto(content_url, wait_until="networkidle", timeout=60000)
        time.sleep(5)
        screenshot(page, "01_app_content")
        print(f"Current URL: {page.url}")
        
        # Get page text to understand what's there
        body_text = page.locator("body").text_content()
        
        # Look for key sections
        keywords = [
            "Data safety", "Advertising ID", "Government apps",
            "Financial features", "Health", "Foreground service", 
            "Exact alarm", "Content rating", "Target audience",
            "Privacy policy", "App access", "Ads", "Store listing"
        ]
        
        print("\n=== Sections found on page ===")
        for kw in keywords:
            if kw.lower() in body_text.lower():
                print(f"  ✓ {kw}")
            else:
                print(f"  ✗ {kw}")

        # Find all "Start" buttons/links
        print("\n=== Looking for action items ===")
        starts = page.get_by_text("Start").all()
        print(f"Found {len(starts)} 'Start' items")
        for i, s in enumerate(starts):
            try:
                txt = s.text_content().strip()
                # Get parent context
                parent_text = s.locator("xpath=ancestor::*[4]").text_content()[:100]
                print(f"  [{i}] '{txt}' in context: {parent_text}")
            except:
                print(f"  [{i}] (could not read)")

        # Also look for links/buttons with declaration names
        print("\n=== Looking for declaration links ===")
        links = page.get_by_role("link").all()
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                text = link.text_content().strip()[:60]
                if any(k.lower() in text.lower() for k in keywords):
                    print(f"  Link: '{text}' -> {href}")
            except:
                pass

        # Take a full page screenshot for analysis
        screenshot(page, "02_full_content")
        
        print(f"\nDone with reconnaissance. Check {ARTIFACTS_DIR}")

if __name__ == "__main__":
    main()
