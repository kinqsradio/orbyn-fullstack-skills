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

## Build budgets are constraints, not latency results

Use for a changed startup/build/deployment boundary with an actual workload or
service constraint. Derive the budget from the consuming project's delivery,
parse/initialization or diagnostic needs; record its owner/source, artifact types,
units, compression basis, per-file versus aggregate scope and what blocks delivery.
Reuse its bundler/build check. Do not import another product's byte limits or add
a plugin/benchmark framework solely to match this example.

Synthetic lazy export viewer: an existing build gate limits the emitted entry's
static JS/CSS dependency closure to a project-agreed budget `B`. Count each asset
once; state whether dynamic viewer assets are excluded until used. A separate gate
requires maps for the chunks the diagnostic contract covers, with a map-size bound
`M`. Not every product requires maps, and private maps need not be publicly served.
Use the target's existing access/upload policy; no upload or credential access is
implied by a local build check.

| Selected control | What it should establish |
| --- | --- |
| Legal closure just under/at the declared inclusive `B` | Correct inclusion, byte units and comparator, not an indiscriminate build failure |
| One byte over `B`, including a shared static import | Gate fails with the owned asset/reason; renaming or splitting chunks cannot hide the same startup closure |
| Missing required map or one byte over `M` | Diagnostic-artifact gate fails; a deliberately exempt non-code asset remains legitimate |
| Deferred viewer opened by the user | Required work and errors are observed through readiness; a shell becoming visible is not the viewer finishing |

These are proposed fixture controls, not executed build or speed measurements.
For a file-oriented constraint use file controls instead; do not silently substitute
startup-closure size for a provider's per-artifact limit. Code splitting/lazy import
presence or smaller bytes alone do not establish fewer fetched bytes, lower memory
or faster startup. Measure those outcomes separately with actual network/runtime
and cold/warm identity. Retain an environment-skipped profile as skipped.

## Example measurement receipt

Keep the record in the existing task output, with raw outcomes rather than a new
mandatory tracker. For a local grouping microbenchmark, record:

- Exact baseline/candidate, build and harness/input hashes; runtime/browser,
  device/CPU and any emulation/throttle; cache/worker state and configuration.
- Interval: for example, transformation invocation through completed result;
  explicitly excluded network, worker/IPC, DOM/layout and presentation costs.
- Correctness witness: equivalent expected groups/values and error behavior,
  not only a checksum/count that could match incorrect output.
- Warmups/samples and chosen distribution/statistic with units, run order,
  failures/timeouts, raw output location and observed resource measures.
- Decision and limits: planned/not run remains unverified; a local phase change
  is not an end-to-end speedup or representative low-end device result.

Match the receipt to the claim. A draw call plus next frame is a paint opportunity,
not proof pixels were presented; one module request is a request-count observation,
not proof of compilation reuse. A finite no-repaint observation has that window,
not an indefinite guarantee. Identify the actual candidate/server when a harness
reuses one. Use the existing comparison loop above for equal completed work,
negative controls, alternating runs and uncertainty; no fixed sample count or
entire-app benchmark follows from this example.
