// Separate a character from one flat image using polygons you draw. No library: the
// polygons are painted with canvas in the page, then feathered and filled here.
// Coordinates are image fractions, y down.
//
//   validateMask(mask)                  Reject a mask that cannot cut anything.
//   paintMask(context, w, h, mask)      Fill include polygons and clear exclude polygons.
//   featherAlpha(alpha, w, h, radius)   Soften a hard edge with three box blurs.
//   fillPlate(pixels, alpha, w, h)      Paint the backdrop back in behind the character.
//   loadPicture(url)                    Open a user image kept beside the page.
//   characterAlpha(w, h, mask)          Page step: the feathered mask, one byte per pixel.
//   cutOut(picture, alpha)              Page step: the character on a clear canvas.
//   plateFrom(picture, alpha)           Page step: the picture with the character removed.

const isPoint = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
const isPolygon = polygon => Array.isArray(polygon) && polygon.length >= 3 && polygon.every(isPoint);
const clampIndex = (i, size) => Math.min(size - 1, Math.max(0, i));

export function validateMask(mask) {
  if (!mask || !Array.isArray(mask.include) || !mask.include.length) throw Error('Mask needs at least one include polygon');
  if (!mask.include.every(isPolygon)) throw Error('Include polygons need at least 3 [x, y] points');
  if (!(mask.exclude ?? []).every(isPolygon)) throw Error('Exclude polygons need at least 3 [x, y] points');
  if (!(Number.isFinite(mask.feather) && mask.feather >= 0)) throw Error('Mask feather must be a fraction of the image height, 0 or more');
  return mask;
}

export function paintMask(context, width, height, mask) {
  validateMask(mask);
  const fill = polygon => {
    context.beginPath();
    polygon.forEach(([x, y], i) => (i ? context.lineTo(x * width, y * height) : context.moveTo(x * width, y * height)));
    context.closePath();
    context.fill();
  };
  context.clearRect(0, 0, width, height);
  context.fillStyle = '#fff';
  mask.include.forEach(fill);
  context.globalCompositeOperation = 'destination-out';
  (mask.exclude ?? []).forEach(fill);
  context.globalCompositeOperation = 'source-over';
}

function boxBlur(from, to, width, height, radius, stepAlong, stepAcross) {
  const lines = stepAlong === 1 ? height : width, length = stepAlong === 1 ? width : height, span = radius * 2 + 1;
  for (let line = 0; line < lines; line++) {
    const start = line * stepAcross;
    let sum = 0;
    for (let i = -radius; i <= radius; i++) sum += from[start + clampIndex(i, length) * stepAlong];
    for (let i = 0; i < length; i++) {
      to[start + i * stepAlong] = sum / span;
      sum += from[start + clampIndex(i + radius + 1, length) * stepAlong] - from[start + clampIndex(i - radius, length) * stepAlong];
    }
  }
}

// Three box blurs land close to a Gaussian, and stay the same on any browser.
export function featherAlpha(alpha, width, height, radius) {
  if (alpha.length !== width * height) throw Error('Alpha must hold one value per pixel');
  if (!(Number.isInteger(radius) && radius >= 0)) throw Error('Feather radius must be a whole number of pixels');
  if (!radius) return Uint8ClampedArray.from(alpha);
  let a = Float32Array.from(alpha), b = new Float32Array(alpha.length);
  for (let pass = 0; pass < 3; pass++) {
    boxBlur(a, b, width, height, radius, 1, width);
    boxBlur(b, a, width, height, radius, width, 1);
  }
  return Uint8ClampedArray.from(a);
}

// Each hole is filled across its row from the backdrop on either side, then softened
// down its column so neighbouring rows do not read as streaks. This is a smooth guess,
// so check that a moving part never uncovers more than a sliver of it.
export function fillPlate(pixels, alpha, width, height) {
  if (pixels.length !== width * height * 4 || alpha.length !== width * height) throw Error('Pixels and alpha must match the size');
  const plate = Uint8ClampedArray.from(pixels), filled = new Array(height).fill(true);
  const copy = (to, from, k = 1) => { for (let c = 0; c < 3; c++) plate[to + c] = plate[from + c] * k; plate[to + 3] = 255; };
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width;) {
      if (!alpha[y * width + x]) { x++; continue; }
      let end = x;
      while (end < width && alpha[y * width + end]) end++;
      const left = x ? (y * width + x - 1) * 4 : -1, right = end < width ? (y * width + end) * 4 : -1;
      if (left < 0 && right < 0) { filled[y] = false; break; }
      for (let i = x; i < end; i++) {
        const k = (i - x + 1) / (end - x + 1), at = (y * width + i) * 4;
        for (let c = 0; c < 3; c++) plate[at + c] = (left < 0 ? plate[right + c] : right < 0 ? plate[left + c] : plate[left + c] * (1 - k) + plate[right + c] * k);
        plate[at + 3] = 255;
      }
      x = end;
    }
  }
  const rows = filled.flatMap((ok, y) => (ok ? [y] : []));
  if (!rows.length) throw Error('The mask covers the whole image, so no backdrop is left to build a plate from');
  for (let y = 0; y < height; y++) {
    if (filled[y]) continue;
    const near = rows.reduce((best, row) => (Math.abs(row - y) < Math.abs(best - y) ? row : best));
    for (let x = 0; x < width; x++) copy((y * width + x) * 4, (near * width + x) * 4);
  }
  const radius = Math.max(1, Math.round(height / 120)), source = Uint8ClampedArray.from(plate);
  for (let x = 0; x < width; x++) {
    const sum = [0, 0, 0];
    for (let i = -radius; i <= radius; i++) for (let c = 0; c < 3; c++) sum[c] += source[(clampIndex(i, height) * width + x) * 4 + c];
    for (let y = 0; y < height; y++) {
      if (alpha[y * width + x]) for (let c = 0; c < 3; c++) plate[(y * width + x) * 4 + c] = sum[c] / (radius * 2 + 1);
      for (let c = 0; c < 3; c++) sum[c] += source[(clampIndex(y + radius + 1, height) * width + x) * 4 + c] - source[(clampIndex(y - radius, height) * width + x) * 4 + c];
    }
  }
  return plate;
}

export async function loadPicture(url) {
  const response = await fetch(url);
  if (!response.ok) throw Error(`Could not open ${url}: ${response.status}`);
  return createImageBitmap(await response.blob());
}

function blankCanvas(width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

export function characterAlpha(width, height, mask) {
  const canvas = blankCanvas(width, height), context = canvas.getContext('2d', {willReadFrequently: true});
  paintMask(context, width, height, mask);
  const painted = context.getImageData(0, 0, width, height).data, alpha = new Uint8ClampedArray(width * height);
  for (let i = 0; i < alpha.length; i++) alpha[i] = painted[i * 4 + 3];
  return featherAlpha(alpha, width, height, Math.round(mask.feather * height));
}

export function cutOut(picture, alpha) {
  const {width, height} = picture, layer = blankCanvas(width, height), shape = new ImageData(width, height);
  for (let i = 0; i < alpha.length; i++) { shape.data.fill(255, i * 4, i * 4 + 3); shape.data[i * 4 + 3] = alpha[i]; }
  layer.getContext('2d').putImageData(shape, 0, 0);
  const context = layer.getContext('2d');
  context.globalCompositeOperation = 'source-in';
  context.drawImage(picture, 0, 0, width, height);
  return layer;
}

export function plateFrom(picture, alpha) {
  const {width, height} = picture, plate = blankCanvas(width, height), context = plate.getContext('2d');
  context.drawImage(picture, 0, 0, width, height);
  const image = context.getImageData(0, 0, width, height);
  image.data.set(fillPlate(image.data, alpha, width, height));
  context.putImageData(image, 0, 0);
  return plate;
}
