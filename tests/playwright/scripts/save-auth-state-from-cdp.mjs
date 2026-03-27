import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const outputPath = process.env.OUTPUT_PATH || ".auth/play.json";
const cdpUrl = process.env.CDP_URL || "http://127.0.0.1:9222";

const absOutputPath = path.resolve(outputPath);
fs.mkdirSync(path.dirname(absOutputPath), { recursive: true });

const browser = await chromium.connectOverCDP(cdpUrl);
const context = browser.contexts()[0];

if (!context) {
  console.error(`No browser context found at ${cdpUrl}`);
  process.exit(1);
}

await context.storageState({ path: absOutputPath });
await browser.close();

console.log(`Saved auth state to ${absOutputPath} from ${cdpUrl}`);
