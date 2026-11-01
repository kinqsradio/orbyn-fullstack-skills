---
name: rea-analysis-optimization
description: "Optimize a measured REA analysis bottleneck while preserving evidence and resource ownership; scoped to REA."
---

# Optimize a completed REA investigation

Use this to reduce REA analysis cost, not ordinary application performance or
test-suite speed. Route suite costs to [REA CI audit](../rea-ci-tests-audit/SKILL.md).
Read the consuming checkout's instructions and current implementation; use
[how](../how/SKILL.md) to trace unfamiliar source.

This local procedure needs no upstream webpage. It does not authorize target
execution, tests or edits outside the task.

## Define the task and oracle

State the analyst question and the facts needed to finish it. Pin source revision,
artifact digest, provider/tool versions, architecture/options, detail and allowed
workload. When measurement is authorized, include a representative large input and
a small/empty case. Preserve an unchanged baseline in an isolated checkout.

Choose a correctness oracle independent of the proposed optimization: known
fixture facts, independently mapped bytes or a verified producer interpretation.
Two adapters sharing the same decoder do not count as independent. Preserve
same-address alternatives, unresolved relationships, coverage and evidence IDs.

If source, artifacts or runtime are unavailable offline, produce a bounded
measurement plan and mark measurements unrun; do not invent before/after numbers.

To compare with the [local-tool path](../reverse-engineer-anything/references/local-tools.md),
answer the same artifact question at comparable coverage. Count tool startup, source
selection, evidence retention and recovery; one raw command against a complete
engine workflow is not a comparison. Treat a small upstream benchmark on another
engine/model/version as a hypothesis for this task, not this installation's result.

## Find the owning cost

Trace the public CLI/MCP path through admission, producer work, decoding, lookup,
projection, serialization, retention and cleanup. Measure phases relevant to the
completed task, including extra discovery/query calls. Check CPU and peak memory
too: a smaller reply can leave both unchanged. Fix incorrect or missing facts before
comparing performance across different coverage.

## Change the owner

- Prefer eliminating repeated interpretation or scanning at its owner.
- Push selection to the earliest capable boundary and reuse validated immutable
  facts when appropriate.
- Avoid a new cache/index without a demonstrated cost. For reuse, define key, owner,
  invalidation, retained size and lifetime. Include result-affecting bytes,
  engine/schema/options and mapping; revalidate live state before calling it current.
  Partial, cancelled or transient failures need their own retry policy.
- Preserve independent caller cancellation and one shared producer's ownership. A
  cancelled waiter must not corrupt peers.
- Bound process-family memory and retained state, not just the parent's heap. Keep
  capacity charged until work and cleanup settle. Report a guard-stopped
  investigation as incomplete.

Use the shared [evidence and recovery method](../reverse-engineer-anything/references/evidence-and-recovery.md)
when retaining partial observations or unresolved resources.

## Compare and stop

When authorized, compare equivalent completed tasks on the baseline and candidate.
Separate fresh sessions, warm caches and OS cache conditions. Record total and
phase time, CPU, peak process-family memory with accounting method, coverage,
resource stops and cleanup. Retain failed attempts and inspect the payload's exit
status, not only the profiler's. Count discovery, arguments, responses, retries and
continuations in any token claim; label estimates separately from observed model usage.

Return the bottleneck, owning change or justified no-change decision, correctness
oracle, measured scope, before/after evidence and limits. Stop when the demonstrated
cost is resolved or further benefit is speculative. See the
[worked example](references/worked-example.md) and shared
[source record](../reverse-engineer-anything/references/source-record.md).
