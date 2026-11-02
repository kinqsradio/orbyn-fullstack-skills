import assert from 'node:assert/strict';
import { readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';
import { encodePng, readPng } from '../scripts/png.mjs';
import { drawText, layoutGrid, scaleImage, textWidth } from '../scripts/sheet.mjs';
import { git, paintRect, runScript, slidingFrame, solid, workspace, writeFrames } from './helpers.mjs';

const OWN = { fps: 25, rights: 'own' };
const count = (image, [r, g, b]) => {
  let total = 0;
  for (let i = 0; i < image.data.length; i += 4) if (image.data[i] === r && image.data[i + 1] === g && image.data[i + 2] === b) total++;
  return total;
};
const ACCENT = [150, 190, 235];

test('filmstrip writes one sheet per page, with captions, and prints each path', (t) => {
  const root = workspace(t);
  writeFrames(join(root, 'frames'), 10, (i) => slidingFrame(i), OWN);
  const run = runScript('sheet.mjs', ['filmstrip', '--frames', 'frames', '--out', 'sheets', '--per-sheet', '4', '--cols', '2', '--width', '64'], root);
  assert.equal(run.status, 0, run.stderr);
  assert.deepEqual(readdirSync(join(root, 'sheets')).sort(), ['sheet-01.png', 'sheet-02.png', 'sheet-03.png']);
  assert.equal(run.stdout.trim().split('\n').length, 3);
  const sheet = readPng(join(root, 'sheets', 'sheet-01.png'));
  assert.ok(sheet.width >= 2 * 64 + 12);
  assert.ok(count(sheet, ACCENT) > 100, 'captions are drawn');
  assert.ok(count(sheet, [240, 240, 240]) > 0, 'frame content is drawn');
});

test('--every and --from pick the frames shown', (t) => {
  const root = workspace(t);
  writeFrames(join(root, 'frames'), 10, (i) => slidingFrame(i), OWN);
  assert.equal(runScript('sheet.mjs', ['filmstrip', '--frames', 'frames', '--out', 'all', '--per-sheet', '1'], root).status, 0);
  assert.equal(readdirSync(join(root, 'all')).length, 10);
  assert.equal(runScript('sheet.mjs', ['filmstrip', '--frames', 'frames', '--out', 'some', '--per-sheet', '1', '--every', '3', '--from', '2'], root).status, 0);
  assert.equal(readdirSync(join(root, 'some')).length, 3);
  assert.equal(runScript('sheet.mjs', ['filmstrip', '--frames', 'frames', '--out', 'none', '--from', '50'], root).status, 2);
});

test('compare lays out reference, ours and diff, one row per frame', (t) => {
  const root = workspace(t);
  writeFrames(join(root, 'r'), 4, (i) => slidingFrame(i, { start: 0, end: 3 }), OWN);
  writeFrames(join(root, 'o'), 4, (i) => slidingFrame(i, { start: 0, end: 3 }), OWN);
  writeFrames(join(root, 'cmp', 'diff'), 4, () => solid(64, 32, [255, 0, 0]));
  writeFileSync(join(root, 'cmp', 'report.json'), JSON.stringify({ frameDetails: [{ mismatch: 0.5 }] }));
  const run = runScript('sheet.mjs', ['compare', '--ref', 'r', '--clone', 'o', '--diff', 'cmp/diff', '--out', 'sheets', '--width', '240'], root);
  assert.equal(run.status, 0, run.stderr);
  const sheet = readPng(join(root, 'sheets', 'compare-01.png'));
  assert.ok(count(sheet, [255, 0, 0]) > 0, 'the diff column is drawn');
  assert.ok(sheet.width >= 3 * 240 + 2 * 12, 'three columns');
  const two = runScript('sheet.mjs', ['compare', '--ref', 'r', '--clone', 'o', '--out', 'two', '--width', '240'], root);
  assert.equal(two.status, 0, two.stderr);
  assert.ok(readPng(join(root, 'two', 'compare-01.png')).width < sheet.width, 'no diff folder, two columns');
});

test('an unknown mode and missing options are usage errors', (t) => {
  const root = workspace(t);
  assert.equal(runScript('sheet.mjs', ['poster', '--out', 'x'], root).status, 2);
  assert.equal(runScript('sheet.mjs', ['filmstrip', '--out', 'x'], root).status, 2);
});

test('sheets from third-party or unlabelled frames must land in an ignored folder', (t) => {
  const root = workspace(t);
  git(root, 'init', '-q');
  writeFileSync(join(root, '.gitignore'), 'private/\n');
  writeFrames(join(root, 'private', 'frames'), 2, (i) => slidingFrame(i), { fps: 25, rights: 'third-party' });
  writeFrames(join(root, 'private', 'plain'), 2, (i) => slidingFrame(i));
  const open = runScript('sheet.mjs', ['filmstrip', '--frames', 'private/frames', '--out', 'sheets'], root);
  assert.equal(open.status, 3);
  assert.match(open.stderr, /not ignored by Git/);
  assert.equal(runScript('sheet.mjs', ['filmstrip', '--frames', 'private/plain', '--out', 'sheets'], root).status, 3);
  assert.equal(runScript('sheet.mjs', ['filmstrip', '--frames', 'private/frames', '--out', 'private/sheets'], root).status, 0);
});

test('text is drawn from the font and its width matches textWidth', () => {
  const image = solid(200, 20, [0, 0, 0]);
  drawText(image, '#12 0.48s', 0, 0, [255, 255, 255], 2);
  const lit = [];
  for (let x = 0; x < 200; x++) for (let y = 0; y < 20; y++) if (image.data[(y * 200 + x) * 4]) lit.push(x);
  assert.ok(lit.length > 80);
  assert.ok(Math.max(...lit) < textWidth('#12 0.48s', 2));
});

test('scaleImage averages, keeps the aspect ratio and composites alpha over black', () => {
  const image = solid(4, 2, [0, 0, 0]);
  paintRect(image, 0, 0, 2, 2, [255, 255, 255]);
  const half = scaleImage(image, 2);
  assert.equal(half.height, 1);
  assert.equal(half.data[0], 255);
  assert.equal(half.data[4], 0);
  const mixed = scaleImage(image, 1);
  assert.ok(Math.abs(mixed.data[0] - 127) <= 1);
  const faded = scaleImage(solid(2, 2, [200, 200, 200, 128]), 1);
  assert.ok(Math.abs(faded.data[0] - 100) <= 2);
});

test('a grid sheet grows to fit a long title', () => {
  const small = layoutGrid('T', [{ image: solid(10, 10, [1, 2, 3]), caption: '#0' }], { cols: 1, width: 10 });
  const wide = layoutGrid('A MUCH LONGER TITLE FOR THE SHEET', [{ image: solid(10, 10, [1, 2, 3]), caption: '#0' }], { cols: 1, width: 10 });
  assert.ok(wide.width > small.width);
  assert.ok(encodePng(wide).length > 0);
});
