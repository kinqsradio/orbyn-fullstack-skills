// Opt-in rendered checks for static teaching fixtures. Set REVIEW_BROWSER_TESTS=1 and
// REVIEW_PLAYWRIGHT/REVIEW_CHROME to existing tools; nothing is installed here.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdtemp, rm, realpath } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const enabled = process.env.REVIEW_BROWSER_TESTS === '1';
const skills = fileURLToPath(new URL('../skills/', import.meta.url));
const types = { '.html': 'text/html', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };

async function serve(t, root) {
  const server = createServer(async (request, response) => {
    const path = normalize(decodeURIComponent(new URL(request.url, 'http://x').pathname));
    try { const body = await readFile(join(root, path)); response.writeHead(200, { 'Content-Type': types[extname(path)] ?? 'application/octet-stream' }); response.end(body); }
    catch { response.writeHead(404); response.end(); }
  });
  // Register each resource immediately; a later acquisition/close failure must
  // not prevent independent cleanup hooks from releasing the other resources.
  t.after(async () => {
    server.closeAllConnections();
    if (server.listening) await new Promise((done, reject) => server.close(error => error ? reject(error) : done()));
  });
  await new Promise((done, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', done);
  });
  return { url: `http://127.0.0.1:${server.address().port}/` };
}
async function launch() {
  const { chromium } = await import(process.env.REVIEW_PLAYWRIGHT || 'playwright');
  return chromium.launch({ headless: true, ...(process.env.REVIEW_CHROME ? { executablePath: process.env.REVIEW_CHROME } : {}) });
}
const focused = page => page.evaluate(() => document.activeElement.id || document.activeElement.tagName);
const settled = page => page.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))));

test('static fixtures keep keyboard focus, line breaks and phone-width layout', { skip: !enabled, timeout: 90000 }, async t => {
  const site = await serve(t, skills);
  const browser = await launch();
  t.after(() => browser.close());
  const page = await browser.newPage({ viewport: { width: 320, height: 800 } });

  await page.goto(site.url + 'orbyn-ui-design/examples/assistant-chat/index.html');
  await page.locator('#draft').fill('line one\nline two'); await page.locator('#send').click();
  await page.locator('[data-outcome=sent]').focus(); await page.keyboard.press('Enter'); await settled(page);
  assert.equal(await focused(page), 'draft', 'Acknowledge disables itself; focus must not fall to the page');
  const message = page.locator('#transcript article p').last();
  assert.match(await message.evaluate(n => getComputedStyle(n).whiteSpace), /pre/, 'Shift+Enter line breaks must render');
  await page.locator('#attach').focus(); for (let i = 0; i < 3; i++) await page.keyboard.press('Enter'); await settled(page);
  assert.equal(await focused(page), 'draft', 'Attachment limit disables the add button');

  await page.goto(site.url + 'orbyn-ui-design/examples/focus-session/preview.html');
  await page.locator('#submit').focus(); await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.getElementById('feedback').textContent.includes('added'));
  await settled(page);
  assert.equal(await focused(page), 'submit', 'Busy state must not strand keyboard focus');
  await page.locator('#reset').evaluate(n => { n.closest('details').open = true; n.click(); });
  assert.equal(await page.locator('#feedback').evaluate(n => getComputedStyle(n).display !== 'none'), true, 'A status region must exist before its message arrives');
  assert.deepEqual(await page.locator('#feedback').evaluate(n => [n.hidden, n.getBoundingClientRect().height]), [false, 0], 'An idle status region stays invisible');

  await page.goto(site.url + 'orbyn-ai-application/examples/project-plan-stream/index.html');
  assert.equal(await page.locator('main h1').count(), 1, 'Fixture content needs a main landmark');
  assert.equal(await page.locator('.eyebrow').evaluate(n => n.getBoundingClientRect().left), 16, 'Phone gutter');
  await page.locator('#start').click();
  await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('Fixture delivered'));
  await page.locator('#accept').focus(); await page.keyboard.press('Enter'); await settled(page);
  assert.equal(await focused(page), 'status', 'The decision result receives focus once its button is disabled');

});

test('spatial package fits a 320px phone with 16px gutters and reports failed geometry', { skip: !enabled, timeout: 90000 }, async t => {
  const temporary = await mkdtemp(join(tmpdir(), 'ui-fixture-spatial-'));
  t.after(() => rm(temporary, { recursive: true, force: true }));
  const root = await realpath(temporary);
  const pkg = join(root, 'package');
  execFileSync(process.env.REVIEW_PYTHON || 'python3', [resolve('skills/orbyn-ui-design/examples/spatial-review/prepare.py'), '--destination', pkg, '--node', process.execPath]);
  const site = await serve(t, pkg);
  const browser = await launch();
  t.after(() => browser.close());
  const page = await browser.newPage({ viewport: { width: 320, height: 800 } });
  await page.goto(site.url + 'index.html'); await page.locator('body[data-review-ready=true]').waitFor();
  assert.deepEqual(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth), 0, 'No horizontal page scroll');
  assert.equal(await page.locator('.intro').evaluate(n => n.getBoundingClientRect().left), 16, 'Phone gutter');
  assert.equal(await page.locator('#review-text').isDisabled(), true, 'Text typed before choosing a target would be erased by the next render');
  await page.locator('#review-target').selectOption({ index: 1 });
  assert.equal(await page.locator('#review-text').isDisabled(), false);

  const failed = await browser.newPage(); await failed.route('**/engine-data.json', route => route.fulfill({ status: 500, body: 'unavailable' }));
  await failed.goto(site.url + 'index.html');
  await failed.waitForFunction(() => /unavailable/i.test(document.getElementById('render-state').textContent), null, { timeout: 5000 });
  assert.match(await failed.locator('#review-status').innerText(), /unavailable/i);
  assert.match(await failed.locator('#review-summary').innerText(), /unavailable/i);

});
