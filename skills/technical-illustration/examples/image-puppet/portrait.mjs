// Paints an original anime-style test portrait in code, then the film treats it as one
// flat picture and cuts it apart with mask.mjs. A real job opens the user's image here
// instead. still_to_layers.py needs OpenCV, so it only comes in if the user approves it.
// Units are thousandths of the frame height, before the portrait's zoom.
export const CX = 889, ZOOM = 1.32, LIFT = 120;
const frame = (c, W, H) => c.setTransform(W / 1778 * ZOOM, 0, 0, H / 1000 * ZOOM, W * (1 - ZOOM) / 2, -LIFT * H / 1000);

function shape(c, points, fill) {
  c.beginPath(); c.moveTo(...points[0]);
  for (const p of points.slice(1)) p.length === 6 ? c.bezierCurveTo(...p) : p.length === 4 ? c.quadraticCurveTo(...p) : c.lineTo(...p);
  c.closePath(); c.fillStyle = fill; c.fill();
}
const ramp = (c, x0, y0, x1, y1, stops) => { const g = c.createLinearGradient(x0, y0, x1, y1); stops.forEach(([at, colour]) => g.addColorStop(at, colour)); return g; };
const mirror = points => points.map(p => p.map((v, i) => (i % 2 ? v : CX * 2 - v)));

const HAIR = c => ramp(c, 0, 90, 0, 900, [[0, '#3f4fb8'], [.3, '#5f7cf0'], [.7, '#8fb6ff'], [1, '#d7c8ff']]);
const SHADE = '#2f3a96';
const SKIN = c => ramp(c, 0, 220, 0, 625, [[0, '#ffdcc9'], [1, '#ffeadf']]);

function lock(c, x, y, length, sway, width, fill) { // One strand, tapered at both ends.
  shape(c, [[x, y], [x - width * 1.1, y + length * .3, x + sway - width * .9, y + length * .7, x + sway, y + length], [x + sway + width * .9, y + length * .68, x + width * 1.1, y + length * .3, x, y]], fill);
}

function closedEye(c, side) {
  const x = CX + side * 86, y = 442;
  c.fillStyle = SKIN(c); // The face's own gradient, so the covered eye leaves no patch.
  c.beginPath(); c.ellipse(x, y - 14, 72, 54, 0, 0, 7); c.fill();
  c.strokeStyle = '#2a1a2e'; c.lineCap = 'round'; c.lineWidth = 8;
  c.beginPath(); c.moveTo(x - 60, y - 2); c.quadraticCurveTo(x, y + 30, x + 60, y - 6); c.stroke();
  c.lineWidth = 4;
  for (const [dx, dy] of [[-58, -2], [-46, 8], [58, -6], [46, 6]]) { c.beginPath(); c.moveTo(x + dx, y + dy); c.lineTo(x + dx * 1.18, y + dy + 10); c.stroke(); }
  c.strokeStyle = '#3a3f9a'; c.lineWidth = 4; c.beginPath(); c.moveTo(x - 50, y - 92); c.quadraticCurveTo(x, y - 106, x + 52, y - 90); c.stroke();
}

function eye(c, side) {
  const x = CX + side * 86, y = 432;
  c.save();
  c.beginPath(); c.moveTo(x - 58, y + 8); c.quadraticCurveTo(x - 6 * side, y - 58, x + 58, y + 2); c.quadraticCurveTo(x, y + 62, x - 58, y + 8); c.closePath();
  c.fillStyle = '#fffaf5'; c.fill(); c.clip();
  c.fillStyle = ramp(c, 0, y - 56, 0, y + 56, [[0, '#7a2a12'], [.5, '#d9772a'], [1, '#ffd36a']]);
  c.beginPath(); c.ellipse(x, y + 2, 38, 54, 0, 0, 7); c.fill();
  c.fillStyle = '#3b1208'; c.beginPath(); c.ellipse(x, y + 4, 19, 30, 0, 0, 7); c.fill();
  c.fillStyle = 'rgba(70,70,150,.28)'; c.fillRect(x - 70, y - 62, 140, 26);
  c.fillStyle = '#fff'; c.beginPath(); c.ellipse(x - 12, y - 18, 13, 17, .3, 0, 7); c.fill();
  c.beginPath(); c.ellipse(x + 15, y + 22, 6, 8, 0, 0, 7); c.fill();
  c.restore();
  c.strokeStyle = '#2a1a2e'; c.lineCap = 'round'; c.lineWidth = 8;
  c.beginPath(); c.moveTo(x - 62, y + 12); c.quadraticCurveTo(x - 6 * side, y - 66, x + 62, y + 2); c.stroke();
  c.lineWidth = 2.5; c.beginPath(); c.moveTo(x - 36, y + 42); c.quadraticCurveTo(x, y + 56, x + 40, y + 34); c.stroke();
  c.strokeStyle = '#3a3f9a'; c.lineWidth = 4; c.beginPath(); c.moveTo(x - 50, y - 86); c.quadraticCurveTo(x, y - 104, x + 52, y - 84); c.stroke();
}

function paintBackground(c, W, H) {
  c.setTransform(W / 1778, 0, 0, H / 1000, 0, 0); // The backdrop stays at frame scale.
  c.fillStyle = ramp(c, 0, 0, 0, 1000, [[0, '#fbe6f2'], [.55, '#e9e4ff'], [1, '#cfe3ff']]); c.fillRect(0, 0, 1778, 1000);
  c.fillStyle = 'rgba(255,255,255,.55)';
  for (const [x, y, r] of [[230, 180, 90], [1500, 260, 120], [1380, 700, 70], [320, 760, 110]]) { c.beginPath(); c.arc(x, y, r, 0, 7); c.fill(); }
}

// One flat picture, as a user's image would arrive. An image passed in keeps its own
// pixels, and the states are drawn over it. Redraw them to match each real face.
export function paintPicture(c, W, H, state = {}, image = null) {
  c.resetTransform(); c.clearRect(0, 0, W, H);
  if (image) {
    c.drawImage(image, 0, 0, W, H); frame(c, W, H);
    if (state.eyesClosed) for (const side of [-1, 1]) closedEye(c, side);
    if (state.mouthOpen) openMouth(c);
    return;
  }
  paintBackground(c, W, H);
  paintCharacter(c, W, H, state);
}

// The same drawing, one layer at a time, for a source that has its layers: back hair,
// then body and face, then the fringe and side locks in front.
export function paintLayer(c, W, H, part, state = {}) {
  c.resetTransform(); c.clearRect(0, 0, W, H);
  paintCharacter(c, W, H, state, part);
}

function openMouth(c) {
  shape(c, [[CX - 30, 552], [CX, 546, CX + 30, 552], [CX + 26, 592, CX - 26, 592, CX - 30, 552]], '#7a2436');
  c.fillStyle = '#ff8d96'; c.beginPath(); c.ellipse(CX, 582, 17, 8, 0, 0, 7); c.fill();
  c.fillStyle = '#fff'; c.fillRect(CX - 20, 552, 40, 7);
}

function paintCharacter(c, W, H, state, part = 'all') {
  frame(c, W, H); c.lineJoin = 'round';
  const hair = HAIR(c), wanted = name => part === 'all' || part === name;
  if (wanted('back')) paintBackHair(c, hair);
  if (wanted('body')) paintBody(c, state);
  if (wanted('top')) paintFrontHair(c, hair);
}

function paintBackHair(c, hair) {
  // One flowing mass with a pointed, uneven hem.
  const hem = [];
  for (let i = 0; i <= 12; i++) hem.push([CX + 300 - i * 50, i % 2 ? 900 + (i % 3) * 22 : 1040 - (i % 4) * 12]);
  shape(c, [[CX - 205, 230], [CX - 330, 420, CX - 350, 760, CX - 300, hem[12][1]], ...hem.slice(0, 12).reverse().map(p => p), [CX + 300, hem[0][1]], [CX + 350, 760, CX + 330, 420, CX + 205, 230], [CX + 120, 90, CX - 120, 90, CX - 205, 230]], hair);
  for (const side of [-1, 1]) for (let i = 0; i < 5; i++) lock(c, CX + side * (120 + i * 42), 330 + i * 18, 640 - i * 30, side * (24 + i * 10), 12 + i, i % 2 ? 'rgba(47,58,150,.55)' : 'rgba(255,255,255,.2)');
}

function paintBody(c, state) {
  // Body, collar and neck.
  shape(c, [[CX - 330, 1010], [CX - 300, 800, CX - 190, 700, CX - 72, 672], [CX + 72, 672], [CX + 190, 700, CX + 300, 800, CX + 330, 1010]], '#1f2a5c');
  shape(c, [[CX - 100, 668], [CX, 860], [CX + 100, 668]], '#fff8f1');
  shape(c, [[CX - 190, 700], [CX - 40, 800, CX, 880], [CX + 40, 800, CX + 190, 700], [CX + 120, 660], [CX, 790], [CX - 120, 660]], '#31408f');
  shape(c, [[CX - 26, 835], [CX + 26, 835], [CX + 48, 905], [CX, 878], [CX - 48, 905]], '#e0465a');
  shape(c, [[CX - 58, 590], [CX + 58, 590], [CX + 66, 690, CX, 730, CX - 66, 690]], '#f6c9b8');
  // Face.
  shape(c, [[CX - 186, 360], [CX - 188, 480, CX - 110, 590, CX, 625], [CX + 110, 590, CX + 188, 480, CX + 186, 360], [CX + 170, 190, CX - 170, 190, CX - 186, 360]], SKIN(c));
  c.fillStyle = 'rgba(255,120,140,.28)';
  for (const side of [-1, 1]) { c.beginPath(); c.ellipse(CX + side * 112, 505, 46, 20, 0, 0, 7); c.fill(); }
  for (const side of [-1, 1]) (state.eyesClosed ? closedEye : eye)(c, side);
  c.strokeStyle = '#d98f7c'; c.lineWidth = 3.5; c.lineCap = 'round'; c.beginPath(); c.moveTo(CX - 5, 508); c.lineTo(CX + 2, 516); c.stroke();
  if (state.mouthOpen) openMouth(c);
  else {
    c.strokeStyle = '#9c3f46'; c.lineWidth = 4.5; c.beginPath(); c.moveTo(CX - 24, 556); c.quadraticCurveTo(CX, 568, CX + 26, 554); c.stroke();
  }
}

function paintFrontHair(c, hair) {
  // Fringe and side locks over the face.
  shape(c, [[CX - 205, 300], [CX - 190, 120, CX + 190, 120, CX + 205, 300], [CX + 150, 230, CX + 60, 200, CX, 205], [CX - 60, 200, CX - 150, 230, CX - 205, 300]], hair);
  for (const [x, length, sway, width] of [[-140, 205, -24, 48], [-74, 222, -10, 52], [-6, 212, 12, 52], [66, 226, 14, 52], [136, 202, 26, 48]]) lock(c, CX + x, 130, length, sway, width, hair);
  for (const side of [-1, 1]) {
    lock(c, CX + side * 214, 230, 610, side * 62, 34, SHADE);
    lock(c, CX + side * 186, 200, 640, side * 40, 46, hair);
  }
  c.strokeStyle = 'rgba(255,255,255,.5)'; c.lineWidth = 9;
  c.beginPath(); c.moveTo(CX - 120, 190); c.quadraticCurveTo(CX, 150, CX + 120, 190); c.stroke();
  // Ribbon.
  for (const side of [-1, 1]) shape(c, [[CX + side * 150, 158], [CX + side * 260, 96, CX + side * 268, 216, CX + side * 150, 190]], '#e0465a');
  c.fillStyle = '#ff6d7f'; c.beginPath(); c.arc(CX + 150, 174, 15, 0, 7); c.arc(CX - 150, 174, 15, 0, 7); c.fill();
}
