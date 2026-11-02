import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';
import { parseEasing } from '../scripts/easing.mjs';
import { checkSpec, draftSpec, unfinished, validateSpec } from '../scripts/spec.mjs';
import { runScript, workspace } from './helpers.mjs';

const OUT = 'cubic-bezier(0.22,1,0.36,1)';

/** A track of three cards with opacity and translateY, plus a fourth still element. */
function track({ delay = 200, stagger = 120, easing = OUT, duration = 700, distance = 48, drift = 0 } = {}) {
  const curve = parseEasing(easing);
  const samples = [];
  for (let t = 0; t <= 1800; t += 1000 / 60) {
    const els = {};
    [0, 1, 2].forEach((i) => {
      const p = curve((t - delay - i * stagger) / duration);
      els[`.card-${i}`] = { x: 0, y: 0, w: 10, h: 10, opacity: p, transform: `matrix(1, 0, 0, 1, 0, ${distance * (1 - p)})` };
    });
    els['.frame'] = { x: 0, y: 0, w: 10, h: 10, opacity: 1, transform: `matrix(1, 0, 0, 1, ${drift * Math.min(1, t / 600)}, 0)` };
    samples.push({ t, els });
  }
  return { selectors: ['.card-0', '.card-1', '.card-2', '.frame'], rights: 'own', samples };
}

function finishedSpec(overrides = {}) {
  return { ...draftSpec(track(), { name: 'cards', fidelity: 'motion', rights: 'own', props: ['opacity', 'translateY', 'translateX'] }), target: 'test page', destination: 'test page', ...overrides };
}

const failures = (result) => result.rows.flatMap((row) => row.failures);

test('draft writes one row per element per property and marks still ones', () => {
  const spec = finishedSpec();
  assert.equal(spec.rows.length, 4 * 3);
  const moving = spec.rows.filter((row) => !row.still);
  assert.equal(moving.length, 6);
  assert.ok(moving.every((row) => row.family === 'out'));
  assert.deepEqual(moving.filter((row) => row.prop === 'opacity').map((row) => Math.round(row.delayMs / 10) * 10), [200, 320, 440]);
  assert.ok(moving.every((row) => Math.abs(row.durationMs - 700) < 25), JSON.stringify(moving.map((row) => row.durationMs)));
});

test('the same motion passes every row and gap', () => {
  const result = checkSpec(finishedSpec(), track());
  assert.equal(result.passed, true, JSON.stringify(failures(result)));
  assert.equal(result.stagger.length, 4);
});

test('a late start fails start and end but not the easing', () => {
  const result = checkSpec(finishedSpec(), track({ delay: 500 }));
  assert.equal(result.passed, false);
  const row = result.rows.find((item) => item.selector === '.card-0' && item.prop === 'opacity');
  assert.ok(Math.abs(row.startErrorMs - 300) < 20);
  assert.ok(row.failures.some((item) => item.startsWith('start')));
  assert.ok(!row.failures.some((item) => item.startsWith('easing')), row.failures.join());
  assert.ok(result.stagger.every((gap) => gap.pass));
});

test('a linear clone fails on easing and names both families', () => {
  const result = checkSpec(finishedSpec(), track({ easing: 'linear' }));
  const row = result.rows.find((item) => item.selector === '.card-1' && item.prop === 'translateY');
  assert.ok(row.easingRmse > 0.2, String(row.easingRmse));
  assert.equal(row.ourFamily, 'linear');
  assert.match(row.failures.join(), /easing RMSE .*spec out, ours linear/);
  assert.ok(Math.abs(row.startErrorMs) <= 80);
});

test('a wrong stagger fails on the gaps, even when each start is inside its own limit', () => {
  const result = checkSpec(finishedSpec(), track({ stagger: 60, delay: 260 }));
  const gaps = result.stagger.filter((gap) => !gap.pass);
  assert.equal(gaps.length, 4);
  assert.ok(gaps.every((gap) => Math.abs(gap.errorMs + 60) < 20));
  const first = result.rows.find((item) => item.selector === '.card-1' && item.prop === 'opacity');
  assert.deepEqual(first.failures, [], 'card 1 starts within 80 ms; only the gap gives it away');
  assert.equal(result.passed, false);
});

test('a short travel distance fails, and 5% stays inside the limit', () => {
  assert.match(failures(checkSpec(finishedSpec(), track({ distance: 30 }))).join(), /distance off by 37.5%/);
  assert.equal(checkSpec(finishedSpec(), track({ distance: 46 })).passed, true);
});

test('something moving where the reference is still fails', () => {
  assert.match(failures(checkSpec(finishedSpec(), track({ drift: 12 }))).join(), /moves by 12 where the reference is still/);
});

test('a row that does not move, or is missing from our track, fails', () => {
  const noMotion = track({ distance: 0 });
  assert.match(failures(checkSpec(finishedSpec(), noMotion)).join(), /does not move/);
  const gone = track();
  gone.samples.forEach((sample) => { delete sample.els['.card-2']; });
  assert.match(failures(checkSpec(finishedSpec(), gone)).join(), /missing from our track/);
});

test('cloneSelector maps a row to our own element', () => {
  const spec = finishedSpec();
  spec.rows.forEach((row) => { if (row.selector === '.card-0') row.cloneSelector = '.tile-0'; });
  const ours = track();
  ours.samples.forEach((sample) => { sample.els['.tile-0'] = sample.els['.card-0']; delete sample.els['.card-0']; });
  assert.equal(checkSpec(spec, ours).passed, true);
});

test('a spring row checks against the spring curve', () => {
  const series = [];
  const stiffness = 170;
  const damping = 14;
  const spec = { schema: 1, name: 's', rights: 'own', fidelity: 'motion', target: 't', destination: 'd', rows: [
    { selector: '.a', prop: 'opacity', from: 0, to: 1, startMs: 100, endMs: 900, delayMs: 100, durationMs: 800, easing: `spring(${stiffness},${damping})`, family: 'spring', overshootPct: 15, source: 'test' },
  ] };
  const omega = Math.sqrt(stiffness);
  const zeta = damping / (2 * omega);
  const damped = omega * Math.sqrt(1 - zeta * zeta);
  const value = (s) => (s <= 0 ? 0 : 1 - Math.exp(-zeta * omega * s) * (Math.cos(damped * s) + (zeta * omega / damped) * Math.sin(damped * s)));
  for (let t = 0; t <= 1800; t += 1000 / 60) series.push({ t, els: { '.a': { x: 0, y: 0, w: 1, h: 1, opacity: value((t - 100) / 1000), transform: 'none' } } });
  const good = checkSpec(spec, { samples: series });
  assert.ok(good.rows[0].easingRmse < 0.02, String(good.rows[0].easingRmse));
});

test('every "?" is listed and stops the check', () => {
  const spec = finishedSpec();
  spec.rows[0].easing = '?';
  assert.deepEqual(unfinished({ ...spec, target: '?' }).length, 2);
  assert.throws(() => validateSpec(spec), /unfinished[\s\S]*easing/);
  assert.throws(() => checkSpec(spec, track()), /unfinished/);
});

test('a draft cannot fit a curve it cannot read, so it writes "?"', () => {
  const noisy = track();
  noisy.samples.forEach((sample, index) => { sample.els['.card-0'].opacity = index % 7 > 3 && sample.t > 200 ? 1 : 0; });
  const spec = draftSpec(noisy, { name: 'n', fidelity: 'motion', rights: 'own', props: ['opacity'], selectors: ['.card-0'] });
  assert.equal(spec.rows[0].easing, '?');
});

test('a third-party reference cannot be drafted or checked at pixel fidelity', () => {
  assert.throws(() => draftSpec(track(), { name: 'x', fidelity: 'pixel', rights: 'third-party' }), /motion level only/);
  assert.throws(() => validateSpec(finishedSpec({ rights: 'third-party', fidelity: 'pixel' })), /motion level only/);
  assert.doesNotThrow(() => validateSpec(finishedSpec({ rights: 'third-party', fidelity: 'motion' })));
  assert.doesNotThrow(() => validateSpec(finishedSpec({ rights: 'licensed', fidelity: 'pixel' })));
});

test('the CLI exits 0 on pass, 1 on fail, 2 on "?" and 3 on a rights refusal', (t) => {
  const root = workspace(t);
  writeFileSync(join(root, 'ref.json'), JSON.stringify(track()));
  writeFileSync(join(root, 'late.json'), JSON.stringify(track({ delay: 500 })));
  const drafted = runScript('spec.mjs', ['draft', '--track', 'ref.json', '--fidelity', 'motion', '--name', 'cards', '--out', 'spec'], root);
  assert.equal(drafted.status, 0, drafted.stderr);
  assert.match(readFileSync(join(root, 'spec', 'spec.md'), 'utf8'), /\| \.card-0 \| opacity \|/);
  const unfinishedRun = runScript('spec.mjs', ['check', '--spec', 'spec/spec.json', '--track', 'ref.json', '--out', 'a'], root);
  assert.equal(unfinishedRun.status, 2);
  assert.match(unfinishedRun.stderr, /target/);
  const spec = JSON.parse(readFileSync(join(root, 'spec', 'spec.json'), 'utf8'));
  writeFileSync(join(root, 'done.json'), JSON.stringify({ ...spec, target: 'page', destination: 'page' }));
  assert.equal(runScript('spec.mjs', ['check', '--spec', 'done.json', '--track', 'ref.json', '--out', 'b'], root).status, 0);
  assert.equal(runScript('spec.mjs', ['check', '--spec', 'done.json', '--track', 'late.json', '--out', 'c'], root).status, 1);
  writeFileSync(join(root, 'pixel.json'), JSON.stringify({ ...spec, target: 'page', destination: 'page', rights: 'third-party', fidelity: 'pixel' }));
  assert.equal(runScript('spec.mjs', ['check', '--spec', 'pixel.json', '--track', 'ref.json', '--out', 'd'], root).status, 3);
});

test('a track with no rights record drafts as third-party', (t) => {
  const root = workspace(t);
  const { rights, ...plain } = track();
  writeFileSync(join(root, 'track.json'), JSON.stringify(plain));
  assert.equal(rights, 'own');
  assert.equal(runScript('spec.mjs', ['draft', '--track', 'track.json', '--fidelity', 'pixel', '--name', 'x', '--out', 'spec'], root).status, 3);
});

const pulseTrack = (height) => ({
  selectors: ['.a'],
  samples: Array.from({ length: 70 }, (_, i) => {
    const t = i * 20;
    const unit = Math.min(1, Math.max(0, (t - 100) / 1000));
    return { t, els: { '.a': { x: 0, y: 0, w: 1, h: 1, opacity: 1 - height * (1 - Math.abs(2 * unit - 1)), transform: 'none' } } };
  }),
});
const pulseRow = { selector: '.a', prop: 'opacity', from: 1, to: 1, peak: 0.5, startMs: 100, endMs: 1100, delayMs: 100, durationMs: 1000, easing: 'linear', family: 'linear' };
const pulseSpec = { schema: 1, name: 'p', rights: 'own', fidelity: 'motion', target: 'a', destination: 'b', rows: [pulseRow] };
const LIMITS = { timingMs: 80, staggerMs: 40, easingRmse: 0.05, distance: 0.1 };

test('a pulse is compared against its peak, so its easing gate stays live', () => {
  assert.equal(checkSpec(pulseSpec, pulseTrack(0.5), LIMITS).passed, true);
  const curved = { ...pulseSpec, rows: [{ ...pulseRow, easing: 'cubic-bezier(0.9,0,1,0.1)' }] };
  const wrong = checkSpec(curved, pulseTrack(0.5), LIMITS);
  assert.equal(wrong.passed, false);
  assert.match(wrong.rows[0].failures.join(), /easing/);
  assert.equal(checkSpec(pulseSpec, pulseTrack(0.2), LIMITS).passed, false);
});

test('a moving row needs real numbers, and a NaN curve can never pass', () => {
  const flat = checkSpec({ ...pulseSpec, rows: [{ ...pulseRow, peak: 1 }] }, pulseTrack(0.5), LIMITS);
  assert.equal(flat.passed, false);
  assert.match(flat.rows[0].failures.join(), /easing/);
  const { delayMs, ...missing } = pulseRow;
  assert.throws(() => validateSpec({ ...pulseSpec, rows: [missing] }), /delayMs/);
  const { peak, ...noPeak } = pulseRow;
  assert.throws(() => validateSpec({ ...pulseSpec, rows: [noPeak] }), /peak/);
  assert.throws(() => validateSpec({ ...pulseSpec, rows: [{ ...pulseRow, endMs: 'soon' }] }), /endMs/);
});

