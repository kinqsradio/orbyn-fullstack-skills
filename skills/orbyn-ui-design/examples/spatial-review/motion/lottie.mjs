import { validateVector, drawVector } from './vector.mjs';
import { rate } from './time.mjs';

// Original bounded interchange, not the full expression-capable Lottie player.
export const LOTTIE_SUBSET = Object.freeze({
  supported: ['2D shape layers', 'nested shape groups', 'static affine transforms', 'line/cubic paths', 'solid fills/strokes', 'linear/hold path keyframes'],
  unsupported: ['expressions', 'plugins', 'external/precomp/image assets', 'text/fonts', 'masks/mattes', '3D', 'blend modes', 'animated style/transform', 'nonlinear easing'],
});
function fields(value, required, optional = []) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || required.some(k => !Object.hasOwn(value, k)) || Object.keys(value).some(k => ![...required, ...optional].includes(k))) throw Error('Unsupported Lottie fields/feature');
}
const num = (v, low = -1e6, high = 1e6) => { if (typeof v !== 'number' || !Number.isFinite(v) || v < low || v > high) throw Error('Invalid Lottie number'); return v; };
function point(v) { if (!Array.isArray(v) || v.length !== 2) throw Error('Expected 2D point'); return v.map(x => num(x)); }
function value(prop, dimensions = 1) {
  fields(prop, ['a', 'k']); if (prop.a !== 0) throw Error('Animated style/transform unsupported');
  if (dimensions === 1) return num(prop.k);
  if (!Array.isArray(prop.k) || prop.k.length < dimensions || prop.k.length > 4) throw Error('Property dimensions');
  prop.k.forEach(x => num(x)); return prop.k.slice(0, dimensions);
}
function shape(s) {
  fields(s, ['i', 'o', 'v', 'c']);
  if (typeof s.c !== 'boolean' || !Array.isArray(s.v) || s.v.length < 2 || s.v.length > 1000 || !Array.isArray(s.i) || !Array.isArray(s.o) || s.i.length !== s.v.length || s.o.length !== s.v.length) throw Error('Invalid Lottie path topology');
  s.v.forEach(point); s.i.forEach(point); s.o.forEach(point); return s;
}
function linearEase(v) {
  fields(v, ['x', 'y']);
  const scalar = x => Array.isArray(x) && x.length === 1 ? x[0] : x;
  if (num(scalar(v.x), 0, 1) !== num(scalar(v.y), 0, 1)) throw Error('Nonlinear Lottie easing unsupported');
}
function validatePath(prop) {
  fields(prop, ['a', 'k']);
  if (prop.a === 0) { shape(prop.k); return; }
  if (prop.a !== 1 || !Array.isArray(prop.k) || prop.k.length < 2 || prop.k.length > 1000) throw Error('Path keyframe budget');
  let last = -Infinity, base;
  for (const key of prop.k) {
    fields(key, ['t', 's'], ['e', 'h', 'i', 'o']); num(key.t, 0);
    if (key.t <= last || !Array.isArray(key.s) || key.s.length !== 1) throw Error('Invalid ordered path keys');
    last = key.t; shape(key.s[0]); base ??= key.s[0];
    if (key.s[0].v.length !== base.v.length || key.s[0].c !== base.c) throw Error('Path keyframe topology mismatch');
    if (Object.hasOwn(key, 'e')) { if (!Array.isArray(key.e) || key.e.length !== 1) throw Error('Invalid end path'); shape(key.e[0]); if (key.e[0].v.length !== base.v.length || key.e[0].c !== base.c) throw Error('End topology mismatch'); }
    if (key.h !== undefined && key.h !== 0 && key.h !== 1) throw Error('Invalid hold');
    if (key.i) linearEase(key.i); if (key.o) linearEase(key.o);
  }
}
function transform(t) {
  fields(t, [], ['o', 'r', 'p', 'a', 's', 'ty', 'nm']);
  if (t.ty !== undefined && t.ty !== 'tr') throw Error('Unsupported transform');
  const position = t.p ? value(t.p, 2) : [0, 0], anchor = t.a ? value(t.a, 2) : [0, 0], scale = t.s ? value(t.s, 2) : [100, 100];
  const rotation = (t.r ? value(t.r) : 0) * Math.PI / 180, opacity = (t.o ? value(t.o) : 100) / 100;
  num(opacity, 0, 1); const c = Math.cos(rotation), s = Math.sin(rotation);
  const m = [c * scale[0] / 100, s * scale[0] / 100, -s * scale[1] / 100, c * scale[1] / 100, position[0], position[1]];
  m[4] -= m[0] * anchor[0] + m[2] * anchor[1]; m[5] -= m[1] * anchor[0] + m[3] * anchor[1]; return { matrix: m, opacity };
}
const multiply = (a, b) => [a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1], a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3], a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5]];
const mapPoint = (p, m) => [m[0]*p[0]+m[2]*p[1]+m[4], m[1]*p[0]+m[3]*p[1]+m[5]];
function validateItems(items, depth = 0) {
  if (depth > 8 || !Array.isArray(items) || items.length > 200) throw Error('Lottie group budget');
  if (items.filter(i => i.ty === 'tr').length > 1 || items.filter(i => i.ty === 'fl').length > 1 || items.filter(i => i.ty === 'st').length > 1) throw Error('Competing group transform/style');
  if (items.some(i => i.ty === 'gr') && items.some(i => i.ty === 'fl' || i.ty === 'st')) throw Error('Style inheritance across groups unsupported; make each group explicit');
  for (const item of items) {
    if (item.ty === 'gr') { fields(item, ['ty', 'it'], ['nm']); validateItems(item.it, depth + 1); }
    else if (item.ty === 'sh') { fields(item, ['ty', 'ks'], ['nm', 'ind']); validatePath(item.ks); }
    else if (item.ty === 'tr') transform(item);
    else if (item.ty === 'fl' || item.ty === 'st') {
      fields(item, ['ty', 'c', 'o', ...(item.ty === 'st' ? ['w'] : [])], ['nm', 'r', 'lc', 'lj']);
      value(item.c, 4).forEach(x => num(x, 0, 1)); num(value(item.o), 0, 100);
      if (value(item.o) !== 100 || value(item.c, 4)[3] !== 1) throw Error('Partial style opacity unsupported');
      if (item.ty === 'st') num(value(item.w), 0, 100);
      if (item.r !== undefined && ![1, 2].includes(item.r)) throw Error('Unsupported fill rule');
      if ((item.lc !== undefined && item.lc !== 2) || (item.lj !== undefined && item.lj !== 2)) throw Error('Only round stroke joins/caps supported');
    } else throw Error('Unsupported Lottie shape feature');
  }
}
export function validateLottie(data) {
  fields(data, ['v', 'fr', 'ip', 'op', 'w', 'h', 'layers'], ['nm', 'ddd', 'assets']);
  if (typeof data.v !== 'string' || data.v.length > 40 || (data.ddd ?? 0) !== 0 || !Array.isArray(data.layers) || !data.layers.length || data.layers.length > 100) throw Error('Lottie root budget/3D');
  if (data.assets !== undefined && (!Array.isArray(data.assets) || data.assets.length)) throw Error('Assets/precompositions unsupported; no URLs loaded');
  num(data.fr, 1, 240); num(data.ip, 0); num(data.op, data.ip + 1e-6); num(data.w, 1, 10000); num(data.h, 1, 10000);
  const ids = new Set();
  for (const layer of data.layers) {
    fields(layer, ['ty', 'ind', 'ks', 'shapes', 'ip', 'op', 'st'], ['nm', 'sr', 'ddd', 'ao', 'bm']);
    if (layer.ty !== 4 || (layer.ddd ?? 0) || (layer.bm ?? 0) || (layer.ao ?? 0) || !Number.isSafeInteger(layer.ind) || ids.has(layer.ind)) throw Error('Unsupported layer/duplicate identity');
    ids.add(layer.ind); num(layer.ip, 0); num(layer.op, layer.ip + 1e-6); num(layer.st); num(layer.sr ?? 1, 1e-6, 1000);
    transform(layer.ks); validateItems(layer.shapes);
  }
  return data;
}
function samplePath(prop, frame) {
  if (!prop.a) return prop.k;
  const keys = prop.k;
  if (frame <= keys[0].t) return keys[0].s[0];
  if (frame >= keys.at(-1).t) return keys.at(-1).s[0];
  const index = keys.findIndex(k => k.t > frame), a = keys[index - 1], b = keys[index];
  const start = a.s[0], end = a.e?.[0] ?? b.s[0], t = a.h ? 0 : (frame - a.t) / (b.t - a.t);
  return Object.fromEntries(['i', 'o', 'v'].map(k => [k, start[k].map((p, i) => p.map((x, j) => x + (end[k][i][j] - x) * t))]).concat([['c', start.c]]));
}
function commandsOf(s, matrix) {
  const commands = [{ op: 'M', values: mapPoint(s.v[0], matrix) }];
  for (let n = 1; n < s.v.length + (s.c ? 1 : 0); n++) {
    const i = n % s.v.length, prev = (n - 1) % s.v.length;
    const curved = s.o[prev].some(x => x !== 0) || s.i[i].some(x => x !== 0);
    if (curved) commands.push({ op: 'C', values: [...mapPoint(s.v[prev].map((x, j) => x + s.o[prev][j]), matrix), ...mapPoint(s.v[i].map((x, j) => x + s.i[i][j]), matrix), ...mapPoint(s.v[i], matrix)] });
    else if (i !== 0) commands.push({ op: 'L', values: mapPoint(s.v[i], matrix) });
  }
  if (s.c) commands.push({ op: 'Z', values: [] }); return commands;
}
const hex = c => '#' + c.slice(0, 3).map(x => Math.round(x * 255).toString(16).padStart(2, '0')).join('');
export function sampleLottie(data, frame) {
  validateLottie(data); num(frame, data.ip, data.op); const shapes = [];
  function walk(items, matrix, opacity, prefix, at) {
    const tr = items.find(i => i.ty === 'tr'); if (items.filter(i => i.ty === 'tr').length > 1) throw Error('Competing group transforms');
    if (tr) { const t = transform(tr); matrix = multiply(matrix, t.matrix); opacity *= t.opacity; }
    const fill = items.filter(i => i.ty === 'fl'), stroke = items.filter(i => i.ty === 'st');
    if (fill.length > 1 || stroke.length > 1) throw Error('Competing group styles');
    // SVG stroke scaling is only equivalent for uniform affine scale.
    const sx = Math.hypot(matrix[0], matrix[1]), sy = Math.hypot(matrix[2], matrix[3]);
    if (stroke.length && Math.abs(sx - sy) > 1e-7) throw Error('Nonuniform stroke transform unsupported');
    items.forEach((item, i) => {
      if (item.ty === 'gr') walk(item.it, matrix, opacity, `${prefix}.${i}`, at);
      if (item.ty === 'sh') shapes.push({ id: `${prefix}.${i}`, commands: commandsOf(samplePath(item.ks, at), matrix), fill: fill.length ? hex(value(fill[0].c, 4)) : 'none', stroke: stroke.length ? hex(value(stroke[0].c, 4)) : 'none', strokeWidth: stroke.length ? value(stroke[0].w) * sx : 0, fillRule: fill[0]?.r === 2 ? 'evenodd' : 'nonzero', trim: 1, opacity });
    });
  }
  // Lottie layer zero paints on top; vector renderer paints in sequence.
  for (const layer of [...data.layers].reverse()) if (frame >= layer.ip && frame < layer.op) {
    const t = transform(layer.ks); walk(layer.shapes, t.matrix, t.opacity, `layer.${layer.ind}`, (frame - layer.st) / (layer.sr ?? 1));
  }
  return { width: data.w, height: data.h, shapes };
}
function lottiePath(commands) {
  const s = { i: [[0, 0]], o: [[0, 0]], v: [commands[0].values.slice()], c: commands.at(-1).op === 'Z' };
  for (const command of commands.slice(1)) {
    if (command.op === 'Z') continue;
    if (command.op === 'M') throw Error('Split subpaths before Lottie export');
    const prev = s.v.at(-1), v = command.values, end = v.slice(-2);
    if (command.op === 'Q') throw Error('Convert quadratic to cubic before Lottie export');
    const out = command.op === 'C' ? [v[0] - prev[0], v[1] - prev[1]] : [0, 0];
    const incoming = command.op === 'C' ? [v[2] - end[0], v[3] - end[1]] : [0, 0];
    s.o[s.o.length - 1] = out; s.v.push(end); s.i.push(incoming); s.o.push([0, 0]);
  }
  return shape(s);
}
const property = k => ({ a: 0, k });
export function toLottie(vector, { fps = 30, durationFrames = 60, title = 'Code-authored vectors' } = {}) {
  validateVector(vector); const r = rate(fps);
  if (!Number.isSafeInteger(durationFrames) || durationFrames < 2 || durationFrames > 100000 || typeof title !== 'string' || title.length > 200) throw Error('Lottie export budget');
  const data = { v: '5.12.2', fr: r.numerator / r.denominator, ip: 0, op: durationFrames, w: vector.width, h: vector.height, nm: title, ddd: 0, assets: [], layers: vector.shapes.map((s, index) => {
    const from = lottiePath(s.from), to = s.to ? lottiePath(s.to) : null;
    const shapeItem = { ty: 'sh', ks: to ? { a: 1, k: [{ t: 0, s: [from], e: [to] }, { t: durationFrames - 1, s: [to] }] } : property(from) };
    const styles = [];
    const channels = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16) / 255).concat(1);
    if (s.fill !== 'none') styles.push({ ty: 'fl', c: property(channels(s.fill)), o: property(100), r: s.fillRule === 'evenodd' ? 2 : 1 });
    if (s.stroke !== 'none') styles.push({ ty: 'st', c: property(channels(s.stroke)), o: property(100), w: property(s.strokeWidth), lc: 2, lj: 2 });
    if (s.trim) throw Error('Bake trimmed path before Lottie export');
    return { ty: 4, ind: index + 1, nm: s.id, ks: {}, shapes: [shapeItem, ...styles], ip: 0, op: durationFrames, st: 0 };
  }).reverse() };
  validateLottie(data); return data;
}
export function lottieComponent() {
  return {
    dependencies: [],
    sample(clip) { const d = clip.props.data; validateLottie(d); return { ...sampleLottie(d, clip.reducedMotion ? d.op - 1 : Math.max(d.ip, Math.min(d.op - 1e-8, d.ip + clip.localTime * d.fr))), id: clip.id, matrix: clip.worldMatrix, opacity: clip.opacity, zIndex: clip.zIndex }; },
    mount(host) { const svg = host.ownerDocument.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.style.position = 'absolute'; svg.style.width = svg.style.height = '100%'; svg.style.pointerEvents = 'none'; svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Code-authored vector animation'); host.append(svg); return svg; },
    update(svg, state) { drawVector(svg, state); svg.dataset.part = state.id; state.shapes.forEach((s, i) => svg.children[i].setAttribute('opacity', String(s.opacity))); svg.style.transformOrigin = '0 0'; svg.style.transform = `matrix(${state.matrix.join(',')})`; svg.style.opacity = String(state.opacity); svg.style.zIndex = String(state.zIndex); },
    async ready(_svg, signal) { if (signal.aborted) throw Error('Cancelled Lottie'); },
    dispose(svg) { svg.remove(); },
  };
}
