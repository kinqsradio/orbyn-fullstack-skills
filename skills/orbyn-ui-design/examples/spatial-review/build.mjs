import { writeFile } from 'node:fs/promises';
import { turning } from './renderer/kit/turn-build.mjs';
import * as G from './renderer/kit/lathe.mjs';
import { CYLINDERS, R, L, PITCH, poses, rad } from './model.mjs';
export const P = { origin: [470, 425], scale: 78, azimuth: 42, elevation: 27 };
export function createEngine() {
  const T = turning(P); T.layer('engine');
  const view = T.group('view', { turn: { range: [-180, 180] } });
  const crank = T.group('crank', { parent: view, hinge: { point: [0, 0, 0], axis: [0, 1, 0], range: [0, 360] } });
  const round = (name, o, axis, r, s0, s1, group, material = 'steel') => T.round({ name, group, F: G.frameAlong(o, axis), r, s0, s1, material, fixed: false });
  round('crankshaft', [0, 0, 0], [0, 1, 0], .105, -3.08, 3.08, crank, 'gunmetal');
  round('flywheel', [0, -3.08, 0], [0, 1, 0], .68, -.16, .02, crank, 'copper');
  const offsets = [0, 120, 240, 240, 120, 0];
  for (let i = 0; i < 6; i++) {
    const y = (i - 2.5) * PITCH, a = rad(offsets[i]);
    round('crankpin-' + (i + 1), [R * Math.sin(a), y, R * Math.cos(a)], [0, 1, 0], .115, -.23, .23, crank, 'chrome');
    for (const side of [-1, 1]) round(`web-${i}-${side}`, [R * Math.sin(a) / 2, y + side * .25, R * Math.cos(a) / 2], [0, 1, 0], .32, -.055, .055, crank, 'gunmetal');
  }
  for (const c of CYLINDERS) {
    const axis = [Math.sin(rad(c.bankAngle)), 0, Math.cos(rad(c.bankAngle))];
    const pg = T.group('piston-' + c.id, { parent: view, free: { origin: [0, c.station, 0] } });
    const rg = T.group('rod-' + c.id, { parent: view, free: { origin: [0, c.station, 0] } });
    round('piston-' + c.id, [0, c.station, 0], axis, .285, -.15, .15, pg, 'chrome');
    round('rod-' + c.id, [0, c.station, 0], [0, 0, 1], .052, 0, L, rg, 'steel');
    round('liner-' + c.id, [0, c.station, 0], axis, .34, L - R - .2, L + R + .24, view, 'steel');
  }
  for (const x of [-.83, .83]) T.prism({ name: 'support-' + x, group: view, plan: { x: x - .08, y: -3, w: .16, d: 6, r: 0 }, z: -.68, h: .16, material: 'gunmetal' });
  return T;
}
const T = createEngine();
// Educational joints deliberately intersect. This is not a solid-clearance certificate.
const states = Array.from({ length: 24 }, (_, i) => poses(i * 30, 0));
const built = T.build({ poses: states, verify: true, strict: false });
await writeFile(new URL('engine-data.json', import.meta.url), JSON.stringify(built.data));
await writeFile(new URL('engine.svg', import.meta.url), built.layerSvg('engine', { width: 960, height: 600 }));
await writeFile(new URL('turn.css', import.meta.url), built.css);
await writeFile(new URL('build-report.json', import.meta.url), JSON.stringify({ ...built.report, limits: 'Rigid-link teaching model; allowed assembled contacts and transparent bore guides. Strict solid separation was not required; no collision, fluid, thermal, valve or full beta-workflow qualification.' }, null, 2));
console.log(JSON.stringify({ parts: built.report.parts, groups: built.report.groups, seconds: built.report.seconds, tightPairs: built.report.tight.length }));
