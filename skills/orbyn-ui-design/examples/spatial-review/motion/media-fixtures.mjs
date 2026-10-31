#!/usr/bin/env node
// Original tiny coded-frame and tone fixtures. Generated media stays in a new ignored output.
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
const args = process.argv.slice(2);
if (args.length !== 4 || args[0] !== '--out' || args[2] !== '--ffmpeg') throw Error('Use --out NEW_DIRECTORY --ffmpeg EXISTING_BINARY');
const root = resolve(args[1]), ffmpeg = resolve(args[3]); await mkdir(root); await mkdir(join(root, 'frames'));
function run(extra, name) { const result = spawnSync(ffmpeg, ['-hide_banner', '-nostdin', '-n', '-v', 'error', '-threads', '2', ...extra], { encoding: 'utf8', timeout: 60000, maxBuffer: 2 * 1024 * 1024 }); if (result.status !== 0) throw Error(name + ': ' + (result.stderr || result.error)); }
const width = 160, height = 96;
for (let index = 0; index < 60; index++) {
  const pixels = Buffer.alloc(width * height * 3);
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) { const offset = (y * width + x) * 3; pixels[offset] = 24 + index * 2; pixels[offset + 1] = 60 + index; pixels[offset + 2] = 100; }
  for (let bit = 0; bit < 8; bit++) for (let y = 8; y < 32; y++) for (let x = 8 + bit * 18; x < 20 + bit * 18; x++) { const offset = (y * width + x) * 3, value = index & 1 << bit ? 240 : 16; pixels.fill(value, offset, offset + 3); }
  await writeFile(join(root, 'frames', String(index).padStart(3, '0') + '.ppm'), Buffer.concat([Buffer.from(`P6\n${width} ${height}\n255\n`), pixels]), { flag: 'wx' });
}
for (const frequency of [440, 880]) { const count = 96000, buffer = Buffer.alloc(44 + count * 2); buffer.write('RIFF', 0); buffer.writeUInt32LE(buffer.length - 8, 4); buffer.write('WAVEfmt ', 8); buffer.writeUInt32LE(16, 16); buffer.writeUInt16LE(1, 20); buffer.writeUInt16LE(1, 22); buffer.writeUInt32LE(48000, 24); buffer.writeUInt32LE(96000, 28); buffer.writeUInt16LE(2, 32); buffer.writeUInt16LE(16, 34); buffer.write('data', 36); buffer.writeUInt32LE(count * 2, 40); for (let n = 0; n < count; n++) buffer.writeInt16LE(Math.round(Math.sin(2 * Math.PI * frequency * n / 48000) * 4000), 44 + n * 2); await writeFile(join(root, `tone-${frequency}.wav`), buffer, { flag: 'wx' }); }
// Sparse Gaussian impulses expose unintended no-op time-stretch latency that a continuous tone hides.
{ const count = 96000, buffer = Buffer.alloc(44 + count * 2); buffer.write('RIFF', 0); buffer.writeUInt32LE(buffer.length - 8, 4); buffer.write('WAVEfmt ', 8); buffer.writeUInt32LE(16, 16); buffer.writeUInt16LE(1, 20); buffer.writeUInt16LE(1, 22); buffer.writeUInt32LE(48000, 24); buffer.writeUInt32LE(96000, 28); buffer.writeUInt16LE(2, 32); buffer.writeUInt16LE(16, 34); buffer.write('data', 36); buffer.writeUInt32LE(count * 2, 40); for (let n = 0; n < count; n++) { const value = [24000, 72000].reduce((sum, center) => sum + .65 * Math.exp(-Math.pow((n - center) / 12, 2)), 0); buffer.writeInt16LE(Math.round(value * 32767), 44 + n * 2); } await writeFile(join(root, 'impulses.wav'), buffer, { flag: 'wx' }); }
const source = ['-framerate', '30', '-i', join(root, 'frames', '%03d.ppm')], audios = ['-i', join(root, 'tone-440.wav'), '-i', join(root, 'tone-880.wav')];
for (const [file, bframes] of [['cfr-ip.mp4', 0], ['cfr-bframes.mp4', 2]]) run([...source, ...audios, '-map', '0:v:0', '-map', '1:a:0', '-map', '2:a:0', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-pix_fmt', 'yuv420p', '-g', '15', '-keyint_min', '15', '-sc_threshold', '0', '-bf', String(bframes), '-c:a', 'aac', '-b:a', '128k', '-t', '2', join(root, file)], file);
run([...source, ...audios, '-map', '0:v:0', '-map', '1:a:0', '-map', '2:a:0', '-c:v', 'ffv1', '-pix_fmt', 'yuv444p', '-c:a', 'pcm_s16le', join(root, 'coded-lossless.mkv')], 'lossless coded frames');
run([...source, '-vf', "setpts='if(lt(N,30),N/(30*TB),(1+(N-30)/15)/TB)'", '-fps_mode', 'vfr', '-c:v', 'ffv1', '-pix_fmt', 'yuv444p', join(root, 'vfr.mkv')], 'VFR fixture');
const files = ['cfr-ip.mp4', 'cfr-bframes.mp4', 'coded-lossless.mkv', 'vfr.mkv', 'tone-440.wav', 'tone-880.wav', 'impulses.wav'], record = { version: 1, author: 'Original Orbyn code-authored fixture', width, height, fps: 30, frames: 60, codedFramePolicy: 'Eight bright/dark blocks at y20, x14+18*bit encode frame ordinal0..59', audio: 'Original synthetic sine tones, not narration/music qualification', assets: {} };
for (const file of files) { const bytes = await readFile(join(root, file)); record.assets[file] = { sha256: createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length }; }
await writeFile(join(root, 'fixtures.json'), JSON.stringify(record, null, 2) + '\n', { flag: 'wx' }); console.log(join(root, 'fixtures.json'));
