// Optional actual-browser regression using existing runtimes only. Owned fixtures retained.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, realpath } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
test('spatial settings, part identity, time, annotation, disk reopen and stale refusal', { skip: process.env.REVIEW_BROWSER_TESTS !== '1', timeout: 90000 }, async () => {
  const { chromium } = await import(process.env.REVIEW_PLAYWRIGHT || 'playwright');
  const root = await realpath(await mkdtemp(join(tmpdir(), 'spatial-review-browser-'))), pkg = join(root, 'package');
  const python = process.env.REVIEW_PYTHON || 'python3';
  execFileSync(python, [resolve('skills/orbyn-ui-design/examples/spatial-review/prepare.py'), '--destination', pkg, '--node', process.execPath]);
  let child, browser, log = '';
  const start = async () => {
    child = spawn(python, [join(pkg, 'serve.py'), '--package', pkg], { stdio: ['ignore', 'pipe', 'pipe'] });
    return await new Promise((res, rej) => { const timer = setTimeout(() => rej(Error('Server timeout')), 10000); child.stdout.on('data', b => { log += b; const match = String(b).match(/http:\/\/127\.0\.0\.1:\d+\//); if (match) { clearTimeout(timer); res(match[0]); } }); child.stderr.on('data', b => { log += b; }); child.once('exit', code => { clearTimeout(timer); rej(Error('Server exited ' + code)); }); });
  };
  const stop = async () => { if (child?.exitCode === null) { child.kill('SIGTERM'); await new Promise((res, rej) => { const timer = setTimeout(() => rej(Error('Owned server did not settle')), 5000); child.once('exit', () => { clearTimeout(timer); res(); }); }); } };
  try {
    let url = await start(); browser = await chromium.launch({ headless: true, ...(process.env.REVIEW_CHROME ? { executablePath: process.env.REVIEW_CHROME } : {}) });
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const ready = async () => { await page.goto(url); await page.locator('body[data-review-ready=true]').waitFor(); };
    const save = async () => { await page.locator('#review-save').click(); await page.waitForFunction(() => document.getElementById('review-status').textContent.includes('saved to repo and reread')); };
    const range = async (id, value) => { await page.locator('#' + id).evaluate((n,v) => { n.value = v; n.dispatchEvent(new Event('input', { bubbles: true })); n.dispatchEvent(new Event('change', { bubbles: true })); }, String(value)); };
    await ready(); assert.equal(await page.locator('#speed').inputValue(), '0.5'); await save();
    let saved = JSON.parse(await readFile(join(pkg, 'review.json'))); assert.equal(saved.review.comments.length, 0);
    for (const rate of ['0.25', '1', '0.5']) { await page.locator('#speed').selectOption(rate); await save(); await page.reload(); await page.locator('body[data-review-ready=true]').waitFor(); assert.equal(await page.locator('#speed').inputValue(), rate); }
    saved = JSON.parse(await readFile(join(pkg, 'review.json')));
    await page.evaluate(d => { d.state = 'draft'; d.pending = { targetId: 'part/piston-A1', context: structuredClone(d.settings), text: 'Pending browser note survives server reopen' }; localStorage.setItem('spatial-review-v2', JSON.stringify(d)); }, structuredClone(saved.review));
    await page.reload(); await page.locator('body[data-review-ready=true]').waitFor();
    assert.equal(await page.locator('#review-recovery').isVisible(), true);
    const recoveryDownload = page.waitForEvent('download'); await page.locator('#review-recovery').click(); const recoveryFile = await recoveryDownload; await recoveryFile.saveAs(join(root, 'pending-recovery.json'));
    assert.equal(JSON.parse(await readFile(join(root, 'pending-recovery.json'))).pending.text, 'Pending browser note survives server reopen');
    await page.evaluate(() => localStorage.removeItem('spatial-review-v2')); await page.reload(); await page.locator('body[data-review-ready=true]').waitFor();
    await page.locator('#story-scenario').selectOption('film'); await range('story-time', 8.25); const title = await page.locator('#film-title').innerText();
    await range('story-time', 1); await range('story-time', 8.25); assert.equal(await page.locator('#film-title').innerText(), title); assert.equal(title, 'MOVEMENT WITH MEANING');
    await page.locator('#story-play').click();
    await range('orbit', 60);
    await page.evaluate(async () => { for (let i = 0; i < 5; i++) await new Promise(requestAnimationFrame); });
    assert.equal(await page.locator('#orbit').inputValue(), '60'); assert.equal(await page.locator('#story-play').innerText(), 'Play story');
    await page.locator('#story-play').click(); await page.locator('#stage').scrollIntoViewIfNeeded(); const box = await page.locator('#stage').boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2); await page.mouse.down(); await page.mouse.move(box.x + box.width / 2 + 40, box.y + box.height / 2, { steps: 4 }); await page.mouse.up();
    const manualYaw = await page.locator('#orbit').inputValue(); await page.evaluate(async () => { for (let i = 0; i < 5; i++) await new Promise(requestAnimationFrame); });
    assert.equal(await page.locator('#orbit').inputValue(), manualYaw); assert.equal(await page.locator('#story-play').innerText(), 'Play story');
    await range('story-time', 8.25); await range('orbit', 60); await page.locator('#guides').uncheck();
    await page.locator('#review-mode').click(); const selected = await page.locator('#selected-id').innerText(); await page.locator('#cylinder-B3').click();
    assert.equal(await page.locator('#selected-id').innerText(), selected); assert.equal(await page.locator('#review-target').inputValue(), 'control/cylinder-B3');
    await page.locator('#review-text').fill('Repeated button feedback'); await page.locator('#review-post').click();
    await page.locator('#review-target').selectOption('part/flywheel'); await page.locator('#review-text').fill('<img src=x onerror="window.injected=true"> Inspect flywheel here'); await page.locator('#review-post').click();
    assert.equal(await page.locator('#review-comments img').count(), 0); assert.equal(await page.evaluate(() => window.injected), undefined);
    await save(); saved = JSON.parse(await readFile(join(pkg, 'review.json'))); assert.equal(saved.review.settings.partId, 'flywheel'); assert.equal(saved.review.comments[1].context.camera.yaw, 60);
    await stop(); url = await start(); await ready(); assert.equal(await page.locator('#review-comments>li').count(), 2); assert.equal(await page.locator('#orbit').inputValue(), '60'); assert.equal(await page.locator('#guides').isChecked(), false);
    assert.equal(await page.locator('#stage [data-name=flywheel]').getAttribute('data-review-active'), 'true'); assert.equal(await page.locator('#play').innerText(), 'Play mechanism');
    await range('orbit', -60); await page.locator('#review-comments>li').nth(1).getByRole('button').click(); await page.waitForFunction(() => document.getElementById('orbit').value === '60'); assert.equal(await page.locator('#orbit').inputValue(), '60');
    await page.locator('#review-import').setInputFiles({ name: 'bad.json', mimeType: 'application/json', buffer: Buffer.from('{"schemaVersion":2,"schemaVersion":2}') }); await page.waitForFunction(() => document.getElementById('review-status').textContent.includes('Import rejected')); assert.equal(await page.locator('#review-comments>li').count(), 2);
    await page.locator('#story-scenario').selectOption('gallery'); await range('story-time', 26.5); assert.equal(await page.locator('#film-stage').getAttribute('data-primitive'), 'logo'); await page.locator('#film-primitive img').evaluate(n => n.decode());
    await save(); const gallerySaved=JSON.parse(await readFile(join(pkg,'review.json'))); assert.equal(gallerySaved.review.settings.animation.scenario,'gallery'); assert.equal(gallerySaved.review.settings.animation.time,26.5); assert.equal(gallerySaved.review.settings.filmRevision, JSON.parse(await readFile(join(pkg,'manifest.json'))).assets['film-gallery.json']);
    await page.emulateMedia({ reducedMotion: 'reduce' }); await page.locator('#story-play').click(); assert.equal(await page.locator('#story-play').innerText(), 'Play story');
    await page.locator('#review-finish').click(); await page.waitForFunction(() => document.getElementById('review-status').textContent.includes('Submitted review saved'));
    saved = JSON.parse(await readFile(join(pkg, 'review.json'))); assert.equal(saved.review.state, 'submitted');
    await page.setViewportSize({ width: 390, height: 844 }); const overflow = await page.evaluate(() => [...document.querySelectorAll('body *')].map(n => ({ tag: n.tagName, id: n.id, cls: typeof n.className === 'string' ? n.className : '', right: n.getBoundingClientRect().right, width: n.getBoundingClientRect().width })).filter(n => n.right > innerWidth + 1));
    await writeFile(join(root, 'narrow-overflow.json'), JSON.stringify(overflow, null, 2));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, JSON.stringify(overflow.slice(0, 12)));
    if (process.env.REVIEW_CAPTURE === '1') await page.screenshot({ path: join(root, 'narrow.png'), fullPage: true });
    await writeFile(join(pkg, 'style.css'), (await readFile(join(pkg, 'style.css'))) + '\n/* changed source */'); await page.locator('#review-comments>li').nth(1).getByRole('button').click(); await page.waitForFunction(() => document.getElementById('review-status').textContent.includes('unavailable'));
    await writeFile(join(root, 'result.json'), JSON.stringify({ passed: true, browser: browser.version(), sourceFingerprint: saved.review.prototype.fingerprint, modelRevision: saved.review.settings.modelRevision, revision: saved.revision, restartReadback: true, limits: ['synthetic SVG/browser only', 'no audio/video encode/native/full accessibility/live agent qualification'] }, null, 2));
    console.log('Owned browser evidence retained: ' + root);
  } catch (error) { await writeFile(join(root, 'failure.txt'), String(error)); console.log('Failed attempt retained: ' + root); throw error; }
  finally { await browser?.close(); await stop(); await writeFile(join(root, 'server.log'), log); }
});
