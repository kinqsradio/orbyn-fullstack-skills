# Attack the premise

When two fixes that share one belief have failed the same check, suspect the belief, not the next fix. Each failure is evidence against what it assumed.

## Decision in practice

What is the one sentence every failed attempt took for granted?

Two retries with longer timeouts both fail the same integration check. The shared premise is "the call is slow". Before a third timeout, make an observation that would look different if the premise were false: do the failures cluster on one tenant, one payload size or one region? If they all hit a single stale credential, no timeout setting could have helped.

## Apply and hand off

1. Write the premise down.
2. Pick the cheapest observation that distinguishes it from a competing cause, and look at how the failures are distributed, not only how large they are. Make it rerunnable.
3. If the evidence contradicts the premise, search for what the failures share that the premise did not predict. If it confirms the premise, ask the next "why": the earlier fixes may have treated a consequence.
4. If one part always lands on the losing side, remove the condition that puts it there instead of adding a mechanism that cleans up after it.

Do not start the next fix until the premise is written and tested. A first fix whose cause and regression are already established needs none of this. For a failing reproduction, [reproduction](../../../how/references/reproduction.md) holds the debugging form of the same pivot. Redesigning around a new requirement is [redesign from first principles](redesign-from-first-principles.md); this one questions a fact the current design assumes.

Return the premise, the observation and the result, and the changed invariant or owner. This principle refines [architect](../../SKILL.md); it adds no mandatory phase.

## Source and license

Adapted from Lauren Tan's pstack [attack the premise](https://github.com/cursor/plugins/blob/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/principle-attack-the-premise/SKILL.md),
revision `ae5650febf4320793844c12c4adaa937f417f8da`.
Orbyn adaptations and worked examples retain the [original MIT notice](LICENSE.txt).
