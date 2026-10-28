// Explicit local qualification command; no automatic dependency install or inference.
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { createServer } from 'node:http';
import { PassThrough } from 'node:stream';
import { cp, mkdir, mkdtemp, readFile, symlink, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
const repository = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
assert.ok(process.env.ILLUSTRATION_PEER_ROOT && process.env.ILLUSTRATION_PROOF_DIR && process.env.CHROME_PATH, 'Explicit existing peers/browser/output required');
const peers = resolve(process.env.ILLUSTRATION_PEER_ROOT);
const require = createRequire(join(peers, 'package.json'));
const React = require('react');
const { renderToPipeableStream } = require('react-dom/server');
const { build } = require('esbuild');
const directory = await mkdtemp(join(resolve(process.env.ILLUSTRATION_PROOF_DIR), 'react-'));
await mkdir(join(directory, 'support/kit/react'), { recursive: true });
const source = join(repository, 'skills/technical-illustration/references/upstream/anatomy');
for (const name of ['kit/iso-kit.ts', 'kit/react/draw.tsx', 'kit/react/live.tsx']) await cp(join(source, name), join(directory, 'support', name));
await cp(join(dirname(fileURLToPath(import.meta.url)), 'react-consumer.tsx'), join(directory, 'consumer.tsx'));
await symlink(join(peers, 'node_modules'), join(directory, 'node_modules'), 'junction');
await writeFile(join(directory, 'tsconfig.json'), JSON.stringify({ compilerOptions: { target: 'ES2022', module: 'ESNext', moduleResolution: 'Bundler', jsx: 'react-jsx', strict: true, noEmit: true, lib: ['ES2022', 'DOM'], skipLibCheck: false }, include: ['consumer.tsx', 'support/kit/**/*.ts*'] }));
await promisify(execFile)(process.execPath, [join(peers, 'node_modules/typescript/bin/tsc'), '--project', join(directory, 'tsconfig.json'), '--noEmit'], { timeout: 30000 });
const aliases = Object.fromEntries(['react', 'react-dom'].map(name => [name, dirname(require.resolve(name+'/package.json'))]));
await build({ entryPoints: [join(directory, 'consumer.tsx')], bundle: true, platform: 'node', format: 'cjs', packages: 'external', outfile: join(directory, 'server.cjs') });
const fixtureRequire = createRequire(join(directory, 'server.cjs'));
assert.equal(fixtureRequire.resolve('react'), require.resolve('react'));
const { App } = fixtureRequire('./server.cjs');
const client = `import React from 'react';import{hydrateRoot}from'react-dom/client';import{App}from'./consumer';window.hydrationErrors=[];window.root=hydrateRoot(document.getElementById('root'),React.createElement(React.StrictMode,null,React.createElement('div',null,React.createElement(App))),{onRecoverableError:e=>window.hydrationErrors.push(e.message)});window.replaceA=()=>window.root.render(React.createElement(React.StrictMode,null,React.createElement('div',null,React.createElement(App,{showA:false}))));`;
await writeFile(join(directory, 'client.tsx'), client);
await build({ entryPoints: [join(directory, 'client.tsx')], bundle: true, platform: 'browser', alias: aliases, outfile: join(directory, 'client.js') });
const chunks = [];
const streams = [];
const server = createServer(async (req, res) => {
  if (req.url === '/client.js') { res.writeHead(200, { 'content-type': 'text/javascript' }); res.end(await readFile(join(directory, 'client.js'))); return; }
  if (req.url !== '/') { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.write('<!doctype html><style>body{font:18px system-ui;background:#f5f7fb;padding:28px;color:#213047}.iso-plate{display:inline-block;background:white;padding:24px;border:1px solid #9ab;margin:12px}svg{width:240px;height:100px;display:block}button{font:inherit;padding:10px}</style><div id="root">');
  let release;
  const gate = { ready: false, pending: new Promise(done => { release = done; }) };
  const record = { chunks: [], initial_shell: null, released: false };
  streams.push(record);
  const sink = new PassThrough();
  sink.on('data', chunk => {
    const text = String(chunk); chunks.push(text); record.chunks.push(text);
    console.log('SSR chunk', JSON.stringify({length:text.length,text}));
    const collected = record.chunks.join('');
    if (!record.released && collected.includes('Preparing explanation')) {
      assert.ok(collected.includes('10') && collected.includes('20') && collected.includes('tokens'));
      assert.ok(!collected.includes('id="streamed"'));
      record.initial_shell = collected;
      record.released = true;
      queueMicrotask(() => { gate.ready = true; release(); });
    }
  });
  sink.pipe(res, { end: false });
  sink.on('end', () => res.end('</div><script src="/client.js"></script>'));
  const stream = renderToPipeableStream(React.createElement(React.StrictMode, null, React.createElement('div', null, React.createElement(App, { gate }))), { onShellReady() { record.shell_ready=true; console.log('SSR shell-ready'); stream.pipe(sink); }, onAllReady(){record.all_ready=true;}, onError(error) { console.error(error); } });
});
await new Promise(done => server.listen(0, '127.0.0.1', done));
const preload = join(directory, 'preload.js');
await writeFile(preload, `window.firstReadouts={};new MutationObserver(()=>{for(const el of document.querySelectorAll('[data-readout]')){const id=el.closest('.iso-plate')?.id;if(id&&!window.firstReadouts[id])window.firstReadouts[id]={text:el.textContent,width:el.getBoundingClientRect().width}}}).observe(document,{subtree:true,childList:true});`);
const receipts = [];
try {
  for (const reduced of [false, true]) {
    const actions = [['until', 'window.hydrated===true'], ['key', 'Enter', '#a button'], ['until', 'document.querySelector("#a [data-readout]").textContent==="11 tokens"'], ['eval', '({a:document.querySelector("#a [data-readout]").textContent,b:document.querySelector("#b [data-readout]").textContent,first:window.firstReadouts,errors:window.hydrationErrors})'], ['shot', join(directory, reduced ? 'reduced.png' : 'active.png'), 'body'], ['eval', 'window.replaceA();true'], ['until', '!document.querySelector("#a")'], ['eval', 'window.oldSay("stale");({b:document.querySelector("#b [data-readout]").textContent,a:!!document.querySelector("#a")})']];
    const argv = [join(source, 'scripts/drive.mjs'), `http://127.0.0.1:${server.address().port}/`, JSON.stringify(actions), '--preload', preload, ...(reduced ? ['--reduced'] : [])];
    const result = await promisify(execFile)(process.execPath, argv, { timeout: 35000, maxBuffer: 1 << 22 });
    const objects = [...result.stdout.matchAll(/eval: (.*)/g)].map(m => JSON.parse(m[1])).filter(value => value && typeof value === 'object');
    assert.equal(objects[0].a, '11 tokens'); assert.equal(objects[0].b, '20 tokens'); assert.deepEqual(objects[0].errors, []);
    assert.equal(objects[0].first.a.text, '10 tokens'); assert.equal(objects[0].first.b.text, '20 tokens'); assert.ok(objects[0].first.a.width > 0);
    assert.deepEqual(objects[1], { b: '20 tokens', a: false });
    receipts.push({ reduced, argv, ...result, observed: objects });
  }
  assert.equal(streams.length, 2);
  for (const stream of streams) {
    assert.ok(stream.initial_shell?.includes('Preparing explanation'));
    assert.ok(!stream.initial_shell.includes('id="streamed"'));
    assert.ok(stream.chunks.join('').includes('id="streamed"'));
    assert.equal(stream.released, true);
  }
  await writeFile(join(directory, 'result.json'), JSON.stringify({ status: 'passed finite actual SSR/streamed DOM/hydration/native input/StrictMode/two-figure/replaced-anchor controls', versions: { react: React.version, react_dom: require('react-dom/package.json').version, typescript: require('typescript/package.json').version, esbuild: require('esbuild/package.json').version }, peer_identity: { server: fixtureRequire.resolve('react'), test: require.resolve('react') }, receipts, chunks, streams, limits: 'Browser DOM/readout/layout observations, not first-paint timing, arbitrary framework or assistive-technology qualification' }, null, 2));
  console.log(JSON.stringify({ status: 'passed', directory }));
} finally { await writeFile(join(directory,'stream-attempt.json'),JSON.stringify(streams,null,2)); server.closeAllConnections(); await new Promise(done => server.close(done)); }
