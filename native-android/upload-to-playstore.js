const { chromium } = require('playwright');

async function uploadToPlayStore() {
  console.log('🚀 Starting Play Console upload automation...');

  // Connect to existing Chrome with Antigravity extension
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const contexts = browser.contexts();
  const context = contexts[0];
  const pages = await context.pages();

  // Find the Play Console tab
  let playConsolePage = pages.find(p => p.url().includes('play.google.com/console'));

  if (!playConsolePage) {
    console.log('📱 Opening Play Console...');
    playConsolePage = await context.newPage();
    await playConsolePage.goto('https://play.google.com/console/u/1/developers/8239620436488925047/app/4976249162120849673/tracks/4701359468888052130');
  }

  console.log('⏳ Waiting for page load...');
  await playConsolePage.waitForLoadState('networkidle');

  // Click "Create new release" button
  console.log('🔘 Clicking "Create new release"...');
  await playConsolePage.click('text=Create new release');

  await playConsolePage.waitForTimeout(2000);

  // Upload the AAB file
  console.log('📦 Uploading AAB...');
  const fileInput = await playConsolePage.locator('input[type="file"]').first();
  await fileInput.setInputFiles('/Users/ganapolsky_i/workspace/git/igor/Random-Timer/native-android/app/build/outputs/bundle/release/app-release.aab');

  console.log('⏳ Waiting for upload to complete (this may take a minute)...');
  // Wait for upload success indicator or Save button to become enabled
  await playConsolePage.waitForSelector('button:has-text("Save"):not([disabled])', { timeout: 120000 });

  // Fill in release notes
  console.log('📝 Adding release notes...');
  const releaseNotesInput = await playConsolePage.locator('textarea').first();
  await releaseNotesInput.fill('Initial release\n\n- Random timer functionality\n- Dark glassmorphism UI\n- Settings persistence');

  await playConsolePage.waitForTimeout(2000);

  // Click "Save" button
  console.log('💾 Saving release...');
  await playConsolePage.click('button:has-text("Save"):not([disabled])');

  await playConsolePage.waitForTimeout(3000);

  // Click "Review release" button
  console.log('👀 Reviewing release...');
  await playConsolePage.click('button:has-text("Review release")');

  await playConsolePage.waitForTimeout(2000);

  // Click "Start rollout to Internal testing"
  console.log('🚢 Starting rollout...');
  await playConsolePage.click('button:has-text("Start rollout")');

  console.log('✅ Upload complete!');

  await browser.close();
}

uploadToPlayStore().catch(console.error);
