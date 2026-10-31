import { canonical, parseJSONStrict } from './review-core.mjs';
import { timeline, SCENARIOS } from './timeline.mjs';
import { validateGraphicsContext } from './motion/graphics-profiles.mjs';
import { validateMotionContext } from './motion/profiles.mjs';
export { canonical, parseJSONStrict };
const fields = (v, names) => { if (!v || typeof v !== 'object' || Array.isArray(v) || Object.keys(v).sort().join('|') !== [...names].sort().join('|')) throw Error('Unknown/missing fields'); };
const finite = (v, low, high) => { if (typeof v !== 'number' || !Number.isFinite(v) || v < low || v > high) throw Error('Invalid finite bound'); };
const text = (v, size, empty = false) => { if (typeof v !== 'string' || v.length > size || (!empty && !v.trim())) throw Error('Invalid text'); };
export function validateContext(c, manifest) {
  if (manifest.prototype.id === 'graphics-review-v1') return validateGraphicsContext(c, manifest);
  if (manifest.prototype.id === 'motion-composition-v1') return validateMotionContext(c, manifest);
  if (manifest.reviewProfile !== undefined) throw Error('Unsupported review profile');
  fields(c, ['modelRevision', 'partId', 'camera', 'animation', 'layers', 'viewport', ...(Object.hasOwn(c ?? {}, 'filmRevision') ? ['filmRevision'] : [])]);
  if (typeof c.partId !== 'string' || typeof c.modelRevision !== 'string' || c.modelRevision !== manifest.assets['engine-data.json'] || !manifest.targets.some(t => t.id === 'part/' + c.partId)) throw Error('Stale model/part');
  fields(c.camera, ['yaw', 'elevation', 'scale']); finite(c.camera.yaw, -180, 180);
  if (c.camera.elevation !== 27 || c.camera.scale !== 78) throw Error('Unsupported camera projection');
  fields(c.animation, ['scenario', 'scene', 'time', 'cycleAngle', 'rate']);
  const { scenario, scene, time, cycleAngle, rate } = c.animation;
  if (Object.hasOwn(c, 'filmRevision') && (!['film', 'gallery'].includes(scenario) || c.filmRevision !== manifest.assets[scenario === 'gallery' ? 'film-gallery.json' : 'film.mjs'])) throw Error('Stale film model');
  if (!SCENARIOS.includes(scenario) || timeline(time, scenario).scene !== scene || ![.25, .5, 1].includes(rate)) throw Error('Invalid timeline scene/rate');
  finite(cycleAngle, 0, 720);
  fields(c.layers, ['guides', 'rods']); if (Object.values(c.layers).some(v => typeof v !== 'boolean')) throw Error('Invalid layer settings');
  fields(c.viewport, ['width', 'height']); for (const v of Object.values(c.viewport)) { finite(v, 160, 8192); if (!Number.isInteger(v)) throw Error('Invalid viewport'); }
  return c;
}
export function validate(doc, manifest) {
  fields(doc, ['schemaVersion', 'prototype', 'settings', 'state', 'pending', 'comments']);
  if (doc.schemaVersion !== 2 || canonical(doc.prototype) !== canonical(manifest.prototype)) throw Error('Stale source/schema');
  validateContext(doc.settings, manifest);
  if (!['draft', 'submitted'].includes(doc.state) || !Array.isArray(doc.comments) || doc.comments.length > 200) throw Error('Invalid review state');
  const checkAnchor = c => { if (!manifest.targets.some(t => t.id === c.targetId)) throw Error('Removed target'); validateContext(c.context, manifest); if (c.targetId.startsWith('part/') && c.targetId !== 'part/' + c.context.partId) throw Error('Wrong part anchor'); };
  const ids = new Set();
  for (const c of doc.comments) {
    fields(c, ['id', 'targetId', 'context', 'text', 'disposition', 'decision']); checkAnchor(c);
    if (typeof c.id !== 'string' || !/^[A-Za-z0-9_-]{1,80}$/.test(c.id) || ids.has(c.id)) throw Error('Duplicate comment'); ids.add(c.id); text(c.text, 3000); text(c.decision, 1500, true);
    if (!['unresolved', 'accepted', 'rejected'].includes(c.disposition) || (c.disposition !== 'unresolved' && !c.decision.trim()) || (doc.state === 'draft' && c.disposition !== 'unresolved')) throw Error('Invalid disposition');
  }
  if (doc.pending !== null) { fields(doc.pending, ['targetId', 'context', 'text']); checkAnchor(doc.pending); text(doc.pending.text, 3000, true); if (doc.state !== 'draft') throw Error('Submitted pending feedback'); }
  return doc;
}
export const parseReview = (raw, manifest) => validate(parseJSONStrict(raw), manifest);
export function fresh(manifest, settings) { return validate({ schemaVersion: 2, prototype: { ...manifest.prototype }, settings: structuredClone(settings), state: 'draft', pending: null, comments: [] }, manifest); }
export function propose(before, doc, manifest) {
  validate(doc, manifest); if (doc.state !== 'submitted') throw Error('Submit first');
  const start = '<!-- spatial-review:start -->', end = '<!-- spatial-review:end -->';
  if ((before.split(start).length - 1) !== (before.split(end).length - 1) || before.split(start).length > 2 || (before.includes(end) && before.indexOf(end) < before.indexOf(start))) throw Error('Ambiguous design block');
  const safe = v => v.replace(/[<>&`*_[\]\\]/g, x => `&#${x.charCodeAt(0)};`).replace(/\r?\n/g, ' / ');
  const lines = [start, '## Spatial prototype review', `Source fingerprint: ${doc.prototype.fingerprint}`, 'Submission is feedback, not automatic design acceptance.'];
  for (const c of doc.comments) lines.push(`- ${c.disposition}: ${c.id}; target ${c.targetId}; ${safe(c.context.animation.scene)} at ${c.context.animation.time}s; camera ${c.context.profile === 'graphics-v1' ? `position ${c.context.camera.position.join(',')}, target ${c.context.camera.target.join(',')}` : c.context.profile === 'motion-v1' ? `x ${c.context.camera.x}, y ${c.context.camera.y}, zoom ${c.context.camera.zoom}` : `yaw ${c.context.camera.yaw}`}; model ${c.context.modelRevision}\n  Feedback: ${safe(c.text)}\n  Decision: ${safe(c.decision || 'Unresolved; retain question')}`);
  lines.push(end);
  const block = lines.join('\n'); return before.includes(start) ? before.slice(0, before.indexOf(start)) + block + before.slice(before.indexOf(end) + end.length) : before + '\n\n' + block + '\n';
}
