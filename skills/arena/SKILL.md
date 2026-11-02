---
name: arena
description: "Build and compare competing design or implementation sketches when a consequential choice cannot be resolved cheaply from existing evidence. Use architect for a single design."
---

# Arena

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

## Method

1. **State the decision** in one sentence, and the artifact. Freeze the inputs, hard constraints and a few observable scoring criteria before generating alternatives.
2. **Build at most two candidates initially,** preferably differing on the uncertain design choice. Give each its own output path and rationale; shared generated files and databases need their own owner. Give both the same task and constraints without steering them toward a preferred answer.
3. **Compare in a table:** constraint, candidate A evidence, candidate B evidence and remaining uncertainty. A hard constraint disqualifies a candidate before aesthetic or convenience scoring. Judge against requirements and maintainability, not model reputation or agreement count.
4. **Inspect every returned artifact** and its rationale yourself rather than trusting its author's summary.
5. **Select one coherent contract,** or report that neither meets the criteria. Incorporate only compatible improvements; never average incompatible assumptions or merge incompatible lifecycles. Preserve useful alternatives and rejected rationale.
6. **Stop when the decision is supported.** The lead reviews the synthesized diff and performs authorized proportional verification. Return the selected artifact, why it won, rejected ideas, remaining uncertainty and the smallest unresolved check to the architecture or implementation owner.

For a live-update decision, feed both sketches the same reconnect, ordering and resource constraints and the same disconnect, duplicate and out-of-order trace. Compare a concrete failure trace and maintenance consequence alongside the happy-path demo; settle delivery correctness from the trace, not a screenshot.

## Delegation limits

The owning lead uses named native Orbyn Architect/Engineer assignments under the [workflow](../orbyn-workflow/SKILL.md), with disjoint candidate paths. Keep within the resolved `max_children` across the task; compare sequentially when slots are occupied. A child forbidden delegation compares sketches directly within its owned scope.

If the host cannot supply permitted delegates, compare sequential sketches directly and disclose that the review was not independent. Unavailable independent/model-family review remains a limit, not permission to change defaults or run a hidden panel.

Follow [coordination](../orbyn-workflow/references/project-policy.md#delegation-and-host-configuration) for user-requested project sessions; candidate comparison alone does not authorize new chats. Never launch hidden CLI model sessions or recursive tournaments. Hand off after the decision, since an ongoing implementation tournament is out of scope. Report two agents agreeing as agreement, never as verified correctness.

## Scored candidates

When comparing scored candidates, keep task acceptance visible but keep judge-only ranking details, model identities and condition metadata outside candidate scope. Use neutral labels and audit leakage under the [evaluation method](../orbyn-skill-creator/references/evaluations.md#candidate-context-and-judge-leakage).
