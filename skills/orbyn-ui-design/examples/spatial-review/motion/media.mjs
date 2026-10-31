// Original non-destructive edit decision validation/planning. No media application dependency.
import { rate, frameTime, audioSample } from './time.mjs';
const plain = v => v && typeof v === 'object' && !Array.isArray(v) && Object.getPrototypeOf(v) === Object.prototype;
const fields = (v, keys) => { if (!plain(v) || Object.keys(v).some(k => !keys.includes(k))) throw Error('Unknown/invalid media record fields'); };
const integer = (v, min = 0, max = 1e6) => { if (!Number.isSafeInteger(v) || v < min || v > max) throw Error('Invalid integer media address'); return v; };
const number = (v, min, max, label) => { if (typeof v !== 'number' || !Number.isFinite(v) || v < min || v > max) throw Error('Invalid ' + label); return v; };
const identity = v => typeof v === 'string' && /^[a-z][\w-]{0,79}$/.test(v);
const path = v => typeof v === 'string' && /^[\w./ -]{1,200}$/.test(v) && !v.startsWith('/') && !v.includes('//') && !v.split('/').some(s => s === '..' || s === '.');
export const rateText = fps => { const r = rate(fps); return `${r.numerator}/${r.denominator}`; };
export function validateEDL(edl) {
  fields(edl, ['version', 'title', 'sourceRevision', 'kind', 'fps', 'durationFrames', 'width', 'height', 'sampleRate', 'assets', 'clips', 'captions', 'loudness']);
  if (edl.version !== 1 || !['video', 'audio'].includes(edl.kind) || typeof edl.title !== 'string' || !edl.title || edl.title.length > 180 || typeof edl.sourceRevision !== 'string' || !edl.sourceRevision || edl.sourceRevision.length > 200) throw Error('Invalid EDL identity');
  rate(edl.fps); integer(edl.durationFrames, 1, 7200); if (frameTime(edl.durationFrames, edl.fps) > 120) throw Error('EDL duration exceeds 120 seconds');
  if (![44100, 48000].includes(edl.sampleRate)) throw Error('Audio clock must be 44100 or 48000 Hz');
  if (edl.kind === 'video') { integer(edl.width, 16, 3840); integer(edl.height, 16, 3840); if (edl.width % 2 || edl.height % 2 || edl.width * edl.height > 8294400) throw Error('Even bounded video dimensions required'); }
  if (!Array.isArray(edl.assets) || !edl.assets.length || edl.assets.length > 32 || !Array.isArray(edl.clips) || !edl.clips.length || edl.clips.length > 64) throw Error('EDL asset/clip budget');
  const ids = new Set(); for (const asset of edl.assets) { fields(asset, ['id', 'path', 'sha256']); if (!identity(asset.id) || ids.has(asset.id) || !path(asset.path) || !/^[\da-f]{64}$/.test(asset.sha256)) throw Error('Invalid/duplicate asset closure'); ids.add(asset.id); }
  let at = 0, hasAudio = null; const clipIds = new Set();
  for (const clip of edl.clips) {
    fields(clip, ['id', 'asset', 'sourceIn', 'sourceOut', 'atFrame', 'durationFrames', 'videoStream', 'audioStream', 'speed', 'mode', 'audioOffsetSamples', 'audioAsset', 'audioSourceIn', 'audioSourceOut', 'audioFill']);
    if (!identity(clip.id) || clipIds.has(clip.id) || !ids.has(clip.asset) || !['copy', 'reencode'].includes(clip.mode)) throw Error('Invalid clip identity/mode'); clipIds.add(clip.id);
    integer(clip.atFrame); integer(clip.durationFrames, 1, 7200); if (clip.atFrame !== at) throw Error('EDL clips must be contiguous and explicitly ordered'); at += clip.durationFrames;
    number(clip.sourceIn, 0, 600, 'source in'); number(clip.sourceOut, clip.sourceIn + 1e-6, 600, 'source out'); const speed = number(clip.speed ?? 1, .25, 4, 'speed');
    if (Math.abs((clip.sourceOut - clip.sourceIn) / speed - frameTime(clip.durationFrames, edl.fps)) > 1e-5) throw Error('Source duration/speed differs from rational output frame duration');
    if (edl.kind === 'video') integer(clip.videoStream, 0, 31); else if (clip.videoStream !== null) throw Error('Audio EDL cannot select video');
    if (clip.audioStream !== null) integer(clip.audioStream, 0, 31);
    if (clip.audioAsset !== undefined && (!ids.has(clip.audioAsset) || clip.audioStream === null)) throw Error('External audio asset must be declared and selected');
    if (clip.audioSourceIn !== undefined) number(clip.audioSourceIn, 0, 600, 'audio source in');
    if (clip.audioSourceOut !== undefined) number(clip.audioSourceOut, (clip.audioSourceIn ?? clip.sourceIn) + 1e-6, 600, 'audio source out');
    if (clip.audioFill !== undefined && !['silence', 'error'].includes(clip.audioFill)) throw Error('Invalid audio fill policy');
    if (edl.kind === 'audio' && clip.audioStream === null) throw Error('Audio EDL needs an audio stream');
    if (hasAudio === null) hasAudio = clip.audioStream !== null; else if (hasAudio !== (clip.audioStream !== null)) throw Error('Mixed missing audio is explicit unsupported input; author silence as an asset');
    integer(clip.audioOffsetSamples ?? 0, -2 * edl.sampleRate, 2 * edl.sampleRate);
  }
  if (at !== edl.durationFrames) throw Error('EDL duration differs from clip placement');
  if (edl.loudness !== undefined) { fields(edl.loudness, ['integrated', 'truePeak', 'range']); if (!hasAudio) throw Error('Loudness requires selected audio'); number(edl.loudness.integrated, -30, -9, 'integrated loudness'); number(edl.loudness.truePeak, -6, -1, 'true peak'); number(edl.loudness.range, 1, 20, 'loudness range'); }
  let end = 0; if (!Array.isArray(edl.captions ?? []) || (edl.captions ?? []).length > 500) throw Error('Caption budget');
  for (const cue of edl.captions ?? []) { fields(cue, ['startFrame', 'endFrame', 'text']); integer(cue.startFrame, end, edl.durationFrames); integer(cue.endFrame, cue.startFrame + 1, edl.durationFrames); if (typeof cue.text !== 'string' || !cue.text.trim() || cue.text.length > 2000 || /\u0000|\r?\n\s*\r?\n|-->/.test(cue.text)) throw Error('Invalid authored caption'); end = cue.endFrame; }
  if (edl.kind === 'audio' && (edl.captions ?? []).length) throw Error('Audio-only caption mux is outside this MP4 profile; retain a transcript separately');
  return edl;
}
const decimal = n => Number(n.toFixed(12)).toString();
const sourceRate = value => { const [n, d] = String(value).split('/').map(Number); return n > 0 && d > 0 ? n / d : NaN; };
function stream(probe, index, type) { const selected = probe.streams.find(s => s.index === index); if (!selected || selected.codec_type !== type) throw Error('Selected source stream is missing or has the wrong type'); return selected; }
function tempo(speed) { if (speed === 1) return ''; const stages = []; while (speed > 2 + 1e-8) { stages.push('atempo=2'); speed /= 2; } while (speed < .5 - 1e-8) { stages.push('atempo=0.5'); speed *= 2; } stages.push('atempo=' + decimal(speed)); return stages.join(','); }

export function planEDL(edl, probes) {
  validateEDL(edl); const fps = rateText(edl.fps), duration = frameTime(edl.durationFrames, edl.fps), expectedAudioSamples = audioSample(edl.durationFrames, edl.fps, edl.sampleRate), filters = [], clips = [], inputs = [], hasAudio = edl.clips[0].audioStream !== null;
  const copy = edl.clips.some(c => c.mode === 'copy');
  if (copy && (edl.clips.length !== 1 || edl.kind !== 'video' || hasAudio || edl.loudness || edl.clips[0].speed !== undefined && edl.clips[0].speed !== 1 || (edl.clips[0].audioOffsetSamples ?? 0) !== 0)) throw Error('Copy profile supports one video-only CFR H264 clip; use explicit reencode for audio, retiming or joins');
  for (const [index, clip] of edl.clips.entries()) {
    const probe = probes[clip.asset]; if (!probe?.streams || !probe.format) throw Error('Missing source probe');
    const videoInput = inputs.length; inputs.push({ asset: clip.asset }); const audioProbe = clip.audioAsset ? probes[clip.audioAsset] : probe; if (!audioProbe?.streams || !audioProbe.format) throw Error('Missing audio asset probe');
    const audioInput = clip.audioAsset && clip.audioAsset !== clip.asset ? inputs.push({ asset: clip.audioAsset }) - 1 : videoInput;
    const video = edl.kind === 'video' ? stream(probe, clip.videoStream, 'video') : null, audio = clip.audioStream !== null ? stream(audioProbe, clip.audioStream, 'audio') : null;
    const sourceDuration = Number(video?.duration ?? audio?.duration ?? probe.format.duration); if (!Number.isFinite(sourceDuration) || clip.sourceOut > sourceDuration + .05) throw Error('Requested source interval is not within the observed media duration');
    const speed = clip.speed ?? 1, seconds = frameTime(clip.durationFrames, edl.fps), samples = audioSample(clip.atFrame + clip.durationFrames, edl.fps, edl.sampleRate) - audioSample(clip.atFrame, edl.fps, edl.sampleRate);
    const firstVideo = Number(video?.start_time ?? probe.format.start_time ?? 0), firstAudio = Number(audio?.start_time ?? audioProbe.format.start_time ?? 0), sourceAudioOffset = audio && video && !clip.audioAsset ? firstAudio - firstVideo : 0;
    const audioIn = clip.audioSourceIn ?? clip.sourceIn, audioOut = clip.audioSourceOut ?? clip.sourceOut, audioDuration = Number(audio?.duration ?? audioProbe.format.duration);
    if (audio && (!Number.isFinite(audioDuration) || audioOut > audioDuration + 2 / edl.sampleRate || (clip.audioFill ?? 'error') === 'error' && Math.abs((audioOut - audioIn) / speed - seconds) > 1 / edl.sampleRate)) throw Error('Selected audio interval is short/unknown; author valid audio bounds and explicit silence fill');
    if (!Number.isFinite(sourceAudioOffset) || Math.abs(sourceAudioOffset) > 30) throw Error('Unbounded/unknown source A/V offset');
    const frames = video ? (probe.framesByStream?.[video.index] ?? []).filter(f => f.media_type === 'video' || !f.media_type).map(f => ({ time: Number(f.best_effort_timestamp_time ?? f.pts_time) - firstVideo, keyframe: Number(f.key_frame) === 1, type: f.pict_type, duration: Number(f.duration_time ?? f.pkt_duration_time ?? 0) })) : [];
    const frameStep = video ? 1 / sourceRate(video.avg_frame_rate) : null;
    const cfrObserved = frames.length > 1 && Number.isFinite(frameStep) && frames.every((f, i) => Number.isFinite(f.time) && (!i || Math.abs(f.time - frames[i - 1].time - frameStep) < 1e-5));
    const observedVideoEnd = video && frames.length ? frames.at(-1).time + (frames.at(-1).duration || frameStep) : null;
    if (video && (!Number.isFinite(observedVideoEnd) || clip.sourceOut > observedVideoEnd + 1e-5)) throw Error('Requested video interval exceeds observed decoded frame coverage');
    if (copy) {
      if (video.codec_name !== 'h264' || Number(video.has_b_frames) !== 0 || !cfrObserved || Math.abs(sourceRate(video.avg_frame_rate) - sourceRate(fps)) > 1e-7 || video.width !== edl.width || video.height !== edl.height) throw Error('Copy profile refuses B-frames, VFR, unknown cadence, mismatched dimensions/rate or non-H264 source; select reencode');
      if (!frames.some(f => f.keyframe && Math.abs(f.time - clip.sourceIn) < 1e-5) || !(frames.some(f => f.keyframe && Math.abs(f.time - clip.sourceOut) < 1e-5) || Math.abs(clip.sourceOut - sourceDuration) < 1e-5)) throw Error('Copy boundaries are not observed keyframes/end-of-stream; select reencode for exact requested frames');
    } else {
      if (video) filters.push(`[${videoInput}:${clip.videoStream}]setpts=PTS-STARTPTS,trim=start=${decimal(clip.sourceIn)}:end=${decimal(clip.sourceOut)},setpts=(PTS-${decimal(clip.sourceIn)}/TB)/${decimal(speed)},fps=${fps}:start_time=0:round=near,scale=${edl.width}:${edl.height}:force_original_aspect_ratio=decrease,pad=${edl.width}:${edl.height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,tpad=stop_mode=clone:stop_duration=1,trim=end_frame=${clip.durationFrames},setpts=N/((${fps})*TB)[v${index}]`);
      if (audio) {
        const shift = clip.audioOffsetSamples ?? 0;
        const offset = shift > 0 ? `,adelay=${shift}S:all=1` : shift < 0 ? `,atrim=start_sample=${-shift},asetpts=PTS-STARTPTS` : '';
        filters.push(`[${audioInput}:${clip.audioStream}]asetpts=PTS-STARTPTS+${decimal(sourceAudioOffset)}/TB,atrim=start=${decimal(audioIn)}:end=${decimal(audioOut)},asetpts=(PTS-${decimal(audioIn)}/TB)/${decimal(speed)},${speed === 1 ? '' : tempo(speed) + ','}aresample=${edl.sampleRate}:async=1:first_pts=0,aformat=sample_fmts=fltp:channel_layouts=stereo${offset},apad,atrim=end_sample=${samples},asetpts=N/SR/TB[a${index}]`);
      }
    }
    clips.push({ id: clip.id, asset: clip.asset, audioAsset: clip.audioAsset ?? clip.asset, mode: clip.mode, sourceIn: clip.sourceIn, sourceOut: clip.sourceOut, audioSourceIn: audioIn, audioSourceOut: audioOut, audioFill: clip.audioFill ?? 'error', atFrame: clip.atFrame, durationFrames: clip.durationFrames, outputSeconds: seconds, expectedAudioSamples: samples, speed, sourceAudioOffsetSeconds: sourceAudioOffset, authoredAudioOffsetSamples: clip.audioOffsetSamples ?? 0, observedCadence: video ? cfrObserved ? 'constant in observed frames' : 'variable/unknown; explicitly resampled' : 'audio only', observedFrames: frames.length, selectedVideoStream: video?.index ?? null, selectedAudioStream: audio?.index ?? null, copyBoundaryVerified: copy });
  }
  if (!copy) {
    const inputs = edl.clips.map((_, i) => `${edl.kind === 'video' ? `[v${i}]` : ''}${hasAudio ? `[a${i}]` : ''}`).join('');
    filters.push(`${inputs}concat=n=${edl.clips.length}:v=${edl.kind === 'video' ? 1 : 0}:a=${hasAudio ? 1 : 0}${edl.kind === 'video' ? '[video]' : ''}${hasAudio ? '[audio]' : ''}`);
  }
  return { version: 1, mode: copy ? 'copy' : 'reencode', kind: edl.kind, fps, duration, outputFrames: edl.durationFrames, expectedAudioSamples, hasAudio, inputs, filterGraph: filters.join(';'), clips, policy: { sourceTime: 'Seconds relative to selected video first PTS, or selected audio first PTS for audio-only; explicit audioAsset has its own audio clock', video: copy ? 'Observed CFR keyframe boundaries, packets copied without reencoding' : 'Resample source cadence to project rational FPS; intentional duplication/culling may occur for VFR or speed changes', audio: 'Global rational frame boundaries map to integer sample addresses; unity speed bypasses time-stretching; non-unity WSOLA retiming may move transients and final padding is explicit; AAC tail reported separately', captions: 'Authored frame addresses; encoded subtitle timestamps checked within 1.1 ms' } };
}

const timestamp = seconds => { const ms = Math.round(seconds * 1000), h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, s = Math.floor(ms / 1000) % 60; return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms % 1000).padStart(3, '0')}`; };
const escape = text => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
export function captionVTT(edl) { validateEDL(edl); return 'WEBVTT\n\n' + (edl.captions ?? []).map((cue, i) => `${i + 1}\n${timestamp(frameTime(cue.startFrame, edl.fps))} --> ${timestamp(frameTime(cue.endFrame, edl.fps))}\n${escape(cue.text.trim())}\n`).join('\n'); }
export function decodeVTT(text) {
  const seconds = value => value.split(':').map(Number).reduce((a, x) => a * 60 + x, 0), result = [], lines = text.replaceAll('\r', '').split('\n');
  for (let i = 0; i < lines.length; i++) if (lines[i].includes(' --> ')) { const [a, b] = lines[i].split(' --> '), words = []; while (++i < lines.length && lines[i].trim()) words.push(lines[i]); result.push({ start: seconds(a), end: seconds(b.split(' ')[0]), text: words.join('\n').replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&amp;', '&') }); }
  return result;
}
