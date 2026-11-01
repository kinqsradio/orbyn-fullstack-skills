import assert from 'node:assert/strict';
import test from 'node:test';
import {layers, regions} from './regions.mjs';
import {blinkClosure, createMesh, defaultFeather, deform, displace, drawnState, invertedTriangles, peakDisplacement, regionWeight, validateRegions} from './puppet.mjs';

const box = [[.2, .1], [.8, .1], [.8, .9], [.2, .9]];
const hair = {id: 'hair', kind: 'hair', polygon: box, root: [.5, .1], tip: [.5, .9], amp: .03, period: 3};
const breath = {id: 'chest', kind: 'breath', polygon: [[.3, .6], [.7, .6], [.7, .95], [.3, .95]], amp: .008, period: 4, peakY: .78};
const sway = {id: 'head', kind: 'sway', polygon: [[.3, .1], [.7, .1], [.7, .5], [.3, .5]], pivot: [.5, .5], amp: .03, period: 5};
const eye = {id: 'eye', kind: 'blink', polygon: [[.3, .3], [.45, .3], [.45, .42], [.3, .42]], lineY: .39, feather: .02, seed: 7};
const rig = [hair, breath, sway, eye];

test('points outside every region stay still, so the background never swims', () => {
  const mesh = createMesh(20, 20);
  const moved = deform(mesh, rig, 1.7);
  for (let i = 0; i < moved.length; i += 2) {
    if (mesh.points[i] <= .2 || mesh.points[i] >= .8) {
      assert.equal(moved[i], mesh.points[i]);
      assert.equal(moved[i + 1], mesh.points[i + 1]);
    }
  }
});

test('the character really moves over time', () => {
  const mesh = createMesh(20, 20);
  const a = deform(mesh, rig, 0), b = deform(mesh, rig, 1.1);
  const most = Math.max(...a.map((v, i) => Math.abs(v - b[i])));
  assert.ok(most > .01, `largest move was ${most}`);
});

test('any frame is identical however it is reached', () => {
  const mesh = createMesh(12, 12);
  const direct = deform(mesh, rig, 3.3);
  for (let f = 0; f < 120; f++) deform(mesh, rig, f / 30);
  assert.deepEqual(deform(mesh, rig, 3.3), direct);
});

test('hair moves most at the tips and stays pinned at the root', () => {
  const at = y => Math.abs(displace(hair, .5, y, .75)[0]);
  assert.equal(at(.1), 0);
  assert.ok(at(.5) < at(.9));
});

test('hair lags its root, so the swing travels down the strand', () => {
  const peak = y => {
    let best = -1, when = 0;
    for (let t = 0; t < 3; t += .01) {
      const v = displace(hair, .5, y, t)[0];
      if (v > best) { best = v; when = t; }
    }
    return when;
  };
  assert.notEqual(peak(.4), peak(.9));
});

test('blinks close quickly, open slower and vary their gaps', () => {
  const starts = [];
  let last = 0;
  for (let t = 0; t < 60; t += 1 / 120) {
    const c = blinkClosure(t);
    assert.ok(c >= 0 && c <= 1);
    if (c > 0 && last === 0) starts.push(t);
    last = c;
  }
  assert.ok(starts.length >= 8, `only ${starts.length} blinks`);
  const gaps = starts.slice(1).map((t, i) => t - starts[i]);
  assert.ok(Math.max(...gaps) - Math.min(...gaps) > 1, 'gaps look like a metronome');
  const start = starts[0];
  assert.ok(blinkClosure(start + .06) > .9, 'the eye should close within about two frames');
  assert.equal(blinkClosure(start + .21), 0);
});

test('the lid moves toward the lash line, then the warp lets go of the drawn eye', () => {
  let moving = 0, swapped = 0;
  for (let t = 0; t < 20; t += 1 / 480) {
    const closure = blinkClosure(t, 7), dy = displace(eye, .37, .33, t)[1];
    if (closure > .3 && closure <= .7) { moving++; assert.ok(dy > 0); }
    if (closure > .7) { swapped++; assert.equal(dy, 0); assert.equal(drawnState([eye], t).eyesClosed, true); }
  }
  assert.ok(moving > 0 && swapped > 0);
  assert.equal(displace(eye, .37, .41, 1)[1], 0);
});

test('a mouth opens from its lip line, driven by supplied timing', () => {
  const mouth = {id: 'mouth', kind: 'mouth', polygon: box, lineY: .5, open: t => (t > 1 ? 1 : 0)};
  assert.equal(displace(mouth, .5, .6, .5)[1], 0);
  assert.ok(displace(mouth, .5, .6, 1.5)[1] > 0);
  assert.equal(displace(mouth, .5, .45, 1.5)[1], 0);
});

test('drawn states take over from the warp at the right moment', () => {
  const mouth = {id: 'mouth', kind: 'mouth', polygon: box, lineY: .5, open: t => (t > 1 ? 1 : 0)};
  assert.deepEqual(drawnState([eye, mouth], .5), {eyesClosed: false, mouthOpen: false});
  assert.equal(drawnState([eye, mouth], 1.5).mouthOpen, true);
  let seen = false;
  for (let t = 0; t < 20; t += 1 / 60) seen ||= drawnState([eye], t).eyesClosed;
  assert.ok(seen);
  assert.deepEqual(drawnState([hair], 3), {eyesClosed: false, mouthOpen: false});
});

test('breathing peaks on its peak line and fades to nothing by its reach', () => {
  const lift = y => -displace(breath, .5, y, 1)[1];
  assert.ok(lift(.78) > 0);
  assert.ok(lift(.78) > lift(.7) && lift(.78) > lift(.86));
  assert.equal(lift(1.5), 0);
});

test('a default feather is 1.5 times the peak displacement, sway included', () => {
  const wide = {id: 'w', kind: 'sway', polygon: [[0, 0], [1, 0], [1, 1], [0, 1]], pivot: [0, 0], amp: .1, period: 5};
  assert.ok(Math.abs(peakDisplacement(wide) - .1 * Math.SQRT2) < 1e-12);
  assert.ok(Math.abs(defaultFeather(wide) - .15 * Math.SQRT2) < 1e-12);
  const strong = {...hair, amp: .1};
  assert.ok(Math.abs(defaultFeather(strong) - 1.5 * peakDisplacement(strong)) < 1e-12);
  assert.equal(defaultFeather({...sway, amp: .001}), .04, 'a small motion keeps the minimum fade');
  assert.equal(defaultFeather(breath), .04);
  const alone = [wide, {...hair, id: 'alone-hair', amp: .06, feather: undefined}], mesh = createMesh(48, 48);
  for (const region of alone) for (let f = 0; f < 90; f++) assert.equal(invertedTriangles(mesh, deform(mesh, [region], f / 30)), 0);
});

test('feathering fades from the edge inward', () => {
  assert.equal(regionWeight(hair, .1, .5), 0);
  assert.equal(regionWeight(hair, .5, .5), 1);
  const edge = regionWeight(hair, .23, .5);
  assert.ok(edge > 0 && edge < 1);
});

test('normal motion never folds the mesh, and overdriven motion is caught', () => {
  const mesh = createMesh(48, 48);
  for (let f = 0; f < 90; f++) assert.equal(invertedTriangles(mesh, deform(mesh, rig, f / 30)), 0);
  const wild = [{...hair, id: 'wild', amp: .5, period: .5, feather: .02}];
  let worst = 0;
  for (let f = 0; f < 30; f++) worst = Math.max(worst, invertedTriangles(mesh, deform(mesh, wild, f / 30)));
  assert.ok(worst > 0);
});

test('a rig that cannot animate is rejected', () => {
  assert.throws(() => validateRegions([]));
  assert.throws(() => validateRegions([{id: 'a', kind: 'dance', polygon: box}]), /Unknown region/);
  assert.throws(() => validateRegions([{id: 'a', kind: 'hair', polygon: box}]), /root/);
  assert.throws(() => validateRegions([{...hair, polygon: [[0, 0]]}]), /polygon/);
  assert.throws(() => validateRegions([hair, hair]), /unique/);
  assert.throws(() => validateRegions([{id: 'm', kind: 'mouth', polygon: box, lineY: .5}]), /open/);
  assert.throws(() => createMesh(0, 4));
  assert.equal(validateRegions(rig), rig);
});

test('a mesh holding a NaN point counts as folded', () => {
  const mesh = createMesh(4, 4), points = new Float32Array(mesh.points);
  points[12] = NaN;
  assert.ok(invertedTriangles(mesh, points) > 0);
  assert.ok(invertedTriangles(mesh, points.fill(NaN)) > 0);
});

test('time must be finite, so a bad clock fails instead of hanging', () => {
  for (const time of [NaN, Infinity, -Infinity]) {
    assert.throws(() => blinkClosure(time), RangeError);
    assert.throws(() => deform(createMesh(2, 2), rig, time), RangeError);
  }
});

test('a malformed rig is rejected before it can move anything', () => {
  const zero = [[.2, .2], [.2, .2], [.2, .2]], line = [[.1, .1], [.5, .5], [.9, .9]];
  for (const [label, region] of Object.entries({
    'short root': {...hair, root: [.5]}, 'NaN tip': {...hair, tip: [.5, NaN]}, 'text root': {...hair, root: ['a', 'b']},
    'object pivot': {...sway, pivot: {x: 1, y: 2}}, 'long pivot': {...sway, pivot: [.5, .5, .5]},
    'infinite amp': {...hair, amp: Infinity}, 'infinite sway': {...sway, amp: Infinity}, 'infinite breath': {...breath, amp: Infinity},
    'infinite period': {...hair, period: Infinity}, 'negative feather': {...hair, feather: -.01}, 'zero feather': {...hair, feather: 0},
    'NaN feather': {...breath, feather: NaN}, 'NaN phase': {...hair, phase: NaN}, 'zero reach': {...breath, reach: 0},
    'no area': {...hair, polygon: zero}, 'straight polygon': {...breath, polygon: line},
  })) assert.throws(() => validateRegions([region]), Error, label);
});

test('the rest of the frame stays covered: a border point never leaves its edge', () => {
  const mesh = createMesh(160, 90), columns = mesh.cols + 1;
  const edge = [];
  for (let i = 0; i < mesh.points.length / 2; i++) {
    const row = Math.floor(i / columns), column = i % columns;
    if (row === 0 || row === mesh.rows) edge.push([i * 2 + 1, mesh.points[i * 2 + 1]]);
    if (column === 0 || column === mesh.cols) edge.push([i * 2, mesh.points[i * 2]]);
  }
  for (let f = 0; f < 300; f++) {
    const moved = deform(mesh, regions, f / 30);
    for (const [at, home] of edge) assert.equal(moved[at], home, `frame ${f}`);
    for (let i = 0; i < moved.length; i++) assert.ok(moved[i] >= 0 && moved[i] <= 1, `frame ${f} left the frame`);
    assert.equal(invertedTriangles(mesh, moved), 0, `frame ${f}`); // Unfolded, with its border on the frame, so it fills the frame.
  }
  const lifted = deform(mesh, regions, 3.9 / 4), row = (mesh.rows - 8) * columns + Math.round(mesh.cols / 2);
  assert.ok(lifted[row * 2 + 1] < mesh.points[row * 2 + 1] - .002, 'the chest still rises above the margin');
});

test('the demo rig stays valid and never folds on any frame at 24, 30 or 60 fps', () => {
  validateRegions(regions);
  const mesh = createMesh(160, 90);
  for (const fps of [24, 30, 60]) for (let f = 0; f < fps * 10; f++) assert.equal(invertedTriangles(mesh, deform(mesh, regions, f / fps)), 0, `frame ${f} at ${fps}`);
});

test('the worst moments of a blink never fold, even between frames', () => {
  const mesh = createMesh(160, 90), seed = regions.find(r => r.kind === 'blink').seed;
  let seen = 0;
  for (let t = 0; t < 10; t += 1 / 480) {
    if (!blinkClosure(t, seed)) continue;
    seen++;
    assert.equal(invertedTriangles(mesh, deform(mesh, regions, t)), 0, `time ${t}`);
  }
  assert.ok(seen > 100);
});

test('a lid pull fades out at the corners and the top of the region', () => {
  const open = regions.find(r => r.id === 'eye-left');
  const close = (() => { for (let t = 0; ; t += 1 / 960) if (blinkClosure(t, open.seed) > .6) return t; })();
  const xs = open.polygon.map(p => p[0]), ys = open.polygon.map(p => p[1]), left = Math.min(...xs), right = Math.max(...xs), top = Math.min(...ys);
  const middle = (left + right) / 2, y = (top + open.lineY) / 2;
  assert.ok(displace(open, middle, y, close)[1] > .02);
  assert.equal(displace(open, left, y, close)[1], 0);
  assert.equal(displace(open, right, y, close)[1], 0);
  assert.equal(displace(open, middle, top, close)[1], 0);
});

test('hair and clothes bend on separate layers, so hair cannot drag the jacket', () => {
  const body = layers.find(l => l.part === 'body').regions.map(r => r.id);
  for (const id of ['back-left', 'back-right', 'lock-left', 'lock-right']) assert.ok(!body.includes(id));
  const mesh = createMesh(160, 90);
  for (const layer of layers) for (let f = 0; f < 300; f++) assert.equal(invertedTriangles(mesh, deform(mesh, layer.regions, f / 30)), 0, `${layer.part} ${f}`);
  const shoulder = deform(mesh, layers.find(l => l.part === 'body').regions, 1.3);
  const at = 2 * (Math.round(.86 * 90) * 161 + Math.round(.26 * 160));
  assert.ok(Math.abs(shoulder[at] - mesh.points[at]) < 1e-6, 'the jacket edge must not swing sideways');
});
