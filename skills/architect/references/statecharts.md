# Make behavior inspectable

Use when lifecycle rules, independently changing actors or a requested statechart
need a shared explanation. Start with the decision, actual owner and one plain
sentence per rule. A design sketch, a bounded checked model and a code reproduction
are different evidence. Label which one each artifact represents.

## Choose proportional rigor

| Question | Smallest useful result |
| --- | --- |
| Layout, hierarchy or content | Visual prototype; no model checker |
| Can someone complete and recover from this interaction? | Interactive preview with explicit states, deterministic scenarios and reset |
| Can concurrent steps violate a costly promise? | Source-linked model or code-level verifier, counterexample and real-code replay where possible |

Use [UI prototypes](../../orbyn-ui-design/references/prototypes.md) for a human
surface, and [property verification](../../tdd/references/formal-verification.md)
for checking. Do not force formal tooling onto every prototype.

## Establish states, events and rules

1. Read the relevant code, domain contract and policy. Separate current behavior,
   proposed behavior and unresolved intent. A supplied picture is evidence of a
   proposed explanation, not proof of a product defect.
2. Identify independent owners: client presentation, durable operation, session,
   worker, lease or checkpoint. Use concurrent regions or a small state tuple;
   avoid one enum for every cross-product combination.
3. Name states and events in the reader's vocabulary. Show start, completion,
   cancellation, timeout, restart and recovery only where they matter. State a
   transition's guard, effect and owner. A cancellation signal cannot undo a
   committed write.
4. Give each important state/event/rule a stable ID. A compact table connects the
   rule to a preview scenario, source function/condition, model action and check.
   Use revision plus source digest for uncommitted code; do not invent a sync commit.
5. Preserve distinctions a rule depends on. Merging two states with identical
   labels must not hide different persisted effects, pending work or authority.
   Treat an overview as a projection; disclose omitted states/edges and retain
   the detailed model and traces. Do not claim a hand-edited chart exhausts it.

For example, “a host must not park while protected work exists” requires defining
what counts as protected work and when admission becomes protected. A reaper's
earlier idle observation may be stale by the time parking commits. Model those
as separate actions unless the code serializes them at one real boundary.

### Worked example: an overview hides protected work

This synthetic design example is not an executed check. A concrete state is
`(parked, jobs, observedIdle)`. The rule `NoProtectedPark` forbids
`parked && jobs > 0`. Each action below is one serialized command;
observing and parking are separate commands.

| Qualified action ID | Guard and effect | Source correspondence to establish |
| --- | --- | --- |
| `Reaper.ObserveIdle` | If jobs = 0, set observedIdle | Actual idle observation and its storage boundary |
| `Worker.Admit` | If not parked and jobs = 0, set jobs = 1 | Admission boundary where work becomes protected |
| `Reaper.Park` | If observedIdle, set parked | Parking commit and whether it rechecks current jobs |

The numbered failure path is: (1) `(false, 0, false)`; (2) observe idle,
`(false, 0, true)`; (3) admit, `(false, 1, true)`; (4) park,
`(true, 1, true)`. The final state violates the rule in this design. An overview
that labels both pre-park states “Idle” hides the newly protected job. It must
retain the job distinction in a state label, annotation or detailed transition
table; it cannot present “Idle → Parked” as evidence of safety.

For any generated overview, record the concrete-to-display mapping and omitted
states/edges. Preserve full IDs such as `Worker.Admit` and `Admin.Admit` in traces
and source mappings even if both display as “Admit”; never join events by the
short label alone. A misleading projection should be rejected or replaced with
the detailed trace. A graph budget may omit a chart without preventing a model
verdict; unavailable projection and checked property are separate fields. See the
[per-property receipt example](../../tdd/references/formal-verification.md#worked-example-report-each-property-separately).

## Produce a chart people can read

Keep editable Mermaid source and an inspected SVG or PNG, with a text transition
table/trace for accessibility. Label events and guards; use a legend and textual
violation labels so color is not the only signal. A large graph needs a focused
overview plus numbered failure paths, not unreadably small text. A proposed fix
gets its own source/model identity and before/after comparison.

Pele is an optional Mermaid-to-SVG renderer, not a checker. The local
[renderer adapter](../scripts/render-statechart.mjs) uses an explicitly supplied,
trusted installed module and never installs one. From the library root:

```sh
node skills/architect/scripts/render-statechart.mjs --input path/to/flow.mmd --output path/to/flow.svg --pele path/to/installed/pele/dist/pele.js
```

The output must be new; retain earlier evidence. Use an existing project renderer
instead when appropriate. Without a renderer, hand off Mermaid and the transition
table with rendering unverified. Without a verifier, hand off an unchecked design;
never label it checked because rendering succeeded. Inspect actual layout at the
review width, including long labels and dark/light backgrounds where relevant.

## Check correspondence and hand off

For an existing implementation, every relevant model action and guard must point
to current source. Model the actual atomicity; a check and effect separated by an
await, transaction or lock boundary cannot be collapsed for convenience. Include
other writers of guarded state and call out excluded actors. Replay a reported
violation through real entry points. An impossible trace indicates a modeling
error until evidence establishes otherwise; preserve the intended property.

For a design with no code yet, label the result model-only. A chart-to-model
translation establishes only the semantics actually encoded, not arbitrary
Mermaid semantics or implementation conformance. Check temporal/liveness promises
with appropriate fairness and checker support; reaching one goal is not proof of
eventual completion for all executions.

Return the agreed rule, source/model identity, chart and source, numbered trace,
actual check command/result, bounds, real-code replay and omissions. Maintain
models under [drift review](../../tdd/references/verification-drift.md). See the
[source record](verification-source.md) for the selected upstream methods.
