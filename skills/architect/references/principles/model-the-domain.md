# Model the domain

Put the real domain in a data structure instead of scattering it across conditionals. Choosing the structure while writing is cheap; recovering it later looks like a refactor and gets deferred.

## Decision in practice

Does the code say what must never happen, or does every caller have to remember it?

A subscription screen tracks `isTrial`, `isPaused` and `isCancelled`, and the next feature adds `isGrace`. Four booleans permit sixteen combinations and the domain allows five. Replace them with one status union and a table of allowed transitions; the new feature adds one member, and the compiler lists every branch that must handle it. A second flag that has to stay in sync with the first is the cue.

## Apply and hand off

Match the structure to what the code must never allow and how the data is read:

- a state machine or union for phases and lifecycles, not booleans;
- a typed model for loose parameters or a repeated shape assumption;
- a map, registry or lookup table for branching spread over files;
- a reducer or command and event model for ad hoc mutation;
- a module around one body of domain knowledge, not a sequence of load, validate, transform and save. Execution order is not ownership, and phase-named modules repeat the same rules in each step;
- a queue, index, graph or tree where the access pattern calls for it.

Keep boring code when the shape is already clear, local and unlikely to grow. An abstraction that removes no branch, duplicate rule or invalid state only adds indirection. Ownership and slicing questions go to [vertical code organization](../vertical-codebase.md), and a lifecycle with races to [statecharts](../statecharts.md).

Return the structure chosen, the states it rules out and the branches it deletes. This principle refines [architect](../../SKILL.md); it adds no mandatory phase.

## Source and license

Adapted from Lauren Tan's pstack [model the domain](https://github.com/cursor/plugins/blob/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/principle-model-the-domain/SKILL.md),
revision `ae5650febf4320793844c12c4adaa937f417f8da`.
Orbyn adaptations and worked examples retain the [original MIT notice](LICENSE.txt).
