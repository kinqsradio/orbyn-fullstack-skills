// The rig for the test portrait: fractions of the frame, y down. Each part has its own
// period, so the figure never pulses as one block. The hair feathers are set by hand
// because the locks overlap and their motion adds up.
import {CX, LIFT, ZOOM} from './portrait.mjs';
const X = v => ((v - CX) * ZOOM + CX) / 1778, Y = v => (v * ZOOM - LIFT) / 1000;
const box = (x0, y0, x1, y1) => [[X(x0), Y(y0)], [X(x1), Y(y0)], [X(x1), Y(y1)], [X(x0), Y(y1)]];

// The character's outline, drawn over a small preview in units of a 1778 by 1000 frame.
// It stops just outside the hair and runs past the bottom of the picture.
const LEFT = [[889, 38], [815, 42], [690, 58], [579, 68], [572, 100], [590, 125], [632, 150], [617, 175], [597, 200], [573, 250],
  [540, 325], [515, 400], [497, 450], [484, 525], [463, 650], [445, 750], [433, 825], [423, 900], [416, 1010]];
const outline = [...LEFT, ...LEFT.slice(1).reverse().map(([x, y]) => [1778 - x, y])];
export const mask = {include: [outline.map(([x, y]) => [x / 1778, y / 1000])], feather: .002};

export const onsets = [1.2, 1.6, 2.8, 3.2, 4.4, 5.2, 6.4, 6.8, 8.0];
const mouthOpen = time => {
  let open = 0;
  for (const at of onsets) if (time >= at) open = Math.max(open, Math.exp(-(time - at) / .13));
  return open;
};

export const regions = [
  {id: 'head', kind: 'sway', polygon: box(CX - 380, 40, CX + 380, 640), pivot: [X(CX), Y(640)], amp: .03, period: 6.7, feather: .08},
  {id: 'chest', kind: 'breath', polygon: box(CX - 400, 640, CX + 400, 1060), peakY: Y(800), reach: .32, amp: .012, period: 3.9, feather: .06},
  {id: 'fringe', kind: 'hair', polygon: box(CX - 215, 190, CX + 215, 400), root: [X(CX), Y(205)], tip: [X(CX), Y(385)], amp: .008, period: 2.9, feather: .05},
  {id: 'lock-left', kind: 'hair', polygon: box(CX - 340, 250, CX - 130, 860), root: [X(CX - 186), Y(260)], tip: [X(CX - 226), Y(830)], amp: .03, period: 3.4, phase: .4, feather: .1},
  {id: 'lock-right', kind: 'hair', polygon: box(CX + 130, 250, CX + 340, 860), root: [X(CX + 186), Y(260)], tip: [X(CX + 226), Y(830)], amp: .034, period: 3.8, phase: 2.1, feather: .11},
  {id: 'back-left', kind: 'hair', polygon: box(CX - 500, 520, CX - 110, 1080), root: [X(CX - 230), Y(540)], tip: [X(CX - 320), Y(1040)], amp: .04, period: 4.6, phase: 1.2, feather: .13},
  {id: 'back-right', kind: 'hair', polygon: box(CX + 110, 520, CX + 500, 1080), root: [X(CX + 230), Y(540)], tip: [X(CX + 320), Y(1040)], amp: .042, period: 4.1, phase: 3, feather: .135},
  {id: 'ribbon', kind: 'hair', polygon: box(CX + 120, 80, CX + 300, 240), root: [X(CX + 150), Y(174)], tip: [X(CX + 225), Y(160)], amp: .014, period: 2.3, feather: .05},
  {id: 'eye-left', kind: 'blink', polygon: box(CX - 158, 372, CX - 16, 505), lineY: Y(470), feather: .018, seed: 11},
  {id: 'eye-right', kind: 'blink', polygon: box(CX + 16, 372, CX + 158, 505), lineY: Y(470), feather: .018, seed: 11},
  {id: 'mouth', kind: 'mouth', polygon: box(CX - 90, 540, CX + 90, 640), lineY: Y(556), open: mouthOpen, height: .007, feather: .03},
];

// Hair and clothes must not share a mesh, or bending one drags the other. Each layer
// bends only under its own regions, and the head turns all three together.
const pick = (...ids) => ids.map(id => regions.find(r => r.id === id));
export const layers = [
  {part: 'back', regions: pick('head', 'back-left', 'back-right')},
  {part: 'body', regions: pick('head', 'chest', 'eye-left', 'eye-right', 'mouth')},
  {part: 'top', regions: pick('head', 'fringe', 'lock-left', 'lock-right', 'ribbon')},
];
