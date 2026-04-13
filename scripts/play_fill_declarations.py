#!/usr/bin/env python3
"""Play Console helpers via CDP (Tier C): attach to your logged-in Chrome on port 9222.

Modes:
  default   Reconnaissance on App content (sections + Start links).
  --health  Health / Health apps declaration assist: open flow, select visible "No" radios, Save/Submit.

Prerequisites:
  Chrome: --remote-debugging-port=9222
  You already signed into play.google.com/console in that Chrome profile.

Screenshots: .artifacts/play_console/ (see play_artifacts.py).
"""

from __future__ import annotations

import argparse
import re
import time
from playwright.sync_api import Page, sync_playwright

from play_artifacts import ARTIFACTS_DIR, screenshot_path

DEV = "8239620436488925047"
APP = "4976249162120849673"
BASE = f"https://play.google.com/console/u/0/developers/{DEV}/app/{APP}"
APP_CONTENT_URL = f"{BASE}/app-content"


def screenshot(page: Page, name: str) -> None:
    path = screenshot_path(f"play_{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")


def click_text(page: Page, text: str, timeout: int = 5000) -> bool:
    try:
        loc = page.get_by_text(text, exact=False).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        loc.click()
        time.sleep(2)
        return True
    except Exception as exc:
        print(f"  Could not click '{text}': {exc}")
        return False


def click_role(page: Page, role: str, name: str, timeout: int = 5000) -> bool:
    try:
        loc = page.get_by_role(role, name=name).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.click()
        time.sleep(2)
        return True
    except Exception:
        return False


def select_no_radio(page: Page) -> bool:
    """Select visible radio options named 'No' (declaration wizards)."""
    try:
        radios = page.get_by_role("radio", name="No").all()
        clicked = False
        for r in radios:
            if r.is_visible():
                r.click()
                time.sleep(0.4)
                clicked = True
        return clicked
    except Exception:
        return False


def click_save_or_advance(page: Page) -> bool:
    for label in ("Save", "Submit", "Next", "Confirm"):
        if click_role(page, "button", label):
            print(f"  Clicked '{label}'")
            time.sleep(2)
            return True
    return False


def connect_play_page(p) -> Page:
    print("Connecting to Chrome (CDP http://localhost:9222)...")
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0]
    play_page = None
    for pg in context.pages:
        if "play.google.com/console" in pg.url:
            play_page = pg
            break
    if not play_page:
        play_page = context.new_page()
    return play_page


def open_declaration_from_app_content(page: Page, decl_fragment: str) -> bool:
    """Click Start/Manage/Update near a row containing decl_fragment (Play Console list UI)."""
    try:
        row = page.get_by_text(decl_fragment, exact=False).first
        row.wait_for(state="visible", timeout=10000)
        row.scroll_into_view_if_needed()
        parent = row.locator("..").locator("..")
        start_btn = parent.get_by_text(re.compile(r"Start|Manage|Update|Complete", re.I)).first
        start_btn.wait_for(state="visible", timeout=5000)
        start_btn.click()
        time.sleep(3)
        return True
    except Exception as exc:
        print(f"  Could not open declaration for {decl_fragment!r}: {exc}")
        return False


def run_reconnaissance(page: Page) -> None:
    print(f"Navigating to: {APP_CONTENT_URL}")
    page.goto(APP_CONTENT_URL, wait_until="networkidle", timeout=120000)
    time.sleep(5)
    screenshot(page, "01_app_content")
    print(f"Current URL: {page.url}")

    body_text = page.locator("body").text_content() or ""
    keywords = [
        "Data safety",
        "Advertising ID",
        "Government apps",
        "Financial features",
        "Health",
        "Foreground service",
        "Exact alarm",
        "Content rating",
        "Target audience",
        "Privacy policy",
        "App access",
        "Ads",
        "Store listing",
    ]

    print("\n=== Sections found on page ===")
    for kw in keywords:
        hit = kw.lower() in body_text.lower()
        print(f"  [{'Y' if hit else 'N'}] {kw}")

    print("\n=== 'Start' items (sample) ===")
    starts = page.get_by_text("Start").all()
    print(f"Found {len(starts)} 'Start' items")
    for i, s in enumerate(starts[:25]):
        try:
            txt = (s.text_content() or "").strip()
            parent_text = s.locator("xpath=ancestor::*[4]").text_content() or ""
            print(f"  [{i}] '{txt}' context: {parent_text[:120]}")
        except Exception:
            print(f"  [{i}] (could not read)")

    screenshot(page, "02_full_content")
    print(f"\nReconnaissance done. Artifacts: {ARTIFACTS_DIR}")


def run_health_declaration(page: Page) -> None:
    print(f"Navigating to App content: {APP_CONTENT_URL}")
    page.goto(APP_CONTENT_URL, wait_until="networkidle", timeout=120000)
    time.sleep(4)
    screenshot(page, "health_00_app_content")

    opened = False
    for fragment in ("Health apps", "Health features", "Health"):
        if open_declaration_from_app_content(page, fragment):
            print(f"  Opened declaration via label containing: {fragment!r}")
            opened = True
            break

    if not opened:
        print("::error::Could not open Health declaration — finish manually. Check screenshots.")
        screenshot(page, "health_failed_open")
        return

    screenshot(page, "health_01_wizard_open")

    max_steps = 12
    for step in range(max_steps):
        select_no_radio(page)
        advanced = click_save_or_advance(page)
        screenshot(page, f"health_step_{step:02d}")
        if not advanced:
            print("  No Save/Submit/Next/Confirm found; stopping semi-agent loop.")
            break
        time.sleep(2)
        if "app-content" in page.url and step > 0:
            print("  Returned to App content; Health flow may be complete.")
            break

    screenshot(page, "health_99_final")
    print(f"Health assist finished. Review screenshots under {ARTIFACTS_DIR}")
    print("If Google shows validation errors, complete remaining fields manually in the same Chrome window.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Play Console CDP helpers (Tier C)")
    parser.add_argument(
        "--health",
        action="store_true",
        help="Assist Health apps / Health features declaration (No radios + Save)",
    )
    args = parser.parse_args()

    with sync_playwright() as p:
        page = connect_play_page(p)
        if args.health:
            run_health_declaration(page)
        else:
            run_reconnaissance(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
