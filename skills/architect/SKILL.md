---
name: architect
description: "Design data shapes, interfaces, ownership, statecharts and module boundaries for substantive features or refactors; use for lifecycle rules, code organization, vertical modules and shared-code extraction."
---

# Architect

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.
Read the relevant [stack boundaries](../orbyn-workflow/references/project-policy.md#stack-and-ownership)
and trace the current design with [how](../how/SKILL.md). Use
[orbyn-research](../orbyn-research/SKILL.md) for a consequential external unknown.

## Method

1. **Start from one real caller** and a failure it must handle. Write the proposed call and result before drawing directories, then the necessary types, owner, interfaces and lifecycle. Include authority, concurrency, failure, recovery and compatibility when the task affects them.
2. **Inventory the current owner** of identity, mutable state, effects and cleanup. A new interface must take responsibility away from callers rather than merely rename their parameters.
3. **Compare alternatives where the choice is consequential.** A small sketch is enough when an established pattern fits. Otherwise follow one normal and one interrupted operation through each alternative's owners, and compare how many independent decisions callers must repeat, compatibility with released consumers and the cost of recovery. Select a design when that resolves the choice. If a measurement is needed, give the smallest prototype a decision threshold and disposable inputs. Use [arena](../arena/SKILL.md) only when competing candidates would settle a real uncertainty; do not launch a model panel for every function boundary.
4. **Choose the smallest coherent design** and explain its trade-off. Keep domain ownership separate from platform rendering: a task editor can share the update contract while web and mobile keep their own focus and navigation behavior. If escape hatches or duplicated state interpretation keep recurring, reconsider the owner/type design and fix that source of complexity instead of adding wrappers.
5. **Check the interface** against a stale write, revoked access and a retry after an unknown result, where those cases apply.
6. **Return** an owner/interface table, a representative call, state transitions, the rejected alternative and a migration order. Use [orbyn-plan](../orbyn-plan/SKILL.md) when the design needs a delivery sequence. Record a durable rationale only when future maintainers need the decision.

For a proposal-approval feature, specify the durable proposal state, authenticated apply operation, stale-version behavior and shared result shape before designing the buttons. Return a contract the API, web and mobile owners can implement without inventing their own lifecycle. A model sketch is enough only when it answers those ownership questions.

## Scope and delivery

A design-only request ends with the design contract and reorganizes no files. This skill request does not authorize reorganizing a consuming application. A small clear fix needs no architecture redesign. Keep sketches out of production code unless they are being completed in the same delivery. Implementation checks belong to the resulting change, within the user's scope.

For substantial implementation, the lead delegates against the selected design under the [workflow](../orbyn-workflow/SKILL.md), reviews the returned diff, performs authorized verification and routes repeated design friction back into the contract. A child implements its owned scope directly.

## Design rules

Choose authoritative data, ownership and lifecycle before adding logic. Simplify the affected design before extending it, and remove needless indirection without losing required behavior. Integrate new requirements into that design, and encode a demonstrated recurring failure at the boundary that can prevent it. Migrate controlled callers and retire the old API once compatibility evidence permits it.

When [comparative research](../orbyn-research/references/comparable-implementations.md) informs the design, translate its assumptions and local mismatches into concrete owners, interfaces, lifecycle/failure rules and regression checks. A similar upstream diagram or implementation does not establish this project's contract.

For durable transitions, put the migration owner's concrete writer/admission contract in the design, including stale-writer rejection and current-writer controls. A link to migration guidance alone is not the deliverable.

## Read when needed

- Where code belongs, cross-feature imports or shared-code extraction: [vertical code organization](references/vertical-codebase.md). Group code by the functionality it owns within existing stack boundaries, and specify public entry points, private internals and allowed dependency directions before moving files. Return the proposed owner map, import contract, trade-off and scoped migration/verification plan. Explaining an existing import path belongs to `how`.

- Statecharts, lifecycle races or behavior a human needs to inspect: [behavior models and statecharts](references/statecharts.md). Separate the agreed design from current-code behavior, expose forbidden states and connect important rules to source and preview scenarios. A chart alone does not verify a property: use `tdd` for model checking and drift, and `orbyn-ui-design` for the human preview.
- Domain artwork over a statechart: [illustrated statecharts](references/illustrated-statecharts.md) and technical-illustration, keeping plain semantics and evidence accessible.
- A picture of deployed services and how they connect, not states over time: [stack-diagram](../stack-diagram/SKILL.md).
- Caller burden, shallow wrappers, dependency cycles or API longevity: [maintainable modules](references/maintainable-modules.md). The [Python/Go/SQL example](examples/polyglot-contract.md) connects one contract across language boundaries without imposing a framework.
- Unresolved language, framework or storage choice: [stack selection](../orbyn-stack-selection/SKILL.md) for the constraint/evidence comparison, then own interfaces and lifecycle here. An established project's bounded feature usually keeps its stack.
- Implementation: the relevant [language reference](../language-best-practices/SKILL.md), preserving FFI/transport encoding, ownership and failure contracts across polyglot boundaries.
- Cross-team, independently released or quantitatively constrained systems: [large changes](references/large-changes.md). Name measured/required/assumed constraints, distinguish code and organizational ownership, pilot a complete slice, then migrate resumable batches. Never infer deployed adoption from local edits.
- A new service or materially changed operating envelope: [service readiness](references/service-readiness.md). Small internal changes keep their existing operating contract.
- Requested command-interface design or terminal behavior: the conditional [CLI contract](references/cli-contract.md), then the target's parser/runtime owners.
- Asynchronous admission, recovery ownership, event ordering, duplicate registry keys or stale catalog entries: [runtime boundaries](references/runtime-boundaries.md).
- Expo modules/views/config plugins, DOM/native bridges, brownfield and incremental web migration: [mobile boundaries](references/mobile-boundaries.md). Preserve target-native ownership; no automatic scaffolding or macro migration.
- Worked examples, to reuse the reasoning shape with the project's actual owners: [reviewing a proposed change](examples/proposal-approval.md) (synthetic input, ownership contract, recovery behavior and a tempting failure) and [organizing a task editor](examples/vertical-task-editor.md) (functional cohesion, a public interface and shared ownership without merging client/server or platform boundaries).
- One decision needing a worked check, reading only that method: [foundations](references/principles/foundational-thinking.md), [subtraction](references/principles/subtract-before-you-add.md), [simplification](references/principles/laziness-protocol.md), [reader load](references/principles/minimize-reader-load.md), [coherent redesign](references/principles/redesign-from-first-principles.md), [structural prevention](references/principles/encode-lessons-in-structure.md), [alternatives](references/principles/exhaust-the-design-space.md) or [API retirement](references/principles/migrate-callers-then-delete-legacy-apis.md).
