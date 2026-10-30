import GALLERY from './film-gallery.mjs';
import { DEFAULT_FILM, sampleFilm } from './film.mjs';
// Original pure story/film frame model. No provider, random state or wall clock.
export const DURATION = 12;
export const SCENARIOS = ['mechanism', 'interface', 'data', 'film', 'gallery'];
export const FILM = Object.freeze({ fps: 30, bpm: 120, duration: DURATION, frames: 360,
  shots: [{ id: 'overview', from: 0, to: 3, beat: 0, composition: 'title' }, { id: 'motion', from: 3, to: 7, beat: 6, composition: 'split' }, { id: 'detail', from: 7, to: 10, beat: 14, composition: 'poster' }, { id: 'end', from: 10, to: 12, beat: 20, composition: 'end-card' }] });
const CONTENT = {
  mechanism: [['One shared mechanism', 'Twelve cylinders share one crankshaft.'], ['Follow the movement', 'Rigid rods convert rotation into reciprocating motion.'], ['See the relationship', 'Inspect one part at a known angle and camera.'], ['Inspect. Explain. Review.', 'A teaching model, not a production engine simulation.']],
  interface: [['Keep your place', 'A synthetic onboarding step starts with a local draft.'], ['Reveal the next step', 'The detail panel enters without discarding draft input.'], ['Ready to continue', 'A clear state and a stable next action replace decorative motion.'], ['Your draft stays yours', 'Cancel, back and reduced motion retain the same information.']],
  data: [['Compare four samples', 'Illustrative values: North 16, South 28, East 44 and West 64.'], ['Reveal the comparison', 'The bars and numeric labels consume the same sampled progress.'], ['Read the actual values', 'The final values remain available without movement.'], ['Keep the evidence visible', 'These are synthetic numbers, not engine measurements.']],
  film: [['MAKE IT CLEAR', 'An original motion study.'], ['ONE IDEA. EVERY FRAME.', 'Typography and composition follow a shared deterministic clock.'], ['MOVEMENT WITH MEANING', 'Readable holds, deliberate cuts and an accessible pause.'], ['INSPECT. REPLAY. REFINE.', 'Twelve seconds. Local source. Reviewable decisions.']]
};
export function timeline(time, scenario = 'mechanism', reduced = false) {
  if (!Number.isFinite(time) || time < 0 || time > (scenario === 'gallery' ? GALLERY.duration : DURATION) || !SCENARIOS.includes(scenario)) throw Error('Invalid timeline sample');
  const index = time < 3 ? 0 : time < 7 ? 1 : time < 10 ? 2 : 3, shot = FILM.shots[index];
  const t = Math.max(0, Math.min(1, (time - 3) / 4)), ease = t * t * (3 - 2 * t);
  const local = (time - shot.from) / (shot.to - shot.from), entrance = reduced ? 1 : Math.min(1, local / .18), smooth = entrance * entrance * (3 - 2 * entrance);
  return { scene: shot.id, composition: shot.composition, time, scenario, progress: time / DURATION, beat: time * FILM.bpm / 60, frameIndex: Math.min(FILM.frames - 1, Math.floor(time * FILM.fps)), angle: (time * 60) % 720,
    yaw: reduced ? 0 : index === 2 ? 35 : -25 + 50 * ease,
    title: (CONTENT[scenario] ?? CONTENT.film)[index][0], caption: (CONTENT[scenario] ?? CONTENT.film)[index][1], panelOpacity: reduced ? (time >= 3 ? 1 : 0) : ease,
    dataValue: Math.round(ease * 100), bars: [16, 28, 44, 64].map(value => Math.round(value * ease)),
    typeScale: 1, typeOffset: reduced ? 0 : (1 - smooth) * 24, opacity: reduced ? 1 : .4 + .6 * smooth, ...(scenario === 'film' || scenario === 'gallery' ? sampleFilm(scenario === 'gallery' ? GALLERY : DEFAULT_FILM, time, reduced) : {}) };
}
export function filmFrame(index, reduced = false) {
  if (!Number.isInteger(index) || index < 0 || index >= FILM.frames) throw Error('Invalid film frame');
  return timeline(index / FILM.fps, 'film', reduced);
}

export const durationFor = scenario => scenario === 'gallery' ? GALLERY.duration : DURATION;
