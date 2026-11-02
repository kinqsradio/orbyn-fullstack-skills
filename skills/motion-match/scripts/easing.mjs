// Fit a recorded motion curve to known easings or a damped spring.
// Reads a capture's track.json, or a plain [[t_ms, value], ...] series. Writes nothing.
import { readFileSync } from 'node:fs';
import { EXIT, UsageError, isMain, parseArgs, readJson, runCli } from './lib.mjs';

const HELP = `
easing.mjs: which easing is this?

  node easing.mjs --track <track.json> --selector <css> --prop <name> [--from-ms T --to-ms T]
  node easing.mjs --series '[[t_ms, value], ...]'
  node easing.mjs --series-file <file.json>
  add --compare-track <other.json> to diff the same property on a second track

Props: x y w h opacity translateX translateY scale scaleX scaleY rotate

Prints start and end values, visible start and end, overshoot, and the best fits. Reads only
the files named. Exits 1 when there are too few samples.
`;

export const PROPS = ['x', 'y', 'w', 'h', 'opacity', 'translateX', 'translateY', 'scale', 'scaleX', 'scaleY', 'rotate'];

function bezier(x1, y1, x2, y2) {
  const steps = 1024;
  const table = new Float64Array(steps + 1);
  const at = (a, b, u) => 3 * (1 - u) ** 2 * u * a + 3 * (1 - u) * u ** 2 * b + u ** 3;
  for (let i = 0; i <= steps; i++) {
    const x = i / steps;
    let low = 0;
    let high = 1;
    for (let k = 0; k < 24; k++) {
      const mid = (low + high) / 2;
      if (at(x1, x2, mid) < x) low = mid; else high = mid;
    }
    table[i] = at(y1, y2, (low + high) / 2);
  }
  table[0] = 0;
  table[steps] = 1;
  return (t) => {
    const position = Math.min(1, Math.max(0, t)) * steps;
    const index = Math.min(steps - 1, Math.floor(position));
    return table[index] + (table[index + 1] - table[index]) * (position - index);
  };
}

const CATALOGUE = [
  ['linear', 'linear'],
  ['ease', 'cubic-bezier(0.25,0.1,0.25,1)'],
  ['ease-in', 'cubic-bezier(0.42,0,1,1)'],
  ['ease-out', 'cubic-bezier(0,0,0.58,1)'],
  ['ease-in-out', 'cubic-bezier(0.42,0,0.58,1)'],
  ['out-quad', 'cubic-bezier(0.5,1,0.89,1)'],
  ['out-cubic', 'cubic-bezier(0.33,1,0.68,1)'],
  ['out-quart', 'cubic-bezier(0.25,1,0.5,1)'],
  ['out-quint', 'cubic-bezier(0.22,1,0.36,1)'],
  ['out-expo', 'cubic-bezier(0.16,1,0.3,1)'],
  ['out-circ', 'cubic-bezier(0.075,0.82,0.165,1)'],
  ['in-cubic', 'cubic-bezier(0.32,0,0.67,0)'],
  ['in-expo', 'cubic-bezier(0.7,0,0.84,0)'],
  ['in-out-quad', 'cubic-bezier(0.45,0,0.55,1)'],
  ['in-out-cubic', 'cubic-bezier(0.65,0,0.35,1)'],
  ['in-out-quart', 'cubic-bezier(0.76,0,0.24,1)'],
  ['in-out-quint', 'cubic-bezier(0.83,0,0.17,1)'],
  ['in-out-expo', 'cubic-bezier(0.87,0,0.13,1)'],
  ['emphasized', 'cubic-bezier(0.2,0,0,1)'],
  ['standard', 'cubic-bezier(0.4,0,0.2,1)'],
  ['out-back', 'cubic-bezier(0.34,1.56,0.64,1)'],
  ['in-out-back', 'cubic-bezier(0.68,-0.6,0.32,1.6)'],
];

/** Damped spring from rest at 0 to 1, for mass 1. time is in seconds. */
export function springCurve(stiffness, damping) {
  const omega = Math.sqrt(stiffness);
  const zeta = damping / (2 * omega);
  const damped = omega * Math.sqrt(Math.max(1e-9, 1 - zeta * zeta));
  return (seconds) => (seconds <= 0 ? 0 : 1 - Math.exp(-zeta * omega * seconds) * (Math.cos(damped * seconds) + (zeta * omega / damped) * Math.sin(damped * seconds)));
}

/** Returns a 0..1 progress function for an easing written in a spec row. */
export function parseEasing(text) {
  const value = String(text).trim().replace(/\s+/g, '');
  if (value === 'linear') return (t) => Math.min(1, Math.max(0, t));
  const named = CATALOGUE.find(([name]) => name === value);
  if (named) return parseEasing(named[1]);
  const curve = value.match(/^cubic-bezier\(([^)]+)\)$/);
  if (curve) {
    const numbers = curve[1].split(',').map(Number);
    if (numbers.length === 4 && numbers.every(Number.isFinite)) return bezier(...numbers);
  }
  throw new UsageError(`Unknown easing "${text}"; use linear, a cubic-bezier(...) or a catalogue name`);
}

export function familyOf(curve) {
  const samples = Array.from({ length: 41 }, (_, i) => curve(i / 40));
  if (Math.max(...samples) > 1.005 || Math.min(...samples) < -0.005) return 'overshoot';
  if (samples.every((value, i) => Math.abs(value - i / 40) < 0.03)) return 'linear';
  const early = curve(0.25) - 0.25;
  const late = curve(0.75) - 0.75;
  if (early > 0 && late > 0) return 'out';
  if (early < 0 && late < 0) return 'in';
  return 'in-out';
}

export function matrixPart(transform) {
  const none = { tx: 0, ty: 0, sx: 1, sy: 1, rot: 0 };
  if (!transform || transform === 'none') return none;
  const match = transform.match(/matrix(3d)?\(([^)]+)\)/);
  if (!match) return none;
  const v = match[2].split(',').map(Number);
  if (match[1]) return { tx: v[12], ty: v[13], sx: Math.hypot(v[0], v[1]), sy: Math.hypot(v[4], v[5]), rot: (Math.atan2(v[1], v[0]) * 180) / Math.PI };
  return { tx: v[4], ty: v[5], sx: Math.hypot(v[0], v[1]), sy: Math.hypot(v[2], v[3]), rot: (Math.atan2(v[1], v[0]) * 180) / Math.PI };
}

export function seriesFromTrack(track, selector, prop) {
  if (!PROPS.includes(prop)) throw new UsageError(`Unknown prop "${prop}"; use one of ${PROPS.join(', ')}`);
  const series = [];
  for (const sample of track.samples ?? []) {
    const element = sample.els?.[selector];
    if (!element) continue;
    const m = matrixPart(element.transform);
    const value = { x: element.x, y: element.y, w: element.w, h: element.h, opacity: element.opacity, translateX: m.tx, translateY: m.ty, scale: m.sx, scaleX: m.sx, scaleY: m.sy, rotate: m.rot }[prop];
    series.push([sample.t, value]);
  }
  return series;
}

function changeFloor(values) {
  const low = Math.min(...values);
  const high = Math.max(...values);
  return { floor: Math.max((high - low) * 0.01, 0.002), spread: high - low };
}

/** First and last visible change, measured the same way for a reference and for ours. */
export function measure(series) {
  if (series.length < 4) throw new Error('Not enough samples: the element is missing from the track, or the window is too narrow');
  const values = series.map(([, value]) => value);
  const from = values[0];
  const to = values[values.length - 1];
  const range = to - from;
  const { floor, spread } = changeFloor(values);
  const first = values.findIndex((value) => Math.abs(value - from) > floor);
  if (first < 0) return { samples: series.length, from, to, range: 0, spread, moved: false, overshootPct: 0 };
  let last = values.length - 1;
  while (last > 0 && Math.abs(values[last] - to) <= floor) last--;
  const direction = Math.sign(range) || 1;
  const furthest = Math.max(...values.map((value) => (value - from) * direction));
  const overshoot = range === 0 ? 0 : Math.max(0, furthest - Math.abs(range)) / Math.abs(range);
  return {
    samples: series.length, from, to, range, spread, moved: true,
    peak: values.reduce((far, value) => (Math.abs(value - from) > Math.abs(far - from) ? value : far), from),
    startMs: series[first - 1][0],
    endMs: series[Math.min(series.length - 1, last + 1)][0],
    stepMs: series[first][0] - series[first - 1][0],
    overshootPct: overshoot * 100,
  };
}

function rmseOf(points, curve, delay, duration) {
  let sum = 0;
  for (const [t, y] of points) {
    const error = curve((t - delay) / duration) - y;
    sum += error * error;
  }
  return Math.sqrt(sum / points.length);
}

/**
 * Search delay and duration together. An ease-in leaves rest long before it passes the 1% floor, so
 * the true start can be far before the visible one. It can also sit up to one sample after the
 * last rest sample, because motion rarely begins exactly on a sample.
 */
function searchTiming(points, curve, start, visible, step) {
  const reach = visible * 0.5 + step;
  const evaluate = (back, scale) => ({ delay: start - back, duration: (visible + back) * scale });
  let best = { rmse: Infinity };
  const consider = (back, scale) => {
    if (back < -step || scale < 0.5) return;
    const { delay, duration } = evaluate(back, scale);
    const rmse = rmseOf(points, curve, delay, duration);
    if (rmse < best.rmse) best = { rmse, delay, duration, back, scale };
  };
  for (let i = 0; i <= 12; i++) for (let k = 0; k <= 25; k++) consider(-step + (reach * i) / 12, 1 + k * 0.04);
  const centre = best;
  for (let i = -4; i <= 4; i++) for (let k = -4; k <= 4; k++) consider(centre.back + (i * reach) / 48, centre.scale + k * 0.01);
  return best;
}

function fitSpring(points, stats, base) {
  const overshoot = Math.max(stats.overshootPct / 100, 0.002);
  const logged = -Math.log(overshoot);
  const zeta0 = logged / Math.sqrt(Math.PI ** 2 + logged ** 2);
  const peak = points.reduce((a, b) => (b[1] > a[1] ? b : a), points[0]);
  const peakSeconds = Math.max(0.016, (peak[0] - base) / 1000);
  const omega0 = Math.PI / (peakSeconds * Math.sqrt(Math.max(1e-6, 1 - zeta0 ** 2)));
  let best = { rmse: Infinity };
  for (let z = 0.7; z <= 1.3001; z += 0.03) {
    for (let w = 0.7; w <= 1.3001; w += 0.03) {
      const zeta = Math.min(0.98, zeta0 * z);
      const omega = omega0 * w;
      const stiffness = omega * omega;
      const damping = 2 * zeta * omega;
      const curve = springCurve(stiffness, damping);
      let sum = 0;
      for (const [t, y] of points) sum += (curve((t - base) / 1000) - y) ** 2;
      const rmse = Math.sqrt(sum / points.length);
      if (rmse < best.rmse) best = { rmse, stiffness, damping, zeta, omega };
    }
  }
  return best;
}

export function fit(series, { candidates = CATALOGUE } = {}) {
  const stats = measure(series);
  if (!stats.moved || stats.range === 0) return { stats, fits: [] };
  const visible = Math.max(1, stats.endMs - stats.startMs);
  const window0 = stats.startMs - visible * 0.5;
  const points = series
    .filter(([t]) => t >= window0 && t <= stats.endMs + visible * 0.05)
    .map(([t, value]) => [t, (value - stats.from) / stats.range]);
  const fits = candidates.map(([name, css]) => {
    const curve = parseEasing(css);
    const found = searchTiming(points, curve, stats.startMs, visible, stats.stepMs);
    return { name, easing: css, family: familyOf(curve), rmse: found.rmse, delayMs: found.delay, durationMs: found.duration };
  });
  if (stats.overshootPct > 0.5) {
    const spring = fitSpring(points.filter(([t]) => t >= stats.startMs), stats, stats.startMs);
    fits.push({
      name: 'spring', family: 'spring',
      easing: `spring(${spring.stiffness.toFixed(1)},${spring.damping.toFixed(2)})`,
      rmse: spring.rmse, delayMs: stats.startMs, durationMs: visible,
      stiffness: spring.stiffness, damping: spring.damping, dampingRatio: spring.zeta,
    });
  }
  fits.sort((a, b) => a.rmse - b.rmse);
  return { stats, fits };
}

export function quality(rmse) {
  return rmse < 0.03 ? 'good fit' : rmse < 0.08 ? 'approximate' : 'poor fit';
}

const round = (value, places = 3) => (value === undefined ? undefined : Number(value.toFixed(places)));

function report({ stats, fits }) {
  const top = fits[0];
  return {
    samples: stats.samples, moved: stats.moved, from: round(stats.from), to: round(stats.to), change: round(stats.range),
    visibleStartMs: round(stats.startMs, 0), visibleEndMs: round(stats.endMs, 0), overshootPct: round(stats.overshootPct, 1),
    verdict: top ? `${top.name} (${top.family}), ${quality(top.rmse)}` : stats.moved ? 'returns to its start: narrow the window with --from-ms and --to-ms' : 'no motion',
    bestFits: fits.slice(0, 5).map((item) => ({
      name: item.name, easing: item.easing, family: item.family, rmse: round(item.rmse, 4),
      delayMs: round(item.delayMs, 0), durationMs: round(item.durationMs, 0),
      ...(item.stiffness ? { stiffness: round(item.stiffness, 1), damping: round(item.damping, 2), dampingRatio: round(item.dampingRatio, 3) } : {}),
    })),
  };
}

export function compareSeries(a, b) {
  const nearest = (series, t) => series.reduce((best, point) => (Math.abs(point[0] - t) < Math.abs(best[0] - t) ? point : best), series[0])[1];
  const diffs = a.map(([t, value]) => nearest(b, t) - value);
  return { samples: b.length, maxAbsDiff: round(Math.max(...diffs.map(Math.abs))), meanAbsDiff: round(diffs.reduce((sum, value) => sum + Math.abs(value), 0) / diffs.length) };
}

function parseSeries(text) {
  let series;
  try { series = JSON.parse(text); } catch { throw new UsageError('Series is not valid JSON'); }
  if (!Array.isArray(series) || series.some((point) => !Array.isArray(point) || point.length !== 2 || !point.every(Number.isFinite))) {
    throw new UsageError('Series must be [[t_ms, value], ...]');
  }
  return series;
}

function main() {
  const args = parseArgs(process.argv.slice(2), {
    track: 'string', selector: 'string', prop: 'string', series: 'string', 'series-file': 'string', 'compare-track': 'string',
    'from-ms': { type: 'number' }, 'to-ms': { type: 'number' },
  });
  if (args.help) { console.log(HELP.trim()); return EXIT.ok; }
  const sources = ['track', 'series', 'series-file'].filter((name) => args[name] !== undefined);
  if (sources.length !== 1) throw new UsageError('Pass exactly one of --track, --series or --series-file (see --help)');
  if (args.track && (!args.selector || !args.prop)) throw new UsageError('--track needs --selector and --prop');
  let series = args.track ? seriesFromTrack(readJson(args.track), args.selector, args.prop)
    : parseSeries(args.series ?? readFileSync(args['series-file'], 'utf8'));
  series = series.filter(([t]) => t >= (args['from-ms'] ?? -Infinity) && t <= (args['to-ms'] ?? Infinity));
  const result = report(fit(series));
  if (args['compare-track']) {
    if (!args.track) throw new UsageError('--compare-track needs --track');
    result.compare = compareSeries(series, seriesFromTrack(readJson(args['compare-track']), args.selector, args.prop));
  }
  console.log(JSON.stringify(result, null, 2));
  return EXIT.ok;
}

if (isMain(import.meta.url)) runCli(main);
