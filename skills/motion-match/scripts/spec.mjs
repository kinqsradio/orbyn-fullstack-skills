// The motion spec as data: one row per element per property, written from a track and checked
// against ours. check reads only the spec and our track, so no reference capture is needed once
// the numbers are written. Writes only inside --out.
import { existsSync, realpathSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { BlockedError, EXIT, FIDELITY, RIGHTS, UsageError, assertIgnored, atomicWrite, child, isMain, oneOf, parseArgs, pathInside, prepareOutput, readJson, requireOptions, runCli, writeJson } from './lib.mjs';
import { familyOf, fit, measure, parseEasing, quality, seriesFromTrack, springCurve } from './easing.mjs';

const HELP = `
spec.mjs: write and check the motion spec.

  node spec.mjs draft --track <ref/track.json> --fidelity <motion|pixel> --name <name> --out <dir> [--props a,b] [--selectors "a, b"]
  node spec.mjs check --spec <spec.json> --track <ours/track.json> --out <dir> [limits]

  --props P            default opacity,translateX,translateY,scale,rotate
  --selectors "a, b"   default every tracked selector
  --root DIR           folder --out must stay inside, default the working directory
  --replace            replace earlier output in --out

check limits
  --timing-ms N        start and end, default 80      --stagger-ms N    gap, default 40
  --easing-rmse N      fit to the spec curve, default 0.05
  --distance N         travel, as a fraction, default 0.10

draft writes spec.json and spec.md. A row it cannot fit gets "?": replace it from the frames.
check exits 0 when every row passes, 1 when one fails, 2 when the spec still has a "?", and 3
when the spec asks for pixel fidelity from a third-party reference.
`;

const DEFAULT_PROPS = ['opacity', 'translateX', 'translateY', 'scale', 'rotate'];
const STILL_LIMIT = { opacity: 0.01, scale: 0.005, scaleX: 0.005, scaleY: 0.005, rotate: 0.5 };
const STILL_PX = 0.5;
const POOR_FIT = 0.08;
const DEFAULT_LIMITS = { timingMs: 80, staggerMs: 40, easingRmse: 0.05, distance: 0.1 };

const round = (value, places = 2) => Number(value.toFixed(places));

export function assertRightsAllowFidelity(rights, fidelity) {
  if (rights === 'third-party' && fidelity === 'pixel') {
    throw new BlockedError('A third-party reference is matched at motion level only: timing, easing, order and distance, built with our own design');
  }
}

/** A pulse has no travel between its ends, so its row records how far it reached. */
function pulsePeak(stats) {
  return stats.to === stats.from && stats.peak !== undefined ? { peak: round(stats.peak, 3) } : {};
}

export function draftSpec(track, { name, fidelity, rights, props = DEFAULT_PROPS, selectors = track.selectors }) {
  assertRightsAllowFidelity(rights, fidelity);
  const rows = [];
  for (const selector of selectors) {
    for (const prop of props) {
      const { stats, fits } = fit(seriesFromTrack(track, selector, prop));
      if (!stats.moved) { rows.push({ selector, prop, still: true, value: round(stats.from, 3) }); continue; }
      const top = fits[0];
      const known = top && top.rmse <= POOR_FIT;
      rows.push({
        selector, prop, from: round(stats.from, 3), to: round(stats.to, 3), ...pulsePeak(stats), startMs: round(stats.startMs), endMs: round(stats.endMs),
        easing: known ? top.easing : '?', family: known ? top.family : '?', delayMs: known ? round(top.delayMs) : '?', durationMs: known ? round(top.durationMs) : '?',
        overshootPct: round(stats.overshootPct, 1), fitRmse: top ? round(top.rmse, 4) : '?', source: 'track',
      });
    }
  }
  return { schema: 1, name, rights, fidelity, target: '?', destination: '?', rows };
}

export function unfinished(spec) {
  const marks = [];
  for (const field of ['target', 'destination', 'name']) if (spec[field] === '?' || spec[field] == null) marks.push(field);
  (spec.rows ?? []).forEach((row, index) => {
    for (const [key, value] of Object.entries(row)) if (value === '?' || value === null) marks.push(`row ${index + 1} (${row.selector} ${row.prop}): ${key}`);
  });
  return marks;
}

export function validateSpec(spec) {
  if (spec?.schema !== 1 || !Array.isArray(spec.rows) || !spec.rows.length) throw new UsageError('Spec needs schema 1 and at least one row');
  oneOf('rights', spec.rights, RIGHTS);
  oneOf('fidelity', spec.fidelity, FIDELITY);
  assertRightsAllowFidelity(spec.rights, spec.fidelity);
  const marks = unfinished(spec);
  if (marks.length) throw new UsageError(`Spec is unfinished, every "?" must be measured:\n  ${marks.join('\n  ')}`);
  spec.rows.forEach((row, index) => {
    if (row.still) return;
    const missing = ['from', 'to', 'startMs', 'endMs', 'delayMs', 'durationMs'].filter((key) => !Number.isFinite(row[key]));
    if (row.from === row.to && !Number.isFinite(row.peak)) missing.push('peak');
    if (missing.length) throw new UsageError(`Row ${index + 1} (${row.selector} ${row.prop}) needs numbers for: ${missing.join(', ')}`);
  });
}

function curveFor(row) {
  const spring = String(row.easing).replace(/\s+/g, '').match(/^spring\(([\d.]+),([\d.]+)\)$/);
  if (!spring) return { progress: parseEasing(row.easing), spring: false };
  return { progress: springCurve(Number(spring[1]), Number(spring[2])), spring: true };
}

/** The curve is compared after removing any start shift, so a late start is reported once. */
function easingError(series, row, clone) {
  const { progress, spring } = curveFor(row);
  const shift = clone.startMs - row.startMs;
  const end = row.endMs + shift;
  // A pulse ends where it began, so progress is measured against its peak.
  const span = row.to !== row.from ? row.to - row.from : row.peak - row.from;
  const points = series.filter(([t]) => t >= clone.startMs && t <= Math.max(end, clone.endMs));
  if (!points.length) return Infinity;
  const sum = points.reduce((total, [t, value]) => {
    const elapsed = t - shift - row.delayMs;
    // A pulse plays its curve up to the peak and back down over the same span.
    const pulse = row.to === row.from;
    const unit = elapsed / row.durationMs;
    const expected = spring ? progress(elapsed / 1000) : progress(pulse ? 1 - Math.abs(2 * unit - 1) : unit);
    return total + ((value - row.from) / span - expected) ** 2;
  }, 0);
  return Math.sqrt(sum / points.length);
}

function checkRow(track, row, limits) {
  const series = seriesFromTrack(track, row.cloneSelector ?? row.selector, row.prop);
  const base = { selector: row.selector, prop: row.prop };
  if (series.length < 4) return { ...base, pass: false, failures: ['element missing from our track'] };
  const stats = measure(series);
  if (row.still) {
    const allowed = STILL_LIMIT[row.prop] ?? STILL_PX;
    const pass = stats.spread <= allowed;
    return { ...base, still: true, pass, spread: round(stats.spread, 3), failures: pass ? [] : [`moves by ${round(stats.spread, 3)} where the reference is still`] };
  }
  if (!stats.moved) return { ...base, pass: false, failures: ['does not move'] };
  const startErrorMs = stats.startMs - row.startMs;
  const endErrorMs = stats.endMs - row.endMs;
  const pulse = row.to === row.from;
  const specDistance = pulse ? row.peak - row.from : row.to - row.from;
  const ourDistance = pulse ? stats.peak - stats.from : stats.to - stats.from;
  const distanceError = Math.abs(ourDistance - specDistance) / Math.max(Math.abs(specDistance), 1e-6);
  const rmse = easingError(series, row, stats);
  const found = fit(series).fits[0];
  const failures = [];
  if (Math.abs(startErrorMs) > limits.timingMs) failures.push(`start ${startErrorMs > 0 ? '+' : ''}${round(startErrorMs)} ms`);
  if (Math.abs(endErrorMs) > limits.timingMs) failures.push(`end ${endErrorMs > 0 ? '+' : ''}${round(endErrorMs)} ms`);
  // Written this way round so an unmeasurable curve fails instead of passing as NaN.
  if (!(rmse <= limits.easingRmse)) failures.push(`easing RMSE ${round(rmse, 3)}: spec ${row.family}, ours ${found?.family ?? 'none'}`);
  if (distanceError > limits.distance) failures.push(`distance off by ${round(distanceError * 100, 1)}%`);
  return {
    ...base, pass: failures.length === 0, startErrorMs: round(startErrorMs), endErrorMs: round(endErrorMs), easingRmse: round(rmse, 4),
    distanceErrorPct: round(distanceError * 100, 1), specFamily: row.family, ourFamily: found?.family ?? 'none', ourFit: found ? `${found.name}, ${quality(found.rmse)}` : 'none',
    ourStartMs: round(stats.startMs), failures,
  };
}

/** Gaps between consecutive starts of the same property, in the spec's order. */
function checkStagger(spec, results, limits) {
  const gaps = [];
  for (const prop of new Set(spec.rows.filter((row) => !row.still).map((row) => row.prop))) {
    const rows = spec.rows.filter((row) => row.prop === prop && !row.still).sort((a, b) => a.startMs - b.startMs);
    for (let i = 1; i < rows.length; i++) {
      const start = (row) => results.find((item) => item.selector === row.selector && item.prop === prop)?.ourStartMs;
      const [before, after] = [start(rows[i - 1]), start(rows[i])];
      if (before === undefined || after === undefined) continue;
      const specGapMs = round(rows[i].startMs - rows[i - 1].startMs);
      const ourGapMs = round(after - before);
      gaps.push({ prop, from: rows[i - 1].selector, to: rows[i].selector, specGapMs, ourGapMs, errorMs: round(ourGapMs - specGapMs), pass: Math.abs(ourGapMs - specGapMs) <= limits.staggerMs });
    }
  }
  return gaps;
}

export function checkSpec(spec, track, limits = DEFAULT_LIMITS) {
  validateSpec(spec);
  const rows = spec.rows.map((row) => checkRow(track, row, limits));
  const stagger = checkStagger(spec, rows, limits);
  return { name: spec.name, rights: spec.rights, fidelity: spec.fidelity, limits, passed: rows.every((row) => row.pass) && stagger.every((gap) => gap.pass), rows, stagger };
}

const cell = (value) => String(value ?? '').replace(/\|/g, '\\|');

function specMarkdown(spec) {
  const moving = spec.rows.filter((row) => !row.still);
  const still = spec.rows.filter((row) => row.still);
  return [
    `# ${spec.name} motion spec`, '',
    `Rights: ${spec.rights}. Fidelity: ${spec.fidelity}.`, `Target: ${spec.target}`, `Destination: ${spec.destination}`, '',
    '| # | element | property | from → to | visible start ms | visible end ms | easing | family | delay ms | duration ms | overshoot % | source |',
    '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |',
    ...moving.map((row, i) => `| ${i + 1} | ${cell(row.selector)} | ${row.prop} | ${row.from} → ${row.to} | ${row.startMs} | ${row.endMs} | ${cell(row.easing)} | ${row.family} | ${row.delayMs} | ${row.durationMs} | ${row.overshootPct} | ${row.source} |`),
    '', `Still: ${still.map((row) => `${row.selector} ${row.prop}`).join(', ') || 'none'}`, '',
  ].join('\n');
}

function checkMarkdown(result) {
  return [
    `# ${result.name} spec check: ${result.passed ? 'PASS' : 'FAIL'}`, '',
    '| element | property | start ms | end ms | easing RMSE | family (spec → ours) | distance % | result |',
    '| --- | --- | --- | --- | --- | --- | --- | --- |',
    ...result.rows.filter((row) => !row.still).map((row) => `| ${cell(row.selector)} | ${row.prop} | ${row.startErrorMs ?? ''} | ${row.endErrorMs ?? ''} | ${row.easingRmse ?? ''} | ${row.specFamily ?? ''} → ${row.ourFamily ?? ''} | ${row.distanceErrorPct ?? ''} | ${row.pass ? 'pass' : `FAIL: ${row.failures.join('; ')}`} |`),
    '', '| property | gap | spec ms | ours ms | error ms | result |', '| --- | --- | --- | --- | --- | --- |',
    ...result.stagger.map((gap) => `| ${gap.prop} | ${cell(gap.from)} → ${cell(gap.to)} | ${gap.specGapMs} | ${gap.ourGapMs} | ${gap.errorMs} | ${gap.pass ? 'pass' : 'FAIL'} |`),
    '', `Still rows failing: ${result.rows.filter((row) => row.still && !row.pass).map((row) => `${row.selector} ${row.prop} (${row.failures.join('; ')})`).join(', ') || 'none'}`, '',
  ].join('\n');
}

function rightsOfTrack(path, track) {
  const beside = join(dirname(realpathSync(path)), 'capture.json');
  const rights = track.rights ?? (existsSync(beside) ? readJson(beside).rights : undefined);
  return RIGHTS.includes(rights) ? rights : 'third-party';
}

function main() {
  const positive = { type: 'number', min: 0 };
  const a = parseArgs(process.argv.slice(2), {
    track: 'string', spec: 'string', out: 'string', fidelity: 'string', name: 'string', props: 'string', selectors: 'string', root: 'string', replace: 'flag',
    'timing-ms': positive, 'stagger-ms': positive, 'easing-rmse': positive, distance: positive,
  }, { positionals: 1 });
  if (a.help) { console.log(HELP.trim()); return EXIT.ok; }
  const mode = a._[0];
  if (mode !== 'draft' && mode !== 'check') throw new UsageError('Choose draft or check (see --help)');
  requireOptions(a, mode === 'draft' ? ['track', 'fidelity', 'name', 'out'] : ['spec', 'track', 'out']);
  const out = pathInside(a.out, a.root ?? '.', 'Output');
  const track = readJson(a.track);
  if (mode === 'draft') {
    const rights = rightsOfTrack(a.track, track);
    const spec = draftSpec(track, {
      name: a.name, fidelity: oneOf('fidelity', a.fidelity, FIDELITY), rights,
      props: a.props ? a.props.split(',').map((item) => item.trim()) : undefined,
      selectors: a.selectors ? a.selectors.split(',').map((item) => item.trim()) : undefined,
    });
    if (rights === 'third-party') assertIgnored(out);
    prepareOutput(out, { marker: 'spec.json', replace: !!a.replace });
    writeJson(child(out, 'spec.json'), spec);
    atomicWrite(child(out, 'spec.md'), specMarkdown(spec));
    console.log(specMarkdown(spec));
    return EXIT.ok;
  }
  const result = checkSpec(readJson(a.spec), track, {
    timingMs: a['timing-ms'] ?? DEFAULT_LIMITS.timingMs, staggerMs: a['stagger-ms'] ?? DEFAULT_LIMITS.staggerMs,
    easingRmse: a['easing-rmse'] ?? DEFAULT_LIMITS.easingRmse, distance: a.distance ?? DEFAULT_LIMITS.distance,
  });
  prepareOutput(out, { marker: 'check.json', replace: !!a.replace });
  writeJson(child(out, 'check.json'), result);
  atomicWrite(child(out, 'check.md'), checkMarkdown(result));
  console.log(checkMarkdown(result));
  return result.passed ? EXIT.ok : EXIT.failed;
}

if (isMain(import.meta.url)) runCli(main);
