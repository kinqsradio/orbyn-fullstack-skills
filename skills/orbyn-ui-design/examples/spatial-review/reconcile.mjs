// Explicit local proposal; never overwrites authored design notes or saved feedback.
import { readFile, writeFile, mkdir, lstat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { canonical, parseJSONStrict, validate, propose } from './review-model.mjs';
const [pkg, owner, decisionsFile, output] = process.argv.slice(2);
if (!pkg || !owner || !decisionsFile || !output || process.argv.length !== 6) throw Error('node reconcile.mjs PACKAGE EXISTING_DESIGN_DOC DECISIONS_JSON NEW_OUTPUT_DIR');
const hash = v => createHash('sha256').update(v).digest('hex');
const manifest = parseJSONStrict(await readFile(join(pkg, 'manifest.json'), 'utf8'));
for (const [name, digest] of Object.entries(manifest.assets)) {
  if (!/^[A-Za-z0-9_-][A-Za-z0-9_.-]*(?:\/[A-Za-z0-9_.-]+)*$/.test(name) || name.split('/').some(p => p.startsWith('.'))) throw Error('Unsafe source path');
  const parts = name.split('/'); for (let i = 1; i <= parts.length; i++) if ((await lstat(join(pkg, ...parts.slice(0, i)))).isSymbolicLink()) throw Error('Source link');
  if (hash(await readFile(join(pkg, name))) !== digest) throw Error('Stale source');
}
const { fingerprint, ...prototype } = manifest.prototype;
if (hash(canonical({ prototype, targets: manifest.targets, assets: manifest.assets })) !== fingerprint) throw Error('Stale manifest');
const saved = parseJSONStrict(await readFile(join(pkg, 'review.json'), 'utf8'));
if (Object.keys(saved).sort().join('|') !== 'review|revision' || !Number.isInteger(saved.revision) || saved.revision < 1) throw Error('Invalid saved revision');
const doc = validate(saved.review, manifest); if (doc.state !== 'submitted') throw Error('Submit first');
const decisions = parseJSONStrict(await readFile(decisionsFile, 'utf8'));
if (!Array.isArray(decisions) || decisions.length > 200) throw Error('Invalid decisions');
const ids = new Set();
for (const d of decisions) {
  if (!d || Object.keys(d).sort().join('|') !== 'commentId|disposition|reason' || ids.has(d.commentId) || !['accepted', 'rejected', 'unresolved'].includes(d.disposition)) throw Error('Invalid decision');
  ids.add(d.commentId); const c = doc.comments.find(c => c.id === d.commentId); if (!c) throw Error('Unknown comment'); c.disposition = d.disposition; c.decision = d.reason;
}
validate(doc, manifest);
const before = await readFile(owner, 'utf8'), proposal = propose(before, doc, manifest);
await mkdir(output); await writeFile(join(output, 'proposed-design.md'), proposal, { flag: 'wx' });
await writeFile(join(output, 'reconciled-review.json'), JSON.stringify(doc, null, 2) + '\n', { flag: 'wx' });
if (await readFile(join(output, 'proposed-design.md'), 'utf8') !== proposal) throw Error('Readback failure');
await writeFile(join(output, 'receipt.json'), JSON.stringify({ revision: saved.revision, sourceFingerprint: fingerprint, beforeSha256: hash(before), proposalSha256: hash(proposal), designDocWritten: false }, null, 2) + '\n', { flag: 'wx' });
