import { validatePrimitive, samplePrimitive, renderPrimitive } from './film-primitives.mjs';
// Original motion-film model and DOM renderer shared by preview and MP4 capture.
export const DEFAULT_FILM = Object.freeze({ version: 1, title: 'Movement with meaning', fps: 30, bpm: 120, duration: 12,
  shots: [
    { id: 'overview', from: 0, to: 3, composition: 'title', title: 'MAKE IT CLEAR', caption: 'An original motion study.' },
    { id: 'motion', from: 3, to: 7, composition: 'split', title: 'ONE IDEA. EVERY FRAME.', caption: 'Typography and composition follow a shared deterministic clock.' },
    { id: 'detail', from: 7, to: 10, composition: 'poster', title: 'MOVEMENT WITH MEANING', caption: 'Readable holds, deliberate cuts and an accessible pause.' },
    { id: 'end', from: 10, to: 12, composition: 'end-card', title: 'INSPECT. REPLAY. REFINE.', caption: 'Twelve seconds. Source files. Reviewable decisions.' }
  ] });
const exact = (v, keys) => { if (!v || typeof v !== 'object' || Array.isArray(v) || Object.keys(v).sort().join('|') !== [...keys].sort().join('|')) throw Error('Unknown/missing film fields'); };
const number = (v, low, high) => { if (typeof v !== 'number' || !Number.isFinite(v) || v < low || v > high) throw Error('Invalid film number'); };
const aligned = v => Math.abs(v - Math.round(v)) < 1e-7;
const text = (v, max) => { if (typeof v !== 'string' || !v.trim() || v.length > max) throw Error('Invalid film text'); };
export function validateFilm(spec) {
  exact(spec, ['version', 'title', 'fps', 'bpm', 'duration', 'shots', ...(Object.hasOwn(spec, 'palette') ? ['palette'] : []), ...(Object.hasOwn(spec, 'font') ? ['font'] : []), ...(Object.hasOwn(spec, 'background') ? ['background'] : [])]);
  if (spec.palette) { exact(spec.palette, ['paper', 'ink', 'accent', 'deep']); if (Object.values(spec.palette).some(v => typeof v !== 'string' || !/^#[0-9a-f]{6}$/i.test(v))) throw Error('Invalid film palette'); } else if (Object.hasOwn(spec, 'palette')) throw Error('Invalid film palette');
  if (Object.hasOwn(spec, 'font') && !['system-ui', 'serif', 'monospace'].includes(spec.font)) throw Error('Unsupported local font family');
  if (Object.hasOwn(spec, 'background')) {
    const b=spec.background; exact(b,['asset','alt','fit','focal','pan','zoom','dim']);
    if (typeof b.asset !== 'string' || !/^media\/[a-z0-9-]+\.(png|jpg|jpeg|webp)$/.test(b.asset) || !['cover','contain'].includes(b.fit)) throw Error('Invalid background asset/fit'); text(b.alt,120);
    exact(b.focal,['x','y']); number(b.focal.x,0,1); number(b.focal.y,0,1); exact(b.pan,['from','to']); exact(b.zoom,['from','to']); number(b.dim,0,.8);
    for(const end of ['from','to']) { exact(b.pan[end],['x','y']); number(b.zoom[end],1,2); number(b.pan[end].x,-.25,.25); number(b.pan[end].y,-.25,.25); if(b.fit==='cover' && (Math.abs(b.pan[end].x)>(b.zoom[end]-1)/2 || Math.abs(b.pan[end].y)>(b.zoom[end]-1)/2)) throw Error('Background pan exposes uncovered frame'); }
  }
  if (spec.version !== 1) throw Error('Unsupported film version'); text(spec.title, 100); number(spec.fps, 10, 60); number(spec.bpm, 20, 240); number(spec.duration, .1, 120);
  if (!Number.isInteger(spec.fps) || !aligned(spec.duration * spec.fps) || spec.duration * spec.fps > 3600 || !Array.isArray(spec.shots) || spec.shots.length < 1 || spec.shots.length > 24) throw Error('Film frame/shot budget');
  let end = 0; const ids = new Set();
  for (const s of spec.shots) {
    exact(s, ['id', 'from', 'to', 'composition', 'title', 'caption', ...(Object.hasOwn(s, 'primitive') ? ['primitive', 'data'] : [])]);
    if (typeof s.id !== 'string' || !/^[a-z][a-z0-9-]{0,39}$/.test(s.id) || ids.has(s.id)) throw Error('Duplicate/invalid shot ID'); ids.add(s.id);
    if (!['title', 'split', 'poster', 'end-card'].includes(s.composition)) throw Error('Unsupported composition');
    number(s.from, 0, spec.duration); number(s.to, 0, spec.duration);
    if (s.from !== end || s.to <= s.from || !aligned(s.from * spec.fps) || !aligned(s.to * spec.fps)) throw Error('Shots must cover contiguous frame-aligned intervals');
    text(s.title, 100); text(s.caption, 240); if (Object.hasOwn(s, 'primitive')) validatePrimitive(s, spec); end = s.to;
  }
  if (end !== spec.duration) throw Error('Incomplete film coverage'); return spec;
}
validateFilm(DEFAULT_FILM);
export function sampleFilm(spec, time, reduced = false) {
  validateFilm(spec); number(time, 0, spec.duration);
  const shot = spec.shots.find(s => time >= s.from && time < s.to) ?? spec.shots.at(-1);
  const local = (time - shot.from) / (shot.to - shot.from), entrance = reduced ? 1 : Math.min(1, local / .18), smooth = entrance * entrance * (3 - 2 * entrance);
  return { scene: shot.id, composition: shot.composition, time, title: shot.title, caption: shot.caption, beat: time * spec.bpm / 60, frameIndex: Math.min(Math.round(spec.duration * spec.fps) - 1, Math.floor(time * spec.fps + 1e-8)), typeOffset: reduced ? 0 : (1 - smooth) * 24, opacity: reduced ? 1 : .4 + .6 * smooth, background: spec.background ? { ...spec.background, x: spec.background.pan.from.x + (spec.background.pan.to.x-spec.background.pan.from.x)*(reduced?0:time/spec.duration), y: spec.background.pan.from.y + (spec.background.pan.to.y-spec.background.pan.from.y)*(reduced?0:time/spec.duration), scale: spec.background.zoom.from + (spec.background.zoom.to-spec.background.zoom.from)*(reduced?0:time/spec.duration) } : null, primitive: shot.primitive ? samplePrimitive(shot, Math.max(0, Math.min(1, local)), spec, reduced) : null };
}
export function subframeTimes(spec, index, samples = 1, shutter = .5) {
  validateFilm(spec); if (!Number.isInteger(index) || index < 0 || index >= Math.round(spec.duration * spec.fps) || !Number.isInteger(samples) || samples < 1 || samples > 4) throw Error('Invalid frame/subframe budget'); number(shutter, 0, 1);
  const time = index / spec.fps, shot = spec.shots.find(s => time >= s.from && time < s.to);
  return Array.from({ length: samples }, (_, j) => Math.max(shot.from, Math.min(shot.to - 1e-9, time + ((j + .5) / samples - .5) * shutter / spec.fps)));
}
export function renderFilm(stage, frame, spec = DEFAULT_FILM) {
  const background = stage.querySelector('#film-background'); background.replaceChildren();
  if(frame.background) { const b=frame.background, image=document.createElement('img'), shade=document.createElement('i'); image.src=b.asset; image.alt=b.alt; image.style.objectFit=b.fit; image.style.objectPosition=`${b.focal.x*100}% ${b.focal.y*100}%`; image.style.transform=`translate(${b.x*100}%,${b.y*100}%) scale(${b.scale})`; shade.style.opacity=String(b.dim); background.append(image,shade); }
  for (const [role, value] of Object.entries(spec.palette ?? {})) stage.style.setProperty('--film-' + role, value);
  stage.querySelector('#film-title').style.fontFamily = spec.font ?? 'system-ui';
  renderPrimitive(stage.querySelector('#film-primitive'), frame.primitive); stage.dataset.primitive = frame.primitive?.kind ?? '';
  stage.dataset.shot = frame.composition; stage.dataset.scene = frame.scene;
  stage.querySelector('#film-title').textContent = frame.title; stage.querySelector('#film-caption').textContent = frame.caption;
  const title = stage.querySelector('#film-title'); title.style.transform = `translateY(${frame.typeOffset}px)`; title.style.opacity = String(frame.opacity);
  stage.querySelector('#film-clock').textContent = `FRAME ${frame.frameIndex} / ${Math.round(spec.duration * spec.fps) - 1} · BEAT ${frame.beat.toFixed(2)} · ${spec.fps} FPS STUDY`;
}
export function validateCues(cues, duration) {
  if (!Array.isArray(cues) || cues.length < 1 || cues.length > 200) throw Error('Caption budget'); let end = 0;
  for (const cue of cues) { exact(cue, ['start', 'end', 'text']); number(cue.start, 0, duration); number(cue.end, 0, duration); text(cue.text, 500); if (cue.start < end || cue.end <= cue.start) throw Error('Caption overlap/order'); end = cue.end; }
  return cues;
}
export function webVTT(cues, duration) {
  validateCues(cues, duration);
  const stamp = t => { const ms = Math.round(t * 1000); return `${String(Math.floor(ms / 3600000)).padStart(2, '0')}:${String(Math.floor(ms / 60000) % 60).padStart(2, '0')}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}.${String(ms % 1000).padStart(3, '0')}`; };
  const safe = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\r/g, '');
  return 'WEBVTT\n\n' + cues.map((c, i) => `${i + 1}\n${stamp(c.start)} --> ${stamp(c.end)}\n${safe(c.text)}\n`).join('\n');
}
