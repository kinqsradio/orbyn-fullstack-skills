// Compare our frames with the reference frames, frame by frame. Reports per-frame mismatch and an
// activity curve (how much changes between consecutive frames), which reads timing and easing
// whatever the colours or copy. Reads the two frame folders. Writes only inside --out.
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { BlockedError, EXIT, FIDELITY, UsageError, assertIgnored, atomicWrite, captureRecord, child, ffmpeg, frameMeta, isMain, listFrames, oneOf, pad, parseArgs, parseRect, pathInside, prepareOutput, requireOptions, resolveFfmpeg, rightsOf, runCli, writeJson } from './lib.mjs';
import { cropImage, encodePng, readPng } from './png.mjs';
import { diffImages } from './diff.mjs';

const HELP = `
compare.mjs: frame-by-frame comparison of our capture against the reference.

  node compare.mjs --ref <frames dir> --clone <frames dir> --out <dir> [options]

  --fidelity F           motion (default) gates on timing and curve; pixel also gates on mismatch.
                         pixel is refused when the reference is third-party or has no rights record
  --offset K             fixed offset: our frame = reference frame + K
  --auto-align           find the offset from the activity curves. Only for a reference with no
                         capture.json, such as a video; two captures already share t = 0
  --max-shift N          auto-align search range, default 15 frames
  --region x,y,w,h       compare only this region, in reference pixels
  --pixel-threshold T    colour sensitivity 0..1, default 0.1
  --activity-threshold T colour sensitivity between frames, default 0.02
  --activity-floor F     fraction of pixels that counts as motion, default 0.002
  --threshold T          pixel mean mismatch limit, default 0.02
  --worst T              pixel worst-frame limit, default 0.05
  --motion-threshold S   start, end and duration limit in seconds, default 0.08
  --curve-threshold C    limit on the cumulative activity curve gap, 0..1, default 0.1
  --fps N                default from frames.json, else 25
  --rescale              rescale our frames to the reference size with ffmpeg (slightly lossy)
  --ffmpeg PATH          system ffmpeg, or FFMPEG_PATH
  --no-diffs             skip diff images; always skipped for a third-party reference
  --root DIR             folder --out must stay inside, default the working directory
  --replace              replace an earlier report in --out

Writes report.json, report.md and diff/NNNN.png inside --out.
Exits 0 when every gate passes, 1 when one fails, 2 on bad usage, 3 when a rights limit stops it.
Different capture settings on the two sides fail the setup gate: fix the capture first.
`;

const SETUP_KEYS = ['viewport', 'scale', 'fps', 'trigger', 'duration', 'preRoll', 'waitBefore', 'clock', 'seed', 'rafHz', 'colorScheme', 'reducedMotion', 'scrollMs', 'scrollSteps'];

export function setupDifferences(ref, clone) {
  if (!ref || !clone) return [];
  return SETUP_KEYS
    .filter((key) => JSON.stringify(ref[key] ?? null) !== JSON.stringify(clone[key] ?? null))
    .map((key) => `${key}: reference ${JSON.stringify(ref[key] ?? null)}, ours ${JSON.stringify(clone[key] ?? null)}`);
}

export function motionWindow(activity, fps, floor = 0.002) {
  let first = -1;
  let last = -1;
  activity.forEach((value, index) => { if (value > floor) { if (first < 0) first = index; last = index; } });
  return { first, last, peak: first < 0 ? -1 : activity.indexOf(Math.max(...activity)), durationS: first < 0 ? 0 : (last - first + 1) / fps };
}

export function cumulative(activity) {
  const total = activity.reduce((sum, value) => sum + value, 0);
  let running = 0;
  return activity.map((value) => { running += value; return total > 0 ? running / total : 0; });
}

/** Shift our curve by the frames that make the two cumulative curves closest. */
export function alignByActivity(reference, ours, maxShift) {
  const target = cumulative(reference);
  let best = { offset: 0, error: Infinity };
  for (let offset = -maxShift; offset <= maxShift; offset++) {
    const shifted = cumulative(shiftCurve(ours, offset, reference.length));
    const error = target.reduce((sum, value, i) => sum + Math.abs(value - shifted[i]), 0) / target.length;
    if (error < best.error - 1e-9 || (error < best.error + 1e-9 && Math.abs(offset) < Math.abs(best.offset))) best = { offset, error };
  }
  return best.offset;
}

export function shiftCurve(curve, offset, length) {
  return Array.from({ length }, (_, i) => curve[i + offset] ?? 0);
}

export function timingReport(refActivity, cloneActivity, fps, { offset = 0, floor = 0.002, motionThreshold = 0.08, curveThreshold = 0.1 } = {}) {
  const shifted = shiftCurve(cloneActivity, offset, refActivity.length);
  const reference = motionWindow(refActivity, fps, floor);
  const ours = motionWindow(shifted, fps, floor);
  const refCurve = cumulative(refActivity);
  const ourCurve = cumulative(shifted);
  const curveError = Math.max(...refCurve.map((value, i) => Math.abs(value - ourCurve[i])));
  const moved = reference.first >= 0 && ours.first >= 0;
  const error = moved ? {
    startS: (ours.first - reference.first) / fps,
    endS: (ours.last - reference.last) / fps,
    durationS: ours.durationS - reference.durationS,
    peakS: (ours.peak - reference.peak) / fps,
  } : null;
  const worst = error ? Math.max(Math.abs(error.startS), Math.abs(error.endS), Math.abs(error.durationS)) : Infinity;
  return { reference, ours, error, curveError, pass: { timing: worst <= motionThreshold, curve: moved && curveError <= curveThreshold } };
}

function loader(region) {
  return (path) => {
    const image = readPng(path);
    return region ? cropImage(image, region) : image;
  };
}

function activityOf(files, load, threshold) {
  const curve = [0];
  let previous = load(files[0]);
  for (let i = 1; i < files.length; i++) {
    const current = load(files[i]);
    curve.push(diffImages(previous, current, { threshold, tolerance: false }).ratio);
    previous = current;
  }
  return curve;
}

function rescaled(cloneFiles, size, out, binary) {
  const folder = child(out, '.rescaled');
  mkdirSync(folder, { recursive: true });
  cloneFiles.forEach((path, i) => ffmpeg(binary, ['-y', '-i', path, '-vf', `scale=${size.width}:${size.height}:flags=lanczos`, '-pix_fmt', 'rgba', child(folder, `${pad(i)}.png`)]));
  return listFrames(folder);
}

const bar = (value) => '#'.repeat(Math.min(40, Math.round(value * 400))) || '.';
const seconds = (value) => (value === null || value === undefined ? 'n/a' : `${value >= 0 ? '+' : ''}${value.toFixed(3)}s`);
const percent = (value) => `${(value * 100).toFixed(2)}%`;

function markdown(r, refAct, cloneAct, refDir, cloneDir) {
  const { error } = r.motion;
  const verdict = (ok) => (ok ? 'PASS' : 'FAIL');
  return [
    `# compare: ${refDir} vs ${cloneDir}`, '',
    `- rights: ${r.rights}; fidelity: ${r.fidelity}; result: **${verdict(r.passed)}**`,
    `- frames compared: ${r.compared}/${r.frames} at ${r.fps} fps, offset ${r.offset}`,
    ...r.setupDifferences.map((item) => `- **captures differ in ${item}**: re-capture before reading the numbers`),
    `- timing (ours minus reference): start ${seconds(error?.startS)}, end ${seconds(error?.endS)}, duration ${seconds(error?.durationS)}, peak ${seconds(error?.peakS)} -> ${verdict(r.pass.timing)} (limit ${r.limits.motionThreshold}s)`,
    `- curve gap: ${r.motion.curveError.toFixed(3)} -> ${verdict(r.pass.curve)} (limit ${r.limits.curveThreshold})`,
    `- motion window: reference frames ${r.motion.reference.first}-${r.motion.reference.last}, ours ${r.motion.ours.first}-${r.motion.ours.last}`,
    `- mean mismatch ${percent(r.meanMismatch)}, worst ${percent(r.maxMismatch)}${r.pass.pixels === undefined ? ' (reported, not gated at motion fidelity)' : ` -> ${verdict(r.pass.pixels)}`}`,
    `- worst frames: ${r.worstFrames.map((item) => `#${item.i} (${percent(item.mismatch)} at ${item.t}s)`).join(', ') || 'none'}`,
    '', '## Activity per frame', '', '```',
    'frame   t(s)   reference                                 ours',
    ...r.frameDetails.map((f) => `${String(f.i).padStart(5)} ${f.t.toFixed(2).padStart(6)}   ${bar(refAct[f.i]).padEnd(40)}  ${f.cloneIndex === null ? '' : bar(cloneAct[f.cloneIndex])}`),
    '```', '',
  ].join('\n');
}

function main() {
  const unit = { type: 'number', min: 0, max: 1 };
  const a = parseArgs(process.argv.slice(2), {
    ref: 'string', clone: 'string', out: 'string', fidelity: 'string', offset: { type: 'number', integer: true }, 'auto-align': 'flag',
    'max-shift': { type: 'number', min: 1, integer: true }, region: 'string', 'pixel-threshold': unit, 'activity-threshold': unit, 'activity-floor': unit,
    threshold: unit, worst: unit, 'motion-threshold': { type: 'number', min: 0 }, 'curve-threshold': unit, fps: { type: 'number', min: 0.1 },
    rescale: 'flag', ffmpeg: 'string', 'no-diffs': 'flag', root: 'string', replace: 'flag',
  });
  if (a.help) { console.log(HELP.trim()); return EXIT.ok; }
  requireOptions(a, ['ref', 'clone', 'out']);
  const fidelity = oneOf('fidelity', a.fidelity ?? 'motion', FIDELITY);
  if (a.offset !== undefined && a['auto-align']) throw new UsageError('Pass --offset or --auto-align, not both');
  const refDir = resolve(a.ref);
  const cloneDir = resolve(a.clone);
  // Either side can hold someone else's pixels, so the stricter record governs the run.
  const rights = [refDir, cloneDir].map(rightsOf).includes('third-party') ? 'third-party' : rightsOf(refDir);
  if (fidelity === 'pixel' && rights === 'third-party') {
    throw new BlockedError('Pixel fidelity is refused: one side is third-party or has no rights record. Offer motion-level matching: timing, easing, order and distance, built with our own design');
  }
  const out = pathInside(a.out, a.root ?? '.', 'Output');
  if (rights === 'third-party') assertIgnored(out);
  const refRecord = captureRecord(refDir);
  const cloneRecord = captureRecord(cloneDir);
  if ((a['auto-align'] || a.offset !== undefined) && refRecord && cloneRecord) {
    throw new UsageError(`--${a.offset !== undefined ? 'offset' : 'auto-align'} would hide a late start: both captures already share t = 0. Fix the start in the build`);
  }
  const refFiles = listFrames(refDir);
  let cloneFiles = listFrames(cloneDir);
  if (!refFiles.length || !cloneFiles.length) throw new UsageError('No frames found');
  const region = parseRect(a.region);
  const refFps = Number(frameMeta(refDir)?.fps) || null;
  const cloneFps = Number(frameMeta(cloneDir)?.fps) || null;
  const fps = a.fps ?? refFps ?? 25;
  const limits = {
    motionThreshold: a['motion-threshold'] ?? 0.08, curveThreshold: a['curve-threshold'] ?? 0.1,
    threshold: a.threshold ?? 0.02, worst: a.worst ?? 0.05, pixelThreshold: a['pixel-threshold'] ?? 0.1,
  };
  const floor = a['activity-floor'] ?? 0.002;
  prepareOutput(out, { marker: 'report.json', replace: !!a.replace });
  const firstRef = readPng(refFiles[0]);
  const firstClone = readPng(cloneFiles[0]);
  if (firstRef.width !== firstClone.width || firstRef.height !== firstClone.height) {
    if (!a.rescale) throw new UsageError(`Frames differ in size: reference ${firstRef.width}x${firstRef.height}, ours ${firstClone.width}x${firstClone.height}. Match the capture, or pass --rescale`);
    cloneFiles = rescaled(cloneFiles, firstRef, out, resolveFfmpeg(a.ffmpeg));
  }
  const load = loader(region);
  const activityThreshold = a['activity-threshold'] ?? 0.02;
  const refActivity = activityOf(refFiles, load, activityThreshold);
  const cloneActivity = activityOf(cloneFiles, load, activityThreshold);
  const offset = a.offset ?? (a['auto-align'] ? alignByActivity(refActivity, cloneActivity, a['max-shift'] ?? 15) : 0);
  const timing = timingReport(refActivity, cloneActivity, fps, { offset, floor, ...limits });

  const wantDiffs = !a['no-diffs'] && rights !== 'third-party';
  const diffDir = wantDiffs ? child(out, 'diff') : undefined;
  if (diffDir) mkdirSync(diffDir, { recursive: true });
  const frames = refFiles.map((path, i) => {
    const j = i + offset;
    const base = { i, t: Number((i / fps).toFixed(3)), cloneIndex: null, mismatch: null };
    if (j < 0 || j >= cloneFiles.length) return base;
    const result = diffImages(load(path), load(cloneFiles[j]), { threshold: limits.pixelThreshold, image: wantDiffs });
    if (diffDir) writeFileSync(child(diffDir, `${pad(i)}.png`), encodePng(result.image));
    return { ...base, cloneIndex: j, mismatch: Number(result.ratio.toFixed(4)) };
  });
  const compared = frames.filter((frame) => frame.mismatch !== null);
  const meanMismatch = compared.reduce((sum, frame) => sum + frame.mismatch, 0) / Math.max(1, compared.length);
  const worstFrames = [...compared].sort((x, y) => y.mismatch - x.mismatch).slice(0, 5);
  const maxMismatch = worstFrames[0]?.mismatch ?? 0;
  const differences = setupDifferences(refRecord, cloneRecord);
  // Frames at different rates line up index by index, which would hide a wrong speed.
  if (refFps !== cloneFps && !differences.some((item) => item.startsWith('fps:'))) {
    differences.push(`fps: reference ${refFps ?? 'unrecorded'}, ours ${cloneFps ?? 'unrecorded'}`);
  }
  const pass = {
    setup: differences.length === 0,
    coverage: compared.length >= frames.length - Math.abs(offset),
    ...timing.pass,
    ...(fidelity === 'pixel' ? { pixels: meanMismatch <= limits.threshold && maxMismatch <= limits.worst } : {}),
  };
  const report = {
    rights, fidelity, passed: Object.values(pass).every(Boolean), pass, fps, region, offset, limits, setupDifferences: differences,
    frames: frames.length, compared: compared.length, meanMismatch: Number(meanMismatch.toFixed(4)), maxMismatch, worstFrames,
    motion: timing, activity: { reference: refActivity.map((v) => Number(v.toFixed(4))), ours: cloneActivity.map((v) => Number(v.toFixed(4))) },
    frameDetails: frames,
  };
  rmSync(child(out, '.rescaled'), { recursive: true, force: true });
  const text = markdown(report, refActivity, cloneActivity, refDir, cloneDir);
  atomicWrite(join(out, 'report.md'), text);
  writeJson(child(out, 'report.json'), report);
  console.log(text.split('\n## Activity')[0].trimEnd());
  return report.passed ? EXIT.ok : EXIT.failed;
}

if (isMain(import.meta.url)) runCli(main);
