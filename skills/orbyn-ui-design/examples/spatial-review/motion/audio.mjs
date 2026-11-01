import { inert } from './composition.mjs';
const hash = value => { if (typeof value !== 'string' || !/^[a-f0-9]{64}$/.test(value)) throw Error('Invalid audio identity'); };
const number = (v, low = 0, high = 3600) => { if (typeof v !== 'number' || !Number.isFinite(v) || v < low || v > high) throw Error('Invalid audio value/time'); return v; };
const fields = (v, required, optional = []) => { if (!v || typeof v !== 'object' || Array.isArray(v) || required.some(k => !Object.hasOwn(v, k)) || Object.keys(v).some(k => ![...required, ...optional].includes(k))) throw Error('Invalid audio fields'); };
function times(values, duration) {
  if (!Array.isArray(values) || values.length > 50000) throw Error('Audio event budget');
  let last = -1;
  for (const value of values) { number(value, 0, duration); if (value <= last) throw Error('Audio times must be strictly ordered'); last = value; }
}
export function validateAnalysis(data, expectedSha256 = data.audio?.sha256) {
  fields(data, ['version', 'audio', 'analysis', 'manual', 'limits']);
  if (data.version !== 1) throw Error('Unsupported audio analysis'); hash(expectedSha256); hash(data.audio.sha256);
  if (data.audio.sha256 !== expectedSha256) throw Error('Stale audio analysis');
  fields(data.audio, ['sha256', 'bytes', 'duration', 'sourceSampleRate', 'sourceChannels']);
  number(data.audio.bytes, 1, 512 * 1024 * 1024); number(data.audio.duration, 1e-6); number(data.audio.sourceSampleRate, 1, 384000); number(data.audio.sourceChannels, 1, 64);
  const a = data.analysis;
  fields(a, ['sampleRate', 'hopLength', 'units', 'duration', 'status', 'tempo', 'beats', 'onsets', 'energy', 'waveform']);
  number(a.sampleRate, 1, 192000); number(a.hopLength, 1, 4096); number(a.duration, 1e-6);
  if (a.units !== 'seconds' || !['silent', 'estimated'].includes(a.status)) throw Error('Audio analysis units/status');
  if (a.tempo !== null) number(a.tempo, 1, 1000);
  times(a.beats, a.duration); times(a.onsets, a.duration);
  for (const [name, records] of [['energy', a.energy], ['waveform', a.waveform]]) {
    if (!Array.isArray(records) || records.length > 50000) throw Error('Audio feature budget');
    let previous = -1;
    for (const row of records) {
      fields(row, name === 'energy' ? ['time', 'rms'] : ['time', 'min', 'max']);
      number(row.time, 0, a.duration); if (row.time <= previous) throw Error('Feature times must be ordered'); previous = row.time;
      if (name === 'energy') number(row.rms, 0, 2);
      else { number(row.min, -1, 1); number(row.max, -1, 1); if (row.min > row.max) throw Error('Invalid waveform envelope'); }
    }
  }
  fields(data.manual, ['beats', 'words']); if (data.manual.beats !== null) times(data.manual.beats, a.duration);
  if (!Array.isArray(data.manual.words) || data.manual.words.length > 10000) throw Error('Word correction budget');
  inert(data.limits); return data;
}
function before(rows, time, field = null) {
  let low = 0, high = rows.length;
  while (low < high) { const mid = (low + high) >>> 1; if ((field ? rows[mid][field] : rows[mid]) <= time) low = mid + 1; else high = mid; }
  return low - 1;
}
export function sampleAudio(data, time, expectedSha256 = data.audio?.sha256) {
  validateAnalysis(data, expectedSha256); number(time, 0, data.analysis.duration);
  const beats = data.manual.beats ?? data.analysis.beats, index = before(beats, time), energy = data.analysis.energy;
  const e = before(energy, time, 'time'); let rms = e < 0 ? 0 : energy[e].rms;
  if (e >= 0 && e + 1 < energy.length) { const a = energy[e], b = energy[e + 1], t = (time - a.time) / (b.time - a.time); rms += (b.rms - rms) * t; }
  return { time, rms, beatIndex: index, beatTime: index < 0 ? null : beats[index],
    beatPhase: index < 0 ? 0 : index + 1 < beats.length ? (time - beats[index]) / (beats[index + 1] - beats[index]) : 0,
    beatSource: data.manual.beats === null ? data.analysis.status : 'manual', audioSha256: expectedSha256 };
}
export function withBeatCorrections(data, expectedSha256, beats) {
  validateAnalysis(data, expectedSha256); times(beats, data.analysis.duration);
  const corrected = structuredClone(data); corrected.manual.beats = [...beats]; return corrected;
}
export function validateFeatures(data, expectedSha256 = data.audioSha256) {
  fields(data, ['version', 'audioSha256', 'sampleRate', 'fps', 'frames', 'fftSize', 'status', 'bands', 'bandEnergy', 'kick', 'barEdgesHz', 'barFloorDb', 'bars', 'grid', 'downbeat', 'boundaries', 'boundaryRotation', 'limits']);
  hash(data.audioSha256); hash(expectedSha256);
  if (data.version !== 1 || data.audioSha256 !== expectedSha256) throw Error('Stale audio features');
  fields(data.fps, ['num', 'den']);
  const whole = (v, low, high) => { if (!Number.isSafeInteger(v) || v < low || v > high) throw Error('Invalid feature count'); return v; };
  whole(data.fps.num, 1, 1e6); whole(data.fps.den, 1, 1e6); whole(data.frames, 1, 1e6); number(data.sampleRate, 1, 192000);
  const unit = v => number(v, 0, 1), series = values => { if (!Array.isArray(values) || values.length !== data.frames) throw Error('Feature frame count'); values.forEach(unit); };
  if (!['silent', 'estimated'].includes(data.status) || !Array.isArray(data.bands) || !data.bands.length) throw Error('Audio feature status/bands');
  series(data.kick);
  if (Object.keys(data.bandEnergy).length !== data.bands.length) throw Error('Audio feature bands');
  for (const band of data.bands) { fields(band, ['name', 'lowHz', 'highHz', 'peak']); if (!Object.hasOwn(data.bandEnergy, band.name)) throw Error('Audio feature bands'); series(data.bandEnergy[band.name]); }
  const edges = data.barEdgesHz; if (!Array.isArray(edges) || edges.length < 2 || edges.some((v, i) => number(v, 1, 96000) <= (edges[i - 1] ?? 0))) throw Error('Spectrum bar edges');
  if (!Array.isArray(data.bars) || data.bars.length !== data.frames) throw Error('Feature frame count');
  for (const row of data.bars) { if (!Array.isArray(row) || row.length !== edges.length - 1) throw Error('Spectrum bar count'); row.forEach(unit); }
  const { grid, downbeat } = data;
  if (!['fitted', 'irregular', 'unknown'].includes(grid?.status) || !['manual', 'estimated', 'unknown', 'conflict'].includes(downbeat?.status)) throw Error('Grid/downbeat status');
  whole(downbeat.beatsPerBar, 2, 12);
  // A bar line is usable only from accent evidence or a person; grid phase never implies one.
  if ((downbeat.time !== null) !== ['manual', 'estimated'].includes(downbeat.status) || (downbeat.time !== null && grid.status !== 'fitted')) throw Error('Downbeat time/status');
  if (downbeat.time !== null) number(downbeat.time);
  inert(data.boundaries); inert(data.boundaryRotation); inert(data.limits); return data;
}
// Validates once: a sampled seek reads one row from a table of every frame.
export function featureSampler(data, expectedSha256 = data.audioSha256) {
  validateFeatures(data, expectedSha256);
  const { fps, grid, downbeat } = data, names = data.bands.map(band => band.name);
  const phase = (time, origin, period) => (((time - origin) / period) % 1 + 1) % 1;
  return frame => {
    if (!Number.isSafeInteger(frame) || frame < 0 || frame >= data.frames) throw Error('Audio feature frame out of range');
    const time = frame * fps.den / fps.num, fitted = grid.status === 'fitted';
    return { frame, time, bands: Object.fromEntries(names.map(name => [name, data.bandEnergy[name][frame]])), kick: data.kick[frame], bars: data.bars[frame],
      gridPhase: fitted ? phase(time, grid.offsetSeconds, grid.periodSeconds) : null, downbeatStatus: downbeat.status,
      barPhase: downbeat.time === null ? null : phase(time, downbeat.time, grid.periodSeconds * downbeat.beatsPerBar), audioSha256: data.audioSha256 };
  };
}
export function validateTranscript(data, expectedSha256 = data.audioSha256) {
  fields(data, ['version', 'audioSha256', 'duration', 'language', 'model', 'revision', 'words', 'history']);
  hash(data.audioSha256); hash(expectedSha256);
  if (data.version !== 1 || data.audioSha256 !== expectedSha256 || !Number.isSafeInteger(data.revision) || data.revision < 1 || typeof data.language !== 'string' || !/^[a-z]{2,3}$/.test(data.language)) throw Error('Transcript source/version/language');
  number(data.duration, 1e-6); inert(data.model);
  if (!Array.isArray(data.words) || data.words.length > 10000 || !Array.isArray(data.history) || data.history.length > 1000) throw Error('Transcript budget');
  const ids = new Set();
  for (const w of data.words) {
    fields(w, ['id', 'text', 'start', 'end', 'status', 'score']);
    if (typeof w.id !== 'string' || !/^[a-z][a-z0-9-]{0,79}$/.test(w.id) || ids.has(w.id) || typeof w.text !== 'string' || !w.text.trim() || w.text.length > 200 || !['aligned', 'inferred', 'missing', 'manual'].includes(w.status)) throw Error('Invalid word identity/content/status');
    ids.add(w.id);
    if (w.start === null || w.end === null) { if (w.status !== 'missing' || w.start !== null || w.end !== null) throw Error('Missing times must remain explicit'); }
    else { number(w.start, 0, data.duration); number(w.end, w.start, data.duration); if (w.end <= w.start) throw Error('Word duration'); }
    if (w.score !== null) number(w.score, 0, 1);
  }
  inert(data.history); return data;
}
export function correctWords(data, { audioSha256, revision, edits }) {
  validateTranscript(data, audioSha256);
  if (revision !== data.revision || !Array.isArray(edits) || edits.length > 1000) throw Error('Stale correction revision/budget');
  const result = structuredClone(data), seen = new Set(), previous = [];
  for (const edit of edits) {
    fields(edit, ['id', 'text', 'start', 'end']);
    const index = result.words.findIndex(w => w.id === edit.id);
    if (index < 0 || seen.has(edit.id)) throw Error('Unknown/duplicate corrected word'); seen.add(edit.id);
    previous.push(structuredClone(result.words[index])); result.words[index] = { ...edit, status: 'manual', score: null };
  }
  result.history.push({ revision, edits: structuredClone(edits), previous }); result.revision++;
  return validateTranscript(result, audioSha256);
}
export function wordsToCues(data, { maxWords = 8, maxDuration = 4, includeModelEstimates = false } = {}) {
  validateTranscript(data);
  if (!Number.isSafeInteger(maxWords) || maxWords < 1 || maxWords > 30) throw Error('Caption word budget'); number(maxDuration, .1, 30);
  const cues = [], unresolved = [], words = [];
  for (const w of data.words) {
    if (w.status === 'missing' || (!includeModelEstimates && w.status !== 'manual')) { unresolved.push(w.id); continue; }
    words.push(w);
  }
  words.sort((a, b) => a.start - b.start);
  let group = [];
  function flush() { if (group.length) cues.push({ start: group[0].start, end: Math.max(...group.map(w => w.end)), text: group.map(w => w.text).join(' ') }); group = []; }
  for (const word of words) { if (group.length && (group.length >= maxWords || word.end - group[0].start > maxDuration)) flush(); group.push(word); }
  flush();
  if (cues.some((c, i) => i && c.start < cues[i - 1].end)) throw Error('Overlapping caption groups need human timing correction');
  return { cues, unresolved, reviewRequired: unresolved.length > 0 || words.some(w => w.status !== 'manual'), audioSha256: data.audioSha256, transcriptRevision: data.revision };
}
// Trusted source registers this closure; saved data cannot load analysis code.
export function audioBarsComponent(analysis = null) {
  if (analysis !== null) validateAnalysis(analysis);
  const data = analysis === null ? null : structuredClone(analysis);
  return {
    dependencies: data ? [{ kind: 'audio-analysis', audioSha256: data.audio.sha256 }] : [],
    sample(clip) { const features = data ?? validateAnalysis(clip.props.analysis); return { ...sampleAudio(features, Math.max(0, Math.min(features.analysis.duration, clip.localTime))), id: clip.id, matrix: clip.worldMatrix, opacity: clip.opacity, reducedMotion: clip.reducedMotion }; },
    mount(host) { const el = host.ownerDocument.createElement('div'); el.style.position = 'absolute'; el.setAttribute('role', 'img'); host.append(el); return el; },
    update(el, state) {
      el.style.transform = `matrix(${state.matrix.join(',')})`; el.style.opacity = String(state.opacity);
      el.style.width = '240px'; el.style.height = '120px'; el.style.border = '1px solid currentColor';
      el.setAttribute('aria-label', `Audio energy ${state.rms.toFixed(3)}; ${state.beatSource} beat ${state.beatIndex}`);
      const fill = el.ownerDocument.createElement('div'); fill.style.height = `${Math.min(1, state.rms * 3) * 100}%`; fill.style.width = '100%'; fill.style.background = '#4d8378';
      const label = el.ownerDocument.createElement('span'); label.textContent = `ENERGY ${state.rms.toFixed(3)} / BEAT ${state.beatIndex}`;
      el.replaceChildren(fill, label);
    },
    async ready(_el, signal) { if (signal.aborted) throw Error('Cancelled audio figure'); },
    dispose(el) { el.remove(); },
  };
}
