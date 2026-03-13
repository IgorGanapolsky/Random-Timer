import fs from "node:fs";
import path from "node:path";
import { chromium } from "@playwright/test";

const defaultPlayUrl =
  "https://play.google.com/console/u/0/developers/8239620436488925047/app/4974974102541773558/app-dashboard";

function fail(message) {
  throw new Error(message);
}

function tryParseUrl(rawUrl) {
  try {
    return new URL(rawUrl);
  } catch {
    return null;
  }
}

function isPlayLoginUrl(rawUrl) {
  const parsed = tryParseUrl(rawUrl);
  if (!parsed) {
    return false;
  }
  return parsed.hostname.toLowerCase() === "accounts.google.com";
}

async function expectAuthenticated(page) {
  const currentUrl = page.url();
  const isLogin = isPlayLoginUrl(currentUrl);
  const hasLoginField = await page
    .locator('input[type="email"]')
    .first()
    .isVisible()
    .catch(() => false);

  if (isLogin || hasLoginField) {
    fail(
      "Play auth state is not authenticated. Refresh PLAY_STORAGE_STATE_JSON and rerun.",
    );
  }
}

async function saveArtifacts(page, dir, name) {
  const screenshotPath = path.join(dir, `${name}.png`);
  const textPath = path.join(dir, `${name}.txt`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const bodyText = await page.locator("body").innerText().catch(() => "");
  fs.writeFileSync(textPath, bodyText, "utf8");
}

async function clickFirst(page, labels) {
  for (const label of labels) {
    const roleLink = page.getByRole("link", { name: label }).first();
    if (await roleLink.isVisible().catch(() => false)) {
      await roleLink.click();
      return label;
    }

    const roleTab = page.getByRole("tab", { name: label }).first();
    if (await roleTab.isVisible().catch(() => false)) {
      await roleTab.click();
      return label;
    }

    const roleButton = page.getByRole("button", { name: label }).first();
    if (await roleButton.isVisible().catch(() => false)) {
      await roleButton.click();
      return label;
    }

    const textNode = page.getByText(label, { exact: false }).first();
    if (await textNode.isVisible().catch(() => false)) {
      await textNode.click();
      return label;
    }
  }

  return null;
}

async function ensureCountrySelected(page, countryName) {
  const bodyBefore = await page.locator("body").innerText().catch(() => "");
  if (new RegExp(countryName, "i").test(bodyBefore)) {
    return { changed: false, reason: `${countryName} already visible on page` };
  }

  const manageClicked = await clickFirst(page, [
    /add countries\/regions/i,
    /manage countries\/regions/i,
    /countries\/regions/i,
    /add countries/i,
    /manage countries/i,
  ]);
  if (!manageClicked) {
    fail("Could not open Play production Countries/regions controls.");
  }

  await page.waitForTimeout(3000);

  const searchInput = page
    .getByPlaceholder(/search/i)
    .or(page.locator('input[aria-label*="Search" i]'))
    .first();
  if (await searchInput.isVisible().catch(() => false)) {
    await searchInput.fill(countryName);
    await page.waitForTimeout(1500);
  }

  const countryOption = page.getByText(new RegExp(countryName, "i")).first();
  if (!(await countryOption.isVisible().catch(() => false))) {
    fail(`Could not find country option for ${countryName}.`);
  }
  await countryOption.click();
  await page.waitForTimeout(1500);

  const confirmClicked = await clickFirst(page, [
    /add countries\/regions/i,
    /apply/i,
    /save/i,
    /done/i,
  ]);
  if (!confirmClicked) {
    fail("Could not confirm Play country selection.");
  }

  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.waitForTimeout(5000);

  const bodyAfter = await page.locator("body").innerText().catch(() => "");
  if (!new RegExp(countryName, "i").test(bodyAfter)) {
    fail(`Country ${countryName} is still not visible after saving.`);
  }

  return { changed: true, reason: `${countryName} added` };
}

async function main() {
  const storageStatePath = process.env.PLAY_STORAGE_STATE_PATH;
  if (!storageStatePath || !fs.existsSync(storageStatePath)) {
    fail("PLAY_STORAGE_STATE_PATH must point to an existing Play auth state file.");
  }

  const playUrl = process.env.PLAY_CONSOLE_URL ?? defaultPlayUrl;
  const countryName = process.env.PLAY_TARGET_COUNTRY ?? "United States";
  const artifactDir =
    process.env.PLAY_COUNTRY_ARTIFACT_DIR ??
    path.resolve(process.cwd(), "test-results/play-production-countries");
  fs.mkdirSync(artifactDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: storageStatePath,
    viewport: { width: 1600, height: 1200 },
  });
  const page = await context.newPage();

  try {
    await page.goto(playUrl, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(5000);
    await expectAuthenticated(page);
    await saveArtifacts(page, artifactDir, "01-dashboard");

    const productionClicked = await clickFirst(page, [/^production$/i, /production/i]);
    if (!productionClicked) {
      fail("Could not navigate to Play Production page.");
    }
    await page.waitForTimeout(4000);
    await saveArtifacts(page, artifactDir, "02-production");

    const countriesClicked = await clickFirst(page, [/countries\/regions/i, /countries/i]);
    if (!countriesClicked) {
      fail("Could not open Play Countries/regions section.");
    }
    await page.waitForTimeout(4000);
    await saveArtifacts(page, artifactDir, "03-countries");

    const result = await ensureCountrySelected(page, countryName);
    await saveArtifacts(page, artifactDir, "04-after-save");

    const resultPath = path.join(artifactDir, "result.json");
    fs.writeFileSync(
      resultPath,
      JSON.stringify(
        {
          changed: result.changed,
          country: countryName,
          reason: result.reason,
          finalUrl: page.url(),
        },
        null,
        2,
      ),
      "utf8",
    );
  } finally {
    await context.close();
    await browser.close();
  }
}

await main();
