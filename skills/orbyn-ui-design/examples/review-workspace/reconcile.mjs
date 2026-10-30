// Explicit local agent operation. Produces a new proposal; never overwrites design docs.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { bindManifest, manifestPayload, parseJSONStrict, validateReview, disposition, proposeDesignDoc } from './model.mjs';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
export async function prepareProposal({ packageRoot, designDoc, output, decisionsFile = null }) {
  const root = resolve(packageRoot), manifest = parseJSONStrict(await readFile(join(root, 'manifest.json'), 'utf8'));
  const fingerprint = hash(manifestPayload(manifest));
  if (fingerprint !== manifest.prototype.fingerprint) throw Error('Invalid source manifest');
  for (const [name, expected] of Object.entries(manifest.assets)) {
    if (!['index.html', 'review.css', 'review.mjs', 'model.mjs', 'boot.mjs'].includes(name) || hash(await readFile(join(root, name))) !== expected) throw Error('Prototype source changed');
  }
  bindManifest(manifest);
  const saved = parseJSONStrict(await readFile(join(root, 'review.json'), 'utf8'));
  if (Object.keys(saved).sort().join('|') !== 'review|revision' || !Number.isInteger(saved.revision) || saved.revision < 1) throw Error('Invalid saved package');
  let review = validateReview(saved.review);
  if (review.state !== 'submitted') throw Error('Review is not submitted');
  if (decisionsFile) {
    const decisions = parseJSONStrict(await readFile(decisionsFile, 'utf8'));
    if (!Array.isArray(decisions) || decisions.length > 200) throw Error('Invalid decisions');
    const seen = new Set();
    for (const d of decisions) {
      if (!d || Object.keys(d).sort().join('|') !== 'commentId|disposition|reason' || seen.has(d.commentId)) throw Error('Duplicate/unknown decision fields');
      seen.add(d.commentId); review = disposition(review, d.commentId, d.disposition, d.reason);
    }
  }
  const before = await readFile(designDoc, 'utf8'), proposed = proposeDesignDoc(before, review);
  // Caller resolves the existing exact-case document owner and authorizes this output.
  // Keep partial outputs on failure instead of deleting another user's files.
  await mkdir(output);
  await writeFile(join(output, 'proposed-design.md'), proposed, { flag: 'wx' });
  await writeFile(join(output, 'reconciled-review.json'), JSON.stringify(review, null, 2) + '\n', { flag: 'wx' });
  const receipt = { sourceFingerprint: fingerprint, reviewRevision: saved.revision, designDoc: resolve(designDoc), beforeSha256: hash(before), proposalSha256: hash(proposed), accepted: review.comments.filter(c => c.disposition === 'accepted').map(c => c.id), unresolved: review.comments.filter(c => c.disposition === 'unresolved').map(c => c.id), designDocWritten: false };
  await writeFile(join(output, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  if (await readFile(join(output, 'proposed-design.md'), 'utf8') !== proposed) throw Error('Proposal readback differs');
  return receipt;
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const args = process.argv.slice(2), values = {};
  if (args.length % 2) throw Error('Use --package PATH --design-doc PATH --output NEW_DIR [--decisions PATH]');
  for (let i = 0; i < args.length; i += 2) {
    if (!['--package', '--design-doc', '--output', '--decisions'].includes(args[i]) || values[args[i]]) throw Error('Unknown/duplicate argument');
    values[args[i]] = args[i + 1];
  }
  if (!values['--package'] || !values['--design-doc'] || !values['--output']) throw Error('Package, existing design document and new output are required');
  console.log(JSON.stringify(await prepareProposal({ packageRoot: values['--package'], designDoc: values['--design-doc'], output: values['--output'], decisionsFile: values['--decisions'] }), null, 2));
}
