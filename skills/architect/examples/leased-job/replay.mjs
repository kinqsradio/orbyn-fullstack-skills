#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { LeasedJob } from './job.mjs';

// This deliberately narrow decoder handles only this sample's scalar/2-slot states.
export function decodeTrace(text) {
  const states = [];
  const parts = text.split(/^State \d+: <([^\n]+)>\r?\n/gm);
  for (let i = 1; i + 1 < parts.length; i += 2) {
    const match = [null, parts[i], parts[i + 1]];
    const values = {};
    for (const line of match[2].split('\n')) {
      const field = line.match(/^\/\\ (\w+) = (.+)$/);
      if (!field) continue;
      const [, key, raw] = field;
      if (raw.startsWith('<<')) values[key] = raw.slice(2, -2).split(',').map(Number);
      else if (/^\d+$/.test(raw)) values[key] = Number(raw);
      else if (raw === 'TRUE' || raw === 'FALSE') values[key] = raw === 'TRUE';
      else if (raw.startsWith('"')) values[key] = JSON.parse(raw);
      else throw new Error(`Unsupported sample value: ${raw}`);
    }
    if (Object.keys(values).length !== 8) throw new Error('Incomplete sample trace state');
    states.push({ action: match[1].split(' ')[0], values });
  }
  if (states.length < 2) throw new Error('No complete sample counterexample');
  return states;
}
function observed(job) {
  const s = job.snapshot();
  return { phase: s.phase, generation: s.generation, owner: s.owner, tokens: s.tokens,
    resultGeneration: s.result?.generation ?? 0, resultWorker: s.result?.worker ?? 0,
    publishCount: s.published.length, lateCancel: s.lateCancel };
}
function invoke(job, before, after, action) {
  if (action === 'Claim') return job.claim(after.owner);
  if (action === 'Complete') {
    const worker = [1, 2].find(w => before.tokens[w - 1] !== after.tokens[w - 1]);
    assert.ok(worker, 'Trace must identify the consumed delivery slot');
    return job.complete(worker);
  }
  const methods = { Expire: 'expire', Cancel: 'cancel', LateCancel: 'cancelAfterCommit', Publish: 'publish', Terminal: 'terminal' };
  assert.ok(methods[action], `Unmapped action ${action}`);
  return job[methods[action]]();
}
export function replay(text) {
  const states = decodeTrace(text);
  const broken = new LeasedJob({ brokenCompletion: true });
  assert.deepEqual(observed(broken), states[0].values);
  const initial = broken.snapshot();
  const events = [];
  for (let i = 1; i < states.length; i++) {
    const accepted = invoke(broken, states[i - 1].values, states[i].values, states[i].action);
    assert.deepEqual(observed(broken), states[i].values, `Broken code diverged at step ${i}`);
    events.push({ step: i, action: states[i].action, accepted, state: broken.snapshot() });
  }
  assert.notEqual(broken.result.generation, broken.generation, 'Broken variant must expose a stale durable payload');
  const fixed = new LeasedJob();
  let rejection = null;
  for (let i = 1; i < states.length; i++) {
    const accepted = invoke(fixed, states[i - 1].values, states[i].values, states[i].action);
    if (!accepted && states[i].action === 'Complete') { rejection = i; break; }
    assert.deepEqual(observed(fixed), states[i].values);
  }
  assert.ok(rejection, 'Fixed code must reject the stale completion');
  assert.equal(fixed.result, null); assert.equal(fixed.phase, 'leased');
  assert.equal(fixed.generation, 2); assert.equal(fixed.tokens.filter(Boolean).length, 1);
  const currentWorker = fixed.owner;
  assert.equal(fixed.tokens[currentWorker - 1], 2);
  assert.equal(fixed.complete(currentWorker), true);
  const result = { ...fixed.result };
  assert.equal(fixed.cancel(), false);
  assert.equal(fixed.cancelAfterCommit(), true);
  assert.deepEqual(fixed.result, result); assert.equal(fixed.phase, 'done');
  assert.equal(fixed.publish(), true); assert.equal(fixed.publish(), true);
  assert.equal(fixed.published.length, 1); assert.equal(fixed.published[0].generation, 2);
  const cancelled = new LeasedJob(); cancelled.claim(1); cancelled.cancel();
  assert.equal(cancelled.complete(1), false); assert.equal(cancelled.publish(), false);
  assert.equal(cancelled.result, null); assert.equal(cancelled.published.length, 0);
  return { status: 'assertions passed', traceSteps: states.length - 1, broken: broken.snapshot(),
    initial, fixedRejectedStep: rejection, fixed: fixed.snapshot(), cancelled: cancelled.snapshot(), events,
    limits: 'Serialized synthetic public methods; not distributed database/lock conformance.' };
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.length !== 3) throw new Error('Usage: node replay.mjs /owned/compiler/tlc.out');
    const text = fs.readFileSync(process.argv[2], 'utf8');
    const receipt = replay(text);
    receipt.traceSha256 = crypto.createHash('sha256').update(text).digest('hex');
    receipt.sourceSha256 = crypto.createHash('sha256').update(fs.readFileSync(new URL('./job.mjs', import.meta.url))).digest('hex');
    console.log(JSON.stringify(receipt, null, 2));
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
