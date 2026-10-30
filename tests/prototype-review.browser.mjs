// Optional actual-browser regression; no dependency/browser installation or product account.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, cp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawn } from 'node:child_process';
const enabled = process.env.REVIEW_BROWSER_TESTS === '1';
test('live review: normal/annotation, page/control feedback, recovery and durable finish', { skip: !enabled, timeout: 60000 }, async () => {
  const { chromium } = await import(process.env.REVIEW_PLAYWRIGHT || 'playwright');
  const root = await mkdtemp(join(tmpdir(), 'review-browser-')), pkg = join(root, 'package');
  const source = new URL('../skills/orbyn-ui-design/examples/review-workspace/', import.meta.url);
  await cp(source, pkg, { recursive: true });
  const child = spawn(process.env.REVIEW_PYTHON || 'python3', [join(pkg, 'serve.py'), '--package', pkg], { stdio: ['ignore', 'pipe', 'pipe'] });
  let output = '', browser;
  try {
    const url = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(Error('Owned server startup timeout')), 10000);
      child.stdout.on('data', chunk => { output += chunk; const match = output.match(/http:\/\/127\.0\.0\.1:\d+\//); if (match) { clearTimeout(timer); resolve(match[0]); } });
      child.stderr.on('data', chunk => { output += chunk; });
      child.once('exit', code => { clearTimeout(timer); reject(Error(`Server exited ${code}`)); });
    });
    browser = await chromium.launch({ headless: true, ...(process.env.REVIEW_CHROME ? { executablePath: process.env.REVIEW_CHROME } : {}) });
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.goto(url); await page.locator('body[data-review-ready=true]').waitFor();
    await page.locator('[data-review-target="work/beta/open"]').click();
    assert.match(await page.locator('#action-result').innerText(), /Research brief/);
    await page.getByRole('button', { name: 'Comment mode', exact: true }).click();
    await page.locator('[data-review-target="work/alpha/open"]').click();
    assert.match(await page.locator('#action-result').innerText(), /Research brief/); // Annotation did not open alpha.
    await page.locator('#comment').fill('<img src=x onerror="window.reviewInjected=true"> Clearer label please');
    await page.locator('#post').click();
    assert.equal(await page.locator('#pins .pin').count(), 1);
    const pinRect = await page.locator('#pins .pin').boundingBox();
    const controlRect = await page.locator('[data-review-target="work/alpha/open"]').boundingBox();
    assert.ok(pinRect.y + pinRect.height <= controlRect.y || pinRect.x >= controlRect.x + controlRect.width || pinRect.x + pinRect.width <= controlRect.x);

    assert.equal(await page.locator('#comments img').count(), 0);
    assert.equal(await page.evaluate(() => window.reviewInjected), undefined);
    await page.getByRole('button', { name: '02 · Preferences', exact: true }).click();
    await page.locator('#target').selectOption('settings/theme');
    await page.locator('#comment').fill('Keep the existing theme options.'); await page.locator('#post').click();
    await page.getByRole('button', { name: 'Comment mode on', exact: true }).click();
    assert.equal(await page.locator('#pins .pin').count(), 0);
    await page.locator('#theme').selectOption('dark');
    await page.locator('#save').click();
    await page.waitForFunction(() => document.getElementById('status').textContent.includes('Draft saved to package'));
    await page.reload(); await page.locator('body[data-review-ready=true]').waitFor();
    assert.equal(await page.locator('#comment-count').innerText(), '2');
    assert.equal(await page.locator('#theme').inputValue(), 'dark');
    await page.locator('#import').setInputFiles({ name: 'bad.json', mimeType: 'application/json', buffer: Buffer.from('{"unexpected":true}') });
    await page.waitForFunction(() => document.getElementById('status').textContent.includes('Import rejected'));
    assert.equal(await page.locator('#comment-count').innerText(), '2');
    await page.getByRole('button', { name: '01 · Work queue', exact: true }).click();
    await page.locator('#target').selectOption('work/alpha/open'); await page.locator('#comment').fill('Pending text stays on Alpha.');
    await page.locator('#target').selectOption('work/beta/open');
    assert.equal(await page.locator('#target').inputValue(), 'work/alpha/open');
    await page.locator('#finish').click();
    assert.match(await page.locator('#status').innerText(), /Post pending/);
    await page.locator('#post').click(); await page.locator('#finish').click();
    await page.waitForFunction(() => document.getElementById('status').textContent.includes('Review submitted and saved'));
    const saved = JSON.parse(await readFile(join(pkg, 'review.json'), 'utf8'));
    assert.equal(saved.review.state, 'submitted'); assert.equal(saved.review.comments.length, 3);
    assert.equal(saved.review.comments[0].targetId, 'work/alpha/open'); assert.equal(saved.review.comments[1].targetId, 'settings/theme');
    assert.equal(saved.review.settings.theme, 'dark');
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
    // Retain candidate images for review; no fabricated/automatically accepted baseline.
    if (process.env.REVIEW_CAPTURE === '1') await page.screenshot({ path: join(root, 'review-narrow.png'), fullPage: true });
    await writeFile(join(root, 'result.json'), JSON.stringify({ result: 'passed', browser: browser.version(), sourceFingerprint: saved.review.prototype.fingerprint, state: saved.review.state, reviewRevision: saved.revision, limits: ['synthetic HTML browser only', 'no native or complete accessibility/user-study qualification', 'candidate image is not approved baseline'] }, null, 2));
    console.log(`Retained owned browser fixture/evidence: ${root}`);
  } catch (error) {
    await writeFile(join(root, 'failure.txt'), String(error)); console.log(`Failed attempt retained: ${root}`); throw error;
  } finally {
    if (browser) await browser.close();
    if (child.exitCode === null) {
      child.kill('SIGTERM');
      await new Promise(resolve => { child.once('exit', resolve); setTimeout(resolve, 3000); });
    }
    await writeFile(join(root, 'server.log'), output);
  }
});
