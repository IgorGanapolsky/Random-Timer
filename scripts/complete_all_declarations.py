#!/usr/bin/env python3
"""Complete ALL remaining Google Play Console App Content declarations.
Uses JavaScript injection for textarea fields that aren't directly interactable."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DEV = "8239620436488925047"
APP = "4976249162120849673"
BASE = f"https://play.google.com/console/u/0/developers/{DEV}/app/{APP}"
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / ".artifacts" / "play_console"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

FGS_JUSTIFICATION = (
    "Random Timer uses a foreground service to run countdown timers that must "
    "continue when the app is in the background. Users set a random timer and "
    "need to be notified precisely when time expires, even if the app is not "
    "in the foreground. The foreground service displays a persistent notification "
    "showing the remaining time."
)

ALARM_JUSTIFICATION = (
    "Random Timer uses exact alarms to schedule precise notifications when a "
    "countdown timer completes. Users expect the timer to fire at the exact "
    "moment it reaches zero, which requires USE_EXACT_ALARM permission. "
    "Without exact alarms, timer notifications could be delayed by minutes, "
    "defeating the purpose of a timer app."
)


def screenshot(page, name):
    path = ARTIFACTS_DIR / f"play_{name}.png"
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")


def js_fill_textarea(page, text, index=0):
    """Use JavaScript to fill textarea elements that aren't directly interactable."""
    return page.evaluate("""
        (args) => {
            const textareas = document.querySelectorAll('textarea');
            if (textareas.length > args.index) {
                const ta = textareas[args.index];
                ta.focus();
                const nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLTextAreaElement.prototype, 'value'
                ).set;
                nativeSetter.call(ta, args.text);
                ta.dispatchEvent(new Event('input', { bubbles: true }));
                ta.dispatchEvent(new Event('change', { bubbles: true }));
                ta.dispatchEvent(new Event('blur', { bubbles: true }));
                return true;
            }
            return false;
        }
    """, {"text": text, "index": index})


def js_fill_input(page, text, index=0):
    """Use JavaScript to fill input elements."""
    return page.evaluate("""
        (args) => {
            const inputs = document.querySelectorAll('input[type="text"], input:not([type])');
            if (inputs.length > args.index) {
                const inp = inputs[args.index];
                inp.focus();
                const nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(inp, args.text);
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                inp.dispatchEvent(new Event('blur', { bubbles: true }));
                return true;
            }
            return false;
        }
    """, {"text": text, "index": index})


def click_text(page, text, timeout=5000, exact=False):
    try:
        loc = page.get_by_text(text, exact=exact).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        time.sleep(0.3)
        loc.click()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"  Could not click '{text}': {type(e).__name__}")
        return False


def click_button(page, name, timeout=5000):
    try:
        loc = page.get_by_role("button", name=name).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        loc.click()
        time.sleep(2)
        return True
    except:
        return False


def click_radio_no(page):
    """Click all visible 'No' radio buttons."""
    try:
        radios = page.locator("input[type='radio']").all()
        for r in radios:
            label = r.locator("xpath=ancestor::label")
            try:
                label_text = label.text_content()
                if "No" in label_text and "Yes" not in label_text:
                    r.click(force=True)
                    time.sleep(0.5)
            except:
                pass
    except:
        pass
    # Also try material radio buttons
    try:
        no_labels = page.get_by_text("No", exact=True).all()
        for label in no_labels:
            try:
                if label.is_visible():
                    label.click()
                    time.sleep(0.5)
            except:
                pass
    except:
        pass


def click_save(page):
    for label in ["Save", "Submit", "Confirm", "Next"]:
        if click_button(page, label):
            print(f"  Clicked '{label}'")
            time.sleep(3)
            return True
    return False


def select_checkbox_or_radio(page, text):
    """Click a checkbox or radio by its label text."""
    try:
        loc = page.get_by_text(text, exact=False).first
        loc.wait_for(state="visible", timeout=3000)
        loc.click()
        time.sleep(1)
        return True
    except:
        return False


def navigate_to_app_content(page):
    """Navigate to App Content page."""
    url = f"{BASE}/app-content"
    print(f"Navigating to App Content: {url}")
    page.goto(url, wait_until="networkidle", timeout=60000)
    time.sleep(5)

    # If redirected to app-list, try clicking into the app first
    if "app-list" in page.url:
        print("Redirected to app-list, clicking into app...")
        click_text(page, "Random Timer")
        time.sleep(3)
        # Try sidebar
        click_text(page, "App content")
        time.sleep(3)

    return page.url


def find_and_click_start(page, section_name):
    """Find a section by name and click its Start/Manage button."""
    try:
        # Try finding the section row and its action button
        section = page.get_by_text(section_name, exact=False).first
        section.scroll_into_view_if_needed()
        time.sleep(0.5)

        # Look for Start/Manage link nearby
        parent = section.locator("xpath=ancestor::*[contains(@class, 'row') or contains(@class, 'section') or contains(@class, 'item')]").first
        action = parent.get_by_text("Start").or_(parent.get_by_text("Manage")).or_(parent.get_by_text("Update")).first
        action.click()
        time.sleep(3)
        return True
    except:
        # Fallback: try clicking Start buttons in order
        return False


def process_data_safety(page):
    """Complete Data Safety declaration."""
    print("\n=== Data Safety ===")
    navigate_to_app_content(page)

    if not find_and_click_start(page, "Data safety"):
        click_text(page, "Data safety")
        time.sleep(3)

    screenshot(page, "data_safety_01")

    # Select "No" for data collection
    click_text(page, "does not collect or share")
    time.sleep(1)
    select_checkbox_or_radio(page, "No, my app does not collect")
    click_save(page)
    screenshot(page, "data_safety_02")


def process_advertising_id(page):
    """Complete Advertising ID declaration."""
    print("\n=== Advertising ID ===")
    navigate_to_app_content(page)

    if not find_and_click_start(page, "Advertising ID"):
        click_text(page, "Advertising ID")
        time.sleep(3)

    screenshot(page, "ad_id_01")
    select_checkbox_or_radio(page, "No")
    click_save(page)
    screenshot(page, "ad_id_02")


def process_government_apps(page):
    """Complete Government Apps declaration."""
    print("\n=== Government Apps ===")
    navigate_to_app_content(page)

    if not find_and_click_start(page, "Government apps"):
        click_text(page, "Government")
        time.sleep(3)

    screenshot(page, "govt_01")
    select_checkbox_or_radio(page, "No")
    click_save(page)
    screenshot(page, "govt_02")


def process_financial_features(page):
    """Complete Financial Features declaration."""
    print("\n=== Financial Features ===")
    navigate_to_app_content(page)

    if not find_and_click_start(page, "Financial features"):
        click_text(page, "Financial")
        time.sleep(3)

    screenshot(page, "financial_01")
    select_checkbox_or_radio(page, "No")
    click_save(page)
    screenshot(page, "financial_02")


def process_health(page):
    """Complete Health Apps declaration."""
    print("\n=== Health Apps ===")
    navigate_to_app_content(page)

    if not find_and_click_start(page, "Health"):
        click_text(page, "Health")
        time.sleep(3)

    screenshot(page, "health_01")
    select_checkbox_or_radio(page, "No")
    click_save(page)
    screenshot(page, "health_02")


def process_foreground_service(page):
    """Complete Foreground Service permission declaration."""
    print("\n=== Foreground Service ===")
    navigate_to_app_content(page)

    if not find_and_click_start(page, "Foreground service"):
        click_text(page, "Foreground service")
        time.sleep(3)

    screenshot(page, "fgs_01")
    print(f"  URL: {page.url}")

    # Select Timer/Stopwatch type
    select_checkbox_or_radio(page, "Timer")
    time.sleep(1)

    # Also try "specialUse" or "SPECIAL_USE"
    select_checkbox_or_radio(page, "Special use")
    time.sleep(1)

    screenshot(page, "fgs_02")

    # Fill justification textarea using JS
    print("  Filling justification via JS...")
    filled = js_fill_textarea(page, FGS_JUSTIFICATION, 0)
    print(f"  Textarea filled: {filled}")

    if not filled:
        # Try all textareas
        for i in range(5):
            if js_fill_textarea(page, FGS_JUSTIFICATION, i):
                print(f"  Filled textarea at index {i}")
                break

    # Also try contenteditable divs
    page.evaluate("""
        (text) => {
            const editables = document.querySelectorAll('[contenteditable="true"]');
            editables.forEach(el => {
                el.focus();
                el.textContent = text;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            });
            return editables.length;
        }
    """, FGS_JUSTIFICATION)

    time.sleep(1)
    screenshot(page, "fgs_03")

    click_save(page)
    screenshot(page, "fgs_04")


def process_exact_alarm(page):
    """Complete Exact Alarm permission declaration."""
    print("\n=== Exact Alarm ===")
    navigate_to_app_content(page)

    if not find_and_click_start(page, "Exact alarm"):
        click_text(page, "Exact alarm")
        time.sleep(3)

    screenshot(page, "alarm_01")
    print(f"  URL: {page.url}")

    # Select Timer/Alarm use case
    select_checkbox_or_radio(page, "Timer")
    time.sleep(1)
    select_checkbox_or_radio(page, "Alarm")
    time.sleep(1)

    screenshot(page, "alarm_02")

    # Fill justification textarea using JS
    print("  Filling justification via JS...")
    filled = js_fill_textarea(page, ALARM_JUSTIFICATION, 0)
    print(f"  Textarea filled: {filled}")

    if not filled:
        for i in range(5):
            if js_fill_textarea(page, ALARM_JUSTIFICATION, i):
                print(f"  Filled textarea at index {i}")
                break

    # Also try contenteditable divs
    page.evaluate("""
        (text) => {
            const editables = document.querySelectorAll('[contenteditable="true"]');
            editables.forEach(el => {
                el.focus();
                el.textContent = text;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            });
            return editables.length;
        }
    """, ALARM_JUSTIFICATION)

    time.sleep(1)
    screenshot(page, "alarm_03")

    click_save(page)
    screenshot(page, "alarm_04")


def verify_completion(page):
    """Navigate to App Content and verify all declarations are complete."""
    print("\n=== Verification ===")
    navigate_to_app_content(page)
    time.sleep(3)
    screenshot(page, "verify_final")

    body = page.locator("body").text_content()
    total = body.count("complete") + body.count("Complete")
    starts = body.count("Start")
    print(f"  'Complete' mentions: {total}")
    print(f"  'Start' mentions: {starts}")
    print(f"  URL: {page.url}")


def main():
    with sync_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]

        # Find Play Console tab
        play_page = None
        for pg in context.pages:
            if "play.google.com/console" in pg.url:
                play_page = pg
                break
        if not play_page:
            play_page = context.new_page()
        page = play_page

        print(f"Starting from: {page.url}")

        # Process all 7 declarations
        process_data_safety(page)
        process_advertising_id(page)
        process_government_apps(page)
        process_financial_features(page)
        process_health(page)
        process_foreground_service(page)
        process_exact_alarm(page)

        # Verify
        verify_completion(page)

        print("\n=== ALL DECLARATIONS PROCESSED ===")
        print(f"Check {ARTIFACTS_DIR} for screenshots of each step.")
        print("Browser left open for manual review.")


if __name__ == "__main__":
    main()
