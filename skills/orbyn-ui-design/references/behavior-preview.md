# Connect a human preview to behavioral rules

Use for a stateful interactive prototype or preview of a critical flow. Preserve
the existing [visual direction](visual-direction.md), content and design system.
State the human decision before adding controls, charts or verification machinery.

## One behavior contract, several forms of evidence

Use stable state/event/rule IDs in a compact table only where they help connect
the work. The UI's state and the server's durable outcome have different owners.
For each material rule, identify the scenario control, expected visible result,
implementation boundary and check, marking anything absent or simulated.

| Scenario | Preview behavior | Underlying rule/evidence |
| --- | --- | --- |
| Save succeeds | Pending then confirmed, with clear status | Confirmation represents the server result; simulated in a standalone demo |
| Server commits, response is lost | Draft retained, outcome unknown, reconcile/retry available | Retry/reconciliation must avoid a second effect; requires real backend evidence |
| Old response arrives after a new edit | New draft/result remains visible | Request/version ownership; use controlled response order |
| Permission or target changes | Current context wins; stale response cannot populate the new target | Authority stays on the server and cached results retain scope |

Select relevant scenarios; do not attach this whole matrix to every preview.
Expose deterministic controls such as delay response, deliver old response, fail,
retry, reconcile and reset. Reset cancels/fences pending callbacks as well as
resetting visible state. A queued callback must not repopulate a reset demo.
Keep scenario controls distinct from product controls and label them as simulation.

## Make the review usable

Deliver an app route/story or local HTML according to [prototypes](prototypes.md).
Give the human a short sequence to try and the decision to make, with a readable
statechart where useful. Include a textual trace/table; color and screenshots
alone do not explain a violation. For large charts, provide an overview and
focused numbered paths, with omissions disclosed.

Inspect the rendered preview and chart, relevant narrow layout, keyboard focus,
status announcements and changed recovery path. Record actual actions and
observations. A browser automation pass proves those exercised assertions;
agent inspection is not participant usability research or full accessibility
certification. Native gestures/navigation require the supported native surface.

Keep four evidence statements independent: rendering inspected; interaction
exercised; property checked in a stated model; implementation replayed. Show
unverified/blocked states honestly. A red model path is a candidate violation
until source correspondence/replay establishes a real defect. A green model does
not establish layout quality, server correctness or every possible deployment.

## Transfer and retain

If implementation is authorized, preserve selected state/event/rule IDs in real
frontend/backend contracts and regression cases where useful. Replace fixtures
with actual adapters, remove demo controls, check uncertain outcomes and inspect
the resulting UI. Keep client presentation state separate from durable operation
state. An approved prototype is a design decision, not deployment acceptance.

Use [artifact lifecycle](../../orbyn-workflow/references/artifact-lifecycle.md) for
storage and cleanup. Durable accepted models/tests belong to the target's tracked
owner; disposable HTML, rendered exports and raw runs use task-scoped ignored
output. Preserve pending human review before removing a worktree, verify retained
links can reopen, and report server lifetime/restart instructions. If raw evidence
later expires, mark it unavailable; historical summaries are not replayable logs.
