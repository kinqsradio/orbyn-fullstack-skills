import { TURN } from './renderer/kit/turn.mjs';
import GALLERY from './film-gallery.mjs';
import { renderFilm } from './film.mjs';
import { timeline, DURATION, durationFor } from './timeline.mjs';
import { CYLINDERS, FIRING, R, L, sample, poses, mod } from './model.mjs';
const $ = id => document.getElementById(id);
let angle = 0, yaw = 0, selected = 'A1', running = false, raf = null, previous = null;
let storyTime = 0, storyScenario = 'mechanism', storyRunning = false, activePart = 'piston-A1';
const listeners = new Set();
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
$('motion-note').textContent = reduced.matches ? 'Reduced motion detected. Start paused; use angle scrubbing or Next firing.' : 'Playback starts paused. 1× is a deliberately slow 30 rpm teaching speed.';
const [svg, data] = await Promise.all([fetch('engine.svg').then(r => { if (!r.ok) throw Error('Geometry unavailable'); return r.text(); }), fetch('engine-data.json').then(r => r.json())]);
// Local builder-owned SVG, never user comments or remote markup.
$('stage').innerHTML = svg;
const controller = TURN.mount($('stage'), data);
const buttons = new Map();
for (const c of CYLINDERS) {
  const b = document.createElement('button'); b.id = 'cylinder-' + c.id; b.textContent = c.id; b.setAttribute('aria-label', 'Inspect cylinder ' + c.id); b.onclick = () => select(c.id); $('cylinders').append(b); buttons.set(c.id, b);
}
$('firing-order').textContent = FIRING.map(c => c.id).join(' → ');
for (const node of $('stage').querySelectorAll('[data-name]')) {
  const id = node.dataset.name.match(/(?:piston|rod|liner)-(A\d|B\d)$/)?.[1];
  if (id) { node.onclick = e => { if (!dragged) select(id); e.stopPropagation(); }; }
}
const descriptions = { Power: 'After the model’s ignition point, the piston travels away from top dead centre.', Exhaust: 'The piston returns toward top dead centre. Exhaust valves are not modelled.', Intake: 'The piston moves down again. Intake flow and valves are not modelled.', Compression: 'The piston returns toward top dead centre before the next model ignition event.' };
function select(id) { activePart = 'piston-' + id; selected = id; update(); $('announce').textContent = `Cylinder ${id} selected. ${sample(angle).find(c => c.id === id).phase} stroke.`; }
function update() {
  const started = performance.now(); controller.set(poses(angle, yaw));
  for (const p of $('stage').querySelectorAll('[data-name]')) p.dataset.reviewActive = String(p.dataset.name === activePart);
  const story = timeline(storyTime, storyScenario, reduced.matches);
  $('story-title').textContent = story.title; $('story-caption').textContent = story.caption;
  $('story-scene').textContent = `${storyScenario} / ${story.scene} · ${storyTime.toFixed(2)}s`;
  $('story-time').max = String(durationFor(storyScenario)); $('story-time').value = String(storyTime); $('story-scenario').value = storyScenario;
  $('story-values').textContent = 'Illustrative values; actual current labels follow the bars.';
  for (const [i, row] of [...$('story-bars').children].entries()) { row.querySelector('i').style.width = `${story.bars[i]}%`; row.querySelector('output').textContent = String(story.bars[i]); }
  $('story-step').textContent = String(Math.min(3, 1 + Math.floor(story.progress * 3)));
  $('film-stage').hidden = !['film','gallery'].includes(storyScenario); renderFilm($('film-stage'), story, storyScenario === 'gallery' ? GALLERY : undefined);
  $('story-card').style.opacity = String(story.panelOpacity); $('story-title').style.transform = `scale(${storyScenario === 'film' ? story.typeScale : 1})`;
  $('story-card').hidden = storyScenario !== 'interface'; $('story-data').hidden = storyScenario !== 'data';
  const values = sample(angle);
  for (const c of values) {
    buttons.get(c.id).setAttribute('aria-pressed', String(c.id === selected)); buttons.get(c.id).dataset.phase = c.phase;
    for (const kind of ['piston', 'rod', 'liner']) {
      const el = $('stage').querySelector(`[data-name="${kind}-${c.id}"]`); el.dataset.selected = String(c.id === selected); el.dataset.phase = c.phase;
    }
  }
  const c = values.find(c => c.id === selected), residual = Math.abs(Math.hypot(...c.piston.map((x, i) => x - c.crank[i])) - L);
  $('selected-id').textContent = selected; $('phase').textContent = c.phase; $('description').textContent = descriptions[c.phase];
  $('travel').textContent = (c.travel * 100).toFixed(1) + '%'; $('cycle').textContent = c.cycle.toFixed(0) + '° / 720°'; $('residual').textContent = residual.toExponential(1) + ' units';
  $('angle').textContent = angle.toFixed(0) + '° / 720°'; $('crank').value = String(angle); $('orbit').value = String(yaw);
  $('render-state').textContent = `BETA 3D / SVG · ${data.parts.length} PARTS`;
  document.body.dataset.ready = 'true'; document.body.dataset.angle = angle.toFixed(4); document.body.dataset.selected = selected;
  document.body.dataset.renderMs = (performance.now() - started).toFixed(2);
  for (const fn of listeners) fn();
}
function pause() { storyRunning = false; $('story-play').textContent = 'Play story'; running = false; if (raf !== null) cancelAnimationFrame(raf); raf = null; previous = null; $('play').textContent = 'Play mechanism'; $('play').setAttribute('aria-pressed', 'false'); }
function tick(now) {
  if (!running || document.hidden) return;
  if (previous !== null) {
    const dt = Math.min(now - previous, 100) / 1000 * Number($('speed').value);
    if (storyRunning) { storyTime = Math.min(durationFor(storyScenario), storyTime + dt); const frame = timeline(storyTime, storyScenario, reduced.matches); angle = frame.angle; yaw = frame.yaw; if (storyTime === durationFor(storyScenario)) { pause(); update(); return; } }
    else angle = mod(angle + dt * 180, 720);
  }
  previous = now; update(); raf = requestAnimationFrame(tick);
}
$('play').onclick = () => { if (running) pause(); else { running = true; previous = null; $('play').textContent = 'Pause mechanism'; $('play').setAttribute('aria-pressed', 'true'); raf = requestAnimationFrame(tick); } };
$('crank').oninput = () => { pause(); angle = Number($('crank').value); update(); };
$('orbit').oninput = () => { pause(); yaw = Number($('orbit').value); update(); };
$('step').onclick = () => { pause(); angle = FIRING.find(c => c.fire > angle + .01)?.fire ?? FIRING[0].fire; update(); $('announce').textContent = 'Crank advanced to ' + angle + ' degrees.'; };
$('reset').onclick = () => { pause(); angle = 0; yaw = 0; selected = 'A1'; activePart = 'piston-A1'; update(); };
$('guides').onchange = () => $('stage').classList.toggle('hide-guides', !$('guides').checked);
$('rods').onchange = () => $('stage').classList.toggle('hide-rods', !$('rods').checked);
let drag = null, dragged = false;
$('stage').addEventListener('pointerdown', e => { if (e.button !== 0) return; pause(); drag = { x: e.clientX, yaw }; dragged = false; });
$('stage').addEventListener('pointermove', e => { if (!drag) return; if (!dragged && Math.abs(e.clientX - drag.x) > 4) { dragged = true; $('stage').setPointerCapture(e.pointerId); } if (dragged) { yaw = Math.max(-180, Math.min(180, drag.yaw + (e.clientX - drag.x) * .45)); update(); } });
$('stage').addEventListener('pointerup', () => { drag = null; }); $('stage').addEventListener('pointercancel', () => { drag = null; });
document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
window.addEventListener('pagehide', () => { pause(); controller.destroy(); });
reduced.addEventListener('change', () => { if (reduced.matches) pause(); });
for (const id of ['play', 'step', 'reset']) $(id).disabled = false;
update();

function seek(time) { pause(); storyTime = time; const frame = timeline(time, storyScenario, reduced.matches); angle = frame.angle; yaw = frame.yaw; update(); }
$('story-time').oninput = () => seek(Number($('story-time').value));
$('story-scenario').onchange = () => { storyScenario = $('story-scenario').value; seek(Math.min(storyTime, durationFor(storyScenario))); };
$('story-play').onclick = () => { if (running) { pause(); update(); return; } if (reduced.matches) { $('announce').textContent = 'Reduced motion: use manual scene seeking.'; return; } if (storyTime === durationFor(storyScenario)) seek(0); storyRunning = true; running = true; previous = null; $('story-play').textContent = 'Pause story'; raf = requestAnimationFrame(tick); };
const api = {
  pause() { pause(); drag = null; dragged = false; },
  capture() { return { partId: activePart, camera: { yaw, elevation: 27, scale: 78 }, animation: { scenario: storyScenario, scene: timeline(storyTime, storyScenario).scene, time: storyTime, cycleAngle: angle, rate: Number($('speed').value) }, layers: { guides: $('guides').checked, rods: $('rods').checked }, viewport: { width: innerWidth, height: innerHeight } }; },
  focusPart(id) { activePart = id; update(); },
  restore(c) { pause(); activePart = c.partId; storyTime = c.animation.time; storyScenario = c.animation.scenario; angle = c.animation.cycleAngle; yaw = c.camera.yaw; const cylinder = c.partId.match(/(?:piston|rod|liner)-(A[1-6]|B[1-6])$/)?.[1]; if (cylinder) selected = cylinder; $('speed').value = String(c.animation.rate); $('guides').checked = c.layers.guides; $('rods').checked = c.layers.rods; $('stage').classList.toggle('hide-guides', !c.layers.guides); $('stage').classList.toggle('hide-rods', !c.layers.rods); update(); },
  onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); }
};
import('./review.mjs').then(m => m.mountReview(api)).catch(error => { $('review-status').textContent = 'Review unavailable: ' + error.message + '. No repo save occurred.'; });
