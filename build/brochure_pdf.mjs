// Renders _brochure/brochure-*.html to PDF (A4 landscape) with Playwright's Chromium.
//   node build/brochure_pdf.mjs            -> every brochure-*.html
//   node build/brochure_pdf.mjs --png      -> also a PNG preview of each page (for review)
import { createRequire } from 'module';
import { readdirSync, mkdirSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath, pathToFileURL } from 'url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dir = join(root, '_brochure');
const png = process.argv.includes('--png');

const browser = await chromium.launch();
for (const f of readdirSync(dir).filter(f => /^brochure-\w+\.html$/.test(f))) {
  const page = await browser.newPage({ viewport: { width: 1123, height: 794 } });
  await page.goto(pathToFileURL(join(dir, f)).href, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const out = join(dir, f.replace('.html', '.pdf'));
  await page.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
  console.log('wrote', out.replace(root + '/', ''));
  if (png) {
    const pdir = join(dir, f.replace('.html', '-png'));
    mkdirSync(pdir, { recursive: true });
    await page.emulateMedia({ media: 'print' });
    const pages = await page.$$('section.page');
    for (let i = 0; i < pages.length; i++)
      await pages[i].screenshot({ path: join(pdir, `${String(i + 1).padStart(2, '0')}.png`) });
  }
  await page.close();
}
await browser.close();
