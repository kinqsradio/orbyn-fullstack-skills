import { stabilizePrimitive } from './film-primitives.mjs';
import { fpsValue, DEFAULT_FILM, validateFilm, sampleFilm, renderFilm } from './film.mjs';
const stage = document.getElementById('film-stage'); let spec = DEFAULT_FILM;
await document.fonts.ready;
window.motionFilm = {
  setSpec(value) { spec = structuredClone(validateFilm(value)); },
  seek(time, reduced = false, outputIndex = null) { const frame = sampleFilm(spec, time, reduced); if (outputIndex !== null) { frame.frameIndex = outputIndex; frame.beat = outputIndex / fpsValue(spec) * spec.bpm / 60; frame.primitive = stabilizePrimitive(frame.primitive, sampleFilm(spec, outputIndex / fpsValue(spec), reduced).primitive); } renderFilm(stage, frame, spec); return frame; },
  async ready() { await document.fonts.ready; await Promise.all([...stage.querySelectorAll('img')].map(n => n.decode())); },
  inspect() {
    const safe = stage.querySelector('.film-safe').getBoundingClientRect();
    const outside = ['film-title', 'film-caption', 'film-kicker', 'film-clock'].filter(id => { const n = document.getElementById(id), r = n.getBoundingClientRect(); return r.left < safe.left - 1 || r.right > safe.right + 1 || r.top < safe.top - 1 || r.bottom > safe.bottom + 1 || n.scrollWidth > n.clientWidth + 1; });
    const primitive = stage.querySelector('#film-primitive'); if (!primitive.hidden) { const bounds = primitive.getBoundingClientRect(); for (const n of primitive.querySelectorAll('.typed-note,.annotation-plane span,svg text,.motion-word,.type-depth span')) { const range = document.createRange(); if (n.matches('.type-depth span')) range.selectNodeContents(n); const r = n.matches('.type-depth span') ? range.getBoundingClientRect() : n.getBoundingClientRect(); if (r.left < bounds.left - 1 || r.right > bounds.right + 1 || r.top < bounds.top - 1 || r.bottom > bounds.bottom + 1 || n.scrollWidth > n.clientWidth + 1) outside.push('primitive-text'); } }
    return { fontStatus: document.fonts.status, outside, scene: stage.dataset.scene };
  }
};
window.motionFilm.seek(0); document.body.dataset.filmReady = 'true';
