const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const slidesDir = path.resolve(__dirname, 'slides');
const outDir = path.resolve(__dirname, 'rendered');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

const files = fs.readdirSync(slidesDir).filter(f => f.endsWith('.html')).sort();

async function main() {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 960, height: 540 },
    deviceScaleFactor: 3,
  });
  const page = await context.newPage();

  for (const f of files) {
    const url = 'file://' + path.join(slidesDir, f);
    await page.goto(url, { waitUntil: 'load' });
    await page.waitForTimeout(300);
    const outPath = path.join(outDir, f.replace('.html', '.png'));
    await page.screenshot({ path: outPath, fullPage: false, clip: { x: 0, y: 0, width: 960, height: 540 } });
    console.log(`Rendered: ${f}`);
  }
  await browser.close();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
