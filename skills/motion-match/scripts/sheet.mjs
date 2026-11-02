// Lay frames out on labelled contact sheets so a whole motion can be read in one image.
//   filmstrip: one folder of frames, with the frame number and time under each
//   compare:   reference, ours and diff side by side, one row per frame
// Drawn with this skill's own PNG code and bitmap font, so it needs no browser. Reads the frame
// folders. Writes only inside --out.
import { existsSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { EXIT, UsageError, assertIgnored, child, frameMeta, isMain, listFrames, pad, parseArgs, pathInside, prepareOutput, readJson, requireOptions, rightsOf, runCli } from './lib.mjs';
import { createImage, encodePng, readPng } from './png.mjs';

const HELP = `
sheet.mjs: labelled contact sheets.

  node sheet.mjs filmstrip --frames <dir> --out <dir> [--cols 6] [--per-sheet 24] [--width 240] [--every K] [--from I --to J]
  node sheet.mjs compare --ref <dir> --clone <dir> --out <dir> [--diff <dir>] [--per-sheet 8] [--width 420] [--every K] [--offset K]

  --fps N      used for time labels, default from frames.json, else 25
  --every K    show every K-th frame, default 1
  --from/--to  frame index range, 0-based, inclusive
  --offset K   compare: our frame = reference frame + K
  --root DIR   folder --out must stay inside, default the working directory
  --replace    replace earlier sheets in --out

Writes sheet-01.png or compare-01.png and so on inside --out, and prints their paths. Read every
sheet. Sheets made from third-party frames need an output folder Git ignores.
`;

// 5x7 bitmap font, one number per row, low five bits.
const FONT = {
  '0': [14, 17, 19, 21, 25, 17, 14], '1': [4, 12, 4, 4, 4, 4, 14], '2': [14, 17, 1, 2, 4, 8, 31], '3': [31, 2, 4, 2, 1, 17, 14],
  '4': [2, 6, 10, 18, 31, 2, 2], '5': [31, 16, 30, 1, 1, 17, 14], '6': [6, 8, 16, 30, 17, 17, 14], '7': [31, 1, 2, 4, 8, 8, 8],
  '8': [14, 17, 17, 14, 17, 17, 14], '9': [14, 17, 17, 15, 1, 2, 12],
  A: [14, 17, 17, 31, 17, 17, 17], B: [30, 17, 17, 30, 17, 17, 30], C: [14, 17, 16, 16, 16, 17, 14], D: [30, 17, 17, 17, 17, 17, 30],
  E: [31, 16, 16, 30, 16, 16, 31], F: [31, 16, 16, 30, 16, 16, 16], G: [14, 17, 16, 23, 17, 17, 15], H: [17, 17, 17, 31, 17, 17, 17],
  I: [14, 4, 4, 4, 4, 4, 14], J: [7, 2, 2, 2, 2, 18, 12], K: [17, 18, 20, 24, 20, 18, 17], L: [16, 16, 16, 16, 16, 16, 31],
  M: [17, 27, 21, 21, 17, 17, 17], N: [17, 25, 21, 19, 17, 17, 17], O: [14, 17, 17, 17, 17, 17, 14], P: [30, 17, 17, 30, 16, 16, 16],
  Q: [14, 17, 17, 17, 21, 18, 13], R: [30, 17, 17, 30, 20, 18, 17], S: [15, 16, 16, 14, 1, 1, 30], T: [31, 4, 4, 4, 4, 4, 4],
  U: [17, 17, 17, 17, 17, 17, 14], V: [17, 17, 17, 17, 17, 10, 4], W: [17, 17, 17, 21, 21, 27, 17], X: [17, 17, 10, 4, 10, 17, 17],
  Y: [17, 17, 10, 4, 4, 4, 4], Z: [31, 1, 2, 4, 8, 16, 31],
  '#': [10, 10, 31, 10, 31, 10, 10], '.': [0, 0, 0, 0, 0, 12, 12], '%': [25, 25, 2, 4, 8, 19, 19], '-': [0, 0, 0, 31, 0, 0, 0],
  '+': [0, 4, 4, 31, 4, 4, 0], ':': [0, 12, 12, 0, 12, 12, 0], '/': [1, 1, 2, 4, 8, 16, 16], '(': [2, 4, 8, 8, 8, 4, 2], ')': [8, 4, 2, 2, 2, 4, 8],
  '=': [0, 0, 31, 0, 31, 0, 0], ' ': [0, 0, 0, 0, 0, 0, 0],
};
const GLYPH = { width: 5, height: 7, advance: 6 };
const INK = { background: [17, 17, 17], text: [221, 221, 221], accent: [150, 190, 235], edge: [64, 64, 64], missing: [40, 0, 0] };
const TEXT_SCALE = 2;
const CAPTION = GLYPH.height * TEXT_SCALE + 8;

export function textWidth(text, scale = TEXT_SCALE) { return text.length * GLYPH.advance * scale; }

function fill(image, x, y, width, height, [r, g, b]) {
  for (let row = Math.max(0, y); row < Math.min(image.height, y + height); row++) {
    for (let col = Math.max(0, x); col < Math.min(image.width, x + width); col++) {
      const i = (row * image.width + col) * 4;
      image.data[i] = r; image.data[i + 1] = g; image.data[i + 2] = b; image.data[i + 3] = 255;
    }
  }
}

export function drawText(image, text, x, y, colour = INK.text, scale = TEXT_SCALE) {
  let cursor = x;
  for (const character of String(text).toUpperCase()) {
    const rows = FONT[character] ?? FONT['-'];
    rows.forEach((bits, row) => {
      for (let col = 0; col < GLYPH.width; col++) {
        if (bits & (1 << (GLYPH.width - 1 - col))) fill(image, cursor + col * scale, y + row * scale, scale, scale, colour);
      }
    });
    cursor += GLYPH.advance * scale;
  }
}

/** Box filter, composited over black so a transparent frame still reads. */
export function scaleImage(source, width) {
  const height = Math.max(1, Math.round((source.height * width) / source.width));
  const out = createImage(width, height);
  for (let y = 0; y < height; y++) {
    const y0 = Math.floor((y * source.height) / height);
    const y1 = Math.max(y0 + 1, Math.floor(((y + 1) * source.height) / height));
    for (let x = 0; x < width; x++) {
      const x0 = Math.floor((x * source.width) / width);
      const x1 = Math.max(x0 + 1, Math.floor(((x + 1) * source.width) / width));
      let r = 0; let g = 0; let b = 0; let n = 0;
      for (let sy = y0; sy < y1; sy++) {
        for (let sx = x0; sx < x1; sx++) {
          const i = (sy * source.width + sx) * 4;
          const alpha = source.data[i + 3] / 255;
          r += source.data[i] * alpha; g += source.data[i + 1] * alpha; b += source.data[i + 2] * alpha; n++;
        }
      }
      const to = (y * width + x) * 4;
      out.data[to] = r / n; out.data[to + 1] = g / n; out.data[to + 2] = b / n; out.data[to + 3] = 255;
    }
  }
  return out;
}

function blit(target, image, x, y) {
  fill(target, x - 1, y - 1, image.width + 2, image.height + 2, INK.edge);
  for (let row = 0; row < image.height; row++) {
    const from = row * image.width * 4;
    target.data.set(image.data.subarray(from, from + image.width * 4), ((y + row) * target.width + x) * 4);
  }
}

const GAP = 12;
const HEADER = CAPTION + GAP;
const label = (index, fps) => `#${index}  ${(index / fps).toFixed(2)}S`;

/** cells: [{ image, caption }]. One grid sheet. */
export function layoutGrid(title, cells, { cols, width }) {
  const thumbs = cells.map((cell) => ({ ...cell, thumb: cell.image ? scaleImage(cell.image, width) : null }));
  const cellHeight = Math.max(...thumbs.map((cell) => cell.thumb?.height ?? 0)) + CAPTION;
  const rows = Math.ceil(thumbs.length / cols);
  const sheetWidth = Math.max(GAP * 2 + cols * width + (cols - 1) * GAP, textWidth(title) + GAP * 2);
  const sheet = createImage(sheetWidth, HEADER + GAP + rows * (cellHeight + GAP));
  fill(sheet, 0, 0, sheet.width, sheet.height, INK.background);
  drawText(sheet, title, GAP, GAP);
  thumbs.forEach((cell, index) => {
    const x = GAP + (index % cols) * (width + GAP);
    const y = HEADER + Math.floor(index / cols) * (cellHeight + GAP);
    if (cell.thumb) blit(sheet, cell.thumb, x, y);
    drawText(sheet, cell.caption, x, y + cellHeight - CAPTION + 4, INK.accent);
  });
  return sheet;
}

/** rows: [{ caption, images: [image|null, ...] }]. One comparison sheet. */
export function layoutRows(title, headings, rows, { width }) {
  const columns = headings.length;
  const scaled = rows.map((row) => ({ ...row, thumbs: row.images.map((image) => (image ? scaleImage(image, width) : null)) }));
  const rowHeight = Math.max(...scaled.flatMap((row) => row.thumbs.map((thumb) => thumb?.height ?? 0))) + CAPTION;
  const sheetWidth = Math.max(GAP * 2 + columns * width + (columns - 1) * GAP, textWidth(title) + GAP * 2);
  const sheet = createImage(sheetWidth, HEADER + CAPTION + GAP + rows.length * (rowHeight + GAP));
  fill(sheet, 0, 0, sheet.width, sheet.height, INK.background);
  drawText(sheet, title, GAP, GAP);
  headings.forEach((heading, column) => drawText(sheet, heading, GAP + column * (width + GAP), HEADER, INK.accent));
  scaled.forEach((row, index) => {
    const y = HEADER + CAPTION + index * (rowHeight + GAP);
    drawText(sheet, row.caption, GAP, y + 2, INK.accent);
    row.thumbs.forEach((thumb, column) => {
      const x = GAP + column * (width + GAP);
      if (thumb) blit(sheet, thumb, x, y + CAPTION);
      else fill(sheet, x, y + CAPTION, width, rowHeight - CAPTION, INK.missing);
    });
  });
  return sheet;
}

const fpsOf = (folder, flag) => flag ?? (Number(frameMeta(folder)?.fps) || 25);

function chunks(items, size) {
  const out = [];
  for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size));
  return out;
}

function filmstrip(a) {
  const folder = resolve(a.frames);
  const fps = fpsOf(folder, a.fps);
  const files = listFrames(folder);
  const from = a.from ?? 0;
  const to = a.to ?? files.length - 1;
  const every = a.every ?? 1;
  const picked = files.map((path, index) => ({ path, index })).filter(({ index }) => index >= from && index <= to && (index - from) % every === 0);
  if (!picked.length) throw new UsageError('No frames selected');
  const title = basename(folder) === 'frames' ? basename(dirname(folder)) : basename(folder);
  return chunks(picked, a['per-sheet'] ?? 24).map((chunk, sheet) => ({
    name: `sheet-${pad(sheet + 1, 2)}.png`,
    image: layoutGrid(`${title}  FRAMES ${chunk[0].index}-${chunk[chunk.length - 1].index}  ${fps} FPS`,
      chunk.map(({ path, index }) => ({ image: readPng(path), caption: label(index, fps) })), { cols: a.cols ?? 6, width: a.width ?? 240 }),
  }));
}

function compareSheets(a) {
  const refDir = resolve(a.ref);
  const cloneDir = resolve(a.clone);
  const diffDir = a.diff ? resolve(a.diff) : undefined;
  const fps = fpsOf(refDir, a.fps);
  const offset = a.offset ?? 0;
  const ref = listFrames(refDir);
  const clone = listFrames(cloneDir);
  const reportPath = diffDir && join(diffDir, '..', 'report.json');
  const report = reportPath && existsSync(reportPath) ? readJson(reportPath) : null;
  const hasDiffs = !!diffDir && listFrames(diffDir).length > 0;
  const from = a.from ?? Math.max(0, -offset);
  const to = Math.min(a.to ?? ref.length - 1, ref.length - 1);
  const picked = [];
  for (let i = from; i <= to; i += a.every ?? 1) picked.push(i);
  if (!picked.length) throw new UsageError('No frames selected');
  const headings = hasDiffs ? ['REFERENCE', 'OURS', 'DIFF RED'] : ['REFERENCE', 'OURS'];
  return chunks(picked, a['per-sheet'] ?? 8).map((chunk, sheet) => ({
    name: `compare-${pad(sheet + 1, 2)}.png`,
    image: layoutRows(`REFERENCE VS OURS  ${fps} FPS  OFFSET ${offset}`, headings, chunk.map((i) => {
      const mismatch = report?.frameDetails?.[i]?.mismatch;
      const diffPath = hasDiffs ? join(diffDir, `${pad(i)}.png`) : null;
      return {
        caption: `${label(i, fps)}${mismatch == null ? '' : `  MISMATCH ${(mismatch * 100).toFixed(1)}%`}`,
        images: [readPng(ref[i]), clone[i + offset] ? readPng(clone[i + offset]) : null, ...(hasDiffs ? [diffPath && existsSync(diffPath) ? readPng(diffPath) : null] : [])],
      };
    }), { width: a.width ?? 420 }),
  }));
}

function main() {
  const size = { type: 'number', min: 1, integer: true };
  const index = { type: 'number', min: 0, integer: true };
  const a = parseArgs(process.argv.slice(2), {
    frames: 'string', ref: 'string', clone: 'string', diff: 'string', out: 'string', root: 'string', replace: 'flag', fps: { type: 'number', min: 0.1 },
    cols: size, 'per-sheet': size, width: { type: 'number', min: 16, max: 4096, integer: true }, every: size, from: index, to: index, offset: { type: 'number', integer: true },
  }, { positionals: 1 });
  if (a.help) { console.log(HELP.trim()); return EXIT.ok; }
  const mode = a._[0];
  if (mode !== 'filmstrip' && mode !== 'compare') throw new UsageError('Choose filmstrip or compare (see --help)');
  requireOptions(a, mode === 'filmstrip' ? ['frames', 'out'] : ['ref', 'clone', 'out']);
  const out = pathInside(a.out, a.root ?? '.', 'Output');
  const sources = mode === 'filmstrip' ? [a.frames] : [a.ref, a.clone];
  if (sources.some((folder) => rightsOf(resolve(folder)) === 'third-party')) assertIgnored(out);
  const sheets = mode === 'filmstrip' ? filmstrip(a) : compareSheets(a);
  prepareOutput(out, { marker: mode === 'filmstrip' ? 'sheet-01.png' : 'compare-01.png', replace: !!a.replace });
  for (const sheet of sheets) {
    const path = child(out, sheet.name);
    writeFileSync(path, encodePng(sheet.image));
    console.log(path);
  }
  return EXIT.ok;
}

if (isMain(import.meta.url)) runCli(main);
