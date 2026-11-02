import assert from 'node:assert/strict';
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';
import { alignByActivity, cumulative, motionWindow, setupDifferences, timingReport } from '../scripts/compare.mjs';
import { runScript, slidingFrame, workspace, writeFrames } from './helpers.mjs';

const FPS = 25;
const OWN = { fps: FPS, rights: 'own' };
const FRAMES = 40;

function pair(root, { late = 0, cloneMeta = OWN, refMeta = OWN, cloneOptions = {} } = {}) {
  writeFrames(join(root, 'ref'), FRAMES, (i) => slidingFrame(i), refMeta);
  writeFrames(join(root, 'ours'), FRAMES, (i) => slidingFrame(i, { start: 8 + late, end: 24 + late, ...cloneOptions }), cloneMeta);
}
const report = (root, name = 'out') => JSON.parse(readFileSync(join(root, name, 'report.json'), 'utf8'));

test('identical frames pass every gate at exit 0', (t) => {
  const root = workspace(t);
  pair(root);
  const run = runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out'], root);
  assert.equal(run.status, 0, run.stderr);
  const r = report(root);
  assert.equal(r.passed, true);
  assert.equal(r.meanMismatch, 0);
  assert.deepEqual(r.motion.error, { startS: 0, endS: 0, durationS: 0, peakS: 0 });
  assert.equal(readdirSync(join(root, 'out', 'diff')).length, FRAMES);
});

test('a planted five-frame delay fails timing and reports its size', (t) => {
  const root = workspace(t);
  pair(root, { late: 5 });
  const run = runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out'], root);
  assert.equal(run.status, 1);
  const r = report(root);
  assert.equal(r.offset, 0, 'a delay must not be aligned away');
  assert.equal(r.pass.timing, false);
  assert.equal(r.pass.curve, false);
  assert.equal(r.motion.error.startS, 5 / FPS);
  assert.equal(r.motion.error.endS, 5 / FPS);
});

test('a one-frame delay stays inside the 0.08 s limit', (t) => {
  const root = workspace(t);
  pair(root, { late: 1 });
  assert.equal(runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out'], root).status, 0);
  assert.equal(report(root).motion.error.startS, 1 / FPS);
});

test('a clone that never moves fails rather than reading as zero error', (t) => {
  const root = workspace(t);
  writeFrames(join(root, 'ref'), 20, (i) => slidingFrame(i), OWN);
  writeFrames(join(root, 'ours'), 20, () => slidingFrame(0), OWN);
  assert.equal(runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out'], root).status, 1);
  assert.equal(report(root).motion.error, null);
});

test('auto-align finds the planted offset for a video reference', (t) => {
  const root = workspace(t);
  pair(root, { late: 5 });
  const run = runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out', '--auto-align'], root);
  assert.equal(run.status, 0, run.stdout + run.stderr);
  const r = report(root);
  assert.equal(r.offset, 5);
  assert.equal(r.motion.error.startS, 0);
});

test('auto-align is refused between two captures, because it would hide a late start', (t) => {
  const root = workspace(t);
  writeFrames(join(root, 'r', 'frames'), 12, (i) => slidingFrame(i, { start: 2, end: 8 }));
  writeFrames(join(root, 'o', 'frames'), 12, (i) => slidingFrame(i, { start: 3, end: 9 }));
  for (const side of ['r', 'o']) {
    writeFileSync(join(root, side, 'capture.json'), JSON.stringify({ fps: FPS }));
    writeFileSync(join(root, side, 'frames.json'), JSON.stringify(OWN));
  }
  const run = runScript('compare.mjs', ['--ref', 'r/frames', '--clone', 'o/frames', '--out', 'out', '--auto-align'], root);
  assert.equal(run.status, 2);
  assert.match(run.stderr, /hide a late start/);
});

test('different capture settings fail the setup gate even when frames match', (t) => {
  const root = workspace(t);
  for (const [side, duration] of [['r', 1000], ['o', 1500]]) {
    writeFrames(join(root, side, 'frames'), 12, (i) => slidingFrame(i, { start: 2, end: 8 }));
    writeFileSync(join(root, side, 'frames.json'), JSON.stringify(OWN));
    writeFileSync(join(root, side, 'capture.json'), JSON.stringify({ fps: FPS, duration, rights: side === 'r' ? 'third-party' : 'own' }));
  }
  assert.equal(runScript('compare.mjs', ['--ref', 'r/frames', '--clone', 'o/frames', '--out', 'out'], root).status, 1);
  const r = report(root);
  assert.equal(r.pass.setup, false);
  assert.match(r.setupDifferences[0], /duration: reference 1000, ours 1500/);
  assert.equal(r.setupDifferences.length, 1, 'rights may differ: the reference and ours have different owners');
});

test('pixel fidelity is refused for a third-party reference and for one with no rights record', (t) => {
  const root = workspace(t);
  pair(root, { refMeta: { fps: FPS, rights: 'third-party' } });
  const refused = runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out', '--fidelity', 'pixel'], root);
  assert.equal(refused.status, 3);
  assert.match(refused.stderr, /motion-level/);
  const unknown = workspace(t);
  writeFrames(join(unknown, 'ref'), 10, (i) => slidingFrame(i));
  writeFrames(join(unknown, 'ours'), 10, (i) => slidingFrame(i));
  assert.equal(runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out', '--fidelity', 'pixel'], unknown).status, 3);
});

test('pixel fidelity gates on mismatch for our own reference', (t) => {
  const root = workspace(t);
  writeFrames(join(root, 'ref'), 12, (i) => slidingFrame(i, { start: 2, end: 8 }), OWN);
  writeFrames(join(root, 'ours'), 12, (i) => { const f = slidingFrame(i, { start: 2, end: 8 }); f.data.fill(255, 0, 64 * 8 * 4); return f; }, OWN);
  assert.equal(runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'motion'], root).status, 0);
  const run = runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'pixel', '--fidelity', 'pixel'], root);
  assert.equal(run.status, 1);
  assert.equal(report(root, 'pixel').pass.pixels, false);
});

test('third-party references get no diff images', (t) => {
  const root = workspace(t);
  pair(root, { refMeta: { fps: FPS, rights: 'third-party' } });
  assert.equal(runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out'], root).status, 0);
  assert.deepEqual(readdirSync(join(root, 'out')).sort(), ['report.json', 'report.md']);
});

test('frames of another size stop the comparison unless --rescale is passed', (t) => {
  const root = workspace(t);
  writeFrames(join(root, 'ref'), 4, (i) => slidingFrame(i), OWN);
  writeFrames(join(root, 'ours'), 4, (i) => slidingFrame(i, { width: 32, height: 16 }), OWN);
  const run = runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out'], root);
  assert.equal(run.status, 2);
  assert.match(run.stderr, /differ in size/);
});

test('--region compares only that part of each frame', (t) => {
  const root = workspace(t);
  writeFrames(join(root, 'ref'), 12, (i) => slidingFrame(i, { start: 2, end: 8 }), OWN);
  writeFrames(join(root, 'ours'), 12, (i) => { const f = slidingFrame(i, { start: 2, end: 8 }); f.data.fill(255, 0, 64 * 8 * 4); return f; }, OWN);
  assert.equal(runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out', '--fidelity', 'pixel', '--region', '0,8,64,24'], root).status, 0);
});

test('an empty folder and a missing folder are usage errors', (t) => {
  const root = workspace(t);
  mkdirSync(join(root, 'ref'));
  writeFrames(join(root, 'ours'), 2, (i) => slidingFrame(i));
  assert.equal(runScript('compare.mjs', ['--ref', 'ref', '--clone', 'ours', '--out', 'out'], root).status, 2);
  assert.equal(runScript('compare.mjs', ['--ref', 'absent', '--clone', 'ours', '--out', 'out'], root).status, 2);
});

test('motionWindow finds first, last and peak, and nothing in a still curve', () => {
  assert.deepEqual(motionWindow([0, 0, 0.01, 0.5, 0.01, 0, 0], 10), { first: 2, last: 4, peak: 3, durationS: 0.3 });
  assert.deepEqual(motionWindow([0, 0, 0], 10), { first: -1, last: -1, peak: -1, durationS: 0 });
});

test('cumulative curves are normalised to end at one', () => {
  assert.deepEqual(cumulative([1, 1, 2]), [0.25, 0.5, 1]);
  assert.deepEqual(cumulative([0, 0]), [0, 0]);
});

test('alignByActivity recovers early and late offsets, and zero for rest', () => {
  const curve = [0, 0, 0, 0, 0.2, 0.5, 0.2, 0.05, 0, 0, 0, 0, 0, 0];
  const later = [0, 0, 0, ...curve.slice(0, -3)];
  assert.equal(alignByActivity(curve, later, 6), 3);
  assert.equal(alignByActivity(later, curve, 6), -3);
  assert.equal(alignByActivity(curve, curve, 6), 0);
});

test('the curve gate catches a shape change that the window misses', () => {
  const frontLoaded = [0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.01, 0.01, 0];
  const even = [0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0];
  const result = timingReport(frontLoaded, even, 25);
  assert.equal(result.pass.timing, true);
  assert.equal(result.pass.curve, false);
});

test('setupDifferences lists only the settings that differ', () => {
  assert.deepEqual(setupDifferences({ fps: 25, seed: 1 }, { fps: 25, seed: 1 }), []);
  assert.deepEqual(setupDifferences({ fps: 25, viewport: { width: 1 } }, { fps: 30, viewport: { width: 1 } }), ['fps: reference 25, ours 30']);
  assert.deepEqual(setupDifferences(null, { fps: 25 }), []);
});
