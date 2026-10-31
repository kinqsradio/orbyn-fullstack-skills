#!/usr/bin/env node
// Original local-CLI EDL executor. Source media and earlier output are never overwritten.
import { readFile, writeFile, mkdir, realpath, lstat, stat, statfs, copyFile } from 'node:fs/promises';
import { createWriteStream } from 'node:fs';
import { resolve, dirname, join, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { validateEDL, planEDL, captionVTT, decodeVTT } from './media.mjs';
import { frameTime, rate } from './time.mjs';
const hash = value => createHash('sha256').update(value).digest('hex');
const safeHTML = text => text.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const demuxers = 'mov,matroska,webm,wav,aiff,mp3,flac,ogg,aac';
async function strictParse(raw) {
  let source = new URL('../review-core.mjs', import.meta.url), bytes;
  try { bytes = await readFile(source); }
  catch (error) { if (error.code !== 'ENOENT') throw error; source = new URL('../../review-workspace/model.mjs', import.meta.url); bytes = await readFile(source); }
  const module = await import(source.href);
  return { value: module.parseJSONStrict(raw), source: { path: fileURLToPath(source), sha256: hash(bytes) } };
}
const ratio = value => { const [n, d] = String(value).split('/').map(Number); return n / d; };
function parseOptions(args) {
  const allowed = ['edl', 'root', 'output', 'ffmpeg', 'ffprobe', 'threads', 'timeout'], options = {};
  for (let i = 0; i < args.length; i += 2) { const key = args[i]?.replace(/^--/, ''); if (!args[i]?.startsWith('--') || !allowed.includes(key) || key in options || !args[i + 1] || args[i + 1].startsWith('--')) throw Error('Invalid/duplicate media option'); options[key] = args[i + 1]; }
  if (['edl', 'root', 'output', 'ffmpeg', 'ffprobe'].some(k => !options[k])) throw Error('Use --edl LOCAL_JSON --root LOCAL_ASSETS --output NEW_DIRECTORY --ffmpeg EXISTING_BINARY --ffprobe EXISTING_BINARY');
  options.threads = Number(options.threads ?? 2); options.timeout = Number(options.timeout ?? 120);
  if (!Number.isInteger(options.threads) || options.threads < 1 || options.threads > 4 || !Number.isFinite(options.timeout) || options.timeout < .1 || options.timeout > 1800) throw Error('Invalid media thread/time budget'); return options;
}
function loudnessJSON(stderr) {
  const blocks = stderr.match(/\{\s*"input_i"[\s\S]*?\}/g); if (!blocks?.length) throw Error('Loudness measurement missing'); const measured = JSON.parse(blocks.at(-1));
  for (const key of ['input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset']) if (!Number.isFinite(Number(measured[key]))) throw Error('Loudness unavailable for silence/nonfinite input; retain the measurement and choose a different policy'); return measured;
}

export async function executeEDL(options) {
  options = { ...options, threads: options.threads ?? 2, timeout: options.timeout ?? 120 };
  if (!Number.isInteger(options.threads) || options.threads < 1 || options.threads > 4 || !Number.isFinite(options.timeout) || options.timeout < .1 || options.timeout > 1800) throw Error('Invalid media thread/time budget');
  const output = resolve(options.output), edlPath = await realpath(options.edl), root = await realpath(options.root), started = Date.now(), owned = new Set(), escalations = new Map(); let created = false, cancelled = false, timedOut = false, timer, receipt, ffmpeg, ffprobe;
  const persist = async () => { if (created) await writeFile(join(output, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n'); };
  function kill(child, signal = 'SIGTERM') { if (child.exitCode !== null || child.signalCode !== null) return; try { process.platform === 'win32' ? child.kill(signal) : process.kill(-child.pid, signal); } catch (error) { if (error.code !== 'ESRCH') { try { child.kill(signal); } catch {} } } if (signal === 'SIGTERM' && !escalations.has(child)) { const escalation = setTimeout(() => kill(child, 'SIGKILL'), 1000); escalations.set(child, escalation); child.once('close', () => { clearTimeout(escalation); escalations.delete(child); }); } }
  function cancel() { cancelled = true; for (const child of owned) kill(child); }
  function budget() { if (cancelled) throw Error('Media edit cancelled'); if (timedOut || Date.now() - started > options.timeout * 1000) throw Error('Media edit deadline exceeded'); }
  async function run(binary, args, label, captureLimit = 16 * 1024 * 1024) {
    budget(); const command = { binary, args, status: 'starting' }; await writeFile(join(output, label + '.command.json'), JSON.stringify(command, null, 2), { flag: 'wx' });
    const stdoutFile = createWriteStream(join(output, label + '.stdout.txt'), { flags: 'wx' }), stderrFile = createWriteStream(join(output, label + '.stderr.txt'), { flags: 'wx' });
    let stdout = '', stderr = '', streamError = null, stdoutBytes = 0, stderrBytes = 0;
    const child = spawn(binary, args, { stdio: ['ignore', 'pipe', 'pipe'], detached: process.platform !== 'win32' }); owned.add(child); command.pid = child.pid;
    const collect = (channel, file, value, which) => { const bytes = which === 'stdout' ? stdoutBytes += value.length : stderrBytes += value.length; if (bytes > captureLimit) { streamError = Error('Media subprocess output exceeds capture budget'); kill(child); return; } if (which === 'stdout') stdout += value.toString(); else stderr += value.toString(); if (!file.write(value)) { channel.pause(); file.once('drain', () => channel.resume()); } };
    child.stdout.on('data', value => collect(child.stdout, stdoutFile, value, 'stdout')); child.stderr.on('data', value => collect(child.stderr, stderrFile, value, 'stderr'));
    for (const file of [stdoutFile, stderrFile]) file.on('error', error => { streamError = error; kill(child); });
    let exitCode, signalCode, spawnError;
    await new Promise(resolve => { child.once('error', error => { spawnError = error; }); child.once('close', (code, signal) => { exitCode = code; signalCode = signal; resolve(); }); });
    await Promise.all([stdoutFile, stderrFile].map(file => new Promise(resolve => file.end(resolve))));
    command.exitCode = exitCode; command.signal = signalCode; command.status = exitCode === 0 && !streamError && !spawnError ? 'completed' : 'failed';
    await writeFile(join(output, label + '.command.json'), JSON.stringify(command, null, 2) + '\n'); budget(); if (spawnError || streamError) throw spawnError ?? streamError; if (exitCode !== 0) throw Error(`${label} failed (${exitCode ?? signalCode}); inspect retained stderr`); return { stdout, stderr };
  }
  const inputArgs = (inputs, sourceFiles) => inputs.flatMap(input => ['-protocol_whitelist', 'file,pipe', '-format_whitelist', demuxers, '-i', sourceFiles[input.asset]]);
  const baseArgs = () => ['-hide_banner', '-nostdin', '-n', '-threads', String(options.threads), '-filter_complex_threads', String(options.threads)];
  try {
    const parent = dirname(output); if ((await lstat(parent)).isSymbolicLink() || await realpath(parent) !== parent) throw Error('Output requires an existing real owner directory');
    await mkdir(output); created = true; receipt = { version: 1, status: 'preparing', output, startedAt: new Date().toISOString(), threads: options.threads, timeoutSeconds: options.timeout, sourceFiles: {}, limits: ['Original non-destructive local edit plan; no GUI authoring app', 'Copy is a strict single-clip video-only CFR/no-B-frame H264 profile', 'Reencode intentionally resamples VFR/retiming to the project rational clock', 'AAC padding is reported separately from intended container/sample duration', 'FFmpeg binary licensing depends on recorded build configuration; no binary redistribution implied'] }; await persist();
    process.on('SIGTERM', cancel); process.on('SIGINT', cancel); timer = setTimeout(() => { timedOut = true; for (const child of owned) kill(child); }, options.timeout * 1000);
    receipt.toolSources = {};
    for (const name of ['edit-media.mjs', 'media.mjs', 'time.mjs']) { const source = new URL(name, import.meta.url); receipt.toolSources[name] = { path: fileURLToPath(source), sha256: hash(await readFile(source)) }; }
    const raw = await readFile(edlPath); if (raw.length > 1048576) throw Error('EDL exceeds 1 MiB'); const parsed = await strictParse(raw.toString('utf8')), edl = validateEDL(parsed.value); receipt.toolSources.strictParser = parsed.source; receipt.edlSha256 = hash(raw); receipt.sourceRevision = edl.sourceRevision; await writeFile(join(output, 'edit-decision.json'), raw, { flag: 'wx' });
    ffmpeg = await realpath(options.ffmpeg); ffprobe = await realpath(options.ffprobe);
    for (const [name, binary] of [['ffmpeg', ffmpeg], ['ffprobe', ffprobe]]) { if (!(await stat(binary)).isFile()) throw Error('Regular local media executable required'); const version = await run(binary, ['-version'], name + '-version'); receipt[name] = { path: binary, sha256: hash(await readFile(binary)), versionAndConfiguration: version.stdout }; }
    const original = {}, sourceFiles = {}, probes = {}; let inputBytes = 0;
    for (const asset of edl.assets) { const file = resolve(root, asset.path); if (!file.startsWith(root + sep) || await realpath(file) !== file || !(await lstat(file)).isFile() || (await lstat(file)).isSymbolicLink()) throw Error('Asset must be a regular non-symlink file inside the selected root'); const size = (await stat(file)).size; if (size > 512 * 1024 * 1024) throw Error('Input media exceeds 512 MiB profile'); inputBytes += size; const bytes = await readFile(file); if (hash(bytes) !== asset.sha256) throw Error('Input asset digest mismatch: ' + asset.id); original[asset.id] = file; receipt.sourceFiles[asset.id] = { relativePath: asset.path, sha256: asset.sha256, bytes: size }; }
    const available = await statfs(output), estimated = inputBytes + (edl.kind === 'video' ? edl.width * edl.height * edl.durationFrames * 1.5 : edl.sampleRate * frameTime(edl.durationFrames, edl.fps) * 16);
    if (Number(available.bavail * available.bsize) < estimated + 256 * 1024 * 1024) throw Error('Insufficient conservative media disk budget');
    await mkdir(join(output, 'sources'));
    for (const [index, asset] of edl.assets.entries()) { const target = join(output, 'sources', String(index) + '.media'); await copyFile(original[asset.id], target); if (hash(await readFile(target)) !== asset.sha256) throw Error('Copied asset readback differs'); sourceFiles[asset.id] = target;
      const observed = await run(ffprobe, ['-v', 'error', '-protocol_whitelist', 'file,pipe', '-format_whitelist', demuxers, '-show_streams', '-show_format', '-of', 'json', target], 'source-' + index + '-probe'); const probe = JSON.parse(observed.stdout); probe.framesByStream = {};
      if (!/^(mov,mp4,m4a,3gp,3g2,mj2|matroska,webm|wav|aiff|mp3|flac|ogg|aac)$/.test(probe.format?.format_name ?? '')) throw Error('Unsupported explicit local media container');
      for (const stream of probe.streams.filter(s => s.codec_type === 'video')) { const frames = await run(ffprobe, ['-v', 'error', '-protocol_whitelist', 'file,pipe', '-format_whitelist', demuxers, '-select_streams', String(stream.index), '-show_frames', '-show_entries', 'frame=media_type,stream_index,key_frame,best_effort_timestamp_time,pkt_duration_time,duration_time,pict_type', '-of', 'json', target], `source-${index}-frames-${stream.index}`); probe.framesByStream[stream.index] = JSON.parse(frames.stdout).frames; if (probe.framesByStream[stream.index].length > 40000) throw Error('Source frame observation budget exceeded'); }
      probes[asset.id] = probe;
    }
    const plan = planEDL(edl, probes); receipt.plan = plan; await writeFile(join(output, 'plan.json'), JSON.stringify(plan, null, 2) + '\n', { flag: 'wx' }); await persist();
    const movie = join(output, edl.kind === 'video' ? 'edited.mp4' : 'edited.m4a'), inputs = inputArgs(plan.inputs, sourceFiles); let filterGraph = plan.filterGraph;
    if (edl.loudness) { const l = edl.loudness, filter = `loudnorm=I=${l.integrated}:TP=${l.truePeak}:LRA=${l.range}:print_format=json`; const analysis = await run(ffmpeg, [...baseArgs(), ...inputs, '-filter_complex', filterGraph.replace(/\[audio\]$/, '[audio-pre]') + `;[audio-pre]${filter}[analyzed]` + (edl.kind === 'video' ? ';[video]nullsink' : ''), '-map', '[analyzed]', '-f', 'null', '-'], 'loudness-pass1'); const measured = loudnessJSON(analysis.stderr); receipt.loudness = { requested: edl.loudness, firstPass: measured };
      filterGraph = filterGraph.replace(/\[audio\]$/, '[audio-pre]') + `;[audio-pre]loudnorm=I=${l.integrated}:TP=${l.truePeak}:LRA=${l.range}:measured_I=${measured.input_i}:measured_TP=${measured.input_tp}:measured_LRA=${measured.input_lra}:measured_thresh=${measured.input_thresh}:offset=${measured.target_offset}:linear=true:print_format=json,aresample=${edl.sampleRate},apad,atrim=end_sample=${plan.expectedAudioSamples},asetpts=N/SR/TB[audio]`; await persist();
    }
    let captionIndex = null; if (edl.captions?.length) { await writeFile(join(output, 'captions.vtt'), captionVTT(edl), { flag: 'wx' }); captionIndex = plan.inputs.length; inputs.push('-i', join(output, 'captions.vtt')); }
    const command = baseArgs();
    if (plan.mode === 'copy') command.push('-ss', String(edl.clips[0].sourceIn), ...inputs, '-t', String(plan.duration), '-map', '0:' + edl.clips[0].videoStream, '-c:v', 'copy', '-an');
    else { command.push(...inputs, '-filter_complex', filterGraph); if (edl.kind === 'video') command.push('-map', '[video]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', plan.fps, '-frames:v', String(plan.outputFrames), '-video_track_timescale', String(rate(edl.fps).numerator)); else command.push('-vn'); if (plan.hasAudio) command.push('-map', '[audio]', '-c:a', 'aac', '-b:a', '192k', '-ar', String(edl.sampleRate), '-ac', '2'); else command.push('-an'); }
    if (captionIndex !== null) command.push('-map', `${captionIndex}:s:0`, '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng');
    command.push('-map_metadata', '-1', '-metadata', 'title=' + edl.title, '-threads', String(options.threads), '-t', String(plan.duration), '-movflags', '+faststart', movie); receipt.status = 'encoding'; await persist(); const encoded = await run(ffmpeg, command, 'encode'); if (edl.loudness) receipt.loudness.secondPass = loudnessJSON(encoded.stderr);
    const observed = JSON.parse((await run(ffprobe, ['-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', movie], 'output-probe')).stdout), video = observed.streams.find(s => s.codec_type === 'video'), audio = observed.streams.find(s => s.codec_type === 'audio'); receipt.outputProbe = observed;
    if (edl.kind === 'video' && (!video || video.codec_name !== 'h264' || video.width !== edl.width || video.height !== edl.height || Number(video.nb_read_frames) !== plan.outputFrames || Math.abs(ratio(video.avg_frame_rate) - ratio(plan.fps)) > 1e-7 || Math.abs(Number(video.duration) - plan.duration) > 1 / ratio(plan.fps))) throw Error('Encoded video differs from rational frame/dimension contract');
    if (plan.hasAudio && (!audio || audio.codec_name !== 'aac' || Number(audio.sample_rate) !== edl.sampleRate || audio.channels !== 2 || Math.abs(Number(audio.duration) - plan.duration) > 2 / edl.sampleRate)) throw Error('Encoded audio container differs from intended sample duration');
    await run(ffmpeg, ['-v', 'error', '-nostdin', '-threads', String(options.threads), '-i', movie, '-map', '0:v?', '-map', '0:a?', '-f', 'null', '-'], 'full-decode'); receipt.decodePassed = true;
    if (plan.hasAudio) { const pcm = join(output, 'decoded-audio.f32'); await run(ffmpeg, ['-v', 'error', '-nostdin', '-n', '-i', movie, '-map', '0:a:0', '-c:a', 'pcm_f32le', '-ar', String(edl.sampleRate), '-ac', '2', '-f', 'f32le', pcm], 'audio-sample-decode'); const decoded = (await stat(pcm)).size / 8; if (!Number.isInteger(decoded) || decoded < plan.expectedAudioSamples || decoded - plan.expectedAudioSamples > 1024) throw Error('Decoded audio differs beyond declared final AAC padding envelope'); receipt.audioSamples = { intended: plan.expectedAudioSamples, decoded, finalPadding: decoded - plan.expectedAudioSamples, policy: 'Container intended duration checked within two samples; decoder AAC tail padding no more than one1024-sample packet' }; const bytes = await readFile(pcm), firstAudible = Array.from({ length: Math.min(plan.expectedAudioSamples, decoded) }, (_, i) => Math.max(Math.abs(bytes.readFloatLE(i * 8)), Math.abs(bytes.readFloatLE(i * 8 + 4)))).findIndex(x => x > .001); receipt.audioSamples.firstAboveMinus60dB = firstAudible;
      if (edl.loudness) { const l = edl.loudness, analysis = await run(ffmpeg, ['-hide_banner', '-nostdin', '-i', movie, '-map', '0:a:0', '-af', `loudnorm=I=${l.integrated}:TP=${l.truePeak}:LRA=${l.range}:print_format=json`, '-f', 'null', '-'], 'loudness-decoded-measurement'); const measured = loudnessJSON(analysis.stderr); receipt.loudness.decodedMeasurement = measured; if (Math.abs(Number(measured.input_i) - l.integrated) > 1 || Number(measured.input_tp) > l.truePeak + .5) throw Error('Decoded loudness differs from declared integrated/true-peak policy'); }
    }
    if (captionIndex !== null) { const decodedPath = join(output, 'captions-decoded.vtt'); await run(ffmpeg, ['-v', 'error', '-nostdin', '-n', '-i', movie, '-map', '0:s:0', '-c:s', 'webvtt', decodedPath], 'captions-decode'); const cues = decodeVTT(await readFile(decodedPath, 'utf8')); if (cues.length !== edl.captions.length || cues.some((c, i) => c.text !== edl.captions[i].text.trim() || Math.abs(c.start - frameTime(edl.captions[i].startFrame, edl.fps)) > .0011 || Math.abs(c.end - frameTime(edl.captions[i].endFrame, edl.fps)) > .0011)) throw Error('Muxed captions differ from authored frame-addressed cues'); receipt.captionsVerified = true; }
    if (hash(await readFile(edlPath)) !== receipt.edlSha256) throw Error('EDL changed during execution'); for (const asset of edl.assets) if (hash(await readFile(original[asset.id])) !== asset.sha256 || hash(await readFile(sourceFiles[asset.id])) !== asset.sha256) throw Error('Source changed during execution');
    for (const source of Object.values(receipt.toolSources)) if (hash(await readFile(source.path)) !== source.sha256) throw Error('Executed tool source closure changed during execution');
    const videoTag = edl.kind === 'video' ? 'video' : 'audio', name = edl.kind === 'video' ? 'edited.mp4' : 'edited.m4a'; await writeFile(join(output, 'playback.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${safeHTML(edl.title)}</title><style>body{font:17px/1.6 system-ui;background:#edf1ea;color:#243c35;margin:40px}main{max-width:1000px;margin:auto}video{width:100%}audio{width:100%}a{color:#325b4b}</style><main><h1>${safeHTML(edl.title)}</h1><${videoTag} controls preload="metadata" src="${name}">${captionIndex !== null ? '<track default kind="captions" src="captions.vtt" srclang="en">' : ''}</${videoTag}><p><a href="${name}">Media</a> · <a href="edit-decision.json">EDL</a> · <a href="receipt.json">Actual verification receipt</a></p><p>${safeHTML(plan.policy.video)}</p></main></html>`, { flag: 'wx' });
    receipt.mediaSha256 = hash(await readFile(movie)); receipt.bytes = (await stat(movie)).size; receipt.status = 'complete'; receipt.elapsedSeconds = (Date.now() - started) / 1000; await persist(); const reread = JSON.parse(await readFile(join(output, 'receipt.json'))); if (reread.mediaSha256 !== hash(await readFile(movie))) throw Error('Final media receipt readback differs'); return { status: 'complete', output, mediaSha256: receipt.mediaSha256, plan: plan.mode, frames: plan.outputFrames, duration: plan.duration };
  } catch (error) { if (created) { receipt.status = cancelled ? 'cancelled' : timedOut ? 'timed-out' : 'failed'; receipt.error = String(error); receipt.elapsedSeconds = (Date.now() - started) / 1000; await persist(); } throw Object.assign(error, { cancelled, timedOut }); }
  finally { clearTimeout(timer); process.off('SIGTERM', cancel); process.off('SIGINT', cancel); for (const child of owned) { kill(child); if (child.exitCode === null && child.signalCode === null) { await Promise.race([new Promise(resolve => child.once('close', resolve)), new Promise(resolve => setTimeout(resolve, 1500))]); if (child.exitCode === null && child.signalCode === null) { kill(child, 'SIGKILL'); await new Promise(resolve => child.once('close', resolve)); } } } if (created) { receipt.cleanup = { processes: [...owned].map(child => ({ pid: child.pid ?? null, exitCode: child.exitCode, signal: child.signalCode })), scope: 'Owned direct children observed settled; process-group stop requested on cancellation, no host-wide audit' }; await persist(); } }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try { const result = await executeEDL(parseOptions(process.argv.slice(2))); console.log(JSON.stringify(result)); }
  catch (error) { console.error(error.message); process.exitCode = error.cancelled ? 143 : 2; }
}
