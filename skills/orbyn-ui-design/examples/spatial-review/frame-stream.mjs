// Long-form capture: page pixels reach the encoder's stdin over loopback, and no frame touches disk.
import { createServer } from 'node:http';
import { readdir, readFile, lstat } from 'node:fs/promises';
import { createHash, randomBytes } from 'node:crypto';
import { join, extname } from 'node:path';

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.bin': 'application/octet-stream', '.wasm': 'application/wasm', '.woff2': 'font/woff2' };
// A header rather than Playwright routing, which would carry every frame body through the control channel.
const OFFLINE = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:";
const MAX_FILES = 256, MAX_BYTES = 256 * 1024 * 1024;

// Headless Chromium on macOS needs Metal to reach the GPU. Other platforms keep Chromium's own choice, so read the recorded renderer.
export const angleArgs = platform => platform === 'darwin' ? ['--use-angle=metal'] : [];
export const softwareRenderer = name => /swiftshader|llvmpipe|software/i.test(name ?? '');

// Reads the page once into memory, so a later edit on disk cannot reach a render already in progress.
export async function sealSource(root) {
  const files = new Map(), excluded = []; let total = 0;
  const walk = async (dir, prefix) => {
    for (const name of (await readdir(dir)).sort()) {
      if (name.startsWith('.')) continue;
      const path = join(dir, name), info = await lstat(path), rel = prefix + name;
      if (info.isSymbolicLink()) throw Error('Frame source link: ' + rel);
      if (info.isDirectory()) { await walk(path, rel + '/'); continue; }
      if (!TYPES[extname(name).toLowerCase()]) { excluded.push(rel); continue; }
      const bytes = await readFile(path); total += bytes.length;
      if (files.size >= MAX_FILES || total > MAX_BYTES) throw Error('Frame source file/byte budget');
      files.set('/' + rel, { bytes, type: TYPES[extname(name).toLowerCase()], sha256: createHash('sha256').update(bytes).digest('hex') });
    }
  };
  await walk(root, '');
  if (!files.has('/index.html')) throw Error('Frame source needs index.html');
  return { files, excluded };
}

// A resolved write means the encoder's pipe accepted the bytes; a full pipe holds the caller here.
export function encoderSink(child) {
  let failure = null, waiter = null, ending = false;
  const abort = error => { failure ??= error; waiter?.(failure); waiter = null; };
  child.stdin.on('error', e => abort(Error('Encoder input closed: ' + (e.code ?? e.message))));
  child.once('exit', (code, signal) => { if (!ending) abort(Error('Encoder exited early: ' + (signal || code))); });
  return {
    abort,
    get failure() { return failure; },
    async write(chunk) {
      if (failure) throw failure;
      if (child.stdin.write(chunk)) return;
      await new Promise((res, rej) => { waiter = rej; child.stdin.once('drain', () => { waiter = null; res(); }); });
    },
    finish() { ending = true; if (!failure) child.stdin.end(); }
  };
}

export function frameServer({ files, frameBytes, write }) {
  const token = randomBytes(16).toString('hex'); let failure = null, calibration = null, accepted = 0, bytes = 0;
  const refuse = (res, status, message) => { failure ??= Error(message); res.writeHead(status, { connection: 'close' }).end(); };
  const server = createServer(async (req, res) => {
    const host = '127.0.0.1:' + server.address().port;
    if (req.headers.host !== host || (req.headers.origin && req.headers.origin !== 'http://' + host)) return void res.writeHead(403).end();
    const path = new URL(req.url, 'http://' + host).pathname;
    if (req.method === 'GET') { const file = files.get(path === '/' ? '/index.html' : path); if (!file) return void res.writeHead(404).end(); return void res.writeHead(200, { 'content-type': file.type, 'cache-control': 'no-store', 'content-security-policy': OFFLINE }).end(file.bytes); }
    const route = req.method === 'POST' && path.match(new RegExp(`^/${token}/(?:calibration|frame/(\\d+))$`));
    if (!route) return void res.writeHead(404).end();
    if (Number(req.headers['content-length']) !== frameBytes) return refuse(res, 413, `Frame size ${req.headers['content-length']} differs from ${frameBytes}`);
    if (route[1] !== undefined && Number(route[1]) !== accepted) return refuse(res, 409, `Frame ${route[1]} arrived out of order; expected ${accepted}`);
    try {
      let received = 0; const held = [];
      for await (const chunk of req) { received += chunk.length; if (route[1] === undefined) held.push(chunk); else await write(chunk); }
      if (received !== frameBytes) return refuse(res, 400, 'Truncated frame');
      if (route[1] === undefined) calibration = Buffer.concat(held); else { accepted++; bytes += received; }
      res.writeHead(204).end();
    } catch (error) { refuse(res, 500, 'Frame sink: ' + error.message); }
  });
  return {
    get failure() { return failure; },
    get calibration() { return calibration; },
    get accepted() { return accepted; },
    get bytes() { return bytes; },
    frameUrl: index => `/${token}/frame/${index}`, calibrationUrl: `/${token}/calibration`,
    listen: () => new Promise((res, rej) => { server.once('error', rej); server.listen(0, '127.0.0.1', () => res(`http://127.0.0.1:${server.address().port}/`)); }),
    close: () => new Promise(res => { server.closeAllConnections(); server.close(res); })
  };
}

// Y-down RGBA test card: row 0 is the top. Red top-left, green top-right, blue bottom-left, white bottom-right.
const QUADRANTS = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]];
export function orientationChart(size = 64) {
  const pixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) pixels.set([...QUADRANTS[(y < size / 2 ? 0 : 2) + (x < size / 2 ? 0 : 1)], 255], (y * size + x) * 4);
  return { width: size, height: size, pixels };
}

export function flipRows(pixels, width, height) {
  const out = new Uint8Array(pixels.length), row = width * 4;
  for (let y = 0; y < height; y++) out.set(pixels.subarray(y * row, (y + 1) * row), (height - 1 - y) * row);
  return out;
}

const NAMES = { 0: 'R', 1: 'G', 2: 'B', 3: 'W' };
const LAYOUTS = { RGBW: 'upright', BWRG: 'flipped-vertical', GRWB: 'flipped-horizontal', WBGR: 'rotated-180' };
// Compares normalised colour, so a mild grade still reads; a grade that moves hue reads as unrecognized.
function nearestQuadrant(r, g, b) {
  const size = Math.hypot(r, g, b); if (size < 8) return '?';
  let best = '?', score = .85;
  QUADRANTS.forEach((q, i) => { const c = (r * q[0] + g * q[1] + b * q[2]) / size / Math.hypot(...q); if (c > score) { score = c; best = NAMES[i]; } });
  return best;
}
export function classifyOrientation(pixels, width, height) {
  const at = (x, y) => { const i = (Math.floor(y * height) * width + Math.floor(x * width)) * 4; return nearestQuadrant(pixels[i], pixels[i + 1], pixels[i + 2]); };
  return LAYOUTS[at(.25, .25) + at(.75, .25) + at(.25, .75) + at(.75, .75)] ?? 'unrecognized';
}
