# Performance

The lead pins the workload and baseline, owns the interpretation and uses the
parent [workflow](../SKILL.md) for substantial diagnosis and implementation.
Write the throughput checkpoint, delegate bounded investigation of expensive
phases, then assign the supported optimization to an Engineer with owned files.
Children investigate or implement their own assigned slice directly.

Review the diff and perform authorized measurement of equivalent completed work.
Retain output quality, authority and coverage. Label cold/warm runs and unmeasured
costs. Smaller output alone does not prove lower tokens or faster execution.
Missing baseline or runtime access remains an evidence gap, not an assumed gain.

Before a comparative claim, inspect what the harness actually times and counts.
Confirm the intended work completes inside that interval, validate its result and
count errors, rejected requests, retries and timeouts. Match relevant builds,
versions, data, concurrency and configuration across candidates; label deliberate
differences. Profile separately to identify the limiting resource without mixing
instrumentation overhead into the reported timing.

Repeat and alternate comparable runs when the claim needs it. Report units, the
chosen statistic, run count and variation; one observed run is a preliminary
measurement, and a difference within noise is inconclusive. Relate a helper's
speedup to its share of the user-visible path rather than claiming the whole flow
improved by that percentage. Preserve the harness, revision and raw outcomes so
another agent can assess the same claim.

## Sustained optimization

Use this loop only for requested sustained optimization, not every known defect.
Before expensive runs, state the decision-changing result, measured noise floor,
correctness/quality floors, workload, resource/time budget and stopping predicate.
Contrast known slower/faster, empty and erroneous work to establish harness
sensitivity. Freeze harness, input and baseline identities before candidate trials;
a harness change is a new experiment, not an implementation speedup.

Profile the limiter, then choose one falsifiable hypothesis. Prefer removing,
reusing, reducing or deferring unnecessary work before concurrency or micro-tuning.
Measure equivalent completed work and errors through the frozen interval, alternate
comparable trials and preserve every reject. Keep a candidate only when correctness
and decision thresholds pass; revert only its owned unsuccessful diff, preserving
unrelated work. Checkpoint accepted units only within delivery authority.

For an adoption comparison, tune each viable option to production-appropriate
settings or explain an untuned limiter. An as-shipped benchmark is legitimate
when labeled, but cannot silently become a universal winner. Check physical and
end-to-end plausibility: a phase consuming 10% of elapsed time cannot by elimination
alone save 50% of the same total. Do not invent hardware bandwidth. A zero-work
or error-fast path is not a gain. On plateau, use evidence to rank a different
mechanism or stop at the declared budget with an inconclusive/blocked result;
no arbitrary minimum iteration count, relaxed target or unlimited hillclimb.

For ordinary UI or RN motion, read the [motion performance method](../../orbyn-ui-design/references/animation-performance.md). Compare the same completed interaction under the same workload, preserving input/layout and runtime identity; screenshots alone cannot establish speed.
