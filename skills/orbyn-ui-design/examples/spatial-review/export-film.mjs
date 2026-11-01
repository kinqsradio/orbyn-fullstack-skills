import {rate} from './motion/time.mjs';
// Original bounded export pipeline. Requires existing Playwright/Chrome/Python/FFmpeg.
import { readFile, writeFile, mkdir, realpath, lstat, copyFile, stat, statfs, open } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { fpsValue, fpsText, DEFAULT_FILM, validateFilm, subframeTimes, webVTT, validateCues } from './film.mjs';
import { canonical, parseJSONStrict } from './review-core.mjs';
import { angleArgs, softwareRenderer, sealSource, encoderSink, frameServer, orientationChart, flipRows, classifyOrientation } from './frame-stream.mjs';
const args = process.argv.slice(2), options = {};
const flags = new Set(['package', 'output', 'spec', 'audio', 'captions', 'width', 'height', 'samples', 'shutter', 'grain', 'bloom', 'threads', 'timeout', 'playwright', 'chrome', 'python', 'ffmpeg', 'ffprobe', 'reduced-motion', 'stream', 'frame-source']);
for (let i = 0; i < args.length; i++) { const name = args[i].replace(/^--/, ''); if (!args[i].startsWith('--') || !flags.has(name) || name in options) throw Error('Unknown/duplicate export option'); if (name === 'reduced-motion' || name === 'stream') options[name] = true; else { if (!args[i + 1] || args[i + 1].startsWith('--')) throw Error('Missing option value'); options[name] = args[++i]; } }
if (!options.package || !options.output) throw Error('Use --package EXISTING_SOURCE_PACKAGE --output NEW_REPO_OWNED_EXPORT_DIRECTORY');
const numeric = (name, fallback, low, high, integer = false) => { const v = Number(options[name] ?? fallback); if (!Number.isFinite(v) || v < low || v > high || (integer && !Number.isInteger(v))) throw Error('Invalid ' + name); return v; };
const width = numeric('width', 1280, 320, 3840, true), height = numeric('height', 720, 240, 3840, true);
if (width % 2 || height % 2 || width * height > 8294400) throw Error('H264 dimensions must be even and within the 4K pixel budget');
const samples = numeric('samples', 1, 1, 4, true), shutter = numeric('shutter', .5, 0, 1), grain = numeric('grain', 0, 0, 20, true), bloom = numeric('bloom', 0, 0, .2), threads = numeric('threads', 2, 1, 4, true), timeout = numeric('timeout', 600, 10, options.stream ? 14400 : 1800);
if (options['frame-source'] && !options.stream) throw Error('--frame-source needs --stream');
const pkg = await realpath(options.package), output = resolve(options.output), hash = v => createHash('sha256').update(v).digest('hex');
if ((await lstat(dirname(output))).isSymbolicLink() || await realpath(dirname(output)) !== dirname(output)) throw Error('Output needs an existing real owner directory');
const spec = validateFilm(options.spec ? parseJSONStrict(await readFile(resolve(options.spec), 'utf8')) : structuredClone(DEFAULT_FILM));
if (spec.longForm && !options.stream) throw Error('A longForm film needs --stream; its raw frames would not fit the disk budget');
const frames = Math.round(spec.duration * fpsValue(spec));
const cues = validateCues(options.captions ? parseJSONStrict(await readFile(resolve(options.captions), 'utf8')) : spec.shots.map(s => ({ start: s.from, end: s.to, text: s.caption })), spec.duration);
if (options.audio && (!(await lstat(resolve(options.audio))).isFile() || (await lstat(resolve(options.audio))).isSymbolicLink())) throw Error('Audio must be an explicitly selected regular local file');
const manifest = parseJSONStrict(await readFile(join(pkg, 'manifest.json'), 'utf8'));
async function verifySource() {
  if (canonical(parseJSONStrict(await readFile(join(pkg, 'manifest.json'), 'utf8'))) !== canonical(manifest)) throw Error('Source manifest changed');
  const { fingerprint, ...prototype } = manifest.prototype;
  if (hash(canonical({ prototype, targets: manifest.targets, assets: manifest.assets })) !== fingerprint) throw Error('Source fingerprint differs');
  for (const [name, expected] of Object.entries(manifest.assets)) {
    if (!/^[A-Za-z0-9_-][A-Za-z0-9_.-]*(?:\/[A-Za-z0-9_.-]+)*$/.test(name) || name.split('/').some(p => p.startsWith('.'))) throw Error('Unsafe source path');
    const parts = name.split('/'); for (let i = 1; i <= parts.length; i++) if ((await lstat(join(pkg, ...parts.slice(0, i)))).isSymbolicLink()) throw Error('Source parent link');
    if (hash(await readFile(join(pkg, name))) !== expected) throw Error('Changed source: ' + name);
  }
}
await verifySource();
const sealed = options['frame-source'] ? await sealSource(await realpath(options['frame-source'])) : null;
const mediaAssets = [...new Set([...(spec.background ? [spec.background.asset] : []), ...spec.shots.filter(s => s.data?.asset).map(s => s.data.asset)])];
if (mediaAssets.some(name => !Object.hasOwn(manifest.assets, name))) throw Error('Film media is not in the approved source package');
// Streaming keeps only the encoded film, so reserve a generous bitrate instead of raw frames.
const disk = await statfs(dirname(output)); if (Number(disk.bavail * disk.bsize) < 100 * 1024 * 1024 + width * height * frames * (options.stream ? .25 : samples * 4.1)) throw Error('Insufficient conservative render disk budget');
await mkdir(output); if (!options.stream) await mkdir(join(output, 'frames')); // Exclusive: never reuse or erase another export.
const started = Date.now(), owned = new Set(); let browser, server, frameHost, encoder, sink, cancelled = false, timer;
const receipt = { status: 'preparing', sourceFingerprint: manifest.prototype.fingerprint, modelRevision: manifest.assets['engine-data.json'], filmSpecSha256: hash(canonical(spec)), fps: spec.fps, frames, duration: spec.duration, width, height, samples, shutter, semanticReadouts: 'Output-frame instant; physical poses sampled within shot', grain, grainSeed: 42, bloom, threads, reducedMotion: !!options['reduced-motion'], captionCuesSha256: hash(canonical(cues)), captionVTTSha256: hash(webVTT(cues, spec.duration)), mediaAssetSha256: Object.fromEntries(mediaAssets.map(n => [n, manifest.assets[n]])), captionSource: options.captions ? 'caller-authored timed text' : 'scene explanation text, not verified audio transcription', limits: ['No provider or paid asset generation', 'No imported Scenario code/fonts/media', 'System fonts require runtime-specific visual review', 'MP4 is this film composition, not a video of the entire V12 review UI', 'No GPU/native/full-accessibility or universal style parity claim'] };
const python = options.python || process.env.REVIEW_PYTHON || 'python3', ffmpeg = options.ffmpeg || 'ffmpeg', ffprobe = options.ffprobe || 'ffprobe';
const persist = async () => writeFile(join(output, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
async function stop(child) {
  if (!child || !child.pid || child.exitCode !== null || child.signalCode !== null) return;
  child.kill('SIGTERM'); await new Promise(res => { const t = setTimeout(() => { child.kill('SIGKILL'); }, 3000); child.once('exit', () => { clearTimeout(t); res(); }); });
}
function cancel() { cancelled = true; sink?.abort(Error('Export cancelled or time budget exceeded')); for (const child of owned) child.kill('SIGTERM'); browser?.close().catch(() => {}); }
process.on('SIGINT', cancel); process.on('SIGTERM', cancel);
const budget = () => { if (cancelled || Date.now() - started > timeout * 1000) throw Error('Export cancelled or time budget exceeded'); };
// Settles on stream end, with a bounded drain in case a descendant keeps the pipes open after the tool exits.
const settled = child => new Promise((res, rej) => { child.once('error', rej); child.once('close', (code, signal) => res(signal || code)); child.once('exit', () => { const drain = setTimeout(() => { child.stdout?.destroy(); child.stderr?.destroy(); }, 2000); child.once('close', () => clearTimeout(drain)); }); });
const fileHash = async path => { const digest = createHash('sha256'); for await (const chunk of createReadStream(path)) digest.update(chunk); return digest.digest('hex'); };
async function topAtoms(path) {
  const file = await open(path), { size: total } = await file.stat(), head = Buffer.alloc(16), atoms = []; let pos = 0;
  try { while (pos + 8 <= total) { await file.read(head, 0, 16, pos); let size = head.readUInt32BE(0), header = 8; const type = head.toString('ascii', 4, 8); if (size === 1) { size = Number(head.readBigUInt64BE(8)); header = 16; } if (!size) size = total - pos; if (size < header || pos + size > total) throw Error('Invalid MP4 atom'); atoms.push({ type, offset: pos }); pos += size; } }
  finally { await file.close(); }
  return atoms;
}
async function run(command, argv, label) {
  budget(); const child = spawn(command, argv, { stdio: ['ignore', 'pipe', 'pipe'] }); owned.add(child);
  let stdout = '', stderr = '';
  child.stdout.on('data', b => { stdout += b; if (stdout.length > 2000000) child.kill('SIGTERM'); }); child.stderr.on('data', b => { stderr += b; if (stderr.length > 2000000) child.kill('SIGTERM'); });
  try { const code = await settled(child); await writeFile(join(output, label + '.log'), stderr + stdout); if (code !== 0) throw Error(label + ' failed: ' + String(code)); budget(); return stdout; }
  finally { await stop(child); owned.delete(child); }
}
try {
  timer = setTimeout(cancel, timeout * 1000); await persist(); await writeFile(join(output, 'film-spec.json'), JSON.stringify(spec, null, 2) + '\n');
  await writeFile(join(output, 'captions.vtt'), webVTT(cues, spec.duration));
  receipt.runtime = { node: process.version, ffmpeg: (await run(ffmpeg, ['-version'], 'ffmpeg-version')).split('\n')[0], ffprobe: (await run(ffprobe, ['-version'], 'ffprobe-version')).split('\n')[0], ...(sealed ? {} : { python: (await run(python, ['--version'], 'python-version')).trim() }) };
  if (options.audio) {
    await copyFile(resolve(options.audio), join(output, 'audio-input'));
    receipt.audioSha256 = hash(await readFile(join(output, 'audio-input')));
    const input = JSON.parse(await run(ffprobe, ['-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_streams', '-show_format', '-of', 'json', join(output, 'audio-input')], 'audio-probe'));
    if (!input.streams?.some(s => s.codec_type === 'audio') || !/^(wav|mp3|flac|ogg|aac|mov,mp4,m4a,3gp,3g2,mj2)$/.test(input.format?.format_name ?? '')) throw Error('Unsupported local audio container');
    receipt.limits.push('Audio is padded/trimmed to film duration; narration alignment, rights and perceptual loudness require caller review');
  }
  // Streaming starts this before the first frame, so every input must already exist.
  const encodeCommand = rowOrder => {
    const scaleTo = `scale=${width}:${height}:flags=lanczos${options.stream ? ':out_color_matrix=bt709:out_range=tv' : ''},setsar=1`;
    const base = (rowOrder === 'bottom-first' ? 'vflip,' : '') + (samples > 1 ? `tmix=frames=${samples}:weights='${Array(samples).fill(1).join(' ')}',select='eq(mod(n,${samples}),${samples - 1})',setpts=N/(${fpsText(spec)}*TB),${scaleTo}` : scaleTo);
    let graph = `[0:v]${base},format=yuv420p[clean];`, current = 'clean';
    if (bloom) { graph += `[clean]split=2[base][highlight];[highlight]lutyuv=y='max(0,val-180)*3':u=128:v=128,gblur=sigma=6[glow];[base][glow]blend=all_mode=screen:all_opacity=${bloom}[bloom];`; current = 'bloom'; }
    if (grain) { graph += `[${current}]noise=alls=${grain}:allf=t+u:all_seed=42[grain];`; current = 'grain'; }
    graph += `[${current}]format=yuv420p[video]`;
    const framerate = `${rate(spec.fps).numerator*samples}/${rate(spec.fps).denominator}`;
    const frameInput = !options.stream ? ['-framerate', framerate, '-i', join(output, 'frames/frame-%06d.png')] : sealed ? ['-f', 'rawvideo', '-pix_fmt', 'rgba', '-video_size', `${width}x${height}`, '-framerate', framerate, '-i', 'pipe:0'] : ['-f', 'image2pipe', '-c:v', 'png', '-framerate', framerate, '-i', 'pipe:0'];
    const input = ['-hide_banner', '-loglevel', 'error', '-n', '-threads', String(threads), ...frameInput];
    let captionIndex = 1;
    if (options.audio) { input.push('-protocol_whitelist', 'file,pipe', '-i', join(output, 'audio-input')); captionIndex++; }
    input.push('-i', join(output, 'captions.vtt'));
    const audio = options.audio ? ['-map', '1:a:0', '-af', `apad,atrim=duration=${spec.duration},asetpts=PTS-STARTPTS`, '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2'] : ['-an'];
    return [...input, '-filter_complex_threads', String(threads), '-filter_complex', graph, '-map', '[video]', ...audio, '-map', `${captionIndex}:s:0`, '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng', '-c:v', 'libx264', '-preset', 'medium', '-level:v', width * height > 2073600 ? '5.2' : '4.2', '-crf', '20', '-pix_fmt', 'yuv420p', ...(options.stream ? ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv'] : []), '-r', fpsText(spec), '-frames:v', String(frames), '-threads', String(threads), '-t', String(spec.duration), '-movflags', '+faststart', join(output, 'film.mp4')];
  };
  let url, serverLog = '';
  if (sealed) { frameHost = frameServer({ files: sealed.files, frameBytes: width * height * 4, write: chunk => sink.write(chunk) }); url = await frameHost.listen(); receipt.frameSource = { files: Object.fromEntries([...sealed.files].map(([name, file]) => [name, file.sha256])), excluded: sealed.excluded }; }
  else {
  server = spawn(python, [join(pkg, 'serve.py'), '--package', pkg], { stdio: ['ignore', 'pipe', 'pipe'] }); owned.add(server);
  url = await new Promise((res, rej) => { const t = setTimeout(() => rej(Error('Source server startup timeout')), 10000); server.stdout.on('data', b => { serverLog += b; const m = String(b).match(/http:\/\/127\.0\.0\.1:\d+\//); if (m) { clearTimeout(t); res(m[0]); } }); server.stderr.on('data', b => { serverLog += b; }); server.once('error', e => { clearTimeout(t); rej(e); }); server.once('exit', code => { clearTimeout(t); rej(Error('Source server exited ' + code)); }); });
  }
  const { chromium } = await import(options.playwright || process.env.REVIEW_PLAYWRIGHT || 'playwright');
  browser = await chromium.launch({ headless: true, args: sealed ? angleArgs(process.platform) : [], ...(options.chrome || process.env.REVIEW_CHROME ? { executablePath: options.chrome || process.env.REVIEW_CHROME } : {}) });
  receipt.runtime.browser = browser.version();
  const scale = sealed ? 1 : Math.max(width, height) / 1280, viewport = sealed ? { width, height } : { width: Math.round(width / scale), height: Math.round(height / scale) }; receipt.capture = { viewport, deviceScaleFactor: scale, normalization: sealed ? 'Canvas pixels at exact output dimensions' : 'Canonical long edge 1280 logical pixels; final Lanczos normalization to exact output dimensions' };
  const page = await browser.newPage({ viewport, deviceScaleFactor: scale, reducedMotion: options['reduced-motion'] ? 'reduce' : 'no-preference' }); page.setDefaultTimeout(10000);
  const browserErrors = []; page.on('pageerror', e => browserErrors.push(e.message));
  const startEncoder = rowOrder => {
    budget(); const command = encodeCommand(rowOrder);
    receipt.encodeCommand = [ffmpeg, ...command.map(v => typeof v === 'string' ? v.replaceAll(output, '<export>') : v)];
    encoder = spawn(ffmpeg, command, { stdio: ['pipe', 'ignore', 'pipe'] }); owned.add(encoder); sink = encoderSink(encoder);
    encoder.once('error', error => sink.abort(error)); encoder.log = ''; encoder.stderr.on('data', b => { encoder.log = (encoder.log + b).slice(-2000000); });
  };
  if (sealed) {
    await page.goto(url + 'index.html'); await page.waitForFunction(() => window.streamFrame);
    const rowOrder = await page.evaluate(async config => { await window.streamFrame.boot(config); return window.streamFrame.rowOrder; }, { width, height, frames, fps: fpsValue(spec), spec, reducedMotion: !!options['reduced-motion'] });
    if (!['top-first', 'bottom-first'].includes(rowOrder)) throw Error('streamFrame.rowOrder must be top-first or bottom-first');
    const renderer = await page.evaluate(() => { const gl = document.createElement('canvas').getContext('webgl2'), info = gl?.getExtension('WEBGL_debug_renderer_info'); return info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : gl?.getParameter(gl.RENDERER) ?? null; });
    const chart = orientationChart();
    await page.evaluate(async ({ size, pixels, post }) => { const s = window.streamFrame; await s.calibrate({ width: size, height: size, pixels: Uint8Array.from(pixels) }); const r = await fetch(post, { method: 'POST', body: new Blob([s.read()]) }); if (!r.ok) throw Error('Calibration sink ' + r.status); }, { size: chart.width, pixels: [...chart.pixels], post: frameHost.calibrationUrl });
    const orientation = classifyOrientation(rowOrder === 'bottom-first' ? flipRows(frameHost.calibration, width, height) : frameHost.calibration, width, height);
    receipt.stream = { capture: 'canvas-rgba', rowOrder, orientation, renderer, softwareRenderer: softwareRenderer(renderer), framesOnDisk: false };
    if (orientation !== 'upright') throw Error('Full-screen pass orientation is ' + orientation + '; trace each pass with the orientation chart before rendering');
    startEncoder(rowOrder);
  } else {
    await page.goto(url + 'film.html'); await page.locator('body[data-film-ready=true]').waitFor(); await page.evaluate(value => window.motionFilm.setSpec(value), spec);
    if (options.stream) { receipt.stream = { capture: 'dom-png', framesOnDisk: false }; startEncoder('top-first'); }
  }
  const devtools = sealed && await page.context().newCDPSession(page), collectEvery = Math.max(1, Math.floor(256 * 1024 * 1024 / (width * height * 4)));
  receipt.status = 'rendering'; await persist();
  for (let index = 0; index < frames; index++) {
    budget(); const times = subframeTimes(spec, index, samples, shutter);
    for (let j = 0; j < samples; j++) {
      const position = index * samples + j;
      if (sealed) {
        // A Blob body uploads 8 MB about five times faster than a typed array, but Chromium holds each Blob until GC and fails near 1 GB.
        const status = await page.evaluate(async ({ time, outputIndex, sample, post }) => { const s = window.streamFrame; await s.render({ index: outputIndex, time, sample }); return (await fetch(post, { method: 'POST', body: new Blob([s.read()]) })).status; }, { time: times[j], outputIndex: index, sample: j, post: frameHost.frameUrl(position) });
        if (status !== 204 || browserErrors.length) throw frameHost.failure ?? sink.failure ?? Error('Frame capture failed: ' + JSON.stringify({ index, status, browserErrors }));
        if ((position + 1) % collectEvery === 0) await devtools.send('HeapProfiler.collectGarbage');
        continue;
      }
      const observed = await page.evaluate(async ({ time, reduced, outputIndex }) => { const frame = window.motionFilm.seek(time, reduced, outputIndex); await window.motionFilm.ready(); return { frame, layout: window.motionFilm.inspect() }; }, { time: times[j], reduced: !!options['reduced-motion'], outputIndex: index });
      if (observed.layout.fontStatus !== 'loaded' || observed.layout.outside.length || browserErrors.length) throw Error('Frame readiness/layout failed: ' + JSON.stringify({ index, observed, browserErrors }));
      if (options.stream) { const shot = await page.screenshot({ animations: 'disabled' }); await sink.write(shot); receipt.stream.frames = position + 1; receipt.stream.bytes = (receipt.stream.bytes ?? 0) + shot.length; }
      else await page.screenshot({ path: join(output, 'frames', 'frame-' + String(position).padStart(6, '0') + '.png'), animations: 'disabled' });
    }
    if (index % 30 === 0) { const remaining = await statfs(output); if (Number(remaining.bavail * remaining.bsize) < 100 * 1024 * 1024) throw Error('Remaining disk reserve below render budget'); receipt.renderedFrames = index + 1; await persist(); }
  }
  await browser.close(); browser = null; await stop(server); owned.delete(server); await writeFile(join(output, 'source-server.log'), serverLog); await verifySource();
  if (sealed) { receipt.stream.frames = frameHost.accepted; receipt.stream.bytes = frameHost.bytes; if (frameHost.accepted !== frames * samples) throw Error('Accepted frames differ from the film'); }
  receipt.status = 'encoding';
  if (options.stream) { await persist(); if (sink.failure) throw sink.failure; const closed = settled(encoder); sink.finish(); const code = await closed; await writeFile(join(output, 'encode.log'), encoder.log); owned.delete(encoder); if (code !== 0 || sink.failure) throw sink.failure ?? Error('encode failed: ' + String(code)); budget(); }
  else { const command = encodeCommand('top-first'); receipt.encodeCommand = [ffmpeg, ...command.map(v => typeof v === 'string' ? v.replaceAll(output, '<export>') : v)]; await persist(); await run(ffmpeg, command, 'encode'); }
  const probe = JSON.parse(await run(ffprobe, ['-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', join(output, 'film.mp4')], options.stream ? 'stream-probe' : 'probe'));
  const video = probe.streams.find(s => s.codec_type === 'video'), rational = v => { const [n, d] = v.split('/').map(Number); return n / d; };
  if (!video || video.codec_name !== 'h264' || video.pix_fmt !== 'yuv420p' || video.width !== width || video.height !== height || Number(video.nb_read_frames) !== frames || Math.abs(rational(video.avg_frame_rate) - fpsValue(spec)) > .001 || Math.abs(Number(video.duration) - spec.duration) > 1 / fpsValue(spec) || (options.audio && !probe.streams.some(s => s.codec_type === 'audio')) || !probe.streams.some(s => s.codec_type === 'subtitle') || (options.stream && (video.color_space !== 'bt709' || video.color_range !== 'tv'))) throw Error('Encoded stream contract differs');
  if (options.stream) {
    // Stream-only decode receipt: any decoder message fails it, and the decoded count must match the film.
    const report = await run(ffmpeg, ['-v', 'error', '-xerror', '-nostats', '-progress', 'pipe:1', '-threads', String(threads), '-i', join(output, 'film.mp4'), '-map', '0:v:0', '-map', '0:a?', '-f', 'null', '-'], 'stream-decode');
    const decodedFrames = Number(report.match(/^frame=\s*(\d+)$/gm)?.at(-1)?.split('=')[1]), decodeLog = await readFile(join(output, 'stream-decode.log'), 'utf8');
    receipt.stream.probe = { codec: video.codec_name, pixelFormat: video.pix_fmt, colorSpace: video.color_space, colorRange: video.color_range, width: video.width, height: video.height, frames: Number(video.nb_read_frames), avgFrameRate: video.avg_frame_rate, duration: Number(video.duration) };
    receipt.stream.decode = { frames: decodedFrames, decoderMessages: decodeLog.length - report.length };
    if (decodedFrames !== frames || decodeLog !== report) throw Error('Stream decode receipt differs: ' + JSON.stringify(receipt.stream.decode));
    receipt.limits.push('Streaming capture retains no source frames; rerender to inspect a frame before encoding');
  } else await run(ffmpeg, ['-v', 'error', '-threads', String(threads), '-i', join(output, 'film.mp4'), '-map', '0:v:0', '-map', '0:a?', '-f', 'null', '-'], 'decode');
  await run(ffmpeg, ['-v', 'error', '-n', '-i', join(output, 'film.mp4'), '-map', '0:s:0', '-c:s', 'webvtt', join(output, 'captions-decoded.vtt')], 'caption-decode');
  const lines = (await readFile(join(output, 'captions-decoded.vtt'), 'utf8')).replace(/\r/g, '').split('\n'), decoded = [];
  const seconds = value => value.split(':').map(Number).reduce((a, n) => a * 60 + n, 0);
  const unescape = value => value.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
  for (let i = 0; i < lines.length; i++) { if (!lines[i].includes(' --> ')) continue; const [a,b] = lines[i].split(' --> '); const words = []; while (++i < lines.length && lines[i].trim()) words.push(lines[i]); if (words.length) decoded.push({ start: seconds(a), end: seconds(b.split(' ')[0]), text: unescape(words.join('\n')).trim() }); }
  if (decoded.length !== cues.length || decoded.some((c,i) => Math.abs(c.start - cues[i].start) > .0011 || Math.abs(c.end - cues[i].end) > .0011 || c.text !== cues[i].text.replace(/\r/g, '').trim())) throw Error('Encoded captions differ from authored cues');
  receipt.captionsVerified = true;
  await run(ffmpeg, ['-v', 'error', '-n', '-threads', String(threads), '-i', join(output, 'film.mp4'), '-frames:v', '1', join(output, 'poster.png')], 'poster');
  const safeHTML = text => text.replace(/[&<>"']/g, value => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[value]));
  await writeFile(join(output, 'playback.html'), '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + safeHTML(spec.title) + '</title><style>body{margin:0;padding:24px;background:#14231f;color:#f5eedf;font:16px/1.6 system-ui}main{max-width:1100px;margin:auto}video{width:100%;max-height:80vh}a{color:#edc285}</style></head><body><main><h1>' + safeHTML(spec.title) + '</h1><video controls playsinline preload="metadata" poster="poster.png"><source src="film.mp4" type="video/mp4"><track kind="captions" src="captions.vtt" srclang="en" label="Authored captions" default></video><p><a href="film.mp4">MP4</a> · <a href="captions.vtt">Captions</a> · <a href="receipt.json">Verification receipt</a></p><h2>Text track</h2>' + cues.map(c => '<p>' + safeHTML(c.text) + '</p>').join('') + '</main></body></html>');
  const atoms = await topAtoms(join(output, 'film.mp4'));
  if (!(atoms.find(a => a.type === 'moov')?.offset < atoms.find(a => a.type === 'mdat')?.offset)) throw Error('MP4 faststart not established');
  await verifySource(); receipt.status = 'complete'; receipt.renderedFrames = frames; receipt.videoSha256 = await fileHash(join(output, 'film.mp4')); receipt.posterSha256 = hash(await readFile(join(output, 'poster.png'))); receipt.bytes = (await stat(join(output, 'film.mp4'))).size; receipt.faststart = true; receipt.decodePassed = true; receipt.probe = probe; receipt.elapsedSeconds = (Date.now() - started) / 1000; await persist();
  const reread = JSON.parse(await readFile(join(output, 'receipt.json'))); if (reread.videoSha256 !== await fileHash(join(output, 'film.mp4'))) throw Error('Final readback differs');
  console.log(JSON.stringify({ status: 'complete', output, frames, fps: spec.fps, duration: spec.duration, width, height, sourceFingerprint: receipt.sourceFingerprint, videoSha256: receipt.videoSha256 }));
} catch (error) { receipt.status = cancelled ? 'cancelled' : 'failed'; receipt.error = String(error); receipt.elapsedSeconds = (Date.now() - started) / 1000; await persist(); throw error; }
finally { clearTimeout(timer); let browserClosed = true; try { await browser?.close(); } catch { browserClosed = false; } await frameHost?.close(); for (const child of owned) await stop(child); receipt.cleanup = { browserCloseCompleted: browserClosed, directChildren: [...owned].map(c => ({ pid: c.pid ?? null, exitCode: c.exitCode, signal: c.signalCode })), scope: 'Owned direct processes and browser API only; not a host-wide process audit' }; await persist(); process.off('SIGINT', cancel); process.off('SIGTERM', cancel); }
