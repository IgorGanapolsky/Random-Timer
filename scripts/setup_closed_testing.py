#!/usr/bin/env python3
"""Set up Closed Testing track with 20 testers in Google Play Console."""

import time
from playwright.sync_api import sync_playwright

DEV = "8239620436488925047"
APP = "4976249162120849673"
BASE = f"https://play.google.com/console/u/0/developers/{DEV}/app/{APP}"

TESTERS = "\n".join([f"ig5973700+tester{i}@gmail.com" for i in range(1, 21)])

AAB_PATH = "/Users/ganapolsky_i/workspace/git/igor/Random-Timer/native-android/app/build/outputs/bundle/release/app-release.aab"


def screenshot(page, name):
    path = f"/tmp/play_{name}.png"
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")


def click_text(page, text, timeout=5000):
    try:
        loc = page.get_by_text(text, exact=False).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        time.sleep(0.3)
        loc.click()
        time.sleep(2)
        return True
    except:
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


def click_link(page, name, timeout=5000):
    try:
        loc = page.get_by_role("link", name=name).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.click()
        time.sleep(2)
        return True
    except:
        return False


def js_fill_textarea(page, text, index=0):
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


def main():
    with sync_playwright() as p:
        print("Connecting to Chrome on port 9222...")
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]

        play_page = None
        for pg in context.pages:
            if "play.google.com/console" in pg.url:
                play_page = pg
                break
        if not play_page:
            play_page = context.new_page()
        page = play_page

        # Step 1: Navigate to Closed Testing
        print("\n=== Step 1: Navigate to Closed Testing ===")
        closed_url = f"{BASE}/tracks/closed-testing"
        page.goto(closed_url, wait_until="networkidle", timeout=60000)
        time.sleep(5)
        screenshot(page, "closed_01_nav")
        print(f"  URL: {page.url}")

        # If redirected, try sidebar navigation
        if "closed" not in page.url.lower() and "track" not in page.url.lower():
            print("  Direct URL didn't work, trying sidebar...")
            # Try going to app dashboard first
            page.goto(f"{BASE}/app-dashboard", wait_until="networkidle", timeout=60000)
            time.sleep(5)

            # Click Testing in sidebar
            if not click_text(page, "Testing"):
                click_text(page, "Release")
            time.sleep(2)

            # Click Closed testing
            if not click_text(page, "Closed testing"):
                click_text(page, "Closed")
            time.sleep(3)
            screenshot(page, "closed_02_sidebar")
            print(f"  URL: {page.url}")

        # Step 2: Create a new closed testing track (if needed)
        print("\n=== Step 2: Create Closed Testing Track ===")
        screenshot(page, "closed_03_page")

        # Look for "Create track" or "Create new release" button
        created = False
        for btn_text in ["Create track", "Create new track", "Create closed track"]:
            if click_button(page, btn_text):
                print(f"  Clicked '{btn_text}'")
                created = True
                break

        if not created:
            # Maybe track already exists, look for "Create new release"
            for btn_text in ["Create new release", "Create release"]:
                if click_button(page, btn_text):
                    print(f"  Clicked '{btn_text}'")
                    created = True
                    break

        time.sleep(3)
        screenshot(page, "closed_04_track")
        print(f"  URL: {page.url}")

        # Step 3: Upload AAB
        print("\n=== Step 3: Upload AAB ===")
        # Look for file upload input
        try:
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(AAB_PATH)
            print(f"  Uploaded AAB: {AAB_PATH}")
            # Wait for upload to complete
            time.sleep(30)
            screenshot(page, "closed_05_aab_uploaded")
        except Exception as e:
            print(f"  File input not found, trying 'Upload' button: {e}")
            if click_button(page, "Upload"):
                time.sleep(2)
                try:
                    file_input = page.locator("input[type='file']").first
                    file_input.set_input_files(AAB_PATH)
                    print(f"  Uploaded AAB via button")
                    time.sleep(30)
                except Exception as e2:
                    print(f"  Upload failed: {e2}")
            screenshot(page, "closed_05_upload_attempt")

        # Step 4: Fill release notes if needed
        print("\n=== Step 4: Release Notes ===")
        release_notes = "Initial release of Random Timer - a fun productivity app that generates random countdown timers."
        filled = js_fill_textarea(page, release_notes, 0)
        if filled:
            print("  Filled release notes")
        else:
            # Try clicking "Add release notes" first
            click_text(page, "Add release notes")
            time.sleep(2)
            js_fill_textarea(page, release_notes, 0)

        screenshot(page, "closed_06_notes")

        # Step 5: Save / Review release
        print("\n=== Step 5: Save Release ===")
        for btn in ["Save", "Review release", "Next", "Save and publish"]:
            if click_button(page, btn):
                print(f"  Clicked '{btn}'")
                time.sleep(3)
                break
        screenshot(page, "closed_07_saved")

        # Step 6: Set up testers list
        print("\n=== Step 6: Add Testers ===")
        # Navigate to testers management
        # Try clicking "Manage track" or "Testers" tab
        click_text(page, "Testers")
        time.sleep(2)

        if not click_text(page, "Manage testers"):
            click_text(page, "Create email list")
        time.sleep(3)
        screenshot(page, "closed_08_testers")

        # Try to find email list creation
        if click_button(page, "Create email list"):
            time.sleep(2)

        # Fill list name
        try:
            name_input = page.locator("input[type='text']").first
            name_input.fill("Beta Testers")
            time.sleep(1)
        except:
            js_fill_textarea(page, "Beta Testers", 0)

        # Add email addresses
        print("  Adding 20 tester emails...")
        # Try textarea for bulk email entry
        filled = False
        for i in range(5):
            if js_fill_textarea(page, TESTERS, i):
                print(f"  Filled emails in textarea index {i}")
                filled = True
                break

        if not filled:
            # Try comma-separated in input
            comma_testers = ", ".join([f"ig5973700+tester{i}@gmail.com" for i in range(1, 21)])
            for i in range(5):
                try:
                    inputs = page.locator("input[type='text']").all()
                    if len(inputs) > i:
                        inputs[i].fill(comma_testers)
                        print(f"  Filled emails in input index {i}")
                        filled = True
                        break
                except:
                    pass

        screenshot(page, "closed_09_emails")

        # Save testers
        for btn in ["Save changes", "Save", "Create", "Done", "Add"]:
            if click_button(page, btn):
                print(f"  Clicked '{btn}'")
                time.sleep(2)
                break

        screenshot(page, "closed_10_saved_testers")

        # Step 7: Start rollout / publish to closed testing
        print("\n=== Step 7: Publish to Closed Testing ===")
        for btn in ["Start rollout", "Roll out", "Publish", "Start roll-out to Closed testing",
                     "Send for review", "Submit for review"]:
            if click_button(page, btn):
                print(f"  Clicked '{btn}'")
                time.sleep(2)
                # Confirm dialog
                click_button(page, "Roll out")
                click_button(page, "Confirm")
                click_button(page, "Yes")
                break

        time.sleep(3)
        screenshot(page, "closed_11_published")

        # Final status check
        print("\n=== Final Status ===")
        print(f"  URL: {page.url}")
        screenshot(page, "closed_12_final")

        body = page.locator("body").text_content()
        if "review" in body.lower():
            print("  App appears to be in review!")
        if "closed testing" in body.lower():
            print("  Closed testing track is set up")

        print("\n=== DONE ===")
        print("Check /tmp/play_closed_*.png for screenshots of each step.")
        print("Browser left open for manual verification.")


if __name__ == "__main__":
    main()
