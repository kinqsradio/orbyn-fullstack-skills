// Shared test helpers: synthetic frames, curves and CLI runs. No browser, no network.
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createImage, encodePng } from '../scripts/png.mjs';

export const SCRIPTS = join(dirname(fileURLToPath(import.meta.url)), '..', 'scripts');

export function workspace(t) {
  const folder = realpathSync(mkdtempSync(join(tmpdir(), 'motion-match-')));
  t.after(() => rmSync(folder, { recursive: true, force: true }));
  return folder;
}

export function runScript(script, args, cwd) {
  return spawnSync(process.execPath, [join(SCRIPTS, script), ...args], { cwd, encoding: 'utf8', env: { ...process.env, PLAYWRIGHT_CORE: '', CHROME_PATH: '' } });
}

export function git(cwd, ...args) {
  const result = spawnSync('git', ['-C', cwd, ...args], { encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr);
}

export function solid(width, height, [r, g, b, a = 255]) {
  const image = createImage(width, height);
  for (let i = 0; i < image.data.length; i += 4) { image.data[i] = r; image.data[i + 1] = g; image.data[i + 2] = b; image.data[i + 3] = a; }
  return image;
}

export function paintRect(image, x, y, width, height, [r, g, b]) {
  for (let row = Math.max(0, y); row < Math.min(image.height, y + height); row++) {
    for (let col = Math.max(0, x); col < Math.min(image.width, x + width); col++) {
      const i = (row * image.width + col) * 4;
      image.data[i] = r; image.data[i + 1] = g; image.data[i + 2] = b; image.data[i + 3] = 255;
    }
  }
}

/** A block that slides across the frame from frame `start` to `end`, at rest otherwise. */
export function slidingFrame(index, { start = 8, end = 24, width = 64, height = 32 } = {}) {
  const image = solid(width, height, [16, 20, 30]);
  const progress = Math.min(1, Math.max(0, (index - start) / (end - start)));
  paintRect(image, Math.round(progress * (width - 12)), 10, 12, 12, [240, 240, 240]);
  return image;
}

export function writeFrames(folder, count, make, meta) {
  mkdirSync(folder, { recursive: true });
  for (let i = 0; i < count; i++) writeFileSync(join(folder, `${String(i + 1).padStart(4, '0')}.png`), encodePng(make(i)));
  if (meta) writeFileSync(join(folder, 'frames.json'), JSON.stringify(meta));
}

/** rAF-rate samples of a 0..1 curve from `from` to `to`. */
export function sampleCurve(curve, { delay = 200, duration = 700, from = 0, to = 100, step = 1000 / 60, length = 1600 } = {}) {
  const series = [];
  for (let t = 0; t <= length; t += step) series.push([t, from + (to - from) * curve(Math.min(1, Math.max(0, (t - delay) / duration)))]);
  return series;
}
