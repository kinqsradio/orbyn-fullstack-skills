// Called with an owned prepared package by Python; no runtime dependencies.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
const pkg = process.argv[2]; if (!pkg) throw Error('Prepared package required');
const { validate, parseReview, propose } = await import(pathToFileURL(join(pkg, 'review-model.mjs')));
const { timeline, filmFrame, FILM } = await import(pathToFileURL(join(pkg, 'timeline.mjs')));
const manifest = JSON.parse(await readFile(join(pkg, 'manifest.json'))), doc = JSON.parse(await readFile(join(pkg, 'input.json')));
assert.equal(validate(doc, manifest), doc);
for (const scenario of ['mechanism', 'interface', 'data', 'film']) {
  const frame = timeline(8.25, scenario); timeline(1, scenario); timeline(11, scenario); assert.deepEqual(timeline(8.25, scenario), frame);
  assert.equal(timeline(2.999, scenario).scene, 'overview'); assert.equal(timeline(3, scenario).scene, 'motion'); assert.equal(timeline(7, scenario).scene, 'detail'); assert.equal(timeline(10, scenario).scene, 'end');
  assert.equal(timeline(8, scenario, true).yaw, 0); assert.equal(timeline(8, scenario, true).typeScale, 1);
}
assert.equal(FILM.frames, 360); assert.equal(filmFrame(90).scene, 'motion'); assert.equal(filmFrame(300).composition, 'end-card'); assert.throws(() => filmFrame(360));
assert.notEqual(timeline(1, 'film').title, timeline(1, 'mechanism').title); assert.deepEqual(timeline(8, 'data').bars, [16,28,44,64]);
assert.throws(() => timeline(Infinity)); assert.throws(() => timeline(-1)); assert.throws(() => timeline(13));
for (const change of [d => d.prototype.version = true, d => d.settings.partId = [], d => d.settings.animation.time = true, d => d.settings.camera.yaw = Infinity, d => d.settings.animation.scene = 'wrong', d => d.settings.layers.guides = 1]) { const bad = structuredClone(doc); change(bad); assert.throws(() => validate(bad, manifest)); }
assert.throws(() => parseReview('{"schemaVersion":2,"\\u0073chemaVersion":2}', manifest));
doc.state = 'submitted'; doc.comments.push({ id: 'one', targetId: 'part/piston-B3', context: structuredClone(doc.settings), text: '<b>Keep words</b>', disposition: 'unresolved', decision: '' });
const authored = '# Existing DESIGN\n\nAuthored notes.\n'; const proposal = propose(authored, doc, manifest);
assert.ok(proposal.startsWith(authored)); assert.ok(proposal.includes(doc.prototype.fingerprint)); assert.ok(proposal.includes('unresolved')); assert.ok(!proposal.includes('<b>'));
assert.equal(propose(proposal, doc, manifest), proposal); assert.throws(() => propose('<!-- spatial-review:end -->\n<!-- spatial-review:start -->', doc, manifest));
console.log('Cross-language schema bad controls, deterministic seeks/cuts/reduced motion and preserved design proposal passed.');
