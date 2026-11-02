// Real ffmpeg and browser paths. Each test skips when its tool is not on this machine; the browser
// tests need CHROME_PATH and PLAYWRIGHT_CORE, and they open only pages served from this process.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { join } from 'node:path';
import { test } from 'node:test';
import { SCRIPTS, runScript, workspace } from './helpers.mjs';

const CHROME = process.env.CHROME_PATH;
const DRIVER = process.env.PLAYWRIGHT_CORE;
const noBrowser = CHROME && DRIVER ? false : 'needs CHROME_PATH and PLAYWRIGHT_CORE';
const FFMPEG = process.env.FFMPEG_PATH || 'ffmpeg';
const noFfmpeg = spawnSync(FFMPEG, ['-version']).error ? 'needs ffmpeg' : false;
const BROWSER_ARGS = ['--chrome', CHROME, '--playwright', DRIVER];
const SHORT = ['--viewport', '320x200', '--duration', '400', '--fps', '10'];

const PAGE = `<!doctype html><title>Secret brand page</title><style>
body{margin:0;background:#101010}#box{width:80px;height:80px;background:rgb(12,34,56);font-family:serif;animation:in 300ms ease-out both}
@keyframes in{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}</style><div id="box">Their private headline</div>`;

async function serve(t, handler) {
  const server = createServer(handler);
  await new Promise((resolve) => { server.listen(0, '127.0.0.1', resolve); });
  t.after(() => server.close());
  return `http://127.0.0.1:${server.address().port}`;
}

/** Spawned asynchronously: the server in this process has to keep answering during the capture. */
function capture(args, cwd) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [join(SCRIPTS, 'capture.mjs'), ...BROWSER_ARGS, ...SHORT, ...args], { cwd });
    let stderr = '';
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('close', (status) => resolve({ status, stderr }));
  });
}

test('frames.mjs extracts a local clip through system ffmpeg', { skip: noFfmpeg }, (t) => {
  const root = workspace(t);
  const made = spawnSync(FFMPEG, ['-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc=size=64x48:rate=10:duration=1', '-pix_fmt', 'yuv420p', join(root, 'clip.mp4')], { encoding: 'utf8' });
  assert.equal(made.status, 0, made.stderr);
  const probe = runScript('frames.mjs', ['--in', 'clip.mp4', '--probe', '--ffmpeg', FFMPEG], root);
  assert.equal(JSON.parse(probe.stdout).width, 64);
  const run = runScript('frames.mjs', ['--in', 'clip.mp4', '--out', 'frames', '--rights', 'own', '--fps', '10', '--crop', '0,0,32,24', '--ffmpeg', FFMPEG], root);
  assert.equal(run.status, 0, run.stderr);
  const meta = JSON.parse(readFileSync(join(root, 'frames', 'frames.json'), 'utf8'));
  assert.equal(meta.rights, 'own');
  assert.equal(meta.count, 10);
  assert.equal(readdirSync(join(root, 'frames')).filter((name) => name.endsWith('.png')).length, 10);
  const sheet = runScript('sheet.mjs', ['filmstrip', '--frames', 'frames', '--out', 'sheets'], root);
  assert.equal(sheet.status, 0, sheet.stderr);
});

test('two captures of a page are identical, byte for byte', { skip: noBrowser }, async (t) => {
  const root = workspace(t);
  writeFileSync(join(root, 'page.html'), PAGE);
  for (const out of ['a', 'b']) {
    const run = await capture(['--url', 'page.html', '--out', out, '--rights', 'own', '--track', '#box'], root);
    assert.equal(run.status, 0, run.stderr);
  }
  const names = readdirSync(join(root, 'a', 'frames'));
  assert.equal(names.length, 5);
  for (const name of names) assert.ok(readFileSync(join(root, 'a', 'frames', name)).equals(readFileSync(join(root, 'b', 'frames', name))), name);
  assert.equal(JSON.stringify(JSON.parse(readFileSync(join(root, 'a', 'track.json'))).samples), JSON.stringify(JSON.parse(readFileSync(join(root, 'b', 'track.json'))).samples));
});

test('a third-party capture writes no design data, and our own capture does', { skip: noBrowser }, async (t) => {
  const root = workspace(t);
  const url = await serve(t, (_, response) => { response.setHeader('content-type', 'text/html'); response.end(PAGE); });
  const own = await capture(['--url', url, '--out', 'own', '--rights', 'own', '--selector', '#box'], root);
  assert.equal(own.status, 0, own.stderr);
  assert.match(readFileSync(join(root, 'own', 'inspect.json'), 'utf8'), /Their private headline/);
  const other = await capture(['--url', url, '--out', 'other', '--rights', 'third-party', '--selector', '#box'], root);
  assert.equal(other.status, 0, other.stderr);
  const written = readFileSync(join(root, 'other', 'inspect.json'), 'utf8');
  for (const leak of ['Their private headline', 'serif', 'rgb(12', 'Secret brand', '#box']) assert.ok(!written.includes(leak), leak);
  const record = JSON.parse(written);
  assert.equal(record.animations[0].timing.duration, 300);
  assert.equal(record.animations[0].keyframes[0].transform, 'translateY(20px)');
});

test('a click trigger starts the motion at t = 0 of the track', { skip: noBrowser }, async (t) => {
  const root = workspace(t);
  writeFileSync(join(root, 'page.html'), `<!doctype html><style>#b{width:40px;height:40px;background:#39c;transition:transform 200ms linear}#b.on{transform:translateX(40px)}</style><div id="b" onclick="this.classList.add('on')"></div>`);
  const run = await capture(['--url', 'page.html', '--out', 'c', '--rights', 'own', '--trigger', 'click', '--target', '#b', '--track', '#b'], root);
  assert.equal(run.status, 0, run.stderr);
  const { samples } = JSON.parse(readFileSync(join(root, 'c', 'track.json')));
  const moved = samples.find((sample) => sample.els['#b'].transform !== 'none');
  assert.ok(samples[0].t < 0, 'pre-roll samples sit before the trigger');
  assert.ok(moved.t >= 0 && moved.t < 50, `first motion at ${moved.t}`);
  assert.equal(JSON.parse(readFileSync(join(root, 'c', 'frames.json'))).triggerFrame, 2);
});

test('a page that answers 403 stops the run at exit 3 and writes no finished capture', { skip: noBrowser }, async (t) => {
  const root = workspace(t);
  const url = await serve(t, (_, response) => { response.statusCode = 403; response.end('no'); });
  const run = await capture(['--url', url, '--out', 'walled', '--rights', 'third-party'], root);
  assert.equal(run.status, 3);
  assert.match(run.stderr, /HTTP 403.*screen recording/);
  assert.ok(!readdirSync(join(root, 'walled')).includes('capture.json'));
});

test('a sign-in redirect on the same site stops a third-party capture at exit 3', { skip: noBrowser }, async (t) => {
  const root = workspace(t);
  const url = await serve(t, (request, response) => {
    if (request.url === '/protected') { response.statusCode = 302; response.setHeader('location', '/login'); response.end(); return; }
    response.setHeader('content-type', 'text/html'); response.end('<title>Sign in</title><p>Welcome</p>');
  });
  const run = await capture(['--url', `${url}/protected`, '--out', 'walled', '--rights', 'third-party'], root);
  assert.equal(run.status, 3, run.stderr);
  assert.match(run.stderr, /moved to \/login/);
});

test('a visible password field stops a third-party capture, and our own page may have one', { skip: noBrowser }, async (t) => {
  const root = workspace(t);
  const url = await serve(t, (_, response) => { response.setHeader('content-type', 'text/html'); response.end('<form><input type="password"></form>'); });
  const walled = await capture(['--url', url, '--out', 'walled', '--rights', 'third-party'], root);
  assert.equal(walled.status, 3, walled.stderr);
  assert.match(walled.stderr, /password field/);
  const own = await capture(['--url', url, '--out', 'mine', '--rights', 'own'], root);
  assert.equal(own.status, 0, own.stderr);
});

test('a redirect to another site stops the run at exit 3', { skip: noBrowser }, async (t) => {
  const root = workspace(t);
  const signIn = await serve(t, (_, response) => { response.setHeader('content-type', 'text/html'); response.end('<title>Sign in</title>'); });
  const url = await serve(t, (_, response) => { response.statusCode = 302; response.setHeader('location', `${signIn}/login`); response.end(); });
  const run = await capture(['--url', url, '--out', 'moved', '--rights', 'third-party'], root);
  assert.equal(run.status, 3, run.stderr);
  assert.match(run.stderr, /sign-in redirect stays closed/);
});

test('a script that sends the page to another site does not get there', { skip: noBrowser }, async (t) => {
  const root = workspace(t);
  let reached = false;
  const signIn = await serve(t, (_, response) => { reached = true; response.end('x'); });
  const url = await serve(t, (_, response) => { response.setHeader('content-type', 'text/html'); response.end(`<script>setTimeout(()=>location.href=${JSON.stringify(signIn)},50)</script>`); });
  await capture(['--url', url, '--out', 'moved', '--rights', 'third-party'], root);
  assert.equal(reached, false);
});
