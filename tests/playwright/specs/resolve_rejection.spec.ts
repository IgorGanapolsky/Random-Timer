import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test('Resolve App Store Rejection and Submit', async ({ page }) => {
  const appId = '6758355312';
  const url = `https://appstoreconnect.apple.com/apps/${appId}/appstore/ios/version/opin`;

  console.log(`Navigating to ${url}...`);
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });

  // Wait for the main content to appear, bypassing the spinner
  try {
    await page.waitForSelector('.app-store-version-page', { timeout: 30000 });
  } catch (e) {
    console.log('Main content selector not found, taking screenshot of current state...');
  }

  await page.screenshot({ path: 'asc_state_loaded.png' });

  // Look for "Resolution Center" or "Unresolved Issues" link
  const resolutionCenter = page.locator('text=Resolution Center');
  if (await resolutionCenter.isVisible()) {
    console.log('Resolution Center found. Clicking...');
    await resolutionCenter.click();
    await page.waitForTimeout(5000);
    await page.screenshot({ path: 'resolution_center.png' });
    
    // Try to find a "Reply" or "Submit" button inside the resolution center
    const submitBtn = page.locator('button:has-text("Submit")');
    if (await submitBtn.isVisible()) {
        console.log('Submit button found in Resolution Center. Clicking...');
        await submitBtn.click();
        await page.waitForTimeout(5000);
    }
  }

  // Go back to version page
  await page.goto(url);
  await page.waitForTimeout(5000);

  // Try to click the main "Submit for Review" button
  const mainSubmitBtn = page.locator('button:has-text("Submit for Review")');
  if (await mainSubmitBtn.isVisible()) {
    console.log('Main Submit for Review button found. Clicking...');
    await mainSubmitBtn.click();
    await page.waitForTimeout(5000);
    await page.screenshot({ path: 'submit_final.png' });
  } else {
    console.log('Submit for Review button not found or already submitted.');
  }
});
