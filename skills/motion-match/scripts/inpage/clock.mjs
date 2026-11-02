// Virtual clock, injected before any page script by capture.mjs.
//
// Seeded Math.random gives the same random values on every capture. Virtual time drives
// performance.now, Date, timers, requestAnimationFrame, requestIdleCallback, event timestamps and
// every CSS or Web Animations animation from one clock that the capturer advances by hand. A frame
// takes as long as it takes to render and the page still sees a steady rate, so frame k is always
// the state at t = k / fps. capture.mjs sends this function's source to the page, so it can use
// only browser globals.
export function installClock(CFG) {
  const w = self;
  if (w.__mmClock) return;

  if (CFG.seed !== null && CFG.seed !== undefined) {
    // mulberry32
    let s = CFG.seed >>> 0 || 1;
    Math.random = function random() {
      s = (s + 0x6d2b79f5) | 0;
      let t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  if (!CFG.virtual) { w.__mmClock = { virtual: false, seed: CFG.seed }; return; }

  const N = {
    setTimeout: w.setTimeout.bind(w), clearTimeout: w.clearTimeout.bind(w),
    raf: w.requestAnimationFrame.bind(w), caf: w.cancelAnimationFrame.bind(w),
    perfNow: performance.now.bind(performance), Date,
  };
  const tsDesc = w.Event && Object.getOwnPropertyDescriptor(w.Event.prototype, 'timeStamp');
  const tlDesc = w.AnimationTimeline && Object.getOwnPropertyDescriptor(w.AnimationTimeline.prototype, 'currentTime');

  // Time starts at a fixed instant, so Date and performance.now read the same on every capture.
  const st = {
    now: 0, dateOffset: CFG.epochMs ?? Date.UTC(2026, 0, 1), nextId: 1, seq: 0, nesting: 0,
    timers: new Map(), rafs: new Map(), tick: 1000 / (CFG.rafHz || 60), nextTick: 0,
    anims: new Map(), frames: 0, keeper: 0,
  };
  st.nextTick = st.tick;

  function call(cb, args) {
    try {
      if (typeof cb === 'string') (0, eval)(cb);
      else if (typeof cb === 'function') cb.apply(w, args);
    } catch (e) {
      N.setTimeout(() => { throw e; });
    }
  }

  // ---------- timers ----------
  function addTimer(cb, delay, args, interval) {
    const id = st.nextId++;
    const nesting = st.nesting + 1;
    let d = Math.max(0, Number(delay) || 0);
    if (nesting > 5 || interval) d = Math.max(d, nesting > 5 ? 4 : 1); // browsers clamp nested timers to 4 ms
    st.timers.set(id, { id, cb, args, delay: d, interval, due: st.now + d, seq: st.seq++, nesting });
    return id;
  }
  function fire(t) {
    if (t.interval) { t.due += t.delay; t.seq = st.seq++; } else st.timers.delete(t.id);
    const previous = st.nesting;
    st.nesting = t.nesting;
    call(t.cb, t.args);
    st.nesting = previous;
  }
  w.setTimeout = function setTimeout(cb, delay, ...args) { return addTimer(cb, delay, args, false); };
  w.setInterval = function setInterval(cb, delay, ...args) { return addTimer(cb, delay, args, true); };
  w.clearTimeout = function clearTimeout(id) { st.timers.delete(id); };
  w.clearInterval = function clearInterval(id) { st.timers.delete(id); };
  w.requestIdleCallback = function requestIdleCallback(cb, opts) {
    return addTimer(() => cb({ didTimeout: false, timeRemaining: () => 10 }), Math.min(50, (opts && opts.timeout) || 1), [], false);
  };
  w.cancelIdleCallback = function cancelIdleCallback(id) { st.timers.delete(id); };

  // ---------- animation frames ----------
  w.requestAnimationFrame = function requestAnimationFrame(cb) {
    const id = st.nextId++;
    st.rafs.set(id, cb);
    return id;
  };
  w.cancelAnimationFrame = function cancelAnimationFrame(id) { st.rafs.delete(id); };
  function runFrame(ts) {
    st.frames++;
    syncAnims();
    syncVideos();
    const due = [...st.rafs.values()];
    st.rafs.clear(); // callbacks registered while these run belong to the next frame
    for (const cb of due) call(cb, [ts]);
  }

  // ---------- CSS animations, transitions and the Web Animations API ----------
  // A running animation on the document timeline is paused when first seen and then seeked to
  // base + (virtual now - first seen) * playbackRate. Finite ones are finish()ed at their end so
  // `finished` promises and finish events still fire. A new animation counts from zero: its
  // currentTime at this point is real time since load, which differs between captures.
  function syncAnims() {
    let list;
    try { list = document.getAnimations(); } catch { return; }
    for (const a of list) {
      if (a.timeline && a.timeline !== document.timeline) continue; // scroll and view timelines follow scroll
      let rec = st.anims.get(a);
      if (!rec && a.playState !== 'running') continue; // paused or finished by the page
      if (!rec || a.playState === 'running') {
        rec = { base: rec ? a.currentTime || 0 : 0, v0: st.now };
        st.anims.set(a, rec);
        try { a.pause(); } catch { continue; }
      }
      const rate = a.playbackRate || 1;
      const t = rec.base + (st.now - rec.v0) * rate;
      let end = Infinity;
      try { end = a.effect ? a.effect.getComputedTiming().endTime : Infinity; } catch {}
      if ((rate > 0 && t >= end) || (rate < 0 && t <= 0)) { st.anims.delete(a); try { a.finish(); } catch {} continue; }
      try { a.currentTime = t; } catch {}
    }
  }
  // <video> plays on the decoder's real clock: pause each playing video when first seen and seek it
  // with the virtual clock. busy() holds the frame until the seek has landed.
  const videos = new Map();
  function syncVideos() {
    let list;
    try { list = document.querySelectorAll('video'); } catch { return; }
    for (const v of list) {
      let rec = videos.get(v);
      if (!rec) {
        if (v.paused) continue;
        rec = { base: v.currentTime, v0: st.now };
        videos.set(v, rec);
        try { v.pause(); } catch {}
      }
      let t = rec.base + ((st.now - rec.v0) / 1000) * (v.playbackRate || 1);
      if (v.loop && v.duration > 0) t %= v.duration;
      else if (v.duration > 0) t = Math.min(t, v.duration);
      if (Math.abs(v.currentTime - t) > 0.001) try { v.currentTime = t; } catch {}
    }
  }

  // While waiting for page load, keep catching new animations so they start at zero rather than
  // running on the real clock.
  function keeper() { syncAnims(); st.keeper = N.raf(keeper); }

  // ---------- time sources ----------
  performance.now = function now() { return st.now; };
  function VDate(...a) {
    if (!new.target) return new N.Date(st.dateOffset + st.now).toString();
    return a.length ? new N.Date(...a) : new N.Date(st.dateOffset + st.now);
  }
  VDate.prototype = N.Date.prototype;
  VDate.now = () => Math.round(st.dateOffset + st.now);
  VDate.parse = N.Date.parse;
  VDate.UTC = N.Date.UTC;
  Object.defineProperty(VDate.prototype, 'constructor', { value: VDate, writable: true, configurable: true });
  w.Date = VDate;
  if (tsDesc && tsDesc.get) {
    Object.defineProperty(w.Event.prototype, 'timeStamp', { configurable: true, get() { return st.now; } });
  }
  if (tlDesc && tlDesc.get) {
    Object.defineProperty(w.AnimationTimeline.prototype, 'currentTime', { configurable: true, get() { return this === document.timeline ? st.now : tlDesc.get.call(this); } });
  }

  // ---------- workers ----------
  // A worker answers on its own real clock. The capturer waits for posted-but-unanswered messages
  // before each frame, so a reply always lands on the same virtual frame. One that never answers
  // stops counting after 2 s. Workers themselves are not seeded.
  const pending = new Map();
  if (w.Worker) {
    const W = w.Worker;
    const post = W.prototype.postMessage;
    W.prototype.postMessage = function postMessage() {
      if (!this.__mmSilent) pending.set(this, N.perfNow());
      if (!this.__mmListening) {
        this.__mmListening = true;
        this.addEventListener('message', () => pending.delete(this));
        this.addEventListener('error', () => pending.delete(this));
      }
      return post.apply(this, arguments);
    };
  }
  function busy() {
    let n = 0;
    for (const v of videos.keys()) if (v.seeking) n++;
    for (const [worker, t] of pending) {
      if (N.perfNow() - t > 2000) { worker.__mmSilent = true; pending.delete(worker); } else n++;
    }
    return n;
  }

  // ---------- control ----------
  // Yielding between callbacks lets promise chains and MessageChannel schedulers keep up.
  const channel = new MessageChannel();
  const waiting = [];
  channel.port1.onmessage = () => { const resume = waiting.shift(); if (resume) resume(); };
  const yieldTask = () => new Promise((resolve) => { waiting.push(resolve); channel.port2.postMessage(0); });

  async function advance(ms) {
    N.caf(st.keeper);
    const target = st.now + Math.max(0, ms);
    for (let guard = 0; guard < 200000; guard++) {
      let next = null;
      for (const t of st.timers.values()) if (!next || t.due < next.due || (t.due === next.due && t.seq < next.seq)) next = t;
      const nextAt = Math.min(next ? next.due : Infinity, st.nextTick);
      if (nextAt > target) break;
      if (next && next.due <= st.nextTick) { st.now = Math.max(st.now, next.due); fire(next); }
      else { st.now = st.nextTick; st.nextTick += st.tick; runFrame(st.now); }
      await yieldTask();
    }
    st.now = target;
    syncAnims();
    syncVideos();
    keeper();
    return st.now;
  }

  w.__mmClock = {
    virtual: true, seed: CFG.seed, advance, busy,
    now: () => st.now,
    state: () => ({ now: st.now, timers: st.timers.size, rafs: st.rafs.size, frames: st.frames, animations: st.anims.size }),
  };
  keeper();
}

/** Page-side source for an init script. */
export const clockScript = (config) => `(${installClock.toString()})(${JSON.stringify(config)});`;
