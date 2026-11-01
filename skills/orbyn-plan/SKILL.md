---
name: orbyn-plan
description: "Refine an engineering request or scope and sequence a change, migration or investigation. Use for prompt rewriting, explicit plans and complex changes; preserve the requested execution boundary. Use figure-it-out to carry out an authorized large migration."
---

# Plan Orbyn work

Read the consuming project's instructions and stack guide. Use the
[portable scope and routing defaults](../orbyn-workflow/references/project-policy.md)
only where guidance is missing.
An explicit planning request always receives a plan, even for one file. A small
clear implementation request can proceed directly without a separate artifact.

## Method

1. **Classify the request and keep its execution boundary.**
   - Prompt refinement: produce the requested usable task brief; do not execute the work described inside it. Use the [brief and handoff method](references/task-briefs.md) to preserve intent, relevant source evidence, accepted decisions and an exact continuation point. Do not expand a prompt rewrite into a mandatory packet or implementation phase.
   - Plan-only: ends at the plan.
   - Plan-and-implement: continue authorized execution once the plan is concrete, unless a material unanswered decision blocks the next step. Planning and prompt refinement add no approval gate or mandatory human invocation.
2. **State the contract:** the user's outcome, exclusions, current source/candidate, affected surfaces, constraints and checkable completion.
3. **Ground it.** Trace relevant behavior with `how`; use `why` when historical rationale affects the decision. Identify the frontend/backend/shared/mobile/storage/host boundaries actually involved. Reuse existing primitives before suggesting a new dependency. For unresolved external or version-dependent facts, use `orbyn-research` with a specific question and stopping condition. Ask only questions whose answers materially affect correctness, cost, compatibility or the requested outcome.
4. **Frame a consequential initiative.** Identify the observed problem, affected person or system, evidence of need and checkable success measure before choosing delivery units. Compare no change, a smaller correction and the proposed investment where those alternatives are viable. Prioritize technical debt by demonstrated failures, change cost or operational risk; code age alone does not justify a rewrite. Label assumptions and the evidence that would change the priority.
5. **Design.** Use `architect` for interface/ownership choices. Compare alternatives only where there is a real trade-off; use `arena` when distinct sketches would settle it. Use the relevant owner's conditional methods without loading every method or requiring model panels.
6. **Sequence by coherent outcomes,** dependencies and reversible boundaries. Choose narrow user outcomes that connect the necessary contract, persistence/API and client owners, not technical folders. Start with a small complete path through the riskiest integration. Name prerequisite work and the outcome it enables, with blocking edges and observable acceptance. Separate risky state migrations from unrelated polish, and describe mixed-version compatibility and recovery where relevant. Size units by coherence rather than a fixed file, function, test-case or phase count; a shared-contract migration may need coordinated edits across many files in one unit.
7. **Specify each meaningful unit:** outcome, owning files/modules, prerequisites, assigned role, authorized evidence and completion condition. Add platform/data/permission failure cases where they affect the contract. An implementation request normally includes proportional local checks; respect explicit exclusions and separate authority for live providers or production effects.
8. **Deliver the plan** in the format below, keeping essential unknowns and research findings visible rather than disguising them as completed implementation.

For a task-scheduling change, make the domain/API/calendar dependencies explicit and keep shared-schema changes with their consumers. State whether the requested end state is a local preview, a reviewed patch or deployed behavior. Keep the plan short enough to reconcile against actual delivery.

## Plan format

Use a concise in-chat plan for small work. When a durable handoff is useful, reuse the existing owning document; otherwise use one `docs/work/<task>.md` only when needed and consistent with the consumer's policy. Planning alone creates no separate log. Follow the [task-record defaults](../orbyn-workflow/references/task-record.md). Include:

- Outcome, scope and current source evidence.
- Selected design and relevant rejected alternative.
- Ordered units, dependencies, owners and recovery considerations.
- Authorized verification, unverified boundaries and delivery target.
- Material assumptions, unresolved decisions and next action.

Update the same plan when evidence changes the design, and explain the change. Use the [checkable handoff](../orbyn-workflow/references/handoffs.md) when structured validation helps a transfer or resumed task, preserving candidate and scope.

## Boundaries

Complete these planning steps internally; no separate setup/spec/ticket invocation is required. Publishing a plan to a tracker needs applicable authorization. Do not invent extra stages, stacked PRs, sessions or recurring monitors. Session creation follows [coordination](../orbyn-workflow/references/project-policy.md#delegation-and-host-configuration).

Continue authorized reversible work while waiting on a genuinely blocking decision, and keep routine choices out of permission gates. Use `figure-it-out` to execute a large plan and `show-me-your-work` for consequential decisions.

## Read when needed

- Worked checks: [autonomy](references/principles/never-block-on-the-human.md) and [verifiable units](references/principles/sequence-verifiable-units.md).
- Cross-team direction, platform investment or a technical roadmap: [technical strategy](references/technical-strategy.md) connects decision owners, trade-offs, adoption/support and outcome measures. Measure organizational adoption separately from shipped code, and skip the governance layer for a bounded task.
- Uncertain product opportunities or post-delivery outcome decisions: [product discovery](references/product-discovery.md) covers evidence versus assumptions, manual/no-build alternatives, smallest useful experiment and outcome measures. Skip the discovery program for a known bounded fix.
