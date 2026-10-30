// Original synthetic review model. No effects, HTML execution or implicit approval.
export const IDENTITY = Object.freeze({ id: 'export-room', version: 1, candidate: 'synthetic-v1' });
export const TARGETS = Object.freeze([
  ['shell/navigation', 'shell', 'component', 'navigation', 'main'],
  ['shell/work', 'shell', 'control', 'navigation', 'work'],
  ['shell/settings', 'shell', 'control', 'navigation', 'settings'],
  ['work/page', 'work', 'page', 'page', 'work'],
  ['work/queue', 'work', 'component', 'queue', 'main'],
  ['work/alpha', 'work', 'component', 'export-row', 'alpha'],
  ['work/alpha/open', 'work', 'control', 'open-export', 'alpha'],
  ['work/beta', 'work', 'component', 'export-row', 'beta'],
  ['work/beta/open', 'work', 'control', 'open-export', 'beta'],
  ['work/detail/alpha', 'work', 'component', 'detail', 'alpha'],
  ['work/detail/beta', 'work', 'component', 'detail', 'beta'],
  ['work/retry', 'work', 'control', 'retry', 'main'],
  ['settings/page', 'settings', 'page', 'page', 'settings'],
  ['settings/preferences', 'settings', 'component', 'preferences', 'main'],
  ['settings/theme', 'settings', 'control', 'theme', 'main'],
  ['settings/density', 'settings', 'control', 'density', 'main'],
  ['settings/notifications', 'settings', 'control', 'notifications', 'main'],
  ['settings/apply', 'settings', 'control', 'apply-preferences', 'main'],
].map(([id, page, kind, component, instance]) => Object.freeze({ id, page, kind, component, instance })));
let sourceFingerprint = null;
const keys = (v, names) => {
  if (!v || typeof v !== 'object' || Array.isArray(v) || Object.keys(v).sort().join('|') !== [...names].sort().join('|')) throw Error('Unexpected or missing fields');
};
const oneOf = (v, values) => { if (!values.includes(v)) throw Error('Unsupported value'); };
const text = (v, max, nonempty = true) => {
  if (typeof v !== 'string' || v.length > max || (nonempty && !v.trim())) throw Error('Invalid text');
};
const integer = (v, min, max) => { if (!Number.isInteger(v) || v < min || v > max) throw Error('Invalid finite integer'); };
export function validateTargets(targets = TARGETS) {
  const ids = new Set();
  for (const t of targets) { if (ids.has(t.id)) throw Error('Duplicate target'); ids.add(t.id); }
  return ids;
}
validateTargets();
export function canonical(value) {
  return JSON.stringify(value, (_key, v) => v && typeof v === 'object' && !Array.isArray(v) ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v);
}
export function manifestPayload(manifest) {
  return canonical({ prototype: { ...IDENTITY }, targets: manifest.targets, assets: manifest.assets });
}
export function bindManifest(manifest) {
  keys(manifest, ['prototype', 'targets', 'assets']);
  keys(manifest.prototype, ['id', 'version', 'candidate', 'fingerprint']);
  if (Object.keys(IDENTITY).some(k => manifest.prototype[k] !== IDENTITY[k]) || !/^[a-f0-9]{64}$/.test(manifest.prototype.fingerprint)) throw Error('Invalid source fingerprint');
  if (canonical(manifest.targets) !== canonical(TARGETS)) throw Error('Stale/duplicate manifest targets');
  keys(manifest.assets, ['index.html', 'review.css', 'review.mjs', 'model.mjs', 'boot.mjs']);
  if (Object.values(manifest.assets).some(v => typeof v !== 'string' || !/^[a-f0-9]{64}$/.test(v))) throw Error('Invalid asset digest');
  if (sourceFingerprint && sourceFingerprint !== manifest.prototype.fingerprint) throw Error('Source changed; start an explicit new review round');
  sourceFingerprint = manifest.prototype.fingerprint;
}
export function freshReview() {
  if (!sourceFingerprint) throw Error('Bind a verified source manifest first');
  return { schemaVersion: 1, prototype: { ...IDENTITY, fingerprint: sourceFingerprint }, settings: { theme: 'light', density: 'comfortable', notifications: true }, state: 'draft', pending: null, comments: [] };
}
function context(c, targetId) {
  keys(c, ['page', 'state', 'theme', 'density', 'viewport']);
  oneOf(c.page, ['work', 'settings']); oneOf(c.state, ['default', 'error']);
  oneOf(c.theme, ['light', 'dark']); oneOf(c.density, ['comfortable', 'compact']);
  keys(c.viewport, ['width', 'height']);
  integer(c.viewport.width, 160, 8192); integer(c.viewport.height, 160, 8192);
  const target = TARGETS.find(t => t.id === targetId);
  if (!target || (target.page !== 'shell' && target.page !== c.page)) throw Error('Stale, removed or wrong-page target');
}
export function validateReview(doc) {
  keys(doc, ['schemaVersion', 'prototype', 'settings', 'state', 'pending', 'comments']);
  if (doc.schemaVersion !== 1) throw Error('Unsupported review schema');
  keys(doc.prototype, ['id', 'version', 'candidate', 'fingerprint']);
  if (!sourceFingerprint || doc.prototype.fingerprint !== sourceFingerprint || Object.keys(IDENTITY).some(k => doc.prototype[k] !== IDENTITY[k])) throw Error('Stale prototype/source version');
  keys(doc.settings, ['theme', 'density', 'notifications']);
  oneOf(doc.settings.theme, ['light', 'dark']); oneOf(doc.settings.density, ['comfortable', 'compact']);
  if (typeof doc.settings.notifications !== 'boolean') throw Error('Invalid setting');
  oneOf(doc.state, ['draft', 'submitted']);
  if (!Array.isArray(doc.comments) || doc.comments.length > 200) throw Error('Too many comments');
  const ids = new Set();
  for (const c of doc.comments) {
    keys(c, ['id', 'targetId', 'context', 'text', 'disposition', 'decision']);
    if (typeof c.id !== 'string' || !/^[a-zA-Z0-9_-]{1,80}$/.test(c.id) || ids.has(c.id)) throw Error('Duplicate/invalid comment ID');
    ids.add(c.id); context(c.context, c.targetId); text(c.text, 3000);
    oneOf(c.disposition, ['unresolved', 'accepted', 'rejected']); text(c.decision, 1500, false);
    if (c.disposition !== 'unresolved' && !c.decision.trim()) throw Error('Disposition needs a separate reason');
    if (doc.state === 'draft' && c.disposition !== 'unresolved') throw Error('Draft has no accepted decisions');
  }
  if (doc.pending !== null) {
    keys(doc.pending, ['targetId', 'context', 'text']); context(doc.pending.context, doc.pending.targetId); text(doc.pending.text, 3000, false);
    if (doc.state !== 'draft') throw Error('Submitted review contains unposted feedback');
  }
  return doc;
}
// JSON.parse alone cannot detect duplicate keys. Scan bounded JSON before parsing.
export function parseJSONStrict(raw) {
  if (typeof raw !== 'string' || new TextEncoder().encode(raw).length > 524288) throw Error('Review JSON exceeds limit');
  let i = 0;
  const ws = () => { while (/[\t\n\r ]/.test(raw[i] ?? '\0')) i++; };
  const string = () => {
    const start = i++;
    while (i < raw.length) {
      if (raw[i] === '\\') { i += 2; continue; }
      if (raw[i++] === '"') return JSON.parse(raw.slice(start, i));
    }
    throw Error('Unterminated JSON string');
  };
  const value = depth => {
    if (depth > 32) throw Error('JSON too deep'); ws();
    const ch = raw[i];
    if (ch === '"') { string(); return; }
    if (ch === '{' || ch === '[') {
      const object = ch === '{', end = object ? '}' : ']'; i++; ws();
      const seen = new Set();
      if (raw[i] === end) { i++; return; }
      while (i < raw.length) {
        ws();
        if (object) {
          if (raw[i] !== '"') throw Error('Expected key'); const key = string();
          if (seen.has(key)) throw Error('Duplicate JSON key'); seen.add(key); ws();
          if (raw[i++] !== ':') throw Error('Expected colon');
        }
        value(depth + 1); ws(); if (raw[i] === end) { i++; return; }
        if (raw[i++] !== ',') throw Error('Expected comma');
      }
      throw Error('Unclosed JSON container');
    }
    const match = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(raw.slice(i));
    if (!match) throw Error('Invalid JSON value'); i += match[0].length;
  };
  value(0); ws(); if (i !== raw.length) throw Error('Trailing JSON');
  return JSON.parse(raw);
}
export const parseReview = raw => validateReview(parseJSONStrict(raw));
export const serializeReview = doc => JSON.stringify(validateReview(doc), null, 2) + '\n';
const copy = doc => parseReview(serializeReview(doc));
export function postPending(doc, id) {
  const next = copy(doc); if (next.state !== 'draft' || !next.pending) throw Error('No draft comment selected');
  text(next.pending.text, 3000); next.comments.push({ id, ...next.pending, disposition: 'unresolved', decision: '' }); next.pending = null;
  return validateReview(next);
}
export function submitReview(doc) {
  const next = copy(doc); if (next.pending?.text.trim()) throw Error('Post pending feedback before finishing');
  next.pending = null; next.state = 'submitted'; return validateReview(next);
}
export function disposition(doc, id, choice, reason) {
  const next = copy(doc); if (next.state !== 'submitted') throw Error('Submit before agent reconciliation');
  const c = next.comments.find(c => c.id === id); if (!c) throw Error('Unknown comment');
  c.disposition = choice; c.decision = reason; return validateReview(next);
}
export function persistBrowser(doc, getStorage) {
  try {
    const storage = getStorage(), raw = serializeReview(doc); storage.setItem('export-room-review-v1', raw);
    if (storage.getItem('export-room-review-v1') !== raw) throw Error('Draft readback differs');
    return { ok: true, message: 'Browser draft saved here only; not saved to repository.' };
  } catch { return { ok: false, message: 'Browser draft storage unavailable/full. Keep this tab open; save to package or export JSON.' }; }
}
export function proposeDesignDoc(existing, doc) {
  validateReview(doc);
  if (doc.state !== 'submitted') throw Error('Submit feedback before proposing design changes');
  const start = '<!-- prototype-review:export-room:start -->', end = '<!-- prototype-review:export-room:end -->';
  const escape = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replace(/[\\`*_\[\]]/g, '\\$&');
  const accepted = doc.comments.filter(c => c.disposition === 'accepted');
  const remaining = doc.comments.filter(c => c.disposition !== 'accepted');
  const section = [start, '## Reviewed prototype decisions', `Source: ${IDENTITY.candidate}; prototype ${IDENTITY.id} v${IDENTITY.version}; source fingerprint ${doc.prototype.fingerprint}.`,
    'Review dispositions are recorded separately from publication/implementation authority.',
    doc.comments.some(c => c.disposition === 'unresolved') ? 'Partial decision proposal: unresolved questions remain.' : 'All recorded comments have dispositions; this is not blanket implementation approval.',
    ...accepted.flatMap(c => [`- ${c.id}: ${c.targetId}`, ...c.decision.split('\n').map(s => `  > ${escape(s)}`)]),
    ...remaining.flatMap(c => [`- ${c.disposition}: ${c.id} (${c.targetId})`, ...c.text.split('\n').map(s => `  > ${escape(s)}`), ...(c.decision ? c.decision.split('\n').map(s => `  > Decision: ${escape(s)}`) : [])]),
    `Preview settings for review: theme=${doc.settings.theme}, density=${doc.settings.density}, notifications=${doc.settings.notifications}.`,
    'Map approved settings to the actual token owner; this summary does not change product configuration.', end].join('\n');
  const starts = existing.split(start).length - 1, ends = existing.split(end).length - 1;
  if (!starts && !ends) return existing.trimEnd() + '\n\n' + section + '\n';
  if (starts !== 1 || ends !== 1 || existing.indexOf(start) > existing.indexOf(end)) throw Error('Ambiguous design-document markers');
  return existing.slice(0, existing.indexOf(start)) + section + existing.slice(existing.indexOf(end) + end.length);
}
