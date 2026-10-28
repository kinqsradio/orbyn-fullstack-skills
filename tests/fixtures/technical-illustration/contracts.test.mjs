import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { promisify } from 'node:util';
import test from 'node:test';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const support = process.env.ILLUSTRATION_SUPPORT_ROOT ?? join(root, 'skills/technical-illustration/references/upstream/anatomy');
const { validateActions } = await import(pathToFileURL(join(support, 'scripts/validate-actions.mjs')));
const run = promisify(execFile);

test('whole action list rejects malformed later effect before browser creation', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'orbyn-action-contract-'));
  try {
    const marker = join(dir, 'browser-started');
    const fake = join(dir, 'fake-browser');
    // Executable Node launcher needs no platform-specific shell quoting.
    await writeFile(fake, '#!/usr/bin/env node\nrequire("node:fs").writeFileSync(process.env.TEST_BROWSER_MARKER,"started");\n', { mode: 0o700 });
    for (const bad of [['wait', -1], ['move', null, 'x', 1], ['key', ''], ['shot', ''], ['eval', ''], ['until', '', 5], ['slow', null], ['drag', null, 0, 0, 1, 1, 0], ['lines', null, null, { tolerance: -1 }]]) {
      const actions = [['eval', 'window.sideEffect=1'], bad];
      assert.throws(() => validateActions(actions, { width: 800, height: 600, scale: 1 }), /Invalid/);
      const result = await run(process.execPath, [join(support, 'scripts/drive.mjs'), join(dir, 'page.html'), JSON.stringify(actions)], {
        timeout: 5000, env: { ...process.env, CHROME_PATH: fake, TEST_BROWSER_MARKER: marker },
      }).then(() => null, error => error);
      assert.ok(result && result.code !== 0);
      assert.match(result.stderr ?? '', /Invalid/);
      await assert.rejects(readFile(marker), error => error.code === 'ENOENT');
    }
    await run(process.execPath, [join(support, 'scripts/drive.mjs'), join(dir, 'page.html'), '[["eval","1"]]'], {
      timeout: 5000, env: { ...process.env, CHROME_PATH: fake, TEST_BROWSER_MARKER: marker },
    }).then(() => assert.fail('Fake browser must fail startup'), error => assert.match(error.stderr, /before startup/));
    assert.equal(await readFile(marker, 'utf8'), 'started');
  } finally { await rm(dir, { recursive: true }); }
});

test('legitimate complete action forms remain valid', () => {
  validateActions([['scroll'], ['wait', 0], ['move', null, 0, 1], ['click', null], ['drag', null, 0, 0, 1, 1, 2], ['key', ' '], ['slow', 1], ['eval', '1'], ['until', 'true', 10], ['shot', 'a.png'], ['lines'], ['turn', { dial: 10 }], ['orbit', 'a.png', 0, 20, 5], ['sheet', 'b.png', 0, 2]], { width: 800, height: 600, scale: 1 });
  for (const bad of [NaN, Infinity, -1, 0]) assert.throws(() => validateActions([], { width: 800, height: 600, scale: bad }));
});

test('excluded experimental packager exports reject rather than read unbundled modules', async () => {
  const kit = await import(pathToFileURL(join(support, 'scripts/inline-kit.mjs')));
  assert.match(kit.kitScript(), /cameraOf/);
  assert.throws(() => kit.fixedScript(), /outside/);
  assert.throws(() => kit.glSharedScript(), /outside/);
});

test('maintained browser launchers never enable sandbox/file/GPU bypass defaults', async () => {
  for (const name of ['capture.mjs', 'drive.mjs', 'turn-check.mjs', 'print.mjs']) {
    const text = await readFile(join(support, 'scripts', name), 'utf8');
    for (const forbidden of ['--no-sandbox', '--allow-file-access-from-files', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']) assert.ok(!text.includes(forbidden), `${name}: ${forbidden}`);
    if (name !== 'print.mjs') assert.match(text, /AbortSignal\.timeout\(10000\)/);
  }
});

test('GL layer frees only owned resources, including failed initialization and repeated disposal', async () => {
  const { glLayer } = await import(pathToFileURL(join(support, 'kit/gl.mjs')));
  const previousWindow = globalThis.window;
  globalThis.window = { devicePixelRatio: 1 };
  try {
    for (const failure of ['compile', 'link', 'none']) {
      const live = new Set();
      let current = null;
      const make = kind => { const value = { kind }; live.add(value); return value; };
      const remove = value => { assert.ok(live.delete(value), 'owned resource deleted exactly once'); };
      const gl = {
        COMPILE_STATUS: 1, LINK_STATUS: 2, ACTIVE_UNIFORMS: 3, CURRENT_PROGRAM: 4,
        VERTEX_SHADER: 5, FRAGMENT_SHADER: 6, ARRAY_BUFFER: 7, STATIC_DRAW: 8, FLOAT: 9,
        createShader: () => make('shader'), shaderSource() {}, compileShader() {},
        getShaderParameter: () => failure !== 'compile', getShaderInfoLog: () => 'planted compile failure',
        createProgram: () => make('program'), attachShader() {}, linkProgram() {},
        getProgramParameter: (_p, what) => what === 3 ? 0 : failure !== 'link',
        getProgramInfoLog: () => 'planted link failure', useProgram: value => { current = value; },
        getParameter: () => current, createBuffer: () => make('buffer'), bindBuffer() {}, bufferData() {},
        getAttribLocation: () => 0, enableVertexAttribArray() {}, vertexAttribPointer() {},
        getUniformLocation: () => null, getExtension: () => { throw new Error('Must not lose shared context'); },
        deleteShader: remove, deleteProgram: remove, deleteBuffer: remove,
      };
      const errors = [];
      const layer = glLayer({ canvas: { getContext: () => gl }, fragment: 'void main(){}', view: [], camera: {}, onError: message => errors.push(message) });
      if (failure === 'none') {
        assert.ok(layer);
        assert.equal(live.size, 4);
        layer.dispose(); layer.dispose();
        assert.throws(() => layer.draw(), /disposed/);
        assert.throws(() => layer.set(), /disposed/);
        assert.throws(() => layer.clear(), /disposed/);
      } else { assert.equal(layer, null); assert.ok(errors.length); }
      assert.equal(live.size, 0);
    }
  } finally { globalThis.window = previousWindow; }
});

test('PDF staging/backup collisions preserve unrelated sentinel and prior owned output', async () => {
  const { printPdf } = await import(pathToFileURL(join(support, 'scripts/print.mjs')));
  const dir = await mkdtemp(join(tmpdir(), 'orbyn-pdf-collision-'));
  const priorChrome = process.env.CHROME_PATH;
  const priorNow = Date.now;
  try {
    const fake = join(dir, 'fake-chrome');
    await writeFile(fake, '#!/usr/bin/env node\nconst fs=require("node:fs");const p=process.argv.find(a=>a.startsWith("--print-to-pdf="));if(p)fs.writeFileSync(p.slice(15),"%PDF-1.4\\n/Type /Page\\n%%EOF");\n', { mode: 0o700 });
    process.env.CHROME_PATH = fake;
    Date.now = () => 12345;
    const html = join(dir, 'input.html'); await writeFile(html, '<p>Controlled fake output</p>');
    for (const collision of ['backup', 'staging']) {
      const pdf = join(dir, `${collision}.pdf`); await writeFile(pdf, 'prior output');
      const sentinel = collision === 'backup' ? `${pdf}.previous-12345` : `${pdf}.new-${process.pid}`;
      await writeFile(sentinel, 'unrelated sentinel');
      await assert.rejects(printPdf(html, pdf), error => {
        assert.equal(error.code, 'EEXIST');
        const retained = error.message.match(/retained staging at (.+)$/)?.[1];
        assert.ok(retained);
        assert.ok(existsSync(join(retained, 'new.pdf')), 'Failed staged output must remain recoverable');
        return true;
      });
      assert.equal(await readFile(sentinel, 'utf8'), 'unrelated sentinel');
      assert.equal(await readFile(pdf, 'utf8'), 'prior output');
    }
  } finally {
    Date.now = priorNow;
    if (priorChrome === undefined) delete process.env.CHROME_PATH; else process.env.CHROME_PATH = priorChrome;
    await rm(dir, { recursive: true });
  }
});
