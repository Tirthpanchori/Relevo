import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
const out = new URL('../../.impeccable/review/', import.meta.url);
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const findings = [];
for (const [device, viewport] of [['desktop', { width: 1440, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
  const page = await browser.newPage({ viewport, reducedMotion: 'reduce' });
  for (const [name, route] of [['home', ''], ['engine', 'engine/#replay'], ['results', 'results/'], ['docs', 'docs/'], ['about', 'about/'], ['privacy', 'privacy/']]) {
    await page.goto(`http://127.0.0.1:4173/Relevo/${route}`);
    await page.locator('main h1').waitFor();
    await page.evaluate(() => document.fonts.ready);
    if (name === 'engine') await page.locator('.event-timeline').waitFor();
    if (name === 'results') await page.locator('table').waitFor();
    await page.screenshot({ path: fileURLToPath(new URL(`${device}${name === 'home' ? '' : `-${name}`}.png`, out)), fullPage: true });
    if (name === 'home') await page.screenshot({ path: fileURLToPath(new URL(`${device}-viewport.png`, out)) });
    findings.push({ device, route, ...await page.evaluate(() => ({ width: innerWidth, scrollWidth: document.documentElement.scrollWidth, fonts: document.fonts.status, h1Size: getComputedStyle(document.querySelector('h1')).fontSize, displayFont: getComputedStyle(document.querySelector('h1')).fontFamily })) });
  }
  await page.close();
}
await writeFile(new URL('capture.json', out), JSON.stringify({ capturedAt: new Date().toISOString(), findings }, null, 2));
await browser.close();
console.log('Captured six pages at desktop/mobile, plus both home viewports.');
