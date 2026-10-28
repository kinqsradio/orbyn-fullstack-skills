# Trace forensics

Use the parent [workflow](../SKILL.md). Identify the supplied capture, producer,
source/build revision, clock, interval, sampling rate and dropped/truncated data.
Inspect aggregate phases before individual spans; keep the original capture
unchanged and derived reports in separate owned output.

For each material hotspot, distinguish inclusive time, self time, blocking,
scheduling delay and repeated work where the capture supports those distinctions.
Correlate events only with evidence of shared identity and ordering. Missing
samples are not proof that a phase never ran, and a long parent span does not
prove its own code consumed CPU.

Map a hot path to source only when symbols and revisions match. For an export,
separate queue delay, browser startup, render and serialization before proposing
an optimization. If the trace excludes startup, do not report whole-export latency.

Return the bounded diagnosis, supporting spans/summary, capture limitations and
next observation that could change the conclusion. Hand a measured improvement
to the [performance playbook](perf-issue.md). A captured profile is not a benchmark
comparison or permission to collect unrelated live telemetry.

For large captures, use the existing format-aware parser/query engine to produce
bounded phase/call-tree/retainer summaries with event IDs and source/symbol identity.
SQLite is an optional query surface, not a mandatory conversion. Preserve original
bytes and sampling/drop limits. A heap diagnosis follows a retained object through
its actual root path, then compares matched repeated-operation captures after a
correction; one large allocation or missing sample cannot establish unique cause.
Keep derived query and symbol provenance so another owner can reproduce the slice.

## Process and observer identity

Record client/server build, process role, run ID and actual capture completion.
Triangulate rendered behavior, API projections and ordered durable history when
they disagree; a fresh snapshot need not contain every earlier event. A partial
heap file cannot support a completed heap analysis. RSS growth can reflect native
allocation, mapped pages or allocator behavior rather than retained JS objects;
follow actual retaining paths and matched workloads before attributing a leak.
Account for debugger/sampling overhead. Preserve and read back the user's color,
motion and focus preferences around a permitted attachment; an observer-induced
media/focus change is a confound, not evidence of the product's ordinary state.
