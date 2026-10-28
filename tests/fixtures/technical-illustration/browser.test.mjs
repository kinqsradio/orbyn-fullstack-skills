import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { promisify } from 'node:util';
import test from 'node:test';
const repository = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const support = join(repository, 'skills/technical-illustration/references/upstream/anatomy');
const enabled = Boolean(process.env.CHROME_PATH && process.env.ILLUSTRATION_PROOF_DIR);
const parent = process.env.ILLUSTRATION_PROOF_DIR ?? tmpdir();
if (enabled) await mkdir(parent, { recursive: true });
const directory = enabled ? await mkdtemp(join(parent, 'browser-')) : null;
const receipts = [];
async function invoke(name, argv) {
  const result = await promisify(execFile)(process.execPath, argv, { timeout: 35000, maxBuffer: 1 << 22 })
    .then(r => ({ code: 0, ...r }), e => ({ code: e.code, stdout: e.stdout, stderr: e.stderr }));
  receipts.push({ name, argv, ...result });
  await writeFile(join(directory, 'commands.json'), JSON.stringify({ node: process.version, receipts }, null, 2));
  return result;
}
function payload(result) {
  assert.equal(result.code, 0, result.stderr);
  return JSON.parse(result.stdout.match(/eval: (.*)/)[1]);
}
const page = script => `<!doctype html><meta charset="utf-8"><style>body{font:18px system-ui;background:#f7f8fb;color:#213047;padding:30px}.iso-plate{width:500px;padding:24px;background:white;border:1px solid #9ab}.iso-stage{width:400px}svg{width:400px;height:200px}button{font:inherit;padding:10px;margin:12px}</style><div class="iso-plate" tabindex="0"><h1>Model-driven fixture</h1><button id="go">Add item</button><div class="iso-stage"><svg class="iso-svg" viewBox="0 0 400 200"><defs><linearGradient id="shade"><stop id="color" stop-color="#dd3333"/><stop offset="1" stop-color="#fff"/></linearGradient><clipPath id="clip"><rect width="300" height="150"/></clipPath></defs><g data-piece="box" clip-path="url(#clip)"><rect x="10" y="10" width="280" height="130" fill="url(#shade)"/></g></svg></div><p data-readout>13 items</p></div><script>window.count=13;document.querySelector('#go').onclick=()=>{window.count++;document.querySelector('[data-readout]').textContent=window.count+' items'};${script}</script>`;
const options = { skip: !enabled };

test('actual native keyboard updates same-state readout and produces inspected capture inputs', options, async () => {
  const file = join(directory, 'native.html'); await writeFile(file, page(''));
  const result = await invoke('native-key', [join(support, 'scripts/drive.mjs'), file, JSON.stringify([['key', 'Enter', '#go'], ['eval', '({count:window.count,text:document.querySelector("[data-readout]").textContent})'], ['shot', join(directory, 'native-active.png'), '.iso-plate']])]);
  assert.deepEqual(payload(result), { count: 14, text: '14 items' });
  const clean = await invoke('clean-capture', [join(support, 'scripts/capture.mjs'), file, '--out', join(directory, 'native-rest.png'), '--wait', '0']);
  assert.equal(clean.code, 0, clean.stderr);
});

test('capture fails on page console error and rejected internal evaluation', options, async () => {
  for (const [name, script, expected] of [
    ['console-error', 'console.error("planted-console-error")', /planted-console-error/],
    ['evaluation-error', 'Object.defineProperty(document.documentElement,"scrollHeight",{get(){throw new Error("planted-evaluation-error")}})', /planted-evaluation-error/],
  ]) {
    const file = join(directory, name+'.html'); await writeFile(file, page(script));
    const result = await invoke(name, [join(support, 'scripts/capture.mjs'), file, '--out', join(directory, name+'.png'), '--wait', '0']);
    assert.equal(result.code, 1); assert.match(result.stdout+result.stderr, expected);
  }
});

test('a real stalled page load fails instead of qualifying after its timeout', options, async () => {
  const server = createServer((_request, response) => { response.writeHead(200, { 'content-type': 'text/html' }); response.write('<!doctype html><p>never completed'); });
  await new Promise(done => server.listen(0, '127.0.0.1', done));
  try {
    const result = await invoke('load-timeout', [join(support, 'scripts/capture.mjs'), `http://127.0.0.1:${server.address().port}/`, '--out', join(directory, 'timeout.png'), '--wait', '0']);
    assert.equal(result.code, 1); assert.match(result.stderr, /load did not complete/);
  } finally { server.closeAllConnections(); await new Promise(done => server.close(done)); }
});

test('distinct captured views namespace same original gradients/clips and required focus fails', options, async () => {
  const { capture } = await import(pathToFileURL(join(support, 'scripts/print.mjs')));
  const file = join(directory, 'print-views.html'); await writeFile(file, page(''));
  const spec = { settle: 0, parts: [{ id: 'box', select: '[data-piece="box"]' }], main: { view: 'rest' }, views: { rest: {}, changed: { actions: [['eval', 'document.querySelector("#color").setAttribute("stop-color","#3333dd")']] } } };
  const captured = await capture(spec, file);
  assert.match(captured.views.rest.layers[0], /view0-ps0-shade/);
  assert.match(captured.views.changed.layers[0], /view1-ps0-shade/);
  assert.match(captured.views.rest.layers[0], /#dd3333/);
  assert.match(captured.views.changed.layers[0], /#3333dd/);
  await writeFile(join(directory, 'captured-views.json'), JSON.stringify(captured, null, 2));
  const missing = { ...spec, parts: [{ id: 'absent', select: '#missing' }] };
  const sheet = join(directory, 'missing-focus.mjs');
  await writeFile(sheet, 'export default '+JSON.stringify({ ...missing, page: file })+';');
  const result = await invoke('missing-print-focus', [join(support, 'scripts/print.mjs'), sheet]);
  assert.equal(result.code, 1); assert.match(result.stderr, /Required selected part absent matched nothing/);
});

test('real WebGL same-task pixels, owned disposal and meaningful no-context fallback', options, async t => {
  const glCode = (await readFile(join(support, 'kit/gl.mjs'), 'utf8')).replace(/^export /gm, '');
  const file = join(directory, 'gpu.html');
  const script = `${glCode}\nconst canvas=document.createElement('canvas');canvas.width=32;canvas.height=32;canvas.style='width:32px;height:32px';document.querySelector('.iso-plate').append(canvas);const errors=[];const layer=glLayer({canvas,fragment:'void main(){gl_FragColor=vec4(1.,0.,0.,1.);}',view:[32,32],camera:{origin:[0,0],k:1,cam:[1,1,1,1]},onError:m=>errors.push(m)});window.probe=()=>{if(!layer)return{available:false,fallback:document.querySelector('[data-readout]').textContent,errors};layer.draw();const pixels=new Uint8Array(4);layer.gl.readPixels(0,0,1,1,layer.gl.RGBA,layer.gl.UNSIGNED_BYTE,pixels);const debug=layer.gl.getExtension('WEBGL_debug_renderer_info');const renderer=debug?layer.gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):layer.gl.getParameter(layer.gl.RENDERER);layer.dispose();layer.dispose();let guarded=false;try{layer.draw()}catch(e){guarded=/disposed/.test(e.message)}return{available:true,pixels:[...pixels],guarded,renderer,errors}};`;
  await writeFile(file, page(script));
  const result = payload(await invoke('gpu-pixels', [join(support, 'scripts/drive.mjs'), file, JSON.stringify([['eval', 'window.probe()']])]));
  await writeFile(join(directory, 'gpu-result.json'), JSON.stringify(result, null, 2));
  if (!result.available) t.skip('Actual GPU context unavailable; finite lifecycle controls are separate');
  else { assert.deepEqual(result.pixels, [255, 0, 0, 255]); assert.equal(result.guarded, true); assert.deepEqual(result.errors, []); }
  const fallback = payload(await invoke('gpu-no-context', [join(support, 'scripts/drive.mjs'), file, JSON.stringify([['eval', 'window.probe()']]), '--no-webgl']));
  assert.equal(fallback.available, false); assert.equal(fallback.fallback, '13 items');
});
