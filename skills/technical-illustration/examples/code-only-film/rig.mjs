// A pure, dependency-free character animation kit. Every sampler reads absolute time, keeps no
// state between calls and returns the same answer for the same input, so a film can seek, rewind
// or render out of order. Bad input throws. Units are metres, seconds and radians; +Y is up.
//
//   fk(skeleton, pose?, root?)              Named joint tree to world { position, matrix } per joint.
//   twoBoneIK(root, target, upper, lower, bend)  Solves a knee or elbow; { mid, end, reached }.
//   humanoid(height?)                       Proportions and upper-body skeleton used by gait().
//   GAITS                                   The walk and run parameter sets.
//   gait(time, options)                     Walk or run: planted feet, world joints, stance state.
//   poseAt(time, poses, keys, options?)     Named poses: eased blend, anticipation, overshoot, stepped.
//   chain(time, root, options?)             Secondary motion as a closed-form response to root(time).
//   held(time, rate)                        Holds time at 12 or 8 fps for animating on twos or threes.
//   accent(time, onsets, options?)          Instant attack, exponential decay, overlaps add, clamped.
//   resolveShot(time, shots)                Shot id, local time and named transition progress.
//   mouth(time, vowels, options?)           Mouth open, wide and round from timed vowels.
//   blink(time, options?), blinkTimes(from, to, options?)  Seeded irregular blinks; 0 open, 1 shut.
//   hash01(seed, ...integers)               Seeded hash to [0, 1).
//
// Feet plant per step, not per frame: plant n of a foot is a function of n alone, so a stance foot
// cannot slide however the body moves. That holds on a curved path and on uneven ground.

const TAU = Math.PI * 2;
const need = (ok, message) => { if (!ok) throw new RangeError(message); };
const isVector = v => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
const needTime = t => need(Number.isFinite(t), 'Time must be finite');
const needVector = (v, name) => need(isVector(v), name + ' must be a finite [x, y, z]');
const positive = (v, name) => need(Number.isFinite(v) && v > 0, name + ' must be positive');

const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const scale = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const length = a => Math.hypot(a[0], a[1], a[2]);
const lerp = (a, b, k) => a + (b - a) * k;
const mix = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
const clamp = (v, low = 0, high = 1) => Math.min(high, Math.max(low, v));
const smooth = (low, high, v) => { const k = clamp((v - low) / (high - low)); return k * k * (3 - 2 * k); };
const turnBetween = (from, to, k) => from + (((to - from + Math.PI) % TAU + TAU) % TAU - Math.PI) * k; // The short way round.

// Rotation matrices are row-major and compose Ry * Rx * Rz.
const fromEuler = ([x, y, z]) => {
  const [cx, sx, cy, sy, cz, sz] = [Math.cos(x), Math.sin(x), Math.cos(y), Math.sin(y), Math.cos(z), Math.sin(z)];
  return [cy * cz + sy * sx * sz, sy * sx * cz - cy * sz, sy * cx, cx * sz, cx * cz, -sx, cy * sx * sz - sy * cz, sy * sz + cy * sx * cz, cy * cx];
};
const multiply = (a, b) => [0, 3, 6].flatMap(r => [0, 1, 2].map(c => a[r] * b[c] + a[r + 1] * b[c + 3] + a[r + 2] * b[c + 6]));
const apply = (m, v) => [m[0] * v[0] + m[1] * v[1] + m[2] * v[2], m[3] * v[0] + m[4] * v[1] + m[5] * v[2], m[6] * v[0] + m[7] * v[1] + m[8] * v[2]];

export function fk(skeleton, pose = {}, root = {}) {
  const { position = [0, 0, 0], rotation = [0, 0, 0] } = root, world = new Map(), active = new Set();
  needVector(position, 'Root position'); needVector(rotation, 'Root rotation');
  for (const name of Object.keys(pose)) need(Object.hasOwn(skeleton, name), 'Unknown posed joint: ' + name);
  const solve = name => {
    if (world.has(name)) return world.get(name);
    need(Object.hasOwn(skeleton, name) && skeleton[name] !== null && typeof skeleton[name] === 'object', 'Unknown joint: ' + name);
    need(!active.has(name), 'Joint cycle at ' + name);
    active.add(name);
    const { parent = null, offset = [0, 0, 0], rotation: rest = [0, 0, 0] } = skeleton[name], turn = Object.hasOwn(pose, name) ? pose[name] : [0, 0, 0];
    needVector(offset, name + ' offset'); needVector(rest, name + ' rotation'); needVector(turn, name + ' pose');
    const base = parent === null ? { position, matrix: fromEuler(rotation) } : solve(parent);
    const matrix = multiply(multiply(base.matrix, fromEuler(rest)), fromEuler(turn));
    active.delete(name);
    const joint = { position: add(base.position, apply(base.matrix, offset)), matrix };
    world.set(name, joint);
    return joint;
  };
  for (const name of Object.keys(skeleton)) solve(name);
  return Object.fromEntries(world);
}

export function twoBoneIK(root, target, upper, lower, bend) {
  needVector(root, 'Root'); needVector(target, 'Target'); needVector(bend, 'Bend direction');
  positive(upper, 'Upper length'); positive(lower, 'Lower length');
  need(length(bend) > 1e-9, 'Bend direction must not be zero');
  const reach = sub(target, root), distance = length(reach), low = Math.abs(upper - lower), high = upper + lower;
  const hint = scale(bend, 1 / length(bend));
  // Beside the root there is no aim, so any axis across the bend will do.
  const fallback = Math.abs(hint[1]) < .9 ? [hint[2], 0, -hint[0]] : [1, 0, 0];
  const aim = distance > 1e-9 ? scale(reach, 1 / distance) : scale(fallback, 1 / length(fallback));
  const span = Math.max(clamp(distance, low, high), 1e-9), along = (upper * upper - lower * lower + span * span) / (2 * span);
  const lift = Math.sqrt(Math.max(0, upper * upper - along * along));
  let side = sub(hint, scale(aim, dot(hint, aim)));
  if (length(side) < 1e-6) side = sub(fallback, scale(aim, dot(fallback, aim))); // Bend along the bone.
  if (length(side) < 1e-6) side = [aim[1], aim[2], aim[0]];
  side = scale(side, 1 / length(side));
  return { mid: add(add(root, scale(aim, along)), scale(side, lift)), end: add(root, scale(aim, span)), reached: distance >= low && distance <= high };
}

export function humanoid(height = 1.7) {
  positive(height, 'Height');
  const k = height / 1.7, m = v => v * k;
  const side = (s, name) => ({
    ['shoulder' + name]: { parent: 'chest', offset: [m(.18) * s, m(.13), 0] },
    ['elbow' + name]: { parent: 'shoulder' + name, offset: [0, m(-.29), 0] },
    ['wrist' + name]: { parent: 'elbow' + name, offset: [0, m(-.26), 0] },
    ['hip' + name]: { parent: 'pelvis', offset: [m(.09) * s, m(-.05), 0] }
  });
  return {
    height, thigh: m(.42), shin: m(.41), ankle: m(.075), footBack: m(.13), footFront: m(.075), heel: m(.19), sole: m(.03), footWidth: m(.085),
    skeleton: {
      pelvis: {}, spine: { parent: 'pelvis', offset: [0, m(.14), 0] }, chest: { parent: 'spine', offset: [0, m(.16), 0] },
      neck: { parent: 'chest', offset: [0, m(.2), 0] }, head: { parent: 'neck', offset: [0, m(.13), 0] }, ...side(1, 'L'), ...side(-1, 'R')
    }
  };
}

// duty: share of the cycle a foot is down; below .5 is a run with a flight phase.
export const GAITS = Object.freeze({
  walk: Object.freeze({ duty: .63, stride: 1.34, crouch: .985, lift: .07, clearance: .05, heelStart: .5, heelOff: .95, toeUp: .3, bob: .021, sway: .026, hipDrop: .05, lean: .05, pelvisYaw: .13, chestYaw: .3, arm: .4, armOut: .07, elbow: .28, elbowSwing: .2, headRest: .55 }),
  run: Object.freeze({ duty: .36, stride: 2.5, crouch: .93, lift: .24, clearance: .1, heelStart: .35, heelOff: 1.05, toeUp: .4, bob: -.036, sway: .012, hipDrop: .06, lean: .17, pelvisYaw: .2, chestYaw: .46, arm: .72, armOut: .12, elbow: 1.3, elbowSwing: .35, headRest: .7 })
});

const straight = s => [0, s], level = () => 0;

export function gait(time, options = {}) {
  const { mode = 'walk', speed = mode === 'run' ? 3.6 : 1.3, distance, path = straight, ground = level, body = humanoid() } = options;
  needTime(time); need(Object.hasOwn(GAITS, mode), 'Unknown gait mode: ' + mode);
  const g = GAITS[mode], duty = options.duty ?? g.duty, stride = options.stride ?? g.stride * body.height / 1.7;
  positive(stride, 'Stride'); need(Number.isFinite(speed) && speed >= 0, 'Speed must not be negative');
  need(Number.isFinite(duty) && duty > .1 && duty < .9, 'Duty must lie between .1 and .9');
  need(typeof path === 'function' && typeof ground === 'function', 'Path and ground must be functions');
  const travelled = distance ?? speed * time;
  need(Number.isFinite(travelled), 'Distance must be finite');

  const frame = s => {
    const [x, z] = path(s), [ax, az] = path(s - .05), [bx, bz] = path(s + .05);
    need(Number.isFinite(x + z), 'Path must return finite [x, z]');
    return { x, z, heading: Math.atan2(bx - ax, bz - az) };
  };
  const forward = a => [Math.sin(a), 0, Math.cos(a)], left = a => [Math.cos(a), 0, -Math.sin(a)];
  const lifted = (x, z) => { const y = ground(x, z); need(Number.isFinite(y), 'Ground must return a finite height'); return y; };
  // A plant depends on the foot and step number only, which is what keeps a stance foot still.
  const plant = (side, offset, n) => {
    const s = (n - offset + duty / 2) * stride + body.footFront, { x, z, heading } = frame(s), f = forward(heading), l = left(heading);
    const px = x + l[0] * side * body.footWidth, pz = z + l[2] * side * body.footWidth, y = lifted(px, pz);
    const heel = lifted(px - f[0] * body.heel, pz - f[2] * body.heel);
    return { ball: [px, y + body.sole, pz], heading, slope: clamp(Math.atan2(heel - y, body.heel), -.6, .6) };
  };
  const place = (ball, heading, pitch, back, up) => {
    const f = forward(heading), along = up * Math.sin(pitch) - back * Math.cos(pitch);
    return add(add(ball, scale(f, along)), [0, back * Math.sin(pitch) + up * Math.cos(pitch), 0]);
  };
  const phase = travelled / stride;
  const foot = (side, offset) => {
    const cycle = Math.floor(phase + offset), u = phase + offset - cycle, from = plant(side, offset, cycle);
    let ball, heading, base, raise, curl = 0, stance = u < duty;
    if (stance) {
      ball = from.ball; heading = from.heading; base = from.slope; raise = g.heelOff * smooth(g.heelStart, 1, u / duty);
    } else {
      const w = (u - duty) / (1 - duty), e = smooth(0, 1, w), arc = Math.sin(Math.PI * w), to = plant(side, offset, cycle + 1);
      ball = mix(from.ball, to.ball, e); heading = turnBetween(from.heading, to.heading, e);
      ball[1] = Math.max(ball[1] + g.lift * arc, lifted(ball[0], ball[2]) + body.sole + g.clearance * arc);
      base = lerp(from.slope, to.slope, e); raise = g.heelOff * (1 - smooth(0, .55, w)); curl = g.toeUp * smooth(.3, .85, w) * (1 - smooth(.85, 1, w));
    }
    const pitch = base + raise - curl;
    return {
      stance, cycle, progress: stance ? u / duty : (u - duty) / (1 - duty), plant: from.ball, ball, heading,
      ankle: place(ball, heading, pitch, body.footBack, body.ankle), heel: place(ball, heading, pitch, body.heel, 0), tip: place(ball, heading, base - curl, -body.footFront, 0)
    };
  };
  const feet = { L: foot(1, 0), R: foot(-1, .5) };

  const { x, z, heading } = frame(travelled), f = forward(heading), l = left(heading);
  const leftStance = Math.cos(TAU * (phase - duty / 2)), bounce = Math.cos(2 * TAU * (phase - duty / 2));
  const legSwing = Math.cos(TAU * (phase - (duty - .5) / 2)); // +1 with the left leg forward.
  const bob = g.bob * bounce * Math.sqrt(stride / (g.stride * body.height / 1.7)), sway = g.sway * leftStance;
  const floor = [-.5, -.25, 0, .25, .5].reduce((sum, k) => { const p = frame(travelled + k * stride); return sum + lifted(p.x, p.z) / 5; }, 0);
  const legs = body.thigh + body.shin;
  const pose = {
    spine: [g.lean * .5, (g.chestYaw + g.pelvisYaw) * .45 * legSwing, -g.hipDrop * .4 * leftStance],
    chest: [g.lean * .5, (g.chestYaw + g.pelvisYaw) * .55 * legSwing, -g.hipDrop * .6 * leftStance],
    neck: [-g.lean * .7, -g.chestYaw * .5 * legSwing, 0]
  };
  for (const [name, s] of [['L', 1], ['R', -1]]) {
    const swing = s * legSwing; // +1 with this arm back.
    pose['shoulder' + name] = [g.arm * swing + g.lean * .4, 0, s * g.armOut];
    pose['elbow' + name] = [-(g.elbow + g.elbowSwing * (1 - swing) * .5), 0, 0];
  }
  const root = { position: [x + l[0] * sway, floor + body.sole + (legs + body.ankle) * g.crouch + bob, z + l[2] * sway], rotation: [g.lean, heading - g.pelvisYaw * legSwing, g.hipDrop * leftStance] };
  const tree = fk(body.skeleton, pose, root);
  // Lower the body until both ankles are in reach, so the solved legs land exactly on the feet.
  let drop = 0;
  for (const name of ['L', 'R']) {
    const hip = tree['hip' + name].position, ankle = feet[name].ankle, across = Math.hypot(hip[0] - ankle[0], hip[2] - ankle[2]), reach = legs * .998;
    drop = Math.max(drop, hip[1] - (ankle[1] + Math.sqrt(Math.max(0, reach * reach - across * across))));
  }
  const joints = {};
  for (const [name, joint] of Object.entries(tree)) joints[name] = add(joint.position, [0, -drop, 0]);
  // The head keeps most of its height and side-to-side line while the body moves under it.
  joints.head = add(add(joints.head, [0, -bob * g.headRest, 0]), scale(l, -sway * g.headRest));
  for (const [name, s] of [['L', 1], ['R', -1]]) {
    const bend = add(scale(f, 1), scale(l, s * .06)), leg = twoBoneIK(joints['hip' + name], feet[name].ankle, body.thigh, body.shin, bend);
    Object.assign(joints, { ['knee' + name]: leg.mid, ['ankle' + name]: leg.end, ['heel' + name]: feet[name].heel, ['toe' + name]: feet[name].ball, ['tip' + name]: feet[name].tip });
  }
  const steadied = mix(apply(tree.chest.matrix, [0, 0, 1]), f, g.headRest + .3), gaze = scale(steadied, 1 / length(steadied));
  const contact = name => ({ stance: feet[name].stance, cycle: feet[name].cycle, progress: feet[name].progress, plant: feet[name].plant });
  return { time, distance: travelled, phase, heading, joints, gaze, feet: { L: contact('L'), R: contact('R') } };
}

const EASE = { linear: k => k, in: k => k * k, out: k => k * (2 - k), inOut: k => smooth(0, 1, k) };

export function poseAt(time, poses, keys, { mode = 'blend' } = {}) {
  needTime(time); need(mode === 'blend' || mode === 'stepped', 'Unknown pose mode: ' + mode);
  need(Array.isArray(keys) && keys.length > 0, 'Pose keys must not be empty');
  keys.forEach((key, i) => {
    need(Number.isFinite(key.time) && (i === 0 || key.time > keys[i - 1].time), 'Pose keys must ascend in time');
    need(Object.hasOwn(poses, key.pose), 'Unknown pose: ' + key.pose);
    need(Object.hasOwn(EASE, key.ease ?? 'inOut'), 'Unknown ease: ' + key.ease);
  });
  let i = 0; while (i + 1 < keys.length && keys[i + 1].time <= time) i++;
  const key = keys[i], next = keys[i + 1], from = poses[key.pose];
  if (!next || time < key.time || mode === 'stepped' || key.hold) return structuredClone(from);
  const k = (time - key.time) / (next.time - key.time), { anticipate = 0, overshoot = 0, ease = 'inOut' } = key;
  // Both shapes return to zero at their ends, so a key is always hit exactly.
  const amount = EASE[ease](k) - anticipate * Math.sin(Math.PI * clamp(k / .35)) + overshoot * Math.sin(Math.PI * clamp((k - .65) / .35)), to = poses[next.pose];
  const blended = {};
  for (const channel of Object.keys(to)) need(Object.hasOwn(from, channel), 'Pose missing channel: ' + channel);
  for (const channel of Object.keys(from)) {
    need(Object.hasOwn(to, channel), 'Pose missing channel: ' + channel);
    const a = from[channel], b = to[channel];
    need(Array.isArray(a) === Array.isArray(b) && (!Array.isArray(a) || a.length === b.length), 'Pose channel shapes differ: ' + channel);
    blended[channel] = Array.isArray(a) ? a.map((v, n) => lerp(v, b[n], amount)) : lerp(a, b, amount);
  }
  return blended;
}

export function chain(time, root, options = {}) {
  const { segments = 6, length: link = .1, rest = [0, -1, 0], lag = .05, frequency = 2.4, damping = .4, taps = 40, wind = null } = options;
  needTime(time); need(typeof root === 'function', 'Chain root must be a function');
  need(Number.isInteger(segments) && segments > 0, 'Segments must be a positive integer');
  positive(link, 'Link length'); positive(lag, 'Lag'); positive(frequency, 'Frequency');
  need(Number.isFinite(damping) && damping > 0 && damping < 1, 'Damping must lie between 0 and 1');
  need(Number.isInteger(taps) && taps > 1, 'Taps must be an integer above 1');
  needVector(rest, 'Rest direction'); need(length(rest) > 1e-9, 'Rest direction must not be zero');
  need(wind === null || typeof wind === 'function', 'Wind must be a function');
  // Impulse response of a damped spring, read at offsets fixed to `time`. Each link sees the same
  // response later, so a tug travels down the chain and nothing depends on the previous frame.
  const step = lag / 2, omega = TAU * frequency, settled = Math.sqrt(1 - damping * damping);
  const weight = Array.from({ length: taps }, (_, k) => { const t = (k + .5) * step; return Math.exp(-damping * omega * t) * Math.sin(omega * settled * t); });
  const total = weight.reduce((sum, w) => sum + w, 0), past = [];
  need(total > 1e-6, 'Chain window is too short for its frequency');
  for (let j = 0; j < taps + segments * 2; j++) { const p = root(time - j * step); needVector(p, 'Chain root'); past.push(p); }
  const response = i => weight.reduce((sum, w, k) => add(sum, scale(past[k + i * 2], w / total)), [0, 0, 0]);
  const points = [past[0]];
  for (let i = 1; i <= segments; i++) {
    const breeze = wind ? wind(time, i) : [0, 0, 0];
    needVector(breeze, 'Wind');
    const goal = add(add(response(i), scale(rest, i * link)), breeze), reach = sub(goal, points[i - 1]);
    const size = length(reach);
    points.push(add(points[i - 1], size > 1e-9 ? scale(reach, link / size) : scale(rest, link / length(rest))));
  }
  return points;
}

export function held(time, rate) {
  needTime(time); positive(rate, 'Hold rate');
  return Math.floor(time * rate + 1e-9) / rate; // The nudge keeps binary rounding from losing a whole held frame.
}

export function accent(time, onsets, { decay = .035, gain = 1, max = 1 } = {}) {
  needTime(time); positive(decay, 'Decay'); positive(max, 'Maximum'); need(Number.isFinite(gain), 'Gain must be finite');
  need(Array.isArray(onsets), 'Onsets must be an array');
  let sum = 0;
  for (const onset of onsets) {
    const at = typeof onset === 'number' ? onset : onset?.time, strength = typeof onset === 'number' ? gain : onset?.gain ?? gain;
    need(Number.isFinite(at) && Number.isFinite(strength), 'Onset must have a finite time and gain');
    if (at <= time) sum += strength * Math.exp((at - time) / decay);
  }
  return Math.min(max, sum);
}

// Shots abut. A shot's `transition` { name, duration } occupies its opening and hands over from the previous shot.
export function resolveShot(time, shots) {
  needTime(time); need(Array.isArray(shots) && shots.length > 0, 'Shots must not be empty');
  const seen = new Set();
  shots.forEach((shot, i) => {
    need(typeof shot.id === 'string' && shot.id && !seen.has(shot.id), 'Shot ids must be unique strings'); seen.add(shot.id);
    need(Number.isFinite(shot.from) && Number.isFinite(shot.to) && shot.to > shot.from, 'Shot needs a finite from < to: ' + shot.id);
    need(i === 0 || Math.abs(shot.from - shots[i - 1].to) < 1e-9, 'Shots must abut: ' + shot.id);
    if (shot.transition) { need(i > 0, 'The first shot has nothing to transition from'); need(typeof shot.transition.name === 'string', 'Transition needs a name'); positive(shot.transition.duration, 'Transition duration'); need(shot.transition.duration <= shot.to - shot.from, 'Transition outlasts its shot: ' + shot.id); }
  });
  const end = shots[shots.length - 1].to;
  need(time >= shots[0].from && time <= end, 'Time lies outside the shots');
  const index = time === end ? shots.length - 1 : shots.findIndex(shot => time < shot.to), shot = shots[index], local = time - shot.from;
  const opening = shot.transition && local < shot.transition.duration;
  return { id: shot.id, index, local, progress: local / (shot.to - shot.from), transition: opening ? { name: shot.transition.name, from: shots[index - 1].id, to: shot.id, progress: local / shot.transition.duration } : null };
}

const VOWELS = { a: [1, .45, .1], e: [.55, .85, 0], i: [.3, 1, 0], o: [.7, .1, .85], u: [.35, 0, 1] };

export function mouth(time, vowels, { attack = .05, release = .09 } = {}) {
  needTime(time); positive(attack, 'Attack'); positive(release, 'Release'); need(Array.isArray(vowels), 'Vowels must be an array');
  let total = 0, strongest = 0, vowel = 'rest'; const shape = [0, 0, 0];
  for (const cue of vowels) {
    need(Object.hasOwn(VOWELS, cue.vowel), 'Unknown vowel: ' + cue.vowel);
    need(Number.isFinite(cue.from) && Number.isFinite(cue.to) && cue.to > cue.from, 'Vowel needs a finite from < to');
    const weight = clamp((time - cue.from) / attack) * clamp(1 - (time - cue.to) / release);
    if (weight <= 0) continue;
    total += weight; VOWELS[cue.vowel].forEach((v, i) => { shape[i] += v * weight; });
    if (weight > strongest) { strongest = weight; vowel = cue.vowel; }
  }
  const k = total > 1 ? 1 / total : 1;
  return { open: shape[0] * k, wide: shape[1] * k, round: shape[2] * k, vowel };
}

export function hash01(seed, ...integers) {
  let h = (Math.imul(seed | 0, 0x9e3779b1) ^ 0x811c9dc5) >>> 0;
  for (const value of integers) { h = Math.imul(h ^ (value | 0), 0x01000193); h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d); h ^= h >>> 13; }
  h = Math.imul(h ^ (h >>> 16), 0x297a2d39);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

const BLINK = { close: .05, shut: .025, open: .12 };
const blinkOptions = ({ seed = 1, mean = 3.4 } = {}) => { need(Number.isInteger(seed), 'Blink seed must be an integer'); need(Number.isFinite(mean) && mean >= 1.5, 'Blink mean must be at least 1.5 seconds'); return { seed, mean }; };
// One blink lands somewhere in each cell, so any time can find its neighbours without a history.
// A double blink is dropped if it could run into the next cell's earliest blink.
const DOUBLE_GAP = .34, MIN_GAP = .25;
const blinksIn = (cell, { seed, mean }) => {
  const at = (cell + .1 + .8 * hash01(seed, cell)) * mean;
  return hash01(seed, cell, 1) < .18 && at + DOUBLE_GAP + MIN_GAP <= (cell + 1.1) * mean ? [at, at + DOUBLE_GAP] : [at];
};

export function blinkTimes(from, to, options) {
  needTime(from); needTime(to); need(to >= from, 'Blink range must ascend');
  const settings = blinkOptions(options), found = [];
  for (let cell = Math.floor(from / settings.mean) - 1; cell * settings.mean <= to; cell++) found.push(...blinksIn(cell, settings).filter(t => t >= from && t < to));
  return found;
}

export function blink(time, options) {
  needTime(time);
  const settings = blinkOptions(options), cell = Math.floor(time / settings.mean);
  let closed = 0;
  for (const at of [...blinksIn(cell - 1, settings), ...blinksIn(cell, settings)]) {
    const t = time - at, { close, shut, open } = BLINK;
    if (t < 0 || t > close + shut + open) continue;
    closed = Math.max(closed, t < close ? t / close : t < close + shut ? 1 : 1 - (t - close - shut) / open);
  }
  return closed;
}
