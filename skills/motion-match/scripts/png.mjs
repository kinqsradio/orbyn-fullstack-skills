// Small PNG codec: reads 8-bit non-interlaced files and writes RGBA.
import { crc32, deflateSync, inflateSync } from 'node:zlib';
import { readFileSync } from 'node:fs';

const SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const CHANNELS = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 };

export function createImage(width, height) {
  return { width, height, data: new Uint8Array(width * height * 4) };
}

export function decodePng(buffer) {
  if (buffer.length < 33 || !buffer.subarray(0, 8).equals(SIGNATURE)) throw new Error('Not a PNG file');
  let position = 8;
  let header = null;
  let palette = null;
  let alphaTable = null;
  const chunks = [];
  while (position + 8 <= buffer.length) {
    const length = buffer.readUInt32BE(position);
    const type = buffer.toString('latin1', position + 4, position + 8);
    const body = buffer.subarray(position + 8, position + 8 + length);
    if (type === 'IHDR') header = { width: body.readUInt32BE(0), height: body.readUInt32BE(4), depth: body[8], colour: body[9], interlace: body[12] };
    else if (type === 'PLTE') palette = body;
    else if (type === 'tRNS') alphaTable = body;
    else if (type === 'IDAT') chunks.push(body);
    else if (type === 'IEND') break;
    position += 12 + length;
  }
  if (!header || !chunks.length) throw new Error('PNG is missing IHDR or IDAT');
  const channels = CHANNELS[header.colour];
  if (header.depth !== 8 || header.interlace !== 0 || !channels) {
    throw new Error(`Unsupported PNG: depth ${header.depth}, colour ${header.colour}, interlace ${header.interlace}. Re-extract frames with frames.mjs`);
  }
  const raw = inflateSync(Buffer.concat(chunks));
  const stride = header.width * channels;
  if (raw.length < (stride + 1) * header.height) throw new Error('PNG data is truncated');
  unfilter(raw, stride, header.height, channels);
  return toRgba(raw, header, stride, channels, palette, alphaTable);
}

// Each row is rewritten in place: the filter byte sits before the row, so rows shift by one per line.
function unfilter(raw, stride, height, bpp) {
  for (let y = 0; y < height; y++) {
    const start = y * (stride + 1);
    const filter = raw[start];
    const row = start + 1;
    const above = row - stride - 1;
    for (let x = 0; x < stride; x++) {
      const left = x >= bpp ? raw[row + x - bpp] : 0;
      const up = y > 0 ? raw[above + x] : 0;
      const upLeft = y > 0 && x >= bpp ? raw[above + x - bpp] : 0;
      let add = 0;
      if (filter === 1) add = left;
      else if (filter === 2) add = up;
      else if (filter === 3) add = (left + up) >> 1;
      else if (filter === 4) add = paeth(left, up, upLeft);
      else if (filter !== 0) throw new Error(`Bad PNG filter ${filter}`);
      raw[row + x] = (raw[row + x] + add) & 255;
    }
  }
}

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
}

function toRgba(raw, { width, height, colour }, stride, channels, palette, alphaTable) {
  const image = createImage(width, height);
  const { data } = image;
  let to = 0;
  for (let y = 0; y < height; y++) {
    let from = y * (stride + 1) + 1;
    for (let x = 0; x < width; x++, to += 4, from += channels) {
      if (colour === 6) { data[to] = raw[from]; data[to + 1] = raw[from + 1]; data[to + 2] = raw[from + 2]; data[to + 3] = raw[from + 3]; }
      else if (colour === 2) { data[to] = raw[from]; data[to + 1] = raw[from + 1]; data[to + 2] = raw[from + 2]; data[to + 3] = 255; }
      else if (colour === 3) {
        const index = raw[from];
        data[to] = palette[index * 3]; data[to + 1] = palette[index * 3 + 1]; data[to + 2] = palette[index * 3 + 2];
        data[to + 3] = alphaTable && index < alphaTable.length ? alphaTable[index] : 255;
      } else {
        data[to] = data[to + 1] = data[to + 2] = raw[from];
        data[to + 3] = colour === 4 ? raw[from + 1] : 255;
      }
    }
  }
  return image;
}

export const readPng = (path) => decodePng(readFileSync(path));

function chunk(type, body) {
  const tag = Buffer.from(type, 'latin1');
  const out = Buffer.alloc(12 + body.length);
  out.writeUInt32BE(body.length, 0);
  tag.copy(out, 4);
  body.copy(out, 8);
  out.writeUInt32BE(crc32(Buffer.concat([tag, body])) >>> 0, 8 + body.length);
  return out;
}

export function encodePng({ width, height, data }) {
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header[8] = 8;
  header[9] = 6;
  const stride = width * 4;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y++) {
    Buffer.from(data.buffer, data.byteOffset + y * stride, stride).copy(raw, y * (stride + 1) + 1);
  }
  return Buffer.concat([SIGNATURE, chunk('IHDR', header), chunk('IDAT', deflateSync(raw, { level: 6 })), chunk('IEND', Buffer.alloc(0))]);
}

export function cropImage(image, { x, y, width, height }) {
  const left = Math.round(x);
  const top = Math.round(y);
  if (left < 0 || top < 0 || left + width > image.width || top + height > image.height) {
    throw new Error(`Crop ${left},${top},${width},${height} is outside ${image.width}x${image.height}`);
  }
  const out = createImage(width, height);
  for (let row = 0; row < height; row++) {
    const start = ((top + row) * image.width + left) * 4;
    out.data.set(image.data.subarray(start, start + width * 4), row * width * 4);
  }
  return out;
}
