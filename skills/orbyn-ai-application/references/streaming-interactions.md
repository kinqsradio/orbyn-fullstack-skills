# Streaming application interactions

Use when an agent/model workflow streams progress, state or tool proposals into an
application, including reconnects and interactive history. Start from the current
transport and application owners. A normal fetch, one-shot structured answer or
static animation does not need a streaming framework. This method is usable
offline and does not select an SDK, hosted delivery service or provider.

## Name the state and its owners

Trace producer → decoder/validator → projection → known component → person’s
choice → authorized effect → verified receipt. Architect owns interfaces and
lifecycles; [tool effects](tool-effects.md) and the
[backend contract](../../orbyn-backend-design/references/service-contracts.md)
own authority, concurrency, operation identity and uncertain outcomes.

| State | Authority and useful identity |
| --- | --- |
| Canonical business record/effect | Current authenticated principal, resource and record version at the domain owner |
| Model/workflow context | Selected thread, run and attempt; it is not the canonical business record |
| Delivery/history | Selected connection/cursor/order contract and retention owner |
| UI projection | Validated records for the current principal/resource/thread/run and connection generation |
| Local draft/decision | Person’s edits and the exact complete proposal/version being reviewed |
| Renderer | Trusted component type and supported props version; registration is not execution authority |

Carry tool/message identity where those entities exist. Bind an effect to its
stable logical operation, not a transient socket, retry attempt or regenerated tool
call. Keep admitted execution identity separate so a new authorized attempt can
reconcile the original receipt while old attempts remain fenced. Reconnect changes a connection lease;
a retry may change attempt identity; switching account/resource invalidates old
subscriptions and callbacks even if a route/thread name repeats. These are design
questions, not mandatory AG-UI field names or a universal event envelope. A
client-supplied identity/cursor never grants access.

## Keep terminal witnesses separate

| Observation | What it establishes |
| --- | --- |
| A partial text/argument delta | Provisional presentation only |
| Argument completion | A candidate to parse and semantically validate |
| Tool result event | A reported result; confirm consequential outcomes with the actual owner |
| Run success/interrupt/cancel/error | That run’s declared protocol outcome; frontend decisions may still be outstanding |
| Transport EOF or an unsubscribe | Delivery stopped; neither run completion nor effect rollback follows |
| Current authorized receipt | The effect owner’s known outcome for that operation |

Choose the mapping for the selected adapter. On premature EOF preserve the draft
and classify incomplete delivery or an unknown effect. Reconcile an existing
operation before retrying. A cancel request and confirmed stop are separate; a
committed effect may survive either. Do not display an idle/success state merely
because history catch-up became quiet. No extra approval is needed for every
chunk; obtain a decision only where the consequence requires it.

## Define convergence before applying deltas

For incremental state, specify the snapshot boundary, delta base, order,
duplicate/gap policy and repair owner. A serial reducer proves arrival order,
not causal continuity after reconnection. If a patch is rejected, a base is
missing or sequence continuity is uncertain, visibly mark the projection
unsynchronized and request an authorized repair/snapshot. Keep the old readable
state and local edits; do not label them current. A diagnostic warning followed
by normal-looking state is insufficient.

Separate projection revision from business record version and draft generation.
Choose whether a newer snapshot preserves a dirty draft with an explicit
conflict, offers a discard/rebase choice or follows an existing editor policy.
Never silently overwrite newer edits or invent a new business version locally.
A one-shot response does not require sequence numbers, a CRDT or event sourcing.
The [UI async owner](../../orbyn-ui-design/references/async-state.md) keeps the
canonical stale-generation and draft-preservation guidance.

## Reconstruct history without replaying effects

Give history an explicit accepted schema/version and malformed-record policy.
Known historical components can render read-only; unknown/retired versions need a
non-executable fallback. Do not import code, HTML or handlers from streamed data.
Retaining a renderer after unmount is different from retaining a callable tool.
Use the existing JavaScript callback/lifecycle owner for teardown and fencing.

Passive replay reconstructs a display and never repeats a write. A supported
pending resume separately checks current access, resource/proposal version,
thread/run/attempt/tool identity and the actual outstanding decision. Another
client may already have answered it. Restore that known result rather than
reopening approval. Durable UI delivery does not itself keep a job running,
restore its execution checkpoint or guarantee exactly-once business effects.

## Bound resources and preserve meaningful ordering

Use the selected decoder’s framing/UTF-8 and byte limits, bounded incomplete
argument buffers, producer/consumer flow control and an explicit overflow policy.
The [JavaScript stream method](../../language-best-practices/references/javascript.md)
remains authoritative for actual backpressure and cleanup. Bounding one event
array does not qualify a transport or a slow-device workload.

Batch display-only updates only when the application can safely discard their
intermediate presentation. Preserve tool, state, decision and terminal ordering;
coalescing must account for skipped delivery positions rather than create a false
gap. Bound dedupe windows/history too; a transient memory window is not durable
idempotency. On overflow stop/degrade and repair rather than silently dropping an
authoritative event.

Correlate safe producer/delivery/run/tool/operation identities and failure reasons.
Do not log raw arguments, state patches, credentials or hidden reasoning as default
progress/diagnostics. Decide redaction/retention with the actual application owner.

## Worked example and verification

The provider-free [project-plan preview](../examples/project-plan-stream/README.md)
uses an original fixture envelope, bounded projection and simulated authorized
effect owner. A person edits, rejects or accepts a complete plan; history replay
cannot execute it. Its tests exercise the actual sample reducer/effect boundary,
including partial/malformed arguments, EOF, gap/repair, draft conflict, duplicates,
revoked resume, another client’s answer and replaced-scope handlers. The in-memory
owner and browser view are simulations, not persistence, an AG-UI decoder, a
CopilotKit client or service conformance.

Choose relevant adverse and legitimate controls for the consuming feature. Report
schema/helper tests, actual app flow, SDK/transport tests and service/runtime
qualification separately. See [TDD reliability](../../tdd/references/test-reliability.md).

## Pinned research and attribution

Independently authored Orbyn guidance informed by source review of
[AG-UI at b2f4a1c](https://github.com/ag-ui-protocol/ag-ui/tree/b2f4a1c1ea637dd486f138d30bc1c208db04f253)
and [CopilotKit at d168487](https://github.com/CopilotKit/CopilotKit/tree/d168487e7a753a1527256c7e4c79344377f3d092).
No upstream source/instructions/runtime are copied here; existing lineage/notices
remain in provenance. These links are attribution/update pointers; execution of
this method does not require downloading them.

At those reviewed pins, base protocol event shapes do not themselves guarantee
delivery sequencing, application-state validation or domain authorization. SDK
hooks/reducers offer version-specific facilities; the separately described
Intelligence delivery service has its own operating/data contract. Source-read
upstream tests were not executed for this addition. The local fixture cannot
qualify those SDKs, durable recovery, hosted/self-hosted services or an Orbyn
product adapter; each requires separately scoped evidence.
