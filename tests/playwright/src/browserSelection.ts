import { existsSync } from "node:fs";
import { devices } from "@playwright/test";

const explicitBrowserChannel = process.env.PLAYWRIGHT_BROWSER_CHANNEL as
  | "chromium"
  | "chrome"
  | "chrome-beta"
  | "chrome-dev"
  | "chrome-canary"
  | undefined;

export const sharedDesktopBrowser = {
  ...devices["Desktop Chrome"],
  ...(resolveBrowserChannel() ? { channel: resolveBrowserChannel() } : {}),
};

export function resolveBrowserChannel():
  | "chromium"
  | "chrome"
  | "chrome-beta"
  | "chrome-dev"
  | "chrome-canary"
  | undefined {
  if (explicitBrowserChannel) {
    return explicitBrowserChannel;
  }

  if (process.platform !== "darwin") {
    return undefined;
  }

  const candidates = [
    { channel: "chrome", appPath: "/Applications/Google Chrome.app" },
    { channel: "chrome-beta", appPath: "/Applications/Google Chrome Beta.app" },
    { channel: "chrome-dev", appPath: "/Applications/Google Chrome Dev.app" },
    {
      channel: "chrome-canary",
      appPath: "/Applications/Google Chrome Canary.app",
    },
  ] as const;

  return candidates.find((candidate) => existsSync(candidate.appPath))?.channel;
}
