// Visual check: screenshots of every page at phone and desktop widths.
// Requires the server running on PORT (default 3000). Output: ../screenshots-out/ (untracked).
import { chromium } from 'playwright';
import fs from 'node:fs';
const base = process.env.BASE_URL || 'http://localhost:3000';
const out = process.env.OUT || '/tmp/claude-0/-home-user-random-proj/f34305d2-2a92-5feb-a3bc-43161fa6f1a6/scratchpad/shots';
fs.mkdirSync(out, { recursive: true });
const pages = ['/', '/about', '/services', '/membership', '/faq', '/schedule', '/contact'];
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
for (const [label, vp] of [['phone', { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true }], ['desktop', { width: 1280, height: 800 }]]) {
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.deviceScaleFactor || 1, isMobile: !!vp.isMobile, hasTouch: !!vp.hasTouch });
  const page = await ctx.newPage();
  for (const p of pages) {
    await page.goto(base + p, { waitUntil: 'networkidle' });
    // scroll through so lazy images load, then back to top
    await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } window.scrollTo(0, 0); });
    // force every lazy image to load and decode before capture
    await page.evaluate(async () => { const imgs = [...document.images]; imgs.forEach(i => { i.loading = 'eager'; }); await Promise.all(imgs.map(i => i.complete ? i.decode().catch(() => {}) : new Promise(r => { i.onload = i.onerror = r; }))); });
    await page.waitForTimeout(200);
    const file = `${out}/${label}${p === '/' ? '-home' : p.replace(/\//g, '-')}.png`;
    await page.screenshot({ path: file, fullPage: true });
    console.log(file);
  }
  await ctx.close();
}
await browser.close();
