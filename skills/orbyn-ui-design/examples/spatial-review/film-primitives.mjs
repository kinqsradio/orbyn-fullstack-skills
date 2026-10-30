// Original parametric film primitives. No imported source blocks or HTML evaluation.
export const PRIMITIVES = ['words', 'crossout', 'chart', '3d-title', 'typing', 'stretch', 'flythrough', 'annotations', 'counter', 'progress', 'chain', 'rewind', 'image', 'logo'];
const fields = (v, keys) => { if (!v || typeof v !== 'object' || Array.isArray(v) || Object.keys(v).sort().join('|') !== [...keys].sort().join('|')) throw Error('Unknown/missing primitive fields'); };
const text = (v, max = 80) => { if (typeof v !== 'string' || !v.trim() || v.length > max) throw Error('Invalid primitive text'); };
const number = (v, low, high) => { if (typeof v !== 'number' || !Number.isFinite(v) || v < low || v > high) throw Error('Invalid primitive number'); };
const strings = (v, max = 8) => { if (!Array.isArray(v) || !v.length || v.length > max) throw Error('Primitive item budget'); for (const s of v) text(s, 32); };
export const validAsset = path => typeof path === 'string' && /^media\/[a-z0-9-]+\.(png|jpg|jpeg|webp)$/.test(path);
export function validatePrimitive(shot, spec) {
  if (!PRIMITIVES.includes(shot.primitive)) throw Error('Unsupported primitive'); const d = shot.data;
  const schema = { words: ['words'], crossout: ['text', 'replacement'], chart: ['labels', 'values'], '3d-title': ['text', 'depth'], typing: ['text'], stretch: ['text'], flythrough: ['words'], annotations: ['notes'], counter: ['from', 'to', 'decimals', 'suffix'], progress: ['steps'], chain: ['nodes'], rewind: ['source'], image: ['asset', 'alt'], logo: ['text', ...(Object.hasOwn(d ?? {}, 'asset') ? ['asset'] : [])] };
  fields(d, schema[shot.primitive]);
  switch (shot.primitive) {
    case 'words': case 'flythrough': strings(d.words); break;
    case 'crossout': text(d.text, 50); text(d.replacement, 50); break;
    case 'chart': strings(d.labels, 6); if (!Array.isArray(d.values) || d.values.length !== d.labels.length) throw Error('Chart series differs'); for (const v of d.values) number(v, 0, 1000000); break;
    case '3d-title': text(d.text, 32); number(d.depth, 1, 12); if (!Number.isInteger(d.depth)) throw Error('Invalid depth'); break;
    case 'typing': text(d.text, 240); break;
    case 'stretch': text(d.text, 24); break;
    case 'annotations': if (!Array.isArray(d.notes) || !d.notes.length || d.notes.length > 6) throw Error('Annotation budget'); for (const n of d.notes) { fields(n, ['x', 'y', 'text']); number(n.x, .1, .9); number(n.y, .1, .9); text(n.text, 32); } break;
    case 'counter': number(d.from, -1000000, 1000000); number(d.to, -1000000, 1000000); number(d.decimals, 0, 3); if (!Number.isInteger(d.decimals)) throw Error('Invalid precision'); if (typeof d.suffix !== 'string' || d.suffix.length > 12) throw Error('Invalid suffix'); break;
    case 'progress': strings(d.steps); break;
    case 'chain': strings(d.nodes, 6); break;
    case 'rewind': { text(d.source, 40); const index = spec.shots.indexOf(shot), source = spec.shots.slice(0, index).find(s => s.id === d.source); if (!source || !source.primitive || source.primitive === 'rewind') throw Error('Rewind needs an earlier nonrecursive primitive clip'); break; }
    case 'image': if (!validAsset(d.asset)) throw Error('Unapproved media path'); text(d.alt, 120); break;
    case 'logo': text(d.text, 40); if (d.asset !== undefined && !validAsset(d.asset)) throw Error('Unapproved logo path'); break;
  }
}
const ease = p => p * p * (3 - 2 * p);
export function samplePrimitive(shot, p, spec, reduced = false) {
  const q = Math.max(0, Math.min(1, p)), progress = reduced ? 1 : ease(q), data = structuredClone(shot.data);
  const base = { kind: shot.primitive, p: q, progress, data };
  switch (shot.primitive) {
    case 'words': { const index = Math.min(data.words.length - 1, Math.floor(q * data.words.length)), local = q * data.words.length - index; return { ...base, word: data.words[index], offset: reduced ? 0 : (1 - ease(Math.min(1, local * 3))) * 24 }; }
    case 'chart': return { ...base, values: data.values.map(v => v * progress) };
    case 'counter': return { ...base, value: data.from + (data.to - data.from) * progress };
    case 'typing': return { ...base, typed: data.text.slice(0, reduced ? data.text.length : Math.floor(data.text.length * q)), cursor: Math.floor(q * 12) % 2 === 0 };
    case 'stretch': return { ...base, scale: reduced ? 1 : .65 + .65 * Math.sin(q * Math.PI) };
    case '3d-title': return { ...base, yaw: reduced ? 0 : -28 + 56 * progress, pitch: reduced ? 0 : 12 - 24 * progress };
    case 'flythrough': return { ...base, planes: data.words.map((word, i) => ({ word, z: reduced ? -i * 100 : (q * data.words.length - i - .5) * 700 })) };
    case 'rewind': { const source = spec.shots.find(s => s.id === data.source); return { ...base, sourceTime: source.from + (source.to - source.from) * Math.min(1 - 1e-9, 1 - q), source: samplePrimitive(source, Math.min(1 - 1e-9, 1 - q), spec, reduced) }; }
    default: return base;
  }
}
const html = (tag, text = '') => { const n = document.createElement(tag); n.textContent = text; return n; };
const svg = (tag, attrs = {}) => { const n = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const [k,v] of Object.entries(attrs)) n.setAttribute(k, String(v)); return n; };
export function renderPrimitive(container, frame) {
  container.replaceChildren(); if (!frame) { container.hidden = true; return; } container.hidden = false; container.dataset.kind = frame.kind;
  const { data: d, progress: p } = frame;
  switch (frame.kind) {
    case 'words': { const n = html('strong', frame.word); n.className = 'motion-word'; n.style.transform = `translateY(${frame.offset}px)`; container.append(n); break; }
    case 'crossout': { const box = html('div'), old = html('div', d.text), line = html('i'), next = html('strong', d.replacement); old.className = 'crossout-old'; line.style.width = `${Math.min(1,p * 2) * 100}%`; old.append(line); next.style.opacity = String(Math.max(0,(p - .5) * 2)); box.append(old, next); container.append(box); break; }
    case 'chart': { const chart = svg('svg', { viewBox: '0 0 600 200', role: 'img', 'aria-label': d.labels.map((x,i) => `${x}: ${frame.values[i].toFixed(0)}`).join(', ') }); const max = Math.max(1, ...d.values), step = 560 / d.labels.length; d.labels.forEach((label,i) => { const h = frame.values[i] / max * 140, x = 20 + i * step; chart.append(svg('rect', { x, y: 155 - h, width: step * .65, height: h, rx: 3, fill: 'currentColor' })); const t = svg('text', { x, y: 180, fill: 'currentColor', 'font-size': 13 }); t.textContent = label; const value = svg('text', { x, y: Math.max(13,145-(frame.semanticValues ?? frame.values)[i]/max*140), fill: 'currentColor', 'font-size': 14 }); value.textContent = (frame.semanticValues ?? frame.values)[i].toFixed(0); chart.append(t,value); }); container.append(chart); break; }
    case '3d-title': { const box = html('div'); box.className = 'type-depth'; box.style.transform = `rotateX(${frame.pitch}deg) rotateY(${frame.yaw}deg)`; for (let i = d.depth; i >= 0; i--) { const layer = html('span', d.text); layer.style.transform = `translateZ(${-i * 2}px)`; layer.style.opacity = i ? '.35' : '1'; box.append(layer); } container.append(box); break; }
    case 'typing': { const n = html('pre', frame.typed + (frame.cursor ? '▌' : ' ')); n.className = 'typed-note'; container.append(n); break; }
    case 'stretch': { const n = html('strong', d.text); n.className = 'motion-word'; n.style.transform = `scaleX(${frame.scale})`; container.append(n); break; }
    case 'flythrough': { const camera = html('div'); camera.className = 'type-camera'; for (const plane of frame.planes) { const n = html('span', plane.word); n.style.transform = `translateZ(${plane.z}px)`; camera.append(n); } container.append(camera); break; }
    case 'annotations': { const box = html('div'); box.className = 'annotation-plane'; const lines = svg('svg', { viewBox: '0 0 600 200', 'aria-hidden': 'true' }); d.notes.forEach((note,i) => { const amount = Math.max(0,Math.min(1,p * d.notes.length - i)); lines.append(svg('line', { x1:300,y1:100,x2:300+(note.x*600-300)*amount,y2:100+(note.y*200-100)*amount,stroke:'currentColor','stroke-width':2 })); const n = html('span', note.text); n.style.left = `${note.x*100}%`; n.style.top = `${note.y*100}%`; n.style.opacity = String(amount); box.append(n); }); box.prepend(lines); container.append(box); break; }
    case 'counter': { const n = html('output', frame.value.toFixed(d.decimals) + d.suffix); n.className = 'motion-word'; container.append(n); break; }
    case 'progress': { const box = html('div'); box.className = 'step-progress'; const bar = html('div'), fill = html('i'); fill.style.width = `${p*100}%`; bar.append(fill); const labels = html('ol'); d.steps.forEach((step,i) => { const n = html('li', step); n.dataset.active = String((frame.semanticProgress ?? p) >= (i + 1) / d.steps.length); labels.append(n); }); box.append(bar, labels, html('output', `${Math.round((frame.semanticProgress ?? p)*100)}%`)); container.append(box); break; }
    case 'chain': { const chart = svg('svg', { viewBox: '0 0 600 200', role:'img', 'aria-label':d.nodes.join(' → ') }); const step = 500/Math.max(1,d.nodes.length-1); d.nodes.forEach((label,i) => { const x=50+i*step, y=i%2?135:65; if (i) { const q=Math.max(0,Math.min(1,p*(d.nodes.length-1)-(i-1))), px=50+(i-1)*step, py=(i-1)%2?135:65; chart.append(svg('line',{x1:px,y1:py,x2:px+(x-px)*q,y2:py+(y-py)*q,stroke:'currentColor','stroke-width':4})); } const circle=svg('circle',{cx:x,cy:y,r:18,fill:'currentColor',opacity:p >= i/Math.max(1,d.nodes.length-1)?1:.2}); const t=svg('text',{x,y:y+36,'text-anchor':'middle','font-size':13,fill:'currentColor'}); t.textContent=label; chart.append(circle,t); }); container.append(chart); break; }
    case 'rewind': { const box=html('div'); box.className='rewind-source'; renderPrimitive(box,frame.source); container.append(box,html('span',`REWIND · ${frame.sourceTime.toFixed(2)}s`)); break; }
    case 'image': { const image=html('img'); image.src=d.asset; image.alt=d.alt; image.style.transform=`scale(${1 + .06*p})`; container.append(image); break; }
    case 'logo': { const box=html('div'); box.className='logo-reveal'; box.style.clipPath=`inset(0 ${100*(1-p)}% 0 0)`; if(d.asset){const image=html('img');image.src=d.asset;image.alt=d.text;box.append(image);}else box.append(html('strong',d.text));container.append(box);break; }
  }
}
// Semantic readouts use the output instant; only geometric poses use subframe time.
export function stabilizePrimitive(frame, semantic) {
  if (!frame || !semantic || frame.kind !== semantic.kind) return frame;
  if (frame.kind === 'counter') frame.value = semantic.value;
  if (frame.kind === 'chart') frame.semanticValues = semantic.values;
  if (frame.kind === 'progress') frame.semanticProgress = semantic.progress;
  if (frame.kind === 'typing') { frame.typed = semantic.typed; frame.cursor = semantic.cursor; }
  if (frame.kind === 'words') { if (frame.word !== semantic.word) frame.offset = semantic.offset; frame.word = semantic.word; }
  if (frame.kind === 'rewind') frame.source = stabilizePrimitive(frame.source, semantic.source);
  return frame;
}
