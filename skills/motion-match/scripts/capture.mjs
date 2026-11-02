// Capture a page the same way every time: frames on a virtual clock, a per-frame track of chosen
// elements, and an inspection record. Reads the --url page. Writes only inside --out. Runs an
// existing browser through an existing playwright-core; installs nothing.
import { copyFileSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { EXIT, BlockedError, RIGHTS, UsageError, assertIgnored, child, isMain, loadChromium, oneOf, pad, parseArgs, parseRect, parseSize, pathInside, prepareOutput, requireOptions, runCli, writeJson } from './lib.mjs';
import { cropImage, encodePng, readPng } from './png.mjs';
import { clockScript } from './inpage/clock.mjs';
import { cleanSamples, inspectArgument, inspectPage, motionOnly } from './inpage/inspect.mjs';

const HELP = `
capture.mjs: film a page so two captures can be compared.

  node capture.mjs --url <url|file.html> --out <dir> --rights <own|licensed|third-party> [options]

Rights (required, read references/capture.md first)
  own, licensed       any fidelity
  third-party         motion measurement only: --out must be ignored by Git, --pre-js is refused,
                      and inspect.json keeps timing, easing and distance only

Browser (nothing is installed or downloaded)
  --playwright PATH   playwright-core index.mjs, or PLAYWRIGHT_CORE
  --chrome PATH       existing browser, or CHROME_PATH

Window
  --viewport WxH      default 1440x900     --scale N             default 1
  --color-scheme S    light | dark         --reduced-motion S    no-preference | reduce

What to look at
  --selector CSS      element to crop frames to     --pad PX     margin around it, default 0
  --clip x,y,w,h      explicit crop in CSS px       --track "CSS, CSS"  elements sampled every frame

How to start the motion
  --trigger T         load (default) | scroll | hover | leave | move | drag | click | none
  --target CSS        element to hover, click or move over (default --selector)
  --hover-at FX,FY    pointer position as fractions of --target, default 0.5,0.5
  --pre-hover CSS     hover this first, for --pre-hover-ms (default 1500)
  --leave-to X,Y      where the pointer goes for leave, default top centre
  --path "FX,FY;..."  move and drag points inside --target   --path-ms MS  per leg, default 400
  --scroll-to PX|CSS  scroll goal   --scroll-ms MS  default 600   --scroll-steps N  default 12
  --wait-before MS    settle before the trigger, default 800
  --pre-js FILE       script to run before the trigger; refused for third-party pages
  --duration MS       length after the trigger, default 3000    --pre-roll MS  default 200

Clock
  --clock C           virtual (default) writes exact frames; real writes track.json only
  --fps N             frames per second, default 25     --raf-hz N    page frame rate, default 60
  --seed N            seeds Math.random, default 1      --network-wait MS  default 3000

Output
  --root DIR          folder --out must stay inside, default the working directory
  --replace           replace an earlier capture in --out
  --timeout MS        navigation limit, default 60000

Writes capture.json, frames.json, frames/NNNN.png, inspect.json and track.json inside --out.
Exits 0 when done, 2 on bad usage, 3 when a rights or access limit stops the run.
`;

const SCHEMA = {
  url: 'string', out: 'string', rights: 'string', playwright: 'string', chrome: 'string', viewport: 'string',
  scale: { type: 'number', min: 0.1, max: 4 }, 'color-scheme': 'string', 'reduced-motion': 'string', selector: 'string',
  pad: { type: 'number', min: 0 }, clip: 'string', track: 'string', trigger: 'string', target: 'string', 'hover-at': 'string',
  'pre-hover': 'string', 'pre-hover-ms': { type: 'number', min: 0 }, 'leave-to': 'string', path: 'string',
  'path-ms': { type: 'number', min: 1 }, 'scroll-to': 'string', 'scroll-ms': { type: 'number', min: 1 },
  'scroll-steps': { type: 'number', min: 1, integer: true }, 'wait-before': { type: 'number', min: 0 }, 'pre-js': 'string',
  duration: { type: 'number', min: 1, max: 600000 }, 'pre-roll': { type: 'number', min: 0 }, clock: 'string',
  fps: { type: 'number', min: 1, max: 240 }, 'raf-hz': { type: 'number', min: 1, max: 240 }, seed: { type: 'number', min: 0, integer: true },
  'network-wait': { type: 'number', min: 0 }, root: 'string', replace: 'flag', timeout: { type: 'number', min: 1 },
};
const TRIGGERS = ['load', 'scroll', 'hover', 'leave', 'move', 'drag', 'click', 'none'];
const NEEDS_TARGET = ['hover', 'click', 'move', 'drag'];

export function pageUrl(value) {
  const text = String(value);
  let url;
  try { url = /^[a-z][a-z0-9+.-]+:/i.test(text) ? new URL(text) : pathToFileURL(resolve(text)); } catch { throw new UsageError(`Bad address "${text}"`); }
  if (!['http:', 'https:', 'file:'].includes(url.protocol)) throw new UsageError(`Unsupported address "${url.protocol}": use http, https or a local file`);
  if (url.username || url.password) throw new UsageError('Addresses with a user name or password are refused: login walls stay closed');
  return url;
}

const fractions = (name, value, fallback) => {
  const parts = String(value ?? fallback).split(',').map(Number);
  if (parts.length !== 2 || parts.some((part) => !Number.isFinite(part))) throw new UsageError(`--${name} expects two numbers`);
  return parts;
};

export function captureOptions(argv) {
  const a = parseArgs(argv, SCHEMA);
  if (a.help) return { help: true };
  requireOptions(a, ['url', 'out', 'rights']);
  const rights = oneOf('rights', a.rights, RIGHTS);
  const trigger = oneOf('trigger', a.trigger ?? 'load', TRIGGERS);
  const clock = oneOf('clock', a.clock ?? 'virtual', ['virtual', 'real']);
  const root = a.root ?? '.';
  const url = pageUrl(a.url);
  const selector = a.selector;
  const target = a.target ?? selector;
  if (NEEDS_TARGET.includes(trigger) && !target) throw new UsageError(`--trigger ${trigger} needs --target or --selector`);
  if (trigger === 'scroll' && !a['scroll-to'] && !selector) throw new UsageError('--trigger scroll needs --scroll-to or --selector');
  if (a.clip && selector) throw new UsageError('Pass --clip or --selector for the crop, not both');
  const viewport = parseSize(a.viewport, { width: 1440, height: 900 });
  const out = pathInside(a.out, root, 'Output');
  if (rights === 'third-party') {
    if (a['pre-js']) throw new BlockedError('--pre-js is refused for third-party pages: capture only what a normal visitor sees');
    assertIgnored(out);
  }
  if (rights !== 'third-party' && !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) {
    console.error(`Note: --rights ${rights} on ${url.hostname} is your statement that you own or licensed it, and it is not checked. Use third-party if you are unsure.`);
  }
  return {
    url, out, rights, trigger, clock, selector, target, viewport,
    playwright: a.playwright, chrome: a.chrome, replace: !!a.replace,
    scale: a.scale ?? 1, colorScheme: a['color-scheme'] ? oneOf('color-scheme', a['color-scheme'], ['light', 'dark']) : undefined,
    reducedMotion: oneOf('reduced-motion', a['reduced-motion'] ?? 'no-preference', ['no-preference', 'reduce']),
    pad: a.pad ?? 0, clip: parseRect(a.clip),
    track: (a.track ?? selector ?? '').split(',').map((item) => item.trim()).filter(Boolean),
    hoverAt: fractions('hover-at', a['hover-at'], '0.5,0.5'),
    preHover: a['pre-hover'], preHoverMs: a['pre-hover-ms'] ?? 1500,
    leaveTo: a['leave-to'] ? fractions('leave-to', a['leave-to']) : [viewport.width / 2, 8],
    path: String(a.path ?? '0.5,0.5').split(';').map((point) => fractions('path', point)),
    pathMs: a['path-ms'] ?? 400, scrollTo: a['scroll-to'], scrollMs: a['scroll-ms'] ?? 600, scrollSteps: a['scroll-steps'] ?? 12,
    waitBefore: a['wait-before'] ?? 800, preJs: a['pre-js'] ? pathInside(a['pre-js'], root, 'Script') : undefined,
    duration: a.duration ?? 3000, preRoll: a['pre-roll'] ?? 200, fps: a.fps ?? 25, rafHz: a['raf-hz'] ?? 60,
    seed: a.seed ?? 1, networkWait: a['network-wait'] ?? 3000, timeout: a.timeout ?? 60000,
  };
}

// Installed before any page script, so motion that starts at load is caught.
const trackerScript = (selectors) => `(() => {
  const selectors = ${JSON.stringify(selectors)};
  window.__mm = { samples: [], running: true };
  const sample = () => {
    if (!window.__mm.running) return;
    const els = {};
    for (const selector of selectors) {
      let el = null;
      try { el = document.querySelector(selector); } catch {}
      if (!el) { els[selector] = null; continue; }
      const r = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      els[selector] = { x: +r.x.toFixed(2), y: +r.y.toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2), opacity: +(+style.opacity).toFixed(3), transform: style.transform };
    }
    window.__mm.samples.push({ t: performance.now(), scrollY: window.scrollY, els });
    requestAnimationFrame(sample);
  };
  requestAnimationFrame(sample);
})();`;

const sameSite = (a, b) => a.protocol === b.protocol && a.host === b.host;

function topLevel(request) {
  if (!request.isNavigationRequest()) return false;
  // frame() throws for a navigation issued before its frame exists, which is always the top frame.
  try { return !request.frame().parentFrame(); } catch { return true; }
}

const barePath = (url) => url.pathname.replace(/\/+$/, '') || '/';

/** Why a page looks like a sign-in wall, or null. A soft wall on a 200 page is not caught here. */
export function wallReason({ requested, final, passwordFields }) {
  if (passwordFields > 0) return 'it shows a password field';
  return barePath(final) === barePath(requested) ? null : `it moved to ${final.pathname}`;
}

async function assertNoWall(page, o) {
  if (o.rights !== 'third-party') return;
  const passwordFields = await page.locator('input[type="password"]:visible').count();
  const reason = wallReason({ requested: o.url, final: new URL(page.url()), passwordFields });
  if (reason) throw new BlockedError(`Stopped: ${reason}. A login wall, paywall or bot check stays closed: ask the user for a screen recording`);
}

function assertOpen(response, page, url) {
  if (response && response.status() >= 400) {
    throw new BlockedError(`The page answered HTTP ${response.status()}. A login wall, paywall or bot check stays closed: ask the user for a screen recording`);
  }
  if (!sameSite(new URL(page.url()), url)) {
    throw new BlockedError(`The page moved to ${new URL(page.url()).host}. Pass that address only if it is the one you were asked to capture; a sign-in redirect stays closed`);
  }
}

async function pointAt(page, selector, fx, fy) {
  const box = await page.locator(selector).first().boundingBox();
  if (!box) throw new Error(`Not visible: ${selector}`);
  return { x: box.x + box.width * fx, y: box.y + box.height * fy };
}

async function scrollGoal(page, o) {
  if (o.scrollTo !== undefined && /^\d+$/.test(o.scrollTo)) return Number(o.scrollTo);
  const selector = o.scrollTo ?? o.selector;
  return page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) throw new Error(`Not found: ${s}`);
    return window.scrollY + el.getBoundingClientRect().top - innerHeight * 0.25;
  }, selector);
}

/** The trigger as input events at times after t = 0, so both clocks replay the same steps. */
async function planTrigger(page, o) {
  const tick = 1000 / o.rafHz;
  const glide = (points) => {
    const actions = [];
    const steps = Math.max(1, Math.round(o.pathMs / tick));
    for (let i = 1; i < points.length; i++) {
      for (let k = 1; k <= steps; k++) {
        const f = k / steps;
        const [a, b] = [points[i - 1], points[i]];
        actions.push({ at: (i - 1 + f) * o.pathMs, run: () => page.mouse.move(a.x + (b.x - a.x) * f, a.y + (b.y - a.y) * f) });
      }
    }
    return actions;
  };
  switch (o.trigger) {
    case 'load': case 'none': return [];
    case 'hover': { const p = await pointAt(page, o.target, ...o.hoverAt); return [{ at: 0, run: () => page.mouse.move(p.x, p.y) }]; }
    case 'leave': return [{ at: 0, run: () => page.mouse.move(o.leaveTo[0], o.leaveTo[1]) }];
    case 'click': return [{ at: 0, run: () => page.click(o.target, { timeout: 10000, noWaitAfter: true }) }];
    case 'move': case 'drag': {
      const points = [];
      for (const [fx, fy] of o.path) points.push(await pointAt(page, o.target, fx, fy));
      const actions = glide(points);
      const lastAt = actions.length ? actions[actions.length - 1].at : 0;
      actions.unshift({ at: 0, run: async () => { await page.mouse.move(points[0].x, points[0].y); if (o.trigger === 'drag') await page.mouse.down(); } });
      if (o.trigger === 'drag') actions.push({ at: lastAt, run: () => page.mouse.up() });
      return actions;
    }
    case 'scroll': {
      const from = await page.evaluate(() => window.scrollY);
      const delta = ((await scrollGoal(page, o)) - from) / o.scrollSteps;
      const actions = [{ at: 0, run: () => page.mouse.move(o.viewport.width / 2, o.viewport.height / 2) }];
      for (let i = 0; i < o.scrollSteps; i++) actions.push({ at: (i * o.scrollMs) / o.scrollSteps, run: () => page.mouse.wheel(0, delta) });
      return actions;
    }
    default: throw new UsageError(`Unknown trigger ${o.trigger}`);
  }
}

async function clipOf(page, o) {
  if (o.clip) return o.clip;
  if (!o.selector) return undefined;
  const r = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    const box = el.getBoundingClientRect();
    return { x: box.x, y: box.y, width: box.width, height: box.height };
  }, o.selector);
  if (!r) throw new Error(`Selector not found: ${o.selector}`);
  return {
    x: Math.max(0, Math.floor(r.x - o.pad)), y: Math.max(0, Math.floor(r.y - o.pad)),
    width: Math.ceil(Math.min(o.viewport.width - r.x + o.pad, r.width + 2 * o.pad)),
    height: Math.ceil(Math.min(o.viewport.height - r.y + o.pad, r.height + 2 * o.pad)),
  };
}

function networkWatcher(page, o) {
  const inflight = new Map();
  page.on('request', (request) => inflight.set(request, Date.now()));
  page.on('requestfinished', (request) => inflight.delete(request));
  page.on('requestfailed', (request) => inflight.delete(request));
  return async function networkQuiet() {
    const until = Date.now() + o.networkWait;
    while (Date.now() < until) {
      // Long polls and streams stop counting after 10 s.
      const busy = [...inflight.values()].some((started) => Date.now() - started < 10000)
        || (o.clock === 'virtual' && (await page.evaluate(() => window.__mmClock?.busy?.() ?? 0).catch(() => 0)) > 0);
      if (!busy) return;
      await new Promise((resolve) => { setTimeout(resolve, 10); });
    }
  };
}

async function prepareTrigger(page, o, settle) {
  await settle(o.waitBefore);
  if (o.preJs) await page.evaluate(readFileSync(o.preJs, 'utf8'));
  if (o.selector && o.trigger !== 'scroll') {
    const found = await page.$(o.selector);
    if (!found) throw new Error(`Selector not found: ${o.selector}`);
    await found.scrollIntoViewIfNeeded();
    await settle(300);
  } else if (o.trigger === 'scroll' && o.selector) {
    // Start just below the fold, so the element enters the viewport during the scroll.
    await page.evaluate((s) => { const el = document.querySelector(s); if (el) window.scrollTo(0, Math.max(0, window.scrollY + el.getBoundingClientRect().top - innerHeight - 20)); }, o.selector);
    await settle(300);
  }
  if (o.preHover) {
    const point = await pointAt(page, o.preHover, ...o.hoverAt);
    await page.mouse.move(point.x, point.y);
    await settle(o.preHoverMs);
  }
}

async function runVirtual(page, o, framesTemp) {
  const quiet = networkWatcher(page, o);
  const advanceBy = (ms) => page.evaluate((x) => window.__mmClock.advance(x), ms);
  const settle = async (ms) => {
    for (let left = ms; left > 0; left -= 100) { await advanceBy(Math.min(100, left)); await quiet(); }
  };
  assertOpen(await page.goto(o.url.href, { waitUntil: 'load', timeout: o.timeout }), page, o.url);
  await assertNoWall(page, o);
  await quiet();
  let pre = 0;
  if (o.trigger !== 'load') { await prepareTrigger(page, o, settle); pre = o.preRoll; }
  const start = await page.evaluate(() => window.__mmClock.now());
  const triggerAt = start + pre;
  const plan = (await planTrigger(page, o)).map((step) => ({ ...step, at: triggerAt + step.at })).sort((a, b) => a.at - b.at);
  const frameMs = 1000 / o.fps;
  const total = Math.round((pre + o.duration) / frameMs) + 1;
  let now = start;
  const advanceTo = async (t) => { if (t > now + 1e-6) now = await advanceBy(t - now); };
  for (let k = 0; k < total; k++) {
    const frameAt = start + k * frameMs;
    while (plan.length && plan[0].at <= frameAt) {
      const step = plan.shift();
      await advanceTo(step.at);
      await step.run();
    }
    await advanceTo(frameAt);
    await quiet();
    await page.screenshot({ path: child(framesTemp, `${pad(k + 1)}.png`), animations: 'allow', caret: 'initial' });
  }
  for (const step of plan) { await advanceTo(step.at); await step.run(); } // for example a drag release after the window
  return { trackZero: triggerAt, total, pre };
}

async function runReal(page, o) {
  const load = o.trigger === 'load';
  assertOpen(await page.goto(o.url.href, { waitUntil: load ? 'commit' : 'load', timeout: o.timeout }), page, o.url);
  if (load) { await page.waitForTimeout(o.duration); await assertNoWall(page, o); return { trackZero: null }; }
  await assertNoWall(page, o);
  await prepareTrigger(page, o, (ms) => page.waitForTimeout(ms));
  const plan = (await planTrigger(page, o)).sort((a, b) => a.at - b.at);
  const trackZero = await page.evaluate(() => performance.now());
  const started = Date.now();
  for (const step of plan) {
    await page.waitForTimeout(Math.max(0, step.at - (Date.now() - started)));
    await step.run();
  }
  await page.waitForTimeout(Math.max(0, o.duration - (Date.now() - started)));
  return { trackZero };
}

function writeFrames(framesTemp, framesDir, clip, scale) {
  mkdirSync(framesDir, { recursive: true });
  for (const name of readdirSync(framesTemp).sort()) {
    if (!clip) { copyFileSync(join(framesTemp, name), child(framesDir, name)); continue; }
    const image = readPng(join(framesTemp, name));
    const x = Math.round(clip.x * scale);
    const y = Math.round(clip.y * scale);
    const box = { x, y, width: Math.min(Math.round(clip.width * scale), image.width - x), height: Math.min(Math.round(clip.height * scale), image.height - y) };
    writeFileSync(child(framesDir, name), encodePng(cropImage(image, box)));
  }
}

async function capture(o) {
  const { chromium, executablePath } = await loadChromium({ playwright: o.playwright, chrome: o.chrome });
  prepareOutput(o.out, { marker: 'capture.json', replace: o.replace });
  const framesTemp = child(o.out, '.frames-temp');
  if (o.clock === 'virtual') mkdirSync(framesTemp, { recursive: true });
  const virtual = o.clock === 'virtual';
  // Wheel scrolling animates on the compositor's real clock unless smooth scrolling is off.
  const browser = await chromium.launch({ headless: true, executablePath, args: virtual ? ['--disable-smooth-scrolling'] : [] });
  try {
    const context = await browser.newContext({ viewport: o.viewport, deviceScaleFactor: o.scale, colorScheme: o.colorScheme, reducedMotion: o.reducedMotion, serviceWorkers: 'block' });
    await context.addInitScript(clockScript({ virtual, seed: o.seed, rafHz: o.rafHz }));
    if (o.track.length) await context.addInitScript(trackerScript(o.track));
    // The top frame stays on the requested site, so a sign-in redirect cannot be followed.
    await context.route('**/*', (route) => {
      const request = route.request();
      return topLevel(request) && !sameSite(new URL(request.url()), o.url) ? route.abort('blockedbyclient') : route.continue();
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', () => pageErrors.push(1));
    const run = virtual ? await runVirtual(page, o, framesTemp) : await runReal(page, o);
    const clip = await clipOf(page, o);
    const samples = o.track.length ? cleanSamples(await page.evaluate(() => { window.__mm.running = false; return window.__mm.samples; }), o.track) : [];
    const raw = await page.evaluate(inspectPage, inspectArgument(o.selector));
    if (virtual) {
      writeFrames(framesTemp, join(o.out, 'frames'), clip, o.scale);
      writeJson(child(o.out, 'frames.json'), {
        fps: o.fps, count: run.total, preRollMs: run.pre, triggerFrame: Math.round((run.pre / 1000) * o.fps), clip, viewport: o.viewport, scale: o.scale, clock: o.clock, seed: o.seed, rafHz: o.rafHz, rights: o.rights,
        note: 'frame i (0-based) is the page state at t = i/fps seconds, with t = 0 at pre-roll before the trigger',
      });
    }
    const zero = run.trackZero ?? samples[0]?.t ?? 0;
    if (o.track.length) {
      writeJson(child(o.out, 'track.json'), {
        selectors: o.track, rights: o.rights, note: 't in ms, 0 = trigger; negative samples are before it',
        samples: samples.map((sample) => ({ ...sample, t: +(sample.t - zero).toFixed(1) })),
      });
    }
    const inspection = o.rights === 'third-party' ? motionOnly(raw) : raw;
    writeJson(child(o.out, 'inspect.json'), inspection);
    // Written last: its presence marks a finished capture.
    writeJson(child(o.out, 'capture.json'), {
      url: o.url.href, rights: o.rights, viewport: o.viewport, scale: o.scale, fps: o.fps, trigger: o.trigger, target: o.target, selector: o.selector, clip,
      duration: o.duration, preRoll: o.preRoll, waitBefore: o.waitBefore, scrollTo: o.scrollTo, scrollMs: o.scrollMs, scrollSteps: o.scrollSteps,
      colorScheme: o.colorScheme, reducedMotion: o.reducedMotion, track: o.track, clock: o.clock, seed: o.seed, rafHz: o.rafHz, pageErrors: pageErrors.length,
    });
    console.log(JSON.stringify({ out: o.out, rights: o.rights, frames: run.total ?? 0, clock: o.clock, clip, trackSamples: samples.length, animations: inspection.animations.length, pageErrors: pageErrors.length }, null, 2));
  } finally {
    await browser.close();
    rmSync(framesTemp, { recursive: true, force: true });
  }
}

async function main() {
  const options = captureOptions(process.argv.slice(2));
  if (options.help) { console.log(HELP.trim()); return EXIT.ok; }
  await capture(options);
  return EXIT.ok;
}

if (isMain(import.meta.url)) runCli(main);
