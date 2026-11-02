# Explain the number

Before you measure, and before you trust, report or act on a number (a speedup, regression, throughput, latency or eval score), find what limits it and rule out that it measured something other than the work.

## Decision in practice

What would this number have to be for a decision to change, and why is it not twice as good?

A synthetic export change reports "30% faster". The profile shows one core pinned in JSON parsing and the changed step is 10% of the run. Removing a 10% piece entirely saves at most about 11%, so 30% measured something else, perhaps a warm cache on one side. Until the limiter and the arithmetic agree with the number, the verdict is inconclusive.

## Apply and hand off

Before running:

- Write the claim in the words you would ship ("export p50 drops 30% on the 60k-row set") and the result that would change the decision. Note the noise floor; stop if run-to-run spread exceeds the effect.
- Read the measurement script: what it times, counts and ignores. Check `uptime` and the core count. On a busy machine, find the load; if you cannot stop it, interleave the sides and say so.

Then answer each with evidence from a run, not from reading code:

1. **Limiter.** Name the core, lock, disk, network or load generator that bounds the result, from a profile or system counters taken in a run you do not report. If a change did not move the number, the limiter says why.
2. **Tuned.** Every side runs as production runs it: release build, flags, pools, cache state, same versions and data. A limiter that is a setting (a commit per row, a debug build, a missing index) means an untuned side. Tune and remeasure, or do not pick a winner. When the user is choosing what to adopt, they adopt the option, not today's settings.
3. **Limits.** Do the arithmetic against bandwidth, cores and the time the changed piece took. A result past a limit measured a cache, a no-op or a bug.
4. **Errors.** Count failures and rejections, and check outputs are correct, not just present. Rejections are fast, timeouts are slow.
5. **Repeatable.** At least five runs per side, alternating A, B, A, B. Report median and range; a gap inside the range is no difference.
6. **Relevant.** Put the micro result next to the end-to-end path a user waits on, with realistic size and concurrency.
7. **Happened.** The work ran inside the timed region: rows written, bytes read, results used. Lazy generators, unawaited promises and timeouts yield numbers for work that never ran.

A quick ballpark the user asked for may be one run; still check 4 and 7 and say it was one run. A choice between options is never a ballpark.

Report the verdict first (faster, slower, no measurable difference or inconclusive), then the number with unit, run count, range and limiter: "p50 41 ms to 33 ms, median of 7 runs per side, range 32 to 35 ms after, bound by JSON parsing on one core." Call it inconclusive when no limiter is named, a side ran untuned, or 4 or 7 went unchecked, and name the gap. Keep a PR body to one number; runs and evidence go in a linked artifact. For an eval score ask the same of the trials: did every run do the task, does the gap hold across trials and models, and does the scenario matter. This is distinct from [prove it works](prove-it-works.md), which checks that an output is real. The [performance playbook](../../playbooks/perf-issue.md) owns the measurement loop.

## Source and license

Adapted from Lauren Tan's pstack [explain the number](https://github.com/cursor/plugins/blob/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/principle-explain-the-number/SKILL.md)
and [benchmark checklist](https://github.com/cursor/plugins/blob/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/benchmark-checklist/SKILL.md),
revision `ae5650febf4320793844c12c4adaa937f417f8da`.
Orbyn adaptations and worked examples retain the [original MIT notice](LICENSE.txt).
