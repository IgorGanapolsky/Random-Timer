import fs from "node:fs";
import path from "node:path";
import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { chromium } from "playwright";

const target = (process.env.TARGET || "asc").toLowerCase();
const outputPath =
  process.env.OUTPUT_PATH ||
  (target === "play" ? ".auth/play.json" : ".auth/appstore.json");
const startUrl =
  process.env.START_URL ||
  (target === "play"
    ? "https://play.google.com/console"
    : "https://appstoreconnect.apple.com");
const browserApp = (process.env.BROWSER_APP || "").trim().toLowerCase();

function resolveExecutablePath(appName) {
  if (appName === "comet") {
    const cometPath = "/Applications/Comet.app/Contents/MacOS/Comet";
    if (fs.existsSync(cometPath)) {
      return cometPath;
    }
    throw new Error(`Comet executable not found at ${cometPath}`);
  }
  return undefined;
}

if (!["asc", "play"].includes(target)) {
  console.error("Invalid TARGET. Use TARGET=asc or TARGET=play.");
  process.exit(1);
}

const absOutputPath = path.resolve(outputPath);
fs.mkdirSync(path.dirname(absOutputPath), { recursive: true });

const executablePath = resolveExecutablePath(browserApp);
const browser = await chromium.launch({
  headless: false,
  executablePath,
});
const context = await browser.newContext();
const page = await context.newPage();

console.log(`Opening ${startUrl}`);
await page.goto(startUrl, { waitUntil: "domcontentloaded" });

if (browserApp) {
  console.log(`Using browser app: ${browserApp}`);
}

console.log("");
console.log(`Login to ${target.toUpperCase()} in the opened browser window.`);
console.log("When the session is fully authenticated, press Enter here.");

const rl = readline.createInterface({ input, output });
await rl.question("");
rl.close();

await context.storageState({ path: absOutputPath });
await browser.close();

console.log(`Saved auth state to ${absOutputPath}`);
