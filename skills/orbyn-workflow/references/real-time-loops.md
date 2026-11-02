# Real-time loops and frame budgets

Read when code runs every frame or tick: games, animation, audio, real-time UI.
Use with the [performance playbook](../playbooks/perf-issue.md).

1. Mark the hot code in its path or name, such as `update.hot.ts` or a `hot/`
   folder, so a rule and a reviewer can find it.
2. Set a frame budget before tuning: a target device and a frame rate. At 60 fps
   the whole frame has about 16.7 ms; give update, render and the rest a share.
3. Forbid per-frame allocation in marked files with a lint rule in the project's
   existing linter: no object or array literals, closures, `new`, or string
   building inside the loop.
4. Preallocate and reuse. Keep a pool for short-lived objects, write into
   existing buffers and reset instead of recreating.
5. Measure with the platform profiler, not a guess: frame-time percentiles (p50,
   p95, p99) and garbage collection pauses on the target device. A mean hides
   dropped frames.

Failing, in `particles.hot.ts`:

```ts
function update(dt: number) {
  for (const p of particles) {
    p.pos = { x: p.pos.x + p.vx * dt, y: p.pos.y + p.vy * dt }; // new object each frame
  }
}
```

Passing: mutate `p.pos.x` and `p.pos.y` in place.

The budget and the allocation rule are the project's choice. Record the device,
frame rate and measured percentiles with the change.
