// The film's pure world: terrain, path, onsets, cubes, cameras and a per-frame state from absolute time.
// The height function exists twice, here and as GLSL in shaders.mjs. Both hash integers, so the feet
// planted by JS land on the surface the shader draws. Change one and you must change the other.
import { accent, chain, gait, hash01, humanoid, held, resolveShot } from './rig.mjs';

export const BPM = 150;
const atBeat = b => b * 60 / BPM; // Multiply first, so whole-frame beats land on exact frame times.
// Sparse on purpose: a hit on each bar, with one extra for the word and one off the beat near the end.
export const ONSETS = [4, 8, 12, 16, 17, 20, 24, 25.5, 28].map(atBeat);
export const WORD = Object.freeze({ text: 'ONWARD', from: atBeat(17), to: atBeat(24) });

const fract = v => v - Math.floor(v);
const clamp = (v, low = 0, high = 1) => Math.min(high, Math.max(low, v));
const smooth = (low, high, v) => { const k = clamp((v - low) / (high - low)); return k * k * (3 - 2 * k); };
const mix = (a, b, k) => a + (b - a) * k;

function lattice(x, y) {
  let h = Math.imul(x, 0x3504f333) ^ Math.imul(y, 0xf1bbcdcb);
  h = Math.imul(h, 741103597); h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d);
  return (h >>> 8) / 16777215;
}
function noise(x, y) {
  const i = Math.floor(x), j = Math.floor(y), u = x - i, v = y - j;
  const a = u * u * u * (u * (u * 6 - 15) + 10), b = v * v * v * (v * (v * 6 - 15) + 10);
  return mix(mix(lattice(i, j), lattice(i + 1, j), a), mix(lattice(i, j + 1), lattice(i + 1, j + 1), a), b);
}
function ridged(x, y, octaves) {
  let sum = 0, amp = .5;
  for (let k = 0; k < octaves; k++) {
    const n = 1 - Math.abs(2 * noise(x, y) - 1); sum += amp * n * n; amp *= .5;
    [x, y] = [(.8 * x + .6 * y) * 2.03 + 17.1, (-.6 * x + .8 * y) * 2.03 + 9.2];
  }
  return sum;
}

// Irregular boulders: at most one per warped cell, a dome cut by a tilted face.
function rocks(x, z, size, salt) {
  const wx = x + (noise(x / size * 1.7 + salt, z / size * 1.7) - .5) * size * .6, wz = z + (noise(z / size * 1.7, x / size * 1.7 + salt) - .5) * size * .6;
  const i = Math.floor(wx / size), j = Math.floor(wz / size), r = lattice(i + salt, j), turn = lattice(i, j + salt) * 6.283;
  if (r < .62) return 0;
  const k = (r - .62) / .38, dx = wx - (i + .5) * size, dz = wz - (j + .5) * size, c = Math.cos(turn), s = Math.sin(turn), a = c * dx + s * dz, b = c * dz - s * dx, u = Math.abs(a), v = Math.abs(b);
  const radius = size * (.16 + .34 * k * k), edge = 1 - Math.max(u * 1.25, v, (u + v) * .72) / radius;
  return edge > 0 ? Math.min(Math.sqrt(edge * (2 - edge)), .65 + .5 * a / radius) * radius * .62 : 0;
}
export const trailX = z => 2.4 * Math.sin(z / 13) + 1.1 * Math.sin(z / 5.7 + 1.2);
export const path = s => [trailX(s), s];
export function height(x, z) {
  const d = Math.abs(x - trailX(z)), m = smooth(5, 70, d), wall = smooth(170, 480, z), clear = smooth(2.5, 11, d);
  const raw = ridged(x * .0105, z * .0105, 5) * (6 + 78 * m + 58 * wall), step = (raw + 7 * noise(x * .021, z * .021)) / 3.4, whole = Math.floor(step);
  const big = mix(raw, (whole + smooth(.1, .5, step - whole)) * 3.4, m * .55);
  const mid = (ridged(x * .07 + 3.1, z * .07, 3) - .42) * (.35 + 5.5 * m);
  const fine = (noise(x * .62, z * .62) - .5) * .42 + (noise(x * 1.9 + 5, z * 1.9) - .5) * .14;
  return big - 5.5 + mid + fine * (.55 + .45 * m) + clear * (rocks(x, z, 7.3, 11) + rocks(x + 1.7, z - .9, 2.9, 23));
}

export const body = humanoid(1.7);
const SPEED = 1.3, STRIDE = 1.3, START = 2;
const walk = time => gait(time, { speed: SPEED, stride: STRIDE, distance: START + SPEED * time, path, ground: height, body });
const anchor = time => { const { neck, chest } = walk(time).joints; return [neck[0] + (neck[0] - chest[0]) * .1, neck[1] - .02, neck[2] + (neck[2] - chest[2]) * .1 - .05]; };
const SCARF = { segments: 8, length: .11, rest: [.34, -.42, -1], lag: .05, frequency: 1.6, damping: .32, wind: (t, i) => [.028 * i * Math.sin(t * 3.1 + i * .9), .012 * i * Math.sin(t * 4.3 + i * 1.7), 0] };

export const JOINTS = ['pelvis', 'spine', 'chest', 'neck', 'head', ...['L', 'R'].flatMap(s => ['shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle', 'heel', 'toe', 'tip'].map(j => j + s))];
export const CUBES = 18, SCARF_POINTS = SCARF.segments + 1;
export const BEACON = Object.freeze({ position: [16, 84, 560], radius: 15 });
export const SUN = (() => { const v = [.14, .13, .98], l = Math.hypot(...v); return v.map(c => c / l); })();

const quaternion = (axis, angle) => { const l = Math.hypot(...axis), s = Math.sin(angle / 2) / l; return [axis[0] * s, axis[1] * s, axis[2] * s, Math.cos(angle / 2)]; };
const matrix = ([x, y, z, w]) => [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w), 2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w), 2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)];
// Seeded; column-major matrices for GLSL. Most hang left of the valley, and none cross the line to the beacon.
function cube(i, time) {
  const r = n => hash01(41, i, n), z = 62 + 170 * r(0) ** 1.3, side = r(12) < .72 ? -1 : 1, x = side * mix(13 + z * .1, 62 + z * .1, r(1)), size = mix(1.2, 6.5, r(2) ** 2.4);
  const y = height(x, z) * .4 + mix(9, 30, r(3)) + z * .05, angle = (r(4) * 6.3) + time * mix(.05, .16, r(5)) * (r(6) < .5 ? -1 : 1);
  return { center: [x + Math.sin(time * .17 + r(7) * 6) * 1.1, y + Math.sin(time * .23 + r(8) * 6) * .9, z], size, rotation: matrix(quaternion([r(9) - .5, r(10) - .5, r(11) - .5 + .001], angle)) };
}

const norm = v => { const l = Math.hypot(...v); return v.map(c => c / l); };
function camera(shot, local, time, focus, heading) {
  const f = [Math.sin(heading), 0, Math.cos(heading)], l = [f[2], 0, -f[0]], at = (b, s, u) => [focus[0] - f[0] * b + l[0] * s, focus[1] + u, focus[2] - f[2] * b + l[2] * s];
  const ahead = (d, s, u) => [focus[0] + f[0] * d + l[0] * s, focus[1] + u, focus[2] + f[2] * d + l[2] * s];
  switch (shot.id) {
    case 'approach': return { eye: at(29 - local * .4, -8 + local * .35, 3.3), look: ahead(9, -2.6, 5.2), fov: 30, exposure: 1 };
    case 'profile': return { eye: ahead(12 - local * .35, 6.5, 2.3), look: at(9, 2 + local * .2, 1.6), fov: 30, exposure: .74 };
    case 'word': return { eye: at(11.5 - local * .25, -1.9 + local * .12, .6), look: ahead(9, 1.2, 1.3), fov: 28, exposure: 1 };
    default: return { eye: at(30 + local * 1.2, -13, 8 + local * 1), look: ahead(40, -2, 6 + local * .3), fov: 34, exposure: 1 };
  }
}

export function frameState(time, shots, { reducedMotion = false, word = true } = {}) {
  const onsets = reducedMotion ? [] : ONSETS, state = walk(time), shot = resolveShot(time, shots), active = shots[shot.index];
  const [cx, cz] = path(state.distance), focus = [cx, height(cx, cz) + 1, cz];
  const hit = accent(time, onsets, { decay: .035 }), latest = onsets.filter(t => t <= time).length;
  const view = camera(active, shot.local, time, focus, Math.atan2(trailX(state.distance + 4) - trailX(state.distance - 4), 8));
  const bump = [hash01(9, latest, 0) - .5, 1, hash01(9, latest, 1) - .5];
  const eye = view.eye.map((v, i) => v + bump[i] * hit * .09);
  // The eye must not pass into a rock in a low shot.
  eye[1] = Math.max(eye[1], height(eye[0], eye[2]) + .4);
  const forward = norm([view.look[0] - eye[0], view.look[1] - eye[1], view.look[2] - eye[2]]), right = norm([forward[2], 0, -forward[0]].map(v => -v));
  const up = [right[1] * forward[2] - right[2] * forward[1], right[2] * forward[0] - right[0] * forward[2], right[0] * forward[1] - right[1] * forward[0]];
  const shown = word && time >= WORD.from && time < WORD.to;
  return {
    shot, eye, exposure: view.exposure, basis: [...right, ...up, ...forward], focal: 1 / Math.tan(view.fov * Math.PI / 360),
    joints: JOINTS.flatMap(name => state.joints[name]),
    scarf: chain(time, anchor, SCARF).flat(), walk: state,
    cubes: Array.from({ length: CUBES }, (_, i) => cube(i, time)),
    turn: time * .32, hit, latest, split: shown ? accent(time, reducedMotion ? [] : [WORD.from], { decay: .022 }) : 0, wordOn: shown ? 1 : 0, boil: held(time, 8)
  };
}
