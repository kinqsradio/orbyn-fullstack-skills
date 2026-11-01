// Animate the character inside one image by bending a mesh over it. Pure and
// dependency-free: every result is a function of absolute time, so any frame can be
// rendered again on its own. Coordinates are image fractions, y down.
//
//   validateRegions(regions)        Reject a rig that cannot animate.
//   createMesh(cols, rows)          Grid of points and triangle indices.
//   regionWeight(region, x, y)      Soft 0-1 mask from the region polygon.
//   displace(region, x, y, time)    One region's offset at a point, unweighted.
//   peakDisplacement(region)        Largest distance one region moves a point, in image fractions.
//   defaultFeather(region)          Fade width used when a region sets none.
//   deform(mesh, regions, time)     Moved points, as a Float32Array of x, y pairs; frame edges stay covered.
//   blinkClosure(time, seed)        Eye closure 0-1 at irregular seeded gaps.
//   invertedTriangles(mesh, points) Count of folded triangles; 0 means no tearing.
//   drawnState(regions, time)       Which registered drawings to show: closed eyes, open mouth.

const TAU = Math.PI * 2;
const KINDS = new Set(['hair', 'breath', 'sway', 'blink', 'mouth']);
const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
const smooth = v => { const t = clamp(v); return t * t * (3 - 2 * t); };
const wave = (time, period, phase = 0) => Math.sin(TAU * time / period + phase);
const isPoint = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
const isPositive = v => Number.isFinite(v) && v > 0;
const optional = (v, ok) => v === undefined || ok(v);
const needTime = time => { if (!Number.isFinite(time)) throw new RangeError('Time must be finite'); };
const polygonArea = polygon => Math.abs(polygon.reduce((sum, [x, y], i) => {
  const [nx, ny] = polygon[(i + 1) % polygon.length];
  return sum + x * ny - nx * y;
}, 0)) / 2;

export function validateRegions(regions) {
  if (!Array.isArray(regions) || !regions.length) throw Error('Rig needs at least one region');
  const ids = new Set();
  for (const r of regions) {
    if (!r || typeof r.id !== 'string' || !r.id || ids.has(r.id)) throw Error('Region ids must be unique strings');
    ids.add(r.id);
    if (!KINDS.has(r.kind)) throw Error(`Unknown region kind: ${r.kind}`);
    if (!Array.isArray(r.polygon) || r.polygon.length < 3 || !r.polygon.every(isPoint)) {
      throw Error(`Region ${r.id} needs a polygon of at least 3 [x, y] points`);
    }
    if (!(polygonArea(r.polygon) > 1e-9)) throw Error(`Region ${r.id} has a polygon with no area`);
    if (!optional(r.feather, isPositive)) throw Error(`Region ${r.id} needs a positive feather`);
    if (!optional(r.phase, Number.isFinite)) throw Error(`Region ${r.id} needs a finite phase`);
    const moves = isPositive(r.amp) && isPositive(r.period);
    if (r.kind === 'hair' && !(isPoint(r.root) && isPoint(r.tip) && moves && optional(r.lag, Number.isFinite))) throw Error(`Hair ${r.id} needs root, tip, amp and period`);
    if (r.kind === 'breath' && !(moves && Number.isFinite(r.peakY) && optional(r.reach, isPositive))) throw Error(`Breath ${r.id} needs amp, period and peakY`);
    if (r.kind === 'sway' && !(isPoint(r.pivot) && moves)) throw Error(`Sway ${r.id} needs pivot, amp and period`);
    if ((r.kind === 'blink' || r.kind === 'mouth') && !Number.isFinite(r.lineY)) throw Error(`${r.id} needs lineY`);
    if (r.kind === 'mouth' && !(typeof r.open === 'function' && optional(r.height, isPositive))) throw Error(`Mouth ${r.id} needs an open(time) function`);
  }
  return regions;
}

export function createMesh(cols, rows) {
  if (!(Number.isInteger(cols) && Number.isInteger(rows) && cols > 0 && rows > 0)) throw Error('Mesh needs positive whole cells');
  const points = new Float32Array((cols + 1) * (rows + 1) * 2);
  const indices = new Uint32Array(cols * rows * 6);
  let at = 0, tri = 0;
  for (let y = 0; y <= rows; y++) for (let x = 0; x <= cols; x++) { points[at++] = x / cols; points[at++] = y / rows; }
  const vertex = (x, y) => y * (cols + 1) + x;
  for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
    indices.set([vertex(x, y), vertex(x + 1, y), vertex(x, y + 1), vertex(x + 1, y), vertex(x + 1, y + 1), vertex(x, y + 1)], tri);
    tri += 6;
  }
  return {cols, rows, points, indices};
}

function edgeDistance(polygon, x, y) {
  let inside = false, best = Infinity;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [ax, ay] = polygon[i], [bx, by] = polygon[j];
    if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) inside = !inside;
    const dx = bx - ax, dy = by - ay, t = clamp(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy || 1));
    best = Math.min(best, Math.hypot(x - ax - t * dx, y - ay - t * dy));
  }
  return inside ? best : -best;
}

// A smoothstep fade is steepest at 1.5 / width, so a fade about 1.5 times the peak
// displacement is the narrowest that keeps points from overtaking their neighbours.
const SWING_PEAK = 1.35; // The two waves in hair() add up to this at most.
export function peakDisplacement(r) {
  switch (r.kind) {
    case 'hair': return r.amp * SWING_PEAK;
    case 'sway': return r.amp * Math.max(...r.polygon.map(([x, y]) => Math.hypot(x - r.pivot[0], y - r.pivot[1])));
    case 'breath': return r.amp;
    case 'mouth': return r.height ?? MOUTH_HEIGHT;
    default: return 0; // A blink's lid arc already reaches zero at the corners.
  }
}
export const defaultFeather = region => Math.max(.04, 1.5 * peakDisplacement(region));

export function regionWeight(region, x, y) {
  return smooth(edgeDistance(region.polygon, x, y) / (region.feather ?? defaultFeather(region)));
}

// Later points along a strand lag the root, which gives a wave instead of a stiff swing.
function hair(r, x, y, time) {
  const [ax, ay] = r.root, [bx, by] = r.tip, dx = bx - ax, dy = by - ay, length = Math.hypot(dx, dy) || 1;
  const along = clamp(((x - ax) * dx + (y - ay) * dy) / (length * length));
  const reach = along ** 1.6;
  const swing = wave(time - along * (r.lag ?? .35), r.period, r.phase) + .35 * wave(time - along * .5, r.period * .43, r.phase);
  const amount = r.amp * reach * swing;
  return [-dy / length * amount, dx / length * amount];
}

function sway(r, x, y, time) {
  const angle = r.amp * wave(time, r.period, r.phase), [px, py] = r.pivot;
  const c = Math.cos(angle), s = Math.sin(angle), dx = x - px, dy = y - py;
  return [dx * c - dy * s - dx, dx * s + dy * c - dy];
}

const BLINK_CLOSE = .07, BLINK_OPEN = .13, DRAWN_EYE_AT = .7, MOUTH_HEIGHT = .012;
function* blinkStarts(seed) {
  let state = seed >>> 0 || 1, at = 0;
  for (;;) {
    state = Math.imul(state, 1664525) + 1013904223 >>> 0;
    at += 2 + 3.5 * state / 2 ** 32;
    yield at;
    if (state % 5 === 0) yield at + .32; // A quick double blink reads as alive.
  }
}

export function blinkClosure(time, seed = 7) {
  needTime(time);
  for (const start of blinkStarts(seed)) {
    if (start > time) return 0;
    const local = time - start;
    if (local < BLINK_CLOSE) return smooth(local / BLINK_CLOSE);
    if (local < BLINK_CLOSE + BLINK_OPEN) return 1 - smooth((local - BLINK_CLOSE) / BLINK_OPEN);
  }
  return 0;
}

// A lid travels most over the iris and not at all at the corners or the top of the
// region, so the region's edges shear gently. A flat pull there folds the mesh as soon
// as head or hair motion is added.
function lidTravel(r, x, y) {
  const xs = r.polygon.map(p => p[0]), left = Math.min(...xs), u = clamp((x - left) / (Math.max(...xs) - left));
  const top = Math.min(...r.polygon.map(p => p[1])), span = r.lineY - top, v = clamp((r.lineY - y) / span);
  return span * v * (1 - v ** 4) * 4 * u * (1 - u);
}

export function displace(r, x, y, time) {
  switch (r.kind) {
    case 'hair': return hair(r, x, y, time);
    case 'sway': return sway(r, x, y, time);
    case 'breath': { // The chest rises most along peakY and fades to nothing by reach.
      const rise = clamp(1 - Math.abs(y - r.peakY) / (r.reach ?? .3));
      return [0, -r.amp * rise * (.5 + .5 * wave(time, r.period, r.phase))];
    }
    case 'blink': { // The lid starts down; once the drawn closed eye takes over the warp lets go.
      const closure = blinkClosure(time, r.seed);
      return [0, y < r.lineY && closure <= DRAWN_EYE_AT ? lidTravel(r, x, y) * closure : 0];
    }
    case 'mouth': // The jaw lowers as a block, so the fade can absorb it without folding.
      return [0, (r.height ?? MOUTH_HEIGHT) * clamp(r.open(time)) * smooth((y - r.lineY) / .012)];
    default: throw Error(`Unknown region kind: ${r.kind}`);
  }
}

// A warp can squash an eye but cannot draw a closed lid or the inside of a mouth, so
// the page swaps to a registered drawing of that state once the warp has done its part.
export function drawnState(regions, time) {
  const eye = regions.find(r => r.kind === 'blink'), mouth = regions.find(r => r.kind === 'mouth');
  return {
    eyesClosed: !!eye && blinkClosure(time, eye.seed) > DRAWN_EYE_AT,
    mouthOpen: !!mouth && mouth.open(time) > .3,
  };
}

// Motion toward or away from a frame edge fades out across this margin, so the border
// stays on the border. Along the edge it is free. Otherwise a chest that rises past the
// bottom row uncovers the backdrop beneath it.
const EDGE_MARGIN = .06;

// Which vertices a region touches, and how much. Only the polygon and feather decide
// this, so it is worked out once per mesh instead of on every frame.
const covers = new WeakMap();
function regionCover(mesh, region) {
  if (!covers.has(mesh)) covers.set(mesh, new WeakMap());
  const known = covers.get(mesh);
  if (!known.has(region)) {
    const vertices = [], weights = [];
    for (let i = 0; i < mesh.points.length; i += 2) {
      const weight = regionWeight(region, mesh.points[i], mesh.points[i + 1]);
      if (weight) { vertices.push(i); weights.push(weight); }
    }
    known.set(region, {vertices, weights});
  }
  return known.get(region);
}

export function deform(mesh, regions, time) {
  needTime(time);
  const moved = new Float32Array(mesh.points), move = new Float64Array(mesh.points.length);
  for (const region of regions) {
    const {vertices, weights} = regionCover(mesh, region);
    vertices.forEach((i, n) => {
      const [dx, dy] = displace(region, mesh.points[i], mesh.points[i + 1], time);
      move[i] += dx * weights[n];
      move[i + 1] += dy * weights[n];
    });
  }
  for (let i = 0; i < moved.length; i += 2) {
    const x = moved[i], y = moved[i + 1];
    moved[i] += move[i] * smooth(Math.min(x, 1 - x) / EDGE_MARGIN);
    moved[i + 1] += move[i + 1] * smooth(Math.min(y, 1 - y) / EDGE_MARGIN);
  }
  return moved;
}

export function invertedTriangles(mesh, points) {
  let inverted = 0;
  for (let i = 0; i < mesh.indices.length; i += 3) {
    const [a, b, c] = [mesh.indices[i], mesh.indices[i + 1], mesh.indices[i + 2]].map(v => v * 2);
    const area = (points[b] - points[a]) * (points[c + 1] - points[a + 1]) - (points[b + 1] - points[a + 1]) * (points[c] - points[a]);
    if (!(area > 0)) inverted++; // Written so a NaN point counts as folded.
  }
  return inverted;
}
