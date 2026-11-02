import assert from 'node:assert/strict';
import { test } from 'node:test';
import { compareSeries, familyOf, fit, matrixPart, measure, parseEasing, seriesFromTrack, springCurve } from '../scripts/easing.mjs';
import { sampleCurve } from './helpers.mjs';

const near = (actual, expected, tolerance, label) => assert.ok(Math.abs(actual - expected) <= tolerance, `${label}: ${actual} is not within ${tolerance} of ${expected}`);

test('an ease-out curve gives its family, delay and full declared duration, not the visible one', () => {
  const series = sampleCurve(parseEasing('cubic-bezier(0.22,1,0.36,1)'));
  const { stats, fits } = fit(series);
  assert.equal(fits[0].family, 'out');
  assert.ok(fits[0].rmse < 0.01, `rmse ${fits[0].rmse}`);
  near(fits[0].delayMs, 200, 20, 'delay');
  near(fits[0].durationMs, 700, 35, 'duration');
  assert.ok(stats.endMs - stats.startMs < 600, 'the visible window ends before the declared duration');
});

test('a start between two samples still fits the declared duration', () => {
  const { fits } = fit(sampleCurve(parseEasing('cubic-bezier(0.22,1,0.36,1)'), { delay: 440 }));
  near(fits[0].delayMs, 440, 8, 'delay');
  near(fits[0].durationMs, 700, 21, 'duration');
});

test('an ease-in curve recovers a start far before the first visible change', () => {
  const series = sampleCurve(parseEasing('cubic-bezier(0.32,0,0.67,0)'));
  const { stats, fits } = fit(series);
  assert.ok(stats.startMs > 300, `visible start ${stats.startMs} should lag the true start`);
  assert.equal(fits[0].family, 'in');
  near(fits[0].delayMs, 200, 45, 'delay');
  near(fits[0].durationMs, 700, 70, 'duration');
});

test('linear and ease-in-out curves are told apart', () => {
  assert.equal(fit(sampleCurve((t) => t)).fits[0].family, 'linear');
  assert.equal(fit(sampleCurve(parseEasing('cubic-bezier(0.65,0,0.35,1)'))).fits[0].family, 'in-out');
});

test('a spring with overshoot fits as a spring and recovers stiffness and damping', () => {
  const curve = springCurve(170, 14);
  const series = [];
  for (let t = 0; t <= 2000; t += 1000 / 60) series.push([t, 100 * curve((t - 100) / 1000)]);
  const { stats, fits } = fit(series);
  near(stats.overshootPct, 13.5, 1, 'overshoot');
  assert.equal(fits[0].name, 'spring');
  assert.equal(fits[0].family, 'spring');
  near(fits[0].stiffness, 170, 34, 'stiffness');
  near(fits[0].damping, 14, 2.8, 'damping');
  assert.ok(fits[0].rmse < 0.02, `rmse ${fits[0].rmse}`);
});

test('a falling value measures the same as a rising one', () => {
  const { stats, fits } = fit(sampleCurve(parseEasing('cubic-bezier(0.22,1,0.36,1)'), { from: 48, to: 0 }));
  assert.equal(stats.range, -48);
  assert.equal(fits[0].family, 'out');
});

test('familyOf classifies by the shape of the curve', () => {
  assert.equal(familyOf((t) => t), 'linear');
  assert.equal(familyOf(parseEasing('ease-out')), 'out');
  assert.equal(familyOf(parseEasing('ease-in')), 'in');
  assert.equal(familyOf(parseEasing('ease-in-out')), 'in-out');
  assert.equal(familyOf(parseEasing('cubic-bezier(0.34,1.56,0.64,1)')), 'overshoot');
});

test('parseEasing rejects what it cannot read', () => {
  assert.throws(() => parseEasing('wobble'), /Unknown easing/);
  assert.throws(() => parseEasing('cubic-bezier(1,2,3)'), /Unknown easing/);
});

test('a flat series reports no motion and a short one is an error', () => {
  assert.equal(measure([[0, 1], [1, 1], [2, 1], [3, 1]]).moved, false);
  assert.deepEqual(fit([[0, 1], [1, 1], [2, 1], [3, 1]]).fits, []);
  assert.throws(() => measure([[0, 1], [1, 2]]), /Not enough samples/);
});

test('motion that returns to its start is measured but has no fit', () => {
  const { stats, fits } = fit([[0, 0], [100, 0], [200, 5], [300, 10], [400, 5], [500, 0], [600, 0]]);
  assert.equal(stats.moved, true);
  assert.equal(stats.startMs, 100);
  assert.deepEqual(fits, []);
});

test('transform matrices give translation, scale and rotation', () => {
  assert.deepEqual(matrixPart('none'), { tx: 0, ty: 0, sx: 1, sy: 1, rot: 0 });
  const part = matrixPart('matrix(0, 2, -2, 0, 5, 7)');
  near(part.tx, 5, 1e-9, 'tx'); near(part.ty, 7, 1e-9, 'ty'); near(part.sx, 2, 1e-9, 'sx'); near(part.rot, 90, 1e-9, 'rot');
  const solid3d = matrixPart('matrix3d(1,0,0,0, 0,1,0,0, 0,0,1,0, 11,13,0,1)');
  near(solid3d.tx, 11, 1e-9, 'tx3d'); near(solid3d.ty, 13, 1e-9, 'ty3d');
});

test('a track gives one series per selector and property, skipping missing elements', () => {
  const track = { samples: [
    { t: 0, els: { '.a': { x: 1, y: 2, w: 3, h: 4, opacity: 0.5, transform: 'matrix(1, 0, 0, 1, 9, 8)' } } },
    { t: 16, els: { '.a': null } },
  ] };
  assert.deepEqual(seriesFromTrack(track, '.a', 'translateY'), [[0, 8]]);
  assert.deepEqual(seriesFromTrack(track, '.a', 'opacity'), [[0, 0.5]]);
  assert.throws(() => seriesFromTrack(track, '.a', 'colour'), /Unknown prop/);
});

test('compareSeries reports the gap between two tracks at matching times', () => {
  assert.deepEqual(compareSeries([[0, 0], [10, 10]], [[0, 1], [10, 13]]), { samples: 2, maxAbsDiff: 3, meanAbsDiff: 2 });
});
