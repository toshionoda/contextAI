const { chromium } = require('playwright');
const path = require('path');

const targets = [
  {
    name: '06a_arerio',
    url: 'https://www.agencysoft.co.jp/bridge/',
    description: 'アレリオ橋梁点検',
  },
  {
    name: '06b_roadmanager',
    url: 'https://urbanx-tech.com/services',
    description: 'RoadManager (UrbanX)',
  },
  {
    name: '06c_hibimikke',
    url: 'https://www.fujifilm.com/jp/ja/business/inspection/infraservice/hibimikke/features',
    description: 'ひびみっけ (富士フイルム)',
  },
  {
    name: '06d_nitaco',
    url: 'https://tsukunobi.com/',
    description: 'NITACO 施工計画書AI',
  },
  {
    name: '06e_cheez',
    url: 'https://cheez.ai/',
    description: 'Cheez 工事写真台帳AI',
  },
  {
    name: '06f_genbaplus',
    url: 'https://archi.fukuicompu.co.jp/products/genba/',
    description: '現場Plus',
  },
  {
    name: '06g_sitebox',
    url: 'https://www.kentem.jp/product-service/sitebox/',
    description: 'SiteBox (KENTEM)',
  },
  {
    name: '06h_modely',
    url: 'https://modely.datalabs.jp/',
    description: 'Modely 3D配筋検査 (DataLabs)',
  },
];

const outDir = path.resolve(__dirname, 'slides/captures');

async function capture(target, browser) {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    locale: 'ja-JP',
  });
  const page = await context.newPage();
  try {
    console.log(`Capturing: ${target.description} (${target.url})`);
    await page.goto(target.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    // Wait for content to render
    await page.waitForTimeout(3000);
    // Dismiss cookie banners etc
    try {
      const acceptBtns = await page.$$('button');
      for (const btn of acceptBtns) {
        const text = await btn.textContent();
        if (text && (text.includes('同意') || text.includes('Accept') || text.includes('OK') || text.includes('閉じる'))) {
          await btn.click();
          await page.waitForTimeout(500);
          break;
        }
      }
    } catch (e) {}

    const outPath = path.join(outDir, `${target.name}.png`);
    await page.screenshot({ path: outPath, fullPage: false });
    console.log(`  -> Saved: ${outPath}`);
  } catch (err) {
    console.error(`  -> ERROR (${target.description}): ${err.message}`);
  } finally {
    await context.close();
  }
}

async function main() {
  const browser = await chromium.launch({ channel: 'chrome' });

  // Run captures in batches of 4 to avoid overwhelming
  for (let i = 0; i < targets.length; i += 4) {
    const batch = targets.slice(i, i + 4);
    await Promise.all(batch.map(t => capture(t, browser)));
  }

  await browser.close();
  console.log('\nDone. All captures saved to slides/captures/');
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
