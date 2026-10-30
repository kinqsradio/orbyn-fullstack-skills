import test from 'node:test'; import assert from 'node:assert/strict';
import { sample, poses, CYLINDERS, FIRING, R, L, rad, mod } from './model.mjs';
import { TURN } from './renderer/kit/turn.mjs';
import { readFile, writeFile } from 'node:fs/promises';
test('12 unique cylinders, six per bank, uniformly phased 720-degree firing', () => {
  assert.equal(new Set(CYLINDERS.map(c => c.id)).size, 12);
  assert.equal(CYLINDERS.filter(c => c.bank === 'A').length, 6);
  for (let i = 0; i < 12; i++) { assert.equal(mod(FIRING[(i + 1) % 12].fire - FIRING[i].fire, 720), 60); assert.ok(Math.abs(sample(FIRING[i].fire).find(c => c.id === FIRING[i].id).travel) < 1e-12); }
});
test('all rods retain length and pistons remain on their bank axes over two revolutions', () => {
  for (let a = 0; a <= 720; a += 1) for (const c of sample(a)) {
    assert.ok(Math.abs(Math.hypot(...c.piston.map((v,i) => v - c.crank[i])) - L) < 1e-12);
    assert.ok(Math.abs(c.piston[0] * Math.cos(rad(c.bankAngle)) - c.piston[2] * Math.sin(rad(c.bankAngle))) < 1e-12);
    assert.ok(c.travel >= -1e-12 && c.travel <= 1 + 1e-12);
  }
});
test('independent dead-centre/stroke controls and finite input rejection', () => {
  const c = CYLINDERS[0], tdc = c.bankAngle - c.offset;
  assert.ok(Math.abs(sample(tdc).find(v => v.id === c.id).along - (L + R)) < 1e-12);
  assert.ok(Math.abs(sample(tdc + 180).find(v => v.id === c.id).along - (L - R)) < 1e-12);
  assert.throws(() => sample(NaN)); assert.throws(() => sample(Infinity));
});
test('actual renderer rod and piston transforms match sampled joint positions', async () => {
  const data = JSON.parse(await readFile(new URL('engine-data.json', import.meta.url)));
  const transform = (p, v) => [0,1,2].map(i => p.t[i] + p.R[i*3] * v[0] + p.R[i*3+1] * v[1] + p.R[i*3+2] * v[2]);
  const close = (a,b) => assert.ok(Math.hypot(...a.map((v,i) => v-b[i])) < .0011);
  let checked = 0;
  for (let angle = 0; angle < 720; angle += 15) for (const yaw of [-135, 0, 90]) {
    const ps = TURN.poses(data.groups, poses(angle, yaw));
    const rotate = p => [p[0]*Math.cos(rad(yaw))-p[1]*Math.sin(rad(yaw)), p[0]*Math.sin(rad(yaw))+p[1]*Math.cos(rad(yaw)), p[2]];
    for (const c of sample(angle)) {
      const part = data.parts.find(p => p.name === 'rod-' + c.id), pose = ps.get('rod-' + c.id), F = part.spec.F;
      close(transform(pose, F.o), rotate(c.crank));
      close(transform(pose, F.o.map((v,i) => v + F.a[i] * part.spec.s1)), rotate(c.piston));
      const pp = data.parts.find(p => p.name === 'piston-' + c.id); close(transform(ps.get('piston-' + c.id), pp.spec.F.o), rotate(c.piston)); checked++;
    }
  }
  const bad = [...sample(45)[0].piston]; bad[0] += .05;
  assert.throws(() => close(bad, sample(45)[0].piston));
  await writeFile(new URL('test-report.json', import.meta.url), JSON.stringify({ status: 'passed', sampledModelAngles: 721, rendererJointChecks: checked, cameraYawSamples: [-135,0,90], badEndpointControlRejected: true, limits: ['finite rigid-link samples', 'not a solid-clearance or combustion model', 'browser interaction separately recorded', 'SVG-projected 3D, not GPU qualification'] }, null, 2));
});
