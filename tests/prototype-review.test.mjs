import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, mkdtemp, cp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { bindManifest, canonical, manifestPayload, TARGETS, freshReview, validateReview, validateTargets, parseReview, parseJSONStrict, serializeReview, postPending, submitReview, disposition, persistBrowser, proposeDesignDoc } from '../skills/orbyn-ui-design/examples/review-workspace/model.mjs';
import { prepareProposal } from '../skills/orbyn-ui-design/examples/review-workspace/reconcile.mjs';
const source = new URL('../skills/orbyn-ui-design/examples/review-workspace/', import.meta.url);
const manifest = JSON.parse(await readFile(new URL('manifest.json', source), 'utf8'));
bindManifest(manifest);
const context = () => ({ page: 'work', state: 'default', theme: 'light', density: 'comfortable', viewport: { width: 1280, height: 800 } });
const draft = (id = 'first', targetId = 'work/alpha/open', text = 'Make this clearer') => {
  const doc = freshReview(); doc.pending = { targetId, context: context(), text }; return postPending(doc, id);
};
const digest = data => createHash('sha256').update(data).digest('hex');
test('manifest is sealed to actual assets and unique target instances', async () => {
  assert.equal(digest(manifestPayload(manifest)), manifest.prototype.fingerprint);
  for (const [name, expected] of Object.entries(manifest.assets)) assert.equal(digest(await readFile(new URL(name, source))), expected);
  assert.equal(canonical(manifest.targets), canonical(TARGETS));
  assert.throws(() => validateTargets([...TARGETS, TARGETS[0]]), /Duplicate/);
  assert.notEqual(TARGETS.find(t => t.id === 'work/alpha/open').instance, TARGETS.find(t => t.id === 'work/beta/open').instance);
});
test('settings, pending text and comment survive strict roundtrip', () => {
  const doc = draft(); doc.settings.theme = 'dark'; doc.pending = { targetId: 'work/beta/open', context: context(), text: 'Unposted words' };
  assert.deepEqual(parseReview(serializeReview(doc)), doc);
  assert.throws(() => submitReview(doc), /Post pending/);
  assert.equal(doc.pending.text, 'Unposted words');
});
test('bad JSON, duplicate escaped keys, unknown fields and oversized input reject', () => {
  const raw = serializeReview(draft());
  assert.throws(() => parseReview('{'));
  assert.throws(() => parseJSONStrict('{"x":1,"\\u0078":2}'), /Duplicate/);
  assert.throws(() => parseReview(raw.replace('"schemaVersion": 1', '"schemaVersion": 1, "extra": true')));
  assert.throws(() => parseJSONStrict(' '.repeat(524289)));
  assert.throws(() => parseJSONStrict('[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[1]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]'));
});
test('stale source/version/target and duplicate comment IDs refuse', () => {
  for (const mutate of [d => d.prototype.version++, d => d.prototype.fingerprint = '0'.repeat(64), d => d.comments[0].targetId = 'removed/button', d => d.comments.push(d.comments[0]), d => d.comments[0].context.page = 'settings']) {
    const doc = draft(); mutate(doc); assert.throws(() => validateReview(doc));
  }
});
test('finite bounded typed fields and actual booleans are required', () => {
  for (const mutate of [d => d.comments[0].context.viewport.width = Infinity, d => d.comments[0].context.viewport.height = true, d => d.settings.notifications = 'yes', d => d.comments[0].text = ' ', d => d.comments[0].text = 'x'.repeat(3001)]) {
    const doc = draft(); mutate(doc); assert.throws(() => validateReview(doc));
  }
  assert.throws(() => parseReview(serializeReview(draft()).replace('1280', '1e400')));
});
test('storage permission/quota/readback failures do not claim saved', () => {
  const doc = draft();
  assert.equal(persistBrowser(doc, () => { throw Error('denied'); }).ok, false);
  assert.equal(persistBrowser(doc, () => ({ setItem() { throw Error('quota'); } })).ok, false);
  assert.equal(persistBrowser(doc, () => ({ setItem() {}, getItem() { return null; } })).ok, false);
  const map = new Map(); const result = persistBrowser(doc, () => ({ setItem(k,v) { map.set(k,v); }, getItem(k) { return map.get(k); } }));
  assert.equal(result.ok, true); assert.match(result.message, /not saved to repository/); assert.equal(doc.comments.length, 1);
});
test('submitted comments retain words; disposition is separate and target stable', () => {
  const original = '<img src=x onerror=alert(1)> Do not execute';
  const doc = submitReview(draft('first', 'work/alpha/open', original));
  const next = disposition(doc, 'first', 'accepted', 'Use a clear outcome label');
  assert.equal(next.comments[0].text, original); assert.equal(next.comments[0].targetId, 'work/alpha/open'); assert.equal(doc.comments[0].disposition, 'unresolved');
  assert.throws(() => disposition(draft(), 'first', 'accepted', 'reason'));
  assert.throws(() => disposition(doc, 'unknown', 'accepted', 'reason'));
  assert.throws(() => disposition(doc, 'first', 'accepted', ''));
});
test('design proposal preserves exact existing content and unresolved questions', () => {
  let doc = draft(); doc.pending = { targetId: 'work/beta/open', context: context(), text: 'Still deciding' }; doc = submitReview(postPending(doc, 'second'));
  doc = disposition(doc, 'first', 'accepted', 'Name the destination');
  const before = '# Existing Design\n\nPreserve my brand and authored notes.\n';
  const proposed = proposeDesignDoc(before, doc);
  assert.ok(proposed.includes(doc.prototype.fingerprint));
  assert.ok(proposed.startsWith(before)); assert.match(proposed, /Name the destination/); assert.match(proposed, /unresolved: second/); assert.match(proposed, /Still deciding/);
  assert.equal(proposeDesignDoc(proposed, doc), proposed);
  assert.throws(() => proposeDesignDoc(before, draft()), /Submit/);
  assert.throws(() => proposeDesignDoc('<!-- prototype-review:export-room:start -->', doc), /Ambiguous/);
});
test('real file proposal readback preserves exact-case owner and rejected state', async () => {
  const root = await mkdtemp(join(tmpdir(), 'prototype-review-'));
  try {
    const pkg = join(root, 'package'); await cp(source, pkg, { recursive: true });
    const doc = submitReview(draft()); await writeFile(join(pkg, 'review.json'), JSON.stringify({ revision: 1, review: doc }));
    const owner = join(root, 'Design.md'), before = '# Product design\n\nKeep this.\n'; await writeFile(owner, before);
    const decisionsFile = join(root, 'decisions.json'); await writeFile(decisionsFile, JSON.stringify([{ commentId: 'first', disposition: 'rejected', reason: 'Keep existing brand' }]));
    const output = join(root, 'proposal'); const receipt = await prepareProposal({ packageRoot: pkg, designDoc: owner, output, decisionsFile });
    assert.equal(await readFile(owner, 'utf8'), before); assert.equal(receipt.designDocWritten, false);
    assert.match(await readFile(join(output, 'proposed-design.md'), 'utf8'), /rejected: first/);
    const saved = JSON.parse(await readFile(join(output, 'reconciled-review.json'), 'utf8')); assert.equal(saved.comments[0].text, doc.comments[0].text);
    await assert.rejects(prepareProposal({ packageRoot: pkg, designDoc: owner, output }), /EEXIST/);
    await writeFile(join(pkg, 'review.css'), 'changed'); await assert.rejects(prepareProposal({ packageRoot: pkg, designDoc: owner, output: join(root, 'stale') }), /source changed/);
  } finally { await rm(root, { recursive: true, force: true }); } // Only this fixture's unique temp root.
});
