import test from 'node:test';
import assert from 'node:assert/strict';
import { validateVector, sampleVector, plotPath, vectorComponent } from './vector.mjs';
import { toLottie, sampleLottie, validateLottie } from './lottie.mjs';

export const fixture = () => ({ version: 1, width: 400, height: 300, shapes: [
  { id: 'contour', fill: '#ffffff', stroke: '#204c52', strokeWidth: 4,
    from: [{ op: 'M', values: [40, 100] }, { op: 'C', values: [80, 20, 120, 20, 160, 100] }, { op: 'L', values: [100, 200] }, { op: 'Z', values: [] }],
    to: [{ op: 'M', values: [60, 120] }, { op: 'C', values: [100, 40, 140, 40, 180, 120] }, { op: 'L', values: [120, 220] }, { op: 'Z', values: [] }],
  },
] });
test('morph samples exact endpoints and midpoint without mutating source or inheriting seek order', () => {
  const spec = fixture(), original = JSON.stringify(spec);
  assert.deepEqual(sampleVector(spec, 0).shapes[0].commands, spec.shapes[0].from);
  assert.deepEqual(sampleVector(spec, 1).shapes[0].commands, spec.shapes[0].to);
  assert.deepEqual(sampleVector(spec, .5).shapes[0].commands[0].values, [50, 110]);
  const later = sampleVector(spec, .7); sampleVector(spec, .1);
  assert.deepEqual(sampleVector(spec, .7), later); assert.equal(JSON.stringify(spec), original);
});
test('unsupported topology, unknown content, nonfinite values and false optional data reject', () => {
  for (const mutate of [s => s.shapes[0].to.pop(), s => s.shapes[0].to[1].op = 'Q', s => s.shapes[0].from[0].values[0] = NaN, s => s.shapes[0].html = '<script>', s => s.shapes[0].to = false, s => s.shapes[0].fillRule = '']) {
    const spec = fixture(); mutate(spec); assert.throws(() => validateVector(spec));
  }
  assert.throws(() => sampleVector(fixture(), Infinity));
});
test('trusted mathematical plot has the expected domain endpoints and refuses invalid function values', () => {
  const p = plotPath(Math.sin, { from: 0, to: Math.PI, samples: 3, scaleX: 1, scaleY: 1 });
  assert.deepEqual(p[0], { op: 'M', values: [0, 0] }); assert.ok(Math.abs(p[1].values[1] - 1) < 1e-12);
  assert.throws(() => plotPath(() => NaN)); assert.throws(() => plotPath('sin(x)'));
});
test('code-authored Lottie preserves cubic geometry and sampled morph values', () => {
  const spec = fixture(), data = toLottie(spec, { durationFrames: 61 });
  const a = sampleLottie(data, 0), b = sampleLottie(data, 30), c = sampleLottie(data, 60);
  assert.deepEqual(a.shapes[0].commands, spec.shapes[0].from);
  assert.deepEqual(b.shapes[0].commands[0].values, [50, 110]);
  assert.deepEqual(c.shapes[0].commands, spec.shapes[0].to);
  assert.deepEqual(sampleLottie(data, 30), b);
});
test('Lottie refuses expression, remote/precomp assets, masks, text and unsupported style instead of stripping them', () => {
  for (const mutate of [d => d.layers[0].ks.x = 'fetch(secret)', d => d.assets.push({ p: 'https://example.com/a.png' }), d => d.layers[0].masksProperties = [], d => d.layers[0].ty = 5, d => d.layers[0].shapes.push({ ty: 'tm' }), d => d.layers[0].shapes[1].o.k = 50, d => d.layers[0].shapes[0].ks.k[0].o = { x: .1, y: .9 }]) {
    const data = toLottie(fixture()); mutate(data); assert.throws(() => validateLottie(data));
  }
});
test('nested groups and static layer transforms preserve actual point positions and opacity', () => {
  const data = toLottie(fixture()); data.layers[0].ks = { p: { a: 0, k: [10, 20] }, o: { a: 0, k: 50 } };
  data.layers[0].shapes = [{ ty: 'gr', it: data.layers[0].shapes }];
  const state = sampleLottie(data, 0);
  assert.deepEqual(state.shapes[0].commands[0].values, [50, 120]); assert.equal(state.shapes[0].opacity, .5);
});
test('custom vector component honors reduced motion independently of track sampling', () => {
  const state = vectorComponent().sample({ id: 'figure', props: { vector: fixture(), duration: 2 }, localTime: .1, worldMatrix: [1, 0, 0, 1, 0, 0], opacity: 1, zIndex: 0, reducedMotion: true });
  assert.deepEqual(state.shapes[0].commands, fixture().shapes[0].to);
});
