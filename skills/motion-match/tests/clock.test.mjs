import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import vm from 'node:vm';
import { clockScript } from '../scripts/inpage/clock.mjs';

// An open port keeps Node alive, so close every channel the clock made.
const channels = [];
after(() => { for (const channel of channels) { channel.port1.close(); channel.port2.close(); } });
function TrackedChannel() {
  const channel = new MessageChannel();
  channels.push(channel);
  return channel;
}

/** A page-shaped global with fake animations, so the clock runs without a browser. */
function page(config, animations = []) {
  const sandbox = {
    performance: { now: () => 12345.678 },
    MessageChannel: TrackedChannel,
    setTimeout, clearTimeout,
    requestAnimationFrame: () => 1,
    cancelAnimationFrame: () => {},
    document: { getAnimations: () => animations, querySelectorAll: () => [], timeline: {} },
    console,
  };
  sandbox.self = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(clockScript(config), sandbox);
  return sandbox;
}

const randoms = (sandbox, count) => vm.runInContext(`Array.from({ length: ${count} }, () => Math.random())`, sandbox);

test('the same seed gives the same random values and another seed does not', () => {
  const a = randoms(page({ virtual: false, seed: 7 }), 5);
  const b = randoms(page({ virtual: false, seed: 7 }), 5);
  const c = randoms(page({ virtual: false, seed: 8 }), 5);
  assert.deepEqual([...a], [...b]);
  assert.notDeepEqual([...a], [...c]);
  assert.ok(a.every((value) => value >= 0 && value < 1));
});

test('without virtual time the page keeps its own clock and timers', () => {
  const sandbox = page({ virtual: false, seed: 1 });
  assert.equal(sandbox.setTimeout, setTimeout);
  assert.equal(sandbox.__mmClock.virtual, false);
});

async function schedule(seed) {
  const sandbox = page({ virtual: true, seed, rafHz: 60 });
  vm.runInContext(`
    self.log = [];
    const note = (name) => self.log.push([name, performance.now(), Math.random()]);
    setTimeout(() => note('t50'), 50);
    setTimeout(() => note('t10'), 10);
    const id = setInterval(() => { note('i30'); if (performance.now() >= 90) clearInterval(id); }, 30);
    const frame = () => { note('raf'); if (performance.now() < 40) requestAnimationFrame(frame); };
    requestAnimationFrame(frame);
    const cancelled = setTimeout(() => note('never'), 5);
    clearTimeout(cancelled);
  `, sandbox);
  await sandbox.__mmClock.advance(60);
  await sandbox.__mmClock.advance(60);
  return { log: vm.runInContext('JSON.stringify(self.log)', sandbox), sandbox };
}

test('two runs of a page produce the same events at the same virtual times', async () => {
  const first = await schedule(3);
  const second = await schedule(3);
  assert.equal(first.log, second.log);
  const log = JSON.parse(first.log);
  assert.deepEqual(log.filter(([name]) => name !== 'raf').map(([name, t]) => [name, Math.round(t)]), [['t10', 10], ['i30', 30], ['t50', 50], ['i30', 60], ['i30', 90]]);
  assert.ok(!log.some(([name]) => name === 'never'), 'a cleared timer does not fire');
  assert.deepEqual(log.filter(([name]) => name === 'raf').map(([, t]) => Math.round(t)), [17, 33, 50]);
});

test('time does not move until the capturer advances it, and starts at the same instant', async () => {
  const sandbox = page({ virtual: true, seed: 1 });
  const read = () => vm.runInContext('[performance.now(), Date.now(), new Date().getTime()]', sandbox);
  assert.deepEqual([...read()], [0, Date.UTC(2026, 0, 1), Date.UTC(2026, 0, 1)]);
  await new Promise((resolve) => { setTimeout(resolve, 15); });
  assert.equal(read()[0], 0);
  assert.equal(await sandbox.__mmClock.advance(250), 250);
  assert.deepEqual([...read()], [250, Date.UTC(2026, 0, 1) + 250, Date.UTC(2026, 0, 1) + 250]);
});

function fakeAnimation(realCurrentTime, end = 1000) {
  return {
    playState: 'running', currentTime: realCurrentTime, playbackRate: 1,
    effect: { getComputedTiming: () => ({ endTime: end }) },
    timeline: undefined,
    pause() { this.playState = 'paused'; },
    finish() { this.playState = 'finished'; this.finished = true; },
  };
}

test('a new animation counts from zero, whatever real time passed before it was seen', async () => {
  const quick = fakeAnimation(3);
  const slow = fakeAnimation(47);
  const sandboxes = [page({ virtual: true, seed: 1 }, [quick]), page({ virtual: true, seed: 1 }, [slow])];
  for (const sandbox of sandboxes) await sandbox.__mmClock.advance(400);
  assert.equal(quick.currentTime, 400);
  assert.equal(slow.currentTime, 400);
  assert.equal(quick.playState, 'paused');
});

test('a finite animation is finished at its end so its events fire', async () => {
  const animation = fakeAnimation(0, 300);
  const sandbox = page({ virtual: true, seed: 1 }, [animation]);
  await sandbox.__mmClock.advance(299);
  assert.equal(animation.finished, undefined);
  await sandbox.__mmClock.advance(2);
  assert.equal(animation.finished, true);
});

test('an animation the page paused is left alone', async () => {
  const animation = fakeAnimation(120);
  animation.playState = 'paused';
  const sandbox = page({ virtual: true, seed: 1 }, [animation]);
  await sandbox.__mmClock.advance(100);
  assert.equal(animation.currentTime, 120);
});

test('the rAF rate follows rafHz', async () => {
  const sandbox = page({ virtual: true, seed: 1, rafHz: 10 });
  vm.runInContext('self.ticks = []; const f = (t) => { self.ticks.push(Math.round(t)); requestAnimationFrame(f); }; requestAnimationFrame(f);', sandbox);
  await sandbox.__mmClock.advance(350);
  assert.deepEqual([...sandbox.ticks], [100, 200, 300]);
});
