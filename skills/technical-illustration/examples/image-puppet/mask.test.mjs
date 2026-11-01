import assert from 'node:assert/strict';
import test from 'node:test';
import {featherAlpha, fillPlate, paintMask, validateMask} from './mask.mjs';
import {mask, regions} from './regions.mjs';

const square = [[.25, .25], [.75, .25], [.75, .75], [.25, .75]];

function recorder() {
  const log = [];
  const context = new Proxy({log}, {
    get: (target, name) => (name in target ? target[name] : (...args) => log.push([name, ...args])),
    set: (target, name, value) => { log.push([name, value]); return true; },
  });
  return {context, log};
}

test('a mask that cannot cut anything is rejected', () => {
  for (const bad of [null, {}, {include: [], feather: 0}, {include: [[[0, 0]]], feather: 0}, {include: [square]}, {include: [square], feather: -1},
    {include: [square], feather: NaN}, {include: [square], exclude: [[[NaN, 0], [1, 1], [0, 1]]], feather: 0}]) assert.throws(() => validateMask(bad));
  assert.equal(validateMask({include: [square], feather: .01}).feather, .01);
});

test('polygons are painted in pixels, and exclude polygons are cleared', () => {
  const {context, log} = recorder();
  paintMask(context, 200, 100, {include: [square], exclude: [[[0, 0], [.1, 0], [.1, .1]]], feather: 0});
  assert.deepEqual(log.find(l => l[0] === 'moveTo'), ['moveTo', 50, 25]);
  assert.deepEqual(log.find(l => l[0] === 'lineTo'), ['lineTo', 150, 25]);
  const order = log.filter(l => l[0] === 'globalCompositeOperation').map(l => l[1]);
  assert.deepEqual(order, ['destination-out', 'source-over']);
  assert.equal(log.filter(l => l[0] === 'fill').length, 2);
});

test('feathering softens an edge and keeps the middle solid', () => {
  const width = 64, height = 8, alpha = new Uint8ClampedArray(width * height);
  for (let y = 0; y < height; y++) alpha.fill(255, y * width + 32, (y + 1) * width);
  const soft = featherAlpha(alpha, width, height, 3), row = Array.from(soft.slice(4 * width, 5 * width));
  assert.equal(row[0], 0);
  assert.equal(row[63], 255);
  assert.ok(row[31] > 0 && row[31] < 255);
  for (let x = 1; x < width; x++) assert.ok(row[x] >= row[x - 1]);
  assert.deepEqual(Array.from(featherAlpha(alpha, width, height, 0)), Array.from(alpha));
});

test('feathering holds at the picture edge, so a body cut by the frame stays solid', () => {
  const soft = featherAlpha(new Uint8ClampedArray(16).fill(255), 4, 4, 2);
  assert.ok(soft.every(v => v === 255));
});

test('bad feather input is rejected', () => {
  assert.throws(() => featherAlpha(new Uint8ClampedArray(3), 2, 2, 1), /one value/);
  assert.throws(() => featherAlpha(new Uint8ClampedArray(4), 2, 2, 1.5), /whole number/);
});

function picture(width, height) {
  const pixels = new Uint8ClampedArray(width * height * 4);
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) pixels.set([x * 10, 100, 200 - y, 255], (y * width + x) * 4);
  return pixels;
}

test('a plate fills the hole from the backdrop on either side', () => {
  const width = 16, height = 6, pixels = picture(width, height), alpha = new Uint8ClampedArray(width * height);
  for (let y = 0; y < height; y++) alpha.fill(255, y * width + 4, y * width + 12);
  const hole = (y, x) => (y * width + x) * 4;
  for (let y = 0; y < height; y++) for (let x = 4; x < 12; x++) pixels.set([255, 0, 255, 255], hole(y, x));
  const plate = fillPlate(pixels, alpha, width, height);
  for (let y = 0; y < height; y++) {
    assert.equal(plate[hole(y, 0)], 0, 'backdrop is untouched');
    for (let x = 4; x < 12; x++) {
      assert.ok(plate[hole(y, x)] >= 30 && plate[hole(y, x)] <= 120, 'no character colour is left');
      assert.equal(plate[hole(y, x) + 1], 100);
      assert.equal(plate[hole(y, x) + 3], 255);
    }
  }
});

test('a hole that reaches the picture edge copies the side that remains', () => {
  const width = 8, height = 3, alpha = new Uint8ClampedArray(width * height);
  for (let y = 0; y < height; y++) alpha.fill(255, y * width, y * width + 4);
  const plate = fillPlate(picture(width, height), alpha, width, height);
  assert.equal(plate[0], 40);
});

test('a row with no backdrop borrows the nearest row, and a full mask fails', () => {
  const width = 4, height = 4, alpha = new Uint8ClampedArray(width * height);
  alpha.fill(255, width, width * 2);
  const plate = fillPlate(picture(width, height), alpha, width, height);
  assert.equal(plate[(width + 1) * 4], 10);
  assert.throws(() => fillPlate(picture(width, height), new Uint8ClampedArray(16).fill(255), width, height), /no backdrop/);
  assert.throws(() => fillPlate(new Uint8ClampedArray(4), alpha, width, height), /match/);
});

test('the demo mask holds every moving part that is in frame', () => {
  validateMask(mask);
  const inside = ([x, y]) => {
    let hit = false;
    for (const polygon of mask.include) for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [ax, ay] = polygon[i], [bx, by] = polygon[j];
      if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) hit = !hit;
    }
    return hit;
  };
  for (const region of regions) {
    for (const point of [region.root, region.tip, region.pivot].filter(Boolean)) {
      if (point[1] < 1) assert.ok(inside(point), `${region.id} ${point}`);
    }
  }
});
