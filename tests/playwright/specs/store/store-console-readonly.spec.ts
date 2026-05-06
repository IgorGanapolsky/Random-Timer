import fs from "node:fs";
import { expect, test } from "@playwright/test";

const defaultAscUrl =
  "https://appstoreconnect.apple.com/apps/6758355312/distribution/ios/version/inflight";
const defaultPlayUrl =
  "https://play.google.com/console/u/0/developers/8239620436488925047/app/4976249162120849673/publishing";

function tryParseUrl(rawUrl: string): URL | null {
  try {
    return new URL(rawUrl);
  } catch {
    return null;
  }
}

function isAscLoginUrl(rawUrl: string): boolean {
  const parsed = tryParseUrl(rawUrl);
  if (!parsed) {
    return false;
  }

  if (parsed.hostname.toLowerCase() !== "appstoreconnect.apple.com") {
    return false;
  }

  const path = parsed.pathname.toLowerCase();
  return path.startsWith("/login") || path.startsWith("/signin");
}

function isPlayLoginUrl(rawUrl: string): boolean {
  const parsed = tryParseUrl(rawUrl);
  if (!parsed) {
    return false;
  }

  return parsed.hostname.toLowerCase() === "accounts.google.com";
}

function isPlayAppDashboardUrl(rawUrl: string): boolean {
  const parsed = tryParseUrl(rawUrl);
  if (!parsed) {
    return false;
  }

  return parsed.hostname.toLowerCase() === "play.google.com" && /\/app\/\d+/i.test(parsed.pathname);
}

async function selectPlayDeveloperAccount(page: any, expectedAccountName: string): Promise<void> {
  const chooserHeading = page.getByRole("heading", { name: /choose developer account/i });
  if (!(await chooserHeading.isVisible().catch(() => false))) {
    return;
  }

  const accountOption = page.getByRole("option", { name: new RegExp(expectedAccountName, "i") }).first();
  if (await accountOption.isVisible().catch(() => false)) {
    await accountOption.click();
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await expect(chooserHeading).toBeHidden({ timeout: 30_000 });
    return;
  }

  throw new Error(`Play developer account chooser is visible, but "${expectedAccountName}" was not found.`);
}

async function openPlayApp(page: any, expectedAppName: string): Promise<void> {
  const appHeading = page.getByText(new RegExp(expectedAppName, "i")).first();
  if (isPlayAppDashboardUrl(page.url()) && (await appHeading.isVisible().catch(() => false))) {
    return;
  }

  const appListEntry = page.getByRole("link", { name: new RegExp(expectedAppName, "i") }).first();
  if (await appListEntry.isVisible().catch(() => false)) {
    await appListEntry.click();
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await page.waitForFunction(() => window.location.pathname.includes("/app/"), null, { timeout: 30_000 });
    return;
  }

  const appTextEntry = page.getByText(new RegExp(expectedAppName, "i")).first();
  if (await appTextEntry.isVisible().catch(() => false)) {
    await appTextEntry.click();
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await page.waitForFunction(() => window.location.pathname.includes("/app/"), null, { timeout: 30_000 });
    return;
  }

  throw new Error(`Play app "${expectedAppName}" was not found after authentication.`);
}

test.describe("Store Console Read-Only Verification", () => {
  test("App Store Connect: version page exposes expected state", async ({ browser }, testInfo) => {
    const storageStatePath = process.env.ASC_STORAGE_STATE_PATH;
    const hasAuthState = Boolean(storageStatePath && fs.existsSync(storageStatePath));
    test.skip(
      !hasAuthState,
      "Set ASC_STORAGE_STATE_PATH to an existing auth state file to run ASC console verification.",
    );
    if (!hasAuthState || !storageStatePath) {
      return;
    }

    const ascUrl = process.env.ASC_VERSION_URL ?? defaultAscUrl;
    const expectedState = process.env.ASC_EXPECTED_STATE_TEXT?.trim() ?? "";
    const expectedAppName = process.env.ASC_EXPECTED_APP_NAME ?? "Random Tactical Timer";

    const context = await browser.newContext({ storageState: storageStatePath });
    const page = await context.newPage();
    await page.goto(ascUrl, { waitUntil: "domcontentloaded" });

    await expect(page).toHaveURL(/^https:\/\/appstoreconnect\.apple\.com(?:\/.*)?$/i);
    const currentUrl = page.url();
    const isAscLogin = isAscLoginUrl(currentUrl);
    const hasAscLoginField = await page
      .getByPlaceholder(/email or phone number/i)
      .first()
      .isVisible()
      .catch(() => false);

    if (isAscLogin || hasAscLoginField) {
      throw new Error(
        "ASC auth state is not authenticated. Refresh with `cd tests/playwright && TARGET=asc npm run auth:save` and sync secrets.",
      );
    }

    await expect(page.getByText(new RegExp(expectedAppName, "i")).first()).toBeVisible({
      timeout: 30_000,
    });

    const bodyText = await page.locator("body").innerText();
    const observedVersionState =
      bodyText.match(/\b\d+\.\d+\.\d+\s+(Waiting for Review|Ready for Distribution|Prepare for Submission|Pending Developer Release|In Review)\b/i)?.[0] ??
      "unknown";
    console.log(`ASC observed version state: ${observedVersionState}`);

    if (expectedState.length > 0) {
      await expect(page.getByText(new RegExp(expectedState, "i")).first()).toBeVisible({
        timeout: 30_000,
      });
    }

    await page.screenshot({
      path: testInfo.outputPath("asc-version-readonly.png"),
      fullPage: true,
    });
    await context.close();
  });

  test("Play Console: dashboard loads with expected app", async ({ browser }, testInfo) => {
    const storageStatePath = process.env.PLAY_STORAGE_STATE_PATH;
    const hasAuthState = Boolean(storageStatePath && fs.existsSync(storageStatePath));
    test.skip(
      !hasAuthState,
      "Set PLAY_STORAGE_STATE_PATH to an existing auth state file to run Play Console verification.",
    );
    if (!hasAuthState || !storageStatePath) {
      return;
    }

    const playUrl = process.env.PLAY_CONSOLE_URL ?? defaultPlayUrl;
    const expectedAppName = process.env.PLAY_EXPECTED_APP_NAME ?? "Random Tactical Timer";
    const expectedAccountName = process.env.PLAY_EXPECTED_ACCOUNT_NAME ?? "IgorGanapolsky";
    const expectedBannerText = process.env.PLAY_EXPECTED_BANNER_TEXT ?? "";

    const context = await browser.newContext({ storageState: storageStatePath });
    const page = await context.newPage();
    await page.goto(playUrl, { waitUntil: "domcontentloaded" });

    const currentUrl = page.url();
    const isPlayLogin = isPlayLoginUrl(currentUrl);
    const hasPlayLoginField = await page
      .locator('input[type="email"]')
      .first()
      .isVisible()
      .catch(() => false);

    if (isPlayLogin || hasPlayLoginField) {
      throw new Error(
        "Play auth state is not authenticated. Refresh with `cd tests/playwright && TARGET=play npm run auth:save` and sync secrets.",
      );
    }

    await selectPlayDeveloperAccount(page, expectedAccountName);
    await openPlayApp(page, expectedAppName);

    await expect(page).toHaveURL(/^https:\/\/play\.google\.com\/console(?:\/.*)?$/i);
    await expect(page.getByText(new RegExp(expectedAppName, "i")).first()).toBeVisible({
      timeout: 30_000,
    });

    const bodyText = await page.locator("body").innerText();
    const appStatus = bodyText.match(/\b(Closed testing|Open testing|Production|Draft)\b/i)?.[0] ?? "unknown";
    const updateStatus = bodyText.match(/\b(Ready to publish|In review|Published)\b/i)?.[0] ?? "unknown";
    console.log(`Play observed app status: ${appStatus}`);
    console.log(`Play observed update status: ${updateStatus}`);

    if (expectedBannerText.trim().length > 0) {
      await expect(page.getByText(new RegExp(expectedBannerText, "i")).first()).toBeVisible({
        timeout: 30_000,
      });
    }

    await page.screenshot({
      path: testInfo.outputPath("play-dashboard-readonly.png"),
      fullPage: true,
    });
    await context.close();
  });
});
