// Original educational 60-degree V12. Ideal rigid links; arbitrary teaching dimensions.
export const R = .4, L = 1.6, BANK = 30, PITCH = .95;
export const mod = (x, n) => ((x % n) + n) % n;
export const rad = x => x * Math.PI / 180;
const throws = [0, 120, 240, 240, 120, 0];
const used = new Map();
export const CYLINDERS = ['A', 'B'].flatMap((bank, b) => throws.map((offset, i) => {
  const bankAngle = b ? BANK : -BANK;
  const tdc = mod(bankAngle - offset, 360);
  const count = used.get(tdc) ?? 0; used.set(tdc, count + 1);
  return { id: bank + (i + 1), bank, station: (i - 2.5) * PITCH + (b ? .10 : -.10), bankAngle, offset, fire: tdc + count * 360 };
}));
export const FIRING = [...CYLINDERS].sort((a, b) => a.fire - b.fire);
export function sample(angle) {
  if (!Number.isFinite(angle)) throw Error('Finite crank angle required');
  return CYLINDERS.map(c => {
    const a = rad(angle + c.offset), b = rad(c.bankAngle), relative = a - b;
    const along = R * Math.cos(relative) + Math.sqrt(L * L - (R * Math.sin(relative)) ** 2);
    const crank = [R * Math.sin(a), c.station, R * Math.cos(a)];
    const piston = [along * Math.sin(b), c.station, along * Math.cos(b)];
    const cycle = mod(angle - c.fire, 720);
    const phase = ['Power', 'Exhaust', 'Intake', 'Compression'][Math.floor(cycle / 180)];
    return { ...c, crank, piston, along, cycle, phase, travel: (L + R - along) / (2 * R), rodAngle: Math.atan2(piston[0] - crank[0], piston[2] - crank[2]) * 180 / Math.PI };
  });
}
export function poses(angle, yaw = 0) {
  const values = { view: yaw, crank: mod(angle, 360) };
  for (const c of sample(angle)) {
    values['piston-' + c.id] = { t: [c.piston[0], 0, c.piston[2]] };
    values['rod-' + c.id] = { axis: [0, 1, 0], angle: c.rodAngle, t: [c.crank[0], 0, c.crank[2]] };
  }
  return values;
}
