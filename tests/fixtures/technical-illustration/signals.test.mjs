import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { once } from 'node:events';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const support = join(root, 'skills/technical-illustration/references/upstream/anatomy');
const parent = process.env.ILLUSTRATION_PROOF_DIR ?? tmpdir();
await mkdir(parent, { recursive: true });
const directory = await mkdtemp(join(parent, 'signal-controls-'));
const delay = ms => new Promise(done => setTimeout(done, ms));
for (const signal of ['SIGINT', 'SIGTERM']) for (const kind of ['capture', 'drive', 'turn-check', 'print', 'print-pdf', 'lines']) {
  test(`${signal} joins only its owned ${kind} browser during pending endpoint request`, async () => {
    const marker = join(directory, `${kind}-${signal}.json`);
    const fake = join(directory, `fake-${kind}-${signal}`);
    const server = createServer((_req, _res) => {});
    await new Promise(done => server.listen(0, '127.0.0.1', done));
    const port = server.address().port;
    await writeFile(fake, `#!${process.execPath}\nconst fs=require('node:fs');fs.writeFileSync(${JSON.stringify(marker)},JSON.stringify({pid:process.pid,profile:process.argv.find(x=>x.startsWith('--user-data-dir=')).slice(16)}));console.error('DevTools listening on ws://127.0.0.1:${port}/devtools/browser/owned');setInterval(()=>{},1000);\n`, { mode: 0o700 });
    const page = join(directory, 'page.html');
    const sheet = join(directory, `sheet-${signal}.mjs`);
    await writeFile(sheet, 'export default '+JSON.stringify({ page, settle: 0, parts: [], main: { view: 'rest' }, views: { rest: {} } })+';');
    const args = kind === 'print-pdf' ? ['--input-type=module', '-e', `import{printPdf}from ${JSON.stringify(new URL('file://'+join(support,'scripts/print.mjs')).href)};await printPdf(${JSON.stringify(page)},${JSON.stringify(join(directory,'result-'+signal+'.pdf'))});`] : [join(support, 'scripts', `${kind}.mjs`), kind === 'print' ? sheet : page, ...(kind === 'drive' ? ['[]'] : [])];
    await writeFile(join(directory, 'page.html'), '<p>Owned fixture</p>');
    const child = spawn(process.execPath, args, { env: { ...process.env, CHROME_PATH: fake }, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '';
    child.stdout.on('data', part => stdout += part); child.stderr.on('data', part => stderr += part);
    const terminal = once(child, 'exit');
    let browser;
    try {
      const deadline = Date.now() + 3000;
      while (!existsSync(marker) && Date.now() < deadline) await delay(10);
      browser = JSON.parse(await readFile(marker, 'utf8'));
      await delay(80); // Child is alive and the endpoint is intentionally pending.
      process.kill(browser.pid, 0);
      child.kill(signal);
      const timeout = setTimeout(() => child.kill('SIGKILL'), 8000);
      const [code, exitSignal] = await terminal; clearTimeout(timeout);
      assert.equal(exitSignal, null, stderr);
      assert.equal(code, signal === 'SIGINT' ? 130 : 143, stderr);
      assert.throws(() => process.kill(browser.pid, 0), error => error.code === 'ESRCH');
      assert.equal(existsSync(browser.profile), kind === 'print-pdf');
      if (kind === 'print-pdf') assert.match(stderr, /Retained owned output directory/);
      await writeFile(join(directory, `${kind}-${signal}-result.json`), JSON.stringify({ signal, code, exitSignal, browser, stdout, stderr, owned_child_terminated: true, owned_profile_removed: !existsSync(browser.profile), retained_output_profile: kind === 'print-pdf' }, null, 2));
    } finally {
      if (child.exitCode === null && child.signalCode === null) child.kill('SIGTERM');
      if (browser) {
        // On failure, verify the exact owned fake executable identity before cleanup.
        try {
          const command = execFileSync('ps', ['-p', String(browser.pid), '-o', 'command='], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
          if (command.includes(fake)) process.kill(browser.pid, 'SIGTERM');
        } catch {}
      }
      server.closeAllConnections(); await new Promise(done => server.close(done));
    }
  });
}
