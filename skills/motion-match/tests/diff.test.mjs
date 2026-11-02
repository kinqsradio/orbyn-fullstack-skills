import assert from 'node:assert/strict';
import { deflateSync } from 'node:zlib';
import { test } from 'node:test';
import { diffImages } from '../scripts/diff.mjs';
import { cropImage, decodePng, encodePng } from '../scripts/png.mjs';
import { paintRect, solid } from './helpers.mjs';

const WHITE = [255, 255, 255];
const BLACK = [0, 0, 0];

test('identical images do not differ', () => {
  assert.equal(diffImages(solid(8, 8, WHITE), solid(8, 8, WHITE)).count, 0);
});

test('black against white is a full difference at any threshold below one', () => {
  const result = diffImages(solid(4, 4, BLACK), solid(4, 4, WHITE), { threshold: 0.99 });
  assert.equal(result.count, 16);
  assert.equal(result.ratio, 1);
});

test('the threshold decides whether a small colour change counts', () => {
  const a = solid(4, 4, [100, 100, 100]);
  const b = solid(4, 4, [110, 110, 110]);
  assert.equal(diffImages(a, b, { threshold: 0.1 }).count, 0);
  assert.equal(diffImages(a, b, { threshold: 0.01, tolerance: false }).count, 16);
});

test('a lone changed pixel counts even with tolerance on', () => {
  const a = solid(9, 9, WHITE);
  const b = solid(9, 9, WHITE);
  paintRect(b, 4, 4, 1, 1, BLACK);
  assert.equal(diffImages(a, b).count, 1);
});

test('an edge moved by one pixel is excused by tolerance and counted without it', () => {
  const a = solid(20, 20, BLACK);
  const b = solid(20, 20, BLACK);
  paintRect(a, 5, 0, 10, 20, WHITE);
  paintRect(b, 6, 0, 10, 20, WHITE);
  assert.equal(diffImages(a, b, { tolerance: true }).count, 0);
  assert.equal(diffImages(a, b, { tolerance: false }).count, 40);
});

test('an edge moved by three pixels is not excused', () => {
  const a = solid(20, 20, BLACK);
  const b = solid(20, 20, BLACK);
  paintRect(a, 5, 0, 10, 20, WHITE);
  paintRect(b, 8, 0, 10, 20, WHITE);
  assert.ok(diffImages(a, b).count >= 40);
});

test('transparent pixels compare as the white they show', () => {
  assert.equal(diffImages(solid(4, 4, [0, 0, 0, 0]), solid(4, 4, WHITE)).count, 0);
});

test('the diff image marks changed pixels red and leaves others grey', () => {
  const a = solid(5, 1, WHITE);
  const b = solid(5, 1, WHITE);
  paintRect(b, 2, 0, 1, 1, BLACK);
  const { image } = diffImages(a, b, { image: true });
  assert.deepEqual([...image.data.subarray(8, 12)], [255, 0, 0, 255]);
  assert.equal(image.data[0], image.data[1]);
  assert.notEqual(image.data[0], 0);
});

test('different sizes are refused', () => {
  assert.throws(() => diffImages(solid(2, 2, WHITE), solid(3, 2, WHITE)), /differ in size/);
});

test('PNG round trip keeps every byte', () => {
  const image = solid(7, 5, [10, 20, 30, 128]);
  paintRect(image, 2, 1, 3, 2, [200, 100, 50]);
  const back = decodePng(encodePng(image));
  assert.equal(back.width, 7);
  assert.equal(back.height, 5);
  assert.deepEqual(back.data, image.data);
});

function handmadePng(width, height, colour, rows, extra = []) {
  const chunk = (type, body) => {
    const out = Buffer.alloc(12 + body.length);
    out.writeUInt32BE(body.length, 0);
    out.write(type, 4, 'latin1');
    body.copy(out, 8);
    return out;
  };
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header[8] = 8;
  header[9] = colour;
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 13, 10, 26, 10]), chunk('IHDR', header), ...extra, chunk('IDAT', deflateSync(Buffer.from(rows))), chunk('IEND', Buffer.alloc(0))]);
}

test('all five PNG filters decode', () => {
  // Grey, 3x5. Expected rows are written below each filtered row.
  const rows = [
    0, 10, 20, 30, //  none: 10 20 30
    1, 5, 5, 5, //     sub: 5 10 15
    2, 1, 1, 1, //     up: 6 11 16
    3, 2, 2, 2, //     average: (0+6)/2+2=5, (5+11)/2+2=10, (10+16)/2+2=15
    4, 1, 1, 1, //     paeth: 5+1=6, a=6 b=10 c=5 picks 10 -> 11, a=11 b=15 c=10 picks 15 -> 16
  ];
  const { data } = decodePng(handmadePng(3, 5, 0, rows));
  assert.deepEqual([...data].filter((_, i) => i % 4 === 0), [10, 20, 30, 5, 10, 15, 6, 11, 16, 5, 10, 15, 6, 11, 16]);
});

test('palette PNGs decode, with transparency', () => {
  const palette = Buffer.from([255, 0, 0, 0, 255, 0]);
  const chunk = (type, body) => {
    const out = Buffer.alloc(12 + body.length);
    out.writeUInt32BE(body.length, 0);
    out.write(type, 4, 'latin1');
    body.copy(out, 8);
    return out;
  };
  const { data } = decodePng(handmadePng(2, 1, 3, [0, 1, 0], [chunk('PLTE', palette), chunk('tRNS', Buffer.from([255, 7]))]));
  assert.deepEqual([...data], [0, 255, 0, 7, 255, 0, 0, 255]);
});

test('unsupported and damaged PNGs are refused with a reason', () => {
  assert.throws(() => decodePng(Buffer.from('not a png, not a png, not a png, not a png')), /Not a PNG/);
  const sixteenBit = handmadePng(1, 1, 0, [0, 0, 0]);
  sixteenBit[24] = 16;
  assert.throws(() => decodePng(sixteenBit), /Unsupported PNG/);
});

test('crop copies the right pixels and refuses a box outside the image', () => {
  const image = solid(4, 4, BLACK);
  paintRect(image, 2, 2, 1, 1, WHITE);
  const crop = cropImage(image, { x: 2, y: 2, width: 2, height: 1 });
  assert.deepEqual([...crop.data.subarray(0, 4)], [255, 255, 255, 255]);
  assert.deepEqual([...crop.data.subarray(4, 8)], [0, 0, 0, 255]);
  assert.throws(() => cropImage(image, { x: 3, y: 0, width: 2, height: 1 }), /outside/);
});
