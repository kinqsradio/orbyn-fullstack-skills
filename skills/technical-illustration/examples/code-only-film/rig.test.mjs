import test from 'node:test';
import assert from 'node:assert/strict';
import { fk, twoBoneIK, humanoid, GAITS, gait, poseAt, chain, held, accent, resolveShot, mouth, blink, blinkTimes, hash01 } from './rig.mjs';

const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const near = (a, b, tolerance = 1e-9) => assert.ok(Math.abs(a - b) <= tolerance, `${a} is not within ${tolerance} of ${b}`);
const bumpy = (x, z) => .08 * Math.sin(x * 1.3 + z * .7) + .05 * Math.sin(z * 2.1);
const curved = s => [1.5 * Math.sin(s / 6), s];
const range = values => Math.max(...values) - Math.min(...values);

// Walks a time range, grouping the samples of every step of one foot.
const stances = (options, name, seconds, rate = 240) => {
  const steps = new Map();
  for (let i = 0; i < seconds * rate; i++) {
    const state = gait(i / rate, options), contact = state.feet[name];
    if (!contact.stance) continue;
    if (!steps.has(contact.cycle)) steps.set(contact.cycle, []);
    steps.get(contact.cycle).push(state);
  }
  return [...steps.values()];
};

test('fk walks a named tree, composes rotation and ignores key order', () => {
  const skeleton = { tip: { parent: 'arm', offset: [0, 0, 1] }, arm: { parent: 'base', offset: [0, 1, 0] }, base: {} };
  const posed = fk(skeleton, { base: [0, Math.PI / 2, 0] }, { position: [1, 2, 3] });
  assert.deepEqual(posed.arm.position.map(v => +v.toFixed(9)), [1, 3, 3]);
  assert.deepEqual(posed.tip.position.map(v => +v.toFixed(9)), [2, 3, 3]);
});

test('fk rejects a cycle, a missing parent and a joint it does not know', () => {
  assert.throws(() => fk({ a: { parent: 'b' }, b: { parent: 'a' } }), /cycle/);
  assert.throws(() => fk({ a: { parent: 'gone' } }), /Unknown joint/);
  assert.throws(() => fk({ a: {} }, { b: [0, 0, 0] }), /Unknown posed joint/);
});

test('two-bone IK reaches its target and holds both bone lengths', () => {
  const root = [.2, 1, -.3], cases = [[.2, .3, .1], [.4, .5, .2], [-.3, .4, .2], [.2, .2, -.3], [.1, 1.4, .4]];
  for (const target of cases) {
    const { mid, end, reached } = twoBoneIK(root, target, .5, .45, [0, 0, 1]);
    assert.ok(reached); assert.ok(dist(end, target) < 1e-9);
    near(dist(root, mid), .5); near(dist(mid, end), .45);
  }
});

test('two-bone IK bends toward the hint', () => {
  const forward = twoBoneIK([0, 1, 0], [0, 0, 0], .6, .6, [0, 0, 1]), back = twoBoneIK([0, 1, 0], [0, 0, 0], .6, .6, [0, 0, -1]);
  assert.ok(forward.mid[2] > .3); assert.ok(back.mid[2] < -.3);
});

test('two-bone IK stops at full extension and at full fold when out of reach', () => {
  const far = twoBoneIK([0, 0, 0], [0, 5, 0], .6, .5, [0, 0, 1]);
  assert.equal(far.reached, false); near(dist(far.end, [0, 0, 0]), 1.1); near(dist(far.mid, far.end), .5); near(far.mid[2], 0);
  const close = twoBoneIK([0, 0, 0], [0, .01, 0], .6, .4, [0, 0, 1]);
  assert.equal(close.reached, false); near(dist(close.mid, [0, 0, 0]), .6); near(dist(close.mid, close.end), .4);
});

test('two-bone IK stays finite with a bend along the bone or a target on the root', () => {
  for (const solved of [twoBoneIK([0, 0, 0], [0, 1, 0], .6, .6, [0, 1, 0]), twoBoneIK([0, 0, 0], [0, 0, 0], .6, .6, [0, 0, 1])]) {
    assert.ok([...solved.mid, ...solved.end].every(Number.isFinite)); near(dist([0, 0, 0], solved.mid), .6);
  }
});

for (const [label, options] of [
  ['walk at 1.0 m/s', { speed: 1 }], ['walk at 1.7 m/s', { speed: 1.7, stride: 1.6 }],
  ['run at 3.2 m/s', { mode: 'run', speed: 3.2 }], ['run at 4.4 m/s', { mode: 'run', speed: 4.4, stride: 2.9 }],
  ['walk on a curved path over bumps', { speed: 1.3, path: curved, ground: bumpy }]
]) test(`stance foot stays fixed in world space: ${label}`, () => {
  for (const name of ['L', 'R']) {
    const steps = stances(options, name, 5).slice(1, -1);
    assert.ok(steps.length >= 2, 'expected whole stance phases');
    for (const samples of steps) {
      const first = samples[0].joints['toe' + name];
      const drift = Math.max(...samples.map(s => dist(s.joints['toe' + name], first)));
      assert.ok(drift < 1e-3, `foot drifted ${drift} m`);
      assert.ok(samples.at(-1).feet[name].progress > .9, 'sampled the whole stance');
    }
  }
});

test('the body actually travels while the foot stays down', () => {
  const samples = stances({ speed: 1.3 }, 'L', 4)[1];
  assert.ok(dist(samples[0].joints.pelvis, samples.at(-1).joints.pelvis) > .6);
});

test('feet rest on the ground under them, including across a step on uneven ground', () => {
  const { sole } = humanoid();
  for (const samples of stances({ speed: 1.3, path: curved, ground: bumpy }, 'R', 4)) {
    const toe = samples[0].joints.toeR;
    near(toe[1], bumpy(toe[0], toe[2]) + sole, 1e-9);
  }
});

test('the swing foot leaves the ground and the plants advance by one stride', () => {
  const options = { speed: 1.3, stride: 1.4 }, plants = stances(options, 'L', 6).map(s => s[0].feet.L.plant);
  for (let i = 1; i < plants.length; i++) near(plants[i][2] - plants[i - 1][2], 1.4);
  let high = 0;
  for (let i = 0; i < 240; i++) { const s = gait(i / 120, options); if (!s.feet.L.stance) high = Math.max(high, s.joints.toeL[1]); }
  assert.ok(high > .06);
});

test('legs keep their length and reach the ankles at every speed', () => {
  const body = humanoid();
  for (const options of [{ speed: 1 }, { speed: 1.7, stride: 1.6 }, { mode: 'run', speed: 4 }, { speed: 1.3, path: curved, ground: bumpy }]) {
    for (let i = 0; i < 400; i++) {
      const { joints } = gait(i / 60, options);
      for (const s of ['L', 'R']) {
        near(dist(joints['hip' + s], joints['knee' + s]), body.thigh, 1e-9);
        near(dist(joints['knee' + s], joints['ankle' + s]), body.shin, 1e-9);
        assert.ok(joints['knee' + s].every(Number.isFinite));
      }
    }
  }
});

test('a walk keeps a foot down, and a run has a flight phase', () => {
  let walkFlight = 0, runFlight = 0;
  for (let i = 0; i < 480; i++) {
    const w = gait(i / 120, { speed: 1.3 }), r = gait(i / 120, { mode: 'run', speed: 3.6 });
    if (!w.feet.L.stance && !w.feet.R.stance) walkFlight++;
    if (!r.feet.L.stance && !r.feet.R.stance) runFlight++;
  }
  assert.equal(walkFlight, 0); assert.ok(runFlight > 40);
});

test('pelvis bobs and sways, shoulders counter the hips and arms counter the legs', () => {
  const stride = 1.3, cycle = stride / 1.3, samples = Array.from({ length: 240 }, (_, i) => gait(i * cycle / 120, { speed: 1.3, stride }));
  assert.ok(range(samples.map(s => s.joints.pelvis[1])) > .015);
  assert.ok(range(samples.map(s => s.joints.pelvis[0])) > .03);
  const across = (s, a, b) => s.joints[a][2] - s.joints[b][2];
  const shoulders = samples.map(s => across(s, 'shoulderL', 'shoulderR')), hips = samples.map(s => across(s, 'hipL', 'hipR'));
  assert.ok(shoulders.reduce((sum, v, i) => sum + v * hips[i], 0) < 0, 'shoulders turn against the hips');
  const arm = samples.map(s => s.joints.wristL[2] - s.joints.pelvis[2]), leg = samples.map(s => s.joints.ankleL[2] - s.joints.pelvis[2]);
  assert.ok(arm.reduce((sum, v, i) => sum + v * leg[i], 0) < 0, 'left arm swings against the left leg');
});

test('the head stays steadier than the body', () => {
  const samples = Array.from({ length: 240 }, (_, i) => gait(i / 120, { speed: 1.3, stride: 1.3 }));
  assert.ok(range(samples.map(s => s.joints.head[1])) < range(samples.map(s => s.joints.pelvis[1])) * .7);
  assert.ok(Math.max(...samples.map(s => Math.abs(Math.atan2(s.gaze[0], s.gaze[2])))) < .08);
  assert.ok(Math.max(...samples.map(s => Math.abs(s.gaze[1]))) < .05);
});

test('speed, stride and body scale the gait', () => {
  assert.notDeepEqual(gait(.7, { speed: 1 }).joints, gait(.7, { speed: 1.4 }).joints);
  assert.notDeepEqual(gait(.7, { speed: 1, stride: 1 }).joints, gait(.7, { speed: 1, stride: 1.5 }).joints);
  assert.ok(gait(0, { body: humanoid(2) }).joints.head[1] > gait(0).joints.head[1] * 1.1);
  near(gait(2.3, { distance: 3 }).distance, 3);
  assert.deepEqual(gait(5, { speed: 0 }).joints, gait(0, { speed: 0 }).joints);
});

// Only stateless code passes these: the direct, forward and rewound routes must give identical bits.
const seekProof = sample => {
  const direct = sample(100);
  for (let i = 0; i <= 99; i++) sample(i);
  assert.deepEqual(sample(100), direct, 'after playing forward');
  for (let i = 300; i > 100; i--) sample(i);
  assert.deepEqual(sample(100), direct, 'after rewinding');
};

for (const [label, options] of [['walk', { speed: 1.3 }], ['run', { mode: 'run', speed: 3.6 }], ['walk on terrain', { speed: 1.3, path: curved, ground: bumpy }]]) {
  test(`seeking is exact for the ${label}`, () => seekProof(i => gait(i / 30, options)));
}

const swaying = t => [Math.sin(t * 3), .1 * Math.sin(t * 7), t * 1.3];

test('seeking is exact for secondary motion', () => seekProof(i => chain(i / 30, swaying, { wind: (t, n) => [.01 * Math.sin(t * 5 + n), 0, 0] })));

test('secondary motion trails its root and keeps its links', () => {
  const points = chain(4, t => [0, 1, t * 1.5], { segments: 6, length: .1 });
  near(points[0][2], 6);
  for (let i = 1; i < points.length; i++) near(dist(points[i], points[i - 1]), .1);
  assert.ok(points[6][2] < points[0][2] - .1, 'moving forward streams the tail behind');
});

test('secondary motion responds late and settles to rest', () => {
  const stopAt = t => [Math.min(t, 2), 1, 0];
  assert.ok(chain(2, stopAt)[5][0] < 1.85, 'the tail lags at the stop');
  const settled = chain(9, stopAt);
  for (const point of settled) near(point[0], 2, 1e-3);
});

test('secondary motion overshoots like a spring rather than easing flat', () => {
  const stopAt = t => [Math.min(t, 2), 1, 0];
  const motion = Array.from({ length: 120 }, (_, i) => chain(2 + i / 60, stopAt, { segments: 3, frequency: 2, damping: .25 })[3][0]);
  assert.ok(Math.max(...motion) > 2.005);
});

const poses = { rest: { arm: [0, 0, 0], reach: 0 }, up: { arm: [1, 2, 3], reach: 1 }, down: { arm: [-1, 0, 2], reach: -1 } };
const keys = [{ time: 0, pose: 'rest' }, { time: 1, pose: 'up' }, { time: 2, pose: 'down' }];

test('poses hit every key exactly and blend with easing between', () => {
  assert.deepEqual(poseAt(0, poses, keys), poses.rest);
  assert.deepEqual(poseAt(1, poses, keys), poses.up);
  assert.deepEqual(poseAt(2, poses, keys), poses.down);
  assert.deepEqual(poseAt(-1, poses, keys), poses.rest);
  assert.deepEqual(poseAt(9, poses, keys), poses.down);
  near(poseAt(.5, poses, keys).reach, .5);
  assert.ok(poseAt(.25, poses, keys).reach < .25, 'eases out of the pose');
});

test('anticipation moves away first and overshoot passes the target', () => {
  const moves = Array.from({ length: 99 }, (_, i) => poseAt((i + 1) / 100, poses, [{ time: 0, pose: 'rest', anticipate: .15, overshoot: .15 }, { time: 1, pose: 'up' }]).reach);
  assert.ok(Math.min(...moves.slice(0, 30)) < -.03);
  assert.ok(Math.max(...moves.slice(60)) > 1.03);
  assert.deepEqual(poseAt(1, poses, [{ time: 0, pose: 'rest', anticipate: .15, overshoot: .15 }, { time: 1, pose: 'up' }]), poses.up);
});

test('stepped holds have no in-between frames and snap on the key', () => {
  const allowed = Object.values(poses).map(p => JSON.stringify(p));
  for (let i = -30; i < 240; i++) {
    const t = i / 60, sampled = poseAt(t, poses, keys, { mode: 'stepped' });
    assert.ok(allowed.includes(JSON.stringify(sampled)), `in-between at ${t}`);
    assert.deepEqual(sampled, t < 1 ? poses.rest : t < 2 ? poses.up : poses.down);
  }
  assert.deepEqual(poseAt(1 - 1e-6, poses, keys, { mode: 'stepped' }), poses.rest);
  assert.deepEqual(poseAt(1, poses, keys, { mode: 'stepped' }), poses.up);
  assert.deepEqual(poseAt(.5, poses, [{ time: 0, pose: 'rest', hold: true }, { time: 1, pose: 'up' }]), poses.rest);
});

test('a returned pose cannot change the named pose', () => {
  poseAt(0, poses, keys).arm[0] = 9;
  assert.equal(poses.rest.arm[0], 0);
});

test('poses drive fk', () => {
  const skeleton = { base: {}, arm: { parent: 'base', offset: [0, 1, 0] } };
  const turned = fk(skeleton, poseAt(1, { flat: { base: [0, 0, 0] }, tipped: { base: [Math.PI / 2, 0, 0] } }, [{ time: 0, pose: 'flat' }, { time: 1, pose: 'tipped' }]));
  near(turned.arm.position[2], 1);
});

test('held time steps at the hold rate while time stays exact on each held frame', () => {
  const twos = Array.from({ length: 60 }, (_, i) => held(i / 24, 12));
  assert.equal(new Set(twos).size, 30);
  for (let i = 0; i < 48; i++) assert.equal(held(i / 24, 12), Math.floor(i / 2) / 12);
  for (let i = 0; i < 48; i++) assert.equal(held(i / 24, 8), Math.floor(i / 3) / 8);
  assert.equal(new Set(Array.from({ length: 30 }, (_, i) => held(i / 30, 8))).size, 8);
  assert.equal(held(1 / 12 * 7, 12), 7 / 12);
});

test('an accent hits at once and decays', () => {
  assert.equal(accent(.999, [1]), 0);
  assert.equal(accent(1, [1]), 1);
  near(accent(1.035, [1], { decay: .035 }), Math.exp(-1));
  assert.ok(accent(1 + 3 / 30, [1], { decay: .035 }) < .06, 'gone within three frames at 30 fps');
});

test('an overlapping onset adds to an unfinished pulse and never drops one', () => {
  const options = { decay: .1, gain: .4 }, first = accent(1.05, [1], options), later = accent(1.05, [1.05], options);
  near(accent(1.05, [1, 1.05], options), first + later);
  const stack = [0, .02, .04, .06, .08], series = Array.from({ length: 200 }, (_, i) => i / 500);
  for (const t of series) {
    const full = accent(t, stack, options);
    for (const left of stack) assert.ok(full >= accent(t, stack.filter(o => o !== left), options) - 1e-12, 'removing a pulse never raises the sum');
  }
  near(accent(.08, [.08, 0], options), accent(.08, [0, .08], options)); // Order does not matter.
});

test('accents clamp and take per-onset gains', () => {
  assert.equal(accent(1, [1, 1, 1, 1]), 1);
  near(accent(1, [{ time: 1, gain: .3 }]), .3);
  assert.equal(accent(1, [1, 1], { max: 2 }), 2);
});

const shots = [{ id: 'a', from: 0, to: 2 }, { id: 'b', from: 2, to: 5, transition: { name: 'whip', duration: .5 } }, { id: 'c', from: 5, to: 6 }];

test('shots resolve to id, local time and named transition progress', () => {
  assert.deepEqual(resolveShot(1, shots), { id: 'a', index: 0, local: 1, progress: .5, transition: null });
  const opening = resolveShot(2.25, shots);
  assert.equal(opening.id, 'b'); near(opening.local, .25);
  assert.deepEqual(opening.transition, { name: 'whip', from: 'a', to: 'b', progress: .5 });
  assert.equal(resolveShot(2.5, shots).transition, null);
  assert.equal(resolveShot(2, shots).id, 'b');
  assert.equal(resolveShot(5, shots).id, 'c');
  assert.equal(resolveShot(6, shots).id, 'c');
});

test('mouth shapes follow the timed vowels and rest between them', () => {
  const vowels = [{ from: 1, to: 1.3, vowel: 'a' }, { from: 1.6, to: 1.9, vowel: 'u' }];
  assert.equal(mouth(.5, vowels).open, 0); assert.equal(mouth(.5, vowels).vowel, 'rest');
  const a = mouth(1.2, vowels), u = mouth(1.8, vowels);
  assert.equal(a.vowel, 'a'); assert.equal(u.vowel, 'u');
  assert.ok(a.open > u.open); assert.ok(u.round > a.round);
  assert.ok(mouth(1.34, vowels).open > 0 && mouth(1.34, vowels).open < a.open, 'releases rather than cuts');
});

test('blinks are irregular, seeded and repeatable', () => {
  const times = blinkTimes(0, 240, { seed: 7 }), gaps = times.slice(1).map((t, i) => t - times[i]);
  assert.ok(times.length > 50);
  const mean = gaps.reduce((a, b) => a + b, 0) / gaps.length, spread = Math.sqrt(gaps.reduce((sum, g) => sum + (g - mean) ** 2, 0) / gaps.length);
  assert.ok(spread / mean > .3, 'not a metronome');
  assert.ok(new Set(gaps.map(g => g.toFixed(2))).size > 30, 'gaps vary, beyond the occasional double blink');
  assert.ok(Math.min(...gaps) > .25, 'blinks never collide');
  assert.deepEqual(blinkTimes(0, 240, { seed: 7 }), times);
  assert.notDeepEqual(blinkTimes(0, 240, { seed: 8 }), times);
});

test('blink closes fast, opens slower and is exact on seek', () => {
  const [at] = blinkTimes(0, 30, { seed: 3 });
  assert.equal(blink(at - .01, { seed: 3 }), 0);
  assert.equal(blink(at + .06, { seed: 3 }), 1);
  assert.ok(blink(at + .025, { seed: 3 }) > 0);
  assert.equal(blink(at + .3, { seed: 3 }), 0);
  seekProof(i => blink(i / 30, { seed: 3 }));
});

test('hash01 is seeded, bounded and spread', () => {
  const values = Array.from({ length: 4000 }, (_, i) => hash01(5, i));
  assert.ok(values.every(v => v >= 0 && v < 1));
  near(values.reduce((a, b) => a + b, 0) / values.length, .5, .02);
  assert.notEqual(hash01(5, 1), hash01(6, 1));
  assert.equal(hash01(5, 1, 2), hash01(5, 1, 2));
});

test('bad input is rejected', () => {
  const bad = [
    () => twoBoneIK([0, 0], [0, 1, 0], 1, 1, [0, 0, 1]), () => twoBoneIK([0, 0, 0], [NaN, 1, 0], 1, 1, [0, 0, 1]), () => twoBoneIK([0, 0, 0], [0, 1, 0], 0, 1, [0, 0, 1]),
    () => twoBoneIK([0, 0, 0], [0, 1, 0], 1, 1, [0, 0, 0]), () => humanoid(0),
    () => gait(NaN), () => gait(1, { mode: 'skip' }), () => gait(1, { speed: -1 }), () => gait(1, { stride: 0 }), () => gait(1, { duty: 1 }),
    () => gait(1, { ground: () => NaN }), () => gait(1, { path: () => [NaN, 0] }), () => gait(1, { distance: Infinity }),
    () => poseAt(0, poses, []), () => poseAt(0, poses, [{ time: 1, pose: 'rest' }, { time: 0, pose: 'up' }]), () => poseAt(0, poses, [{ time: 0, pose: 'nope' }]),
    () => poseAt(0, poses, keys, { mode: 'smear' }), () => poseAt(.5, { a: { x: 1 }, b: { y: 1 } }, [{ time: 0, pose: 'a' }, { time: 1, pose: 'b' }]), () => poseAt(0, poses, [{ time: 0, pose: 'rest', ease: 'wobble' }]),
    () => chain(NaN, swaying), () => chain(0, 'root'), () => chain(0, swaying, { segments: 0 }), () => chain(0, swaying, { damping: 1 }), () => chain(0, () => [NaN, 0, 0]),
    () => chain(0, () => [0, 0, 0], { rest: [0, 0, 0] }), () => chain(0, swaying, { wind: () => [NaN, 0, 0] }), () => chain(0, swaying, { wind: () => 1 }), () => chain(0, swaying, { wind: 'gust' }),
    () => held(1, 0), () => held(NaN, 12), () => accent(0, [NaN]), () => accent(0, 1), () => accent(0, [0], { decay: 0 }),
    () => resolveShot(0, []), () => resolveShot(7, shots), () => resolveShot(0, [{ id: 'a', from: 0, to: 1 }, { id: 'b', from: 2, to: 3 }]), () => resolveShot(0, [{ id: 'a', from: 0, to: 1 }, { id: 'a', from: 1, to: 2 }]),
    () => resolveShot(0, [{ id: 'a', from: 0, to: 1, transition: { name: 'x', duration: .1 } }]), () => resolveShot(0, [{ id: 'a', from: 0, to: 1 }, { id: 'b', from: 1, to: 2, transition: { name: 'x', duration: 5 } }]),
    () => mouth(0, [{ from: 0, to: 1, vowel: 'q' }]), () => mouth(0, [{ from: 1, to: 0, vowel: 'a' }]),
    () => blink(0, { mean: .1 }), () => blink(0, { seed: 1.5 }), () => blinkTimes(2, 1)
  ];
  bad.forEach((attempt, i) => assert.throws(attempt, RangeError, `case ${i}`));
});

test('a swing foot turns the short way across the back of the circle', () => {
  const southward = s => [.06 * Math.sin(s * 2.6), -s];
  for (let i = 0; i < 480; i++) {
    const { joints, feet } = gait(i / 120, { speed: 1.3, path: southward });
    for (const name of ['L', 'R']) {
      if (feet[name].stance) continue;
      const toe = joints['toe' + name], heel = joints['heel' + name];
      assert.ok(toe[2] - heel[2] < 0, `foot ${name} turned away at ${i / 120}`);
      assert.ok(Math.abs(toe[0] - heel[0]) < .1, `foot ${name} spun at ${i / 120}`);
    }
  }
});

test('fk reads only a skeleton and pose\'s own properties', () => {
  const skeleton = { constructor: {}, toString: { parent: 'constructor', offset: [0, 1, 0] }, valueOf: { parent: 'toString', offset: [1, 0, 0] } };
  const posed = fk(skeleton);
  assert.deepEqual(Object.keys(posed).sort(), ['constructor', 'toString', 'valueOf']);
  assert.deepEqual(posed.constructor.position, [0, 0, 0]);
  assert.deepEqual(posed.valueOf.position, [1, 1, 0]);
  assert.throws(() => fk({ a: { parent: 'toString' } }), /Unknown joint/);
  assert.throws(() => fk({ a: null }), RangeError);
});

test('a pose blend needs every channel at both ends, so none can snap on at a key', () => {
  const pair = { a: { x: 1 }, b: { x: 2, y: 5 } }, ordered = [{ time: 0, pose: 'a' }, { time: 1, pose: 'b' }];
  assert.throws(() => poseAt(.5, pair, ordered), /missing channel: y/);
  assert.throws(() => poseAt(.5, pair, [{ time: 0, pose: 'b' }, { time: 1, pose: 'a' }]), /missing channel: y/);
  assert.deepEqual(poseAt(.5, pair, ordered, { mode: 'stepped' }), pair.a, 'a stepped pose has no in-betweens to snap');
});

test('blink times stay sorted and apart at the shortest allowed mean', () => {
  for (let seed = 1; seed <= 40; seed++) {
    const times = blinkTimes(0, 300, { seed, mean: 1.5 });
    assert.ok(times.length > 100);
    for (let i = 1; i < times.length; i++) assert.ok(times[i] - times[i - 1] >= .25, `seed ${seed}: ${times[i - 1]} then ${times[i]}`);
  }
});

test('double blinks remain at the default mean', () => {
  assert.ok(blinkTimes(0, 240, { seed: 7 }).some((t, i, all) => Math.abs(all[i + 1] - t - .34) < 1e-9), 'double blinks remain');
});

test('the gait table stays frozen', () => {
  assert.ok(Object.isFrozen(GAITS.walk));
});
