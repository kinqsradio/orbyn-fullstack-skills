// Frame difference. Colour distance is the "redmean" weighted RGB formula, normalised so black
// against white is 1. With tolerance on, a pixel that has a close match within one pixel in both
// images is treated as anti-aliasing or a sub-pixel shift rather than a real difference.
import { createImage } from './png.mjs';

const MAX_DISTANCE = 9 * 255 * 255;

function distance(a, i, b, j) {
  // Composite over white so a transparent pixel compares as what the viewer sees.
  const alphaA = a[i + 3] / 255;
  const alphaB = b[j + 3] / 255;
  const r1 = 255 + (a[i] - 255) * alphaA;
  const g1 = 255 + (a[i + 1] - 255) * alphaA;
  const b1 = 255 + (a[i + 2] - 255) * alphaA;
  const r2 = 255 + (b[j] - 255) * alphaB;
  const g2 = 255 + (b[j + 1] - 255) * alphaB;
  const b2 = 255 + (b[j + 2] - 255) * alphaB;
  const mean = (r1 + r2) / 2;
  const dr = r1 - r2;
  const dg = g1 - g2;
  const db = b1 - b2;
  return (2 + mean / 256) * dr * dr + 4 * dg * dg + (2 + (255 - mean) / 256) * db * db;
}

function hasNearMatch(from, to, x, y, width, height, limit) {
  const i = (y * width + x) * 4;
  for (let dy = -1; dy <= 1; dy++) {
    const ny = y + dy;
    if (ny < 0 || ny >= height) continue;
    for (let dx = -1; dx <= 1; dx++) {
      const nx = x + dx;
      if (nx < 0 || nx >= width || (dx === 0 && dy === 0)) continue;
      if (distance(from, i, to, (ny * width + nx) * 4) <= limit) return true;
    }
  }
  return false;
}

/** Returns { count, ratio, image? }. threshold is 0..1; 0.1 is about 25 grey levels. */
export function diffImages(a, b, { threshold = 0.1, tolerance = true, image = false } = {}) {
  if (a.width !== b.width || a.height !== b.height) {
    throw new Error(`Frames differ in size: ${a.width}x${a.height} and ${b.width}x${b.height}`);
  }
  const { width, height } = a;
  const limit = threshold * threshold * MAX_DISTANCE;
  const output = image ? createImage(width, height) : null;
  let count = 0;
  for (let y = 0, i = 0; y < height; y++) {
    for (let x = 0; x < width; x++, i += 4) {
      const differs = distance(a.data, i, b.data, i) > limit
        && !(tolerance && hasNearMatch(a.data, b.data, x, y, width, height, limit) && hasNearMatch(b.data, a.data, x, y, width, height, limit));
      if (differs) count++;
      if (output) {
        const grey = differs ? 0 : Math.round(220 + (a.data[i] + a.data[i + 1] + a.data[i + 2]) / 3 / 255 * 35);
        output.data[i] = differs ? 255 : grey;
        output.data[i + 1] = differs ? 0 : grey;
        output.data[i + 2] = differs ? 0 : grey;
        output.data[i + 3] = 255;
      }
    }
  }
  return { count, ratio: count / (width * height), image: output ?? undefined };
}
