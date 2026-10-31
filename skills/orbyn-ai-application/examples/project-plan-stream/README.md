# Project-plan interaction fixture

This is an independently authored, provider-free teaching example of the
[streaming interaction method](../../references/streaming-interactions.md). It
uses plain browser/Node JavaScript and no packages, SDK, service or database.
Its event names/envelope and policies are **fixture choices**, not AG-UI schema
requirements. State, grants, pending decisions and receipts live only in memory;
reload/process death loses them. A stored UI trace is not execution recovery.

## Try it

From the library root, using existing tools:

```sh
node --test skills/orbyn-ai-application/examples/project-plan-stream/interaction.test.mjs
python3 -m http.server 8765 --bind 127.0.0.1 --directory skills/orbyn-ai-application/examples/project-plan-stream
```

Open the reported loopback URL. The server serves static example files only.
Start the complete fixture, edit its title, then accept or reject. The simulated
record and write count come from the actual sample effect owner, not a badge.
Replay the complete history: it does not repeat the effect. A supported pending
resume rechecks the current owner and can discover another client’s answer.
Choose mid-call EOF, rejected patch or an unknown renderer for adverse controls.
The complete replay source is a canned fixture, not a durable delivery service.
Browser interaction/rendering requires its own observed check; Node assertions
alone do not qualify layout, accessibility, a real transport or a framework.

## Owners and selected policies

| Boundary | File/owner | Concrete policy |
| --- | --- | --- |
| Synthetic producer | fixtures.mjs | Nine typed events; selected faults modify delivery, not real accounts/services |
| Event admission | interaction.mjs decodeEvent | Complete JSON event ≤8 KiB; fixed fixture envelope/current scope |
| Projection | session reducer | Exact sequence, snapshot revision and delta base; invalid/gapped state requires repair |
| Local draft | session + preview | Complete proposal only; dirty draft survives a new snapshot with an explicit keep/discard choice |
| Known component | preview.mjs | Fixed project-plan view; textContent/value rendering, no streamed imports/HTML |
| Decision/effect | createEffectOwner | Current principal/account/resource, complete semantics, version and stable logical call identity |
| Replay/resume | session + effect owner | History passive; current outstanding proposal/authority/version required to activate |
| Delivery bounds | queue + caller | 32 KiB/64 queued records; only adjacent progress coalesces with an explicit covered sequence range |

The proposal declares a stable `operation` ID, scoped to principal/account/resource.
Thread/run/attempt/tool identify the currently admitted execution, and connection
identifies delivery. A retry can change run, attempt and tool identity while
reconciling the same logical operation. Trusted producer admission selects the
current attempt; replay cannot admit itself or execute effects. After a retry is
admitted, old attempts are fenced. Each execution/tool tuple stays bound to one
logical operation, including after replacement; conflicting producer registration
fails before changing the original pending call. The regression commits once, loses the reply,
admits a new attempt, recovers the same receipt and rejects a changed payload.
Connection generation is a delivery lease, not an idempotency key. This fixture
intentionally supports one outstanding proposal per run; it is not an interleaved
multi-run/multi-tool history implementation. A replaced
scope rejects old events and captured decision callbacks. The real consuming
application must derive authority at its authenticated boundary; this same-process
fake is not an authentication or tenant-isolation implementation.

The projection revision, business record version and local draft are different.
The delta vocabulary here is deliberately limited to replacing a title and
appending one task; it is not a JSON Patch engine. Rejected patches preserve the
old readable projection but mark it unsynchronized. Explicit repair accepts an
authorized current snapshot; it cannot reconstruct missing tool arguments. A
complete replay/new attempt is needed for those.

Argument fragments are provisional. Only a complete valid project-plan v1
proposal enables a current decision. Transport EOF and the run’s reported outcome
remain separate from the owner’s receipt. A reported result is unverified until
reconciled. If a reply is lost after a simulated commit, look up the same logical
operation; do not create a new key. Rejections finish a decision without a business
write. Repeated equivalent payloads can reconcile the existing receipt; a changed
payload on an answered call conflicts.

The person may edit plan content within the proposal’s fixed target, renderer and
expected version. A real implementation needs its own allowed-edit/approval rule;
this does not grant arbitrary model arguments. Pending records are registered by
the synthetic producer through the fake owner, never by replaying stream events.
Another client’s answer or a revoked/stale pending record cannot reopen approval.

## Bounds and evidence limits

- The fixture admits **complete JSON records**. It does not decode SSE frames,
  split UTF-8 transport chunks or prove SDK conformance. Argument fragments do
  exercise a separate 4096-byte UTF-8 buffer.
- Only adjacent display progress coalesces, up to 1024 positions per batch. State,
  tool and terminal records retain order. The consumer advances across the
  declared display range; it does not misclassify intentionally omitted progress
  as a missing state event. Overflow stops delivery and requires repair.
- Trace is a 32-entry redacted correlation ring; dedupe retains at most 128 event
  signatures. The owner holds at most eight logical calls and 64 immutable execution bindings.
  Admission overflow refuses the new attempt without changing the admitted one. These are serialized
  record/input bounds, not a measured total heap, sustained event-rate result or
  durable duplicate-delivery guarantee.
- Tests exercise the actual sample reducer, queue and fake effect boundary.
  They are new-helper controls, not failing-before evidence against AG-UI,
  CopilotKit or an existing application. No upstream tests or model calls run.
- No provider/host configuration, capture, telemetry, real persistence or target
  installation follows. Existing nesting, skill owners and defaults are unchanged.

The canonical method contains the pinned research attribution. No upstream code,
component collection or workflow text is copied into this example.
