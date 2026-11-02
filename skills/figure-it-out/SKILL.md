---
name: figure-it-out
description: "Execute an authorized large migration or cross-cutting change through to its measurable end state, tracking every unit. Use orbyn-plan when the deliverable is only a plan."
---

# Figure it out

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.
Use [orbyn-plan](../orbyn-plan/SKILL.md) to establish or revise the execution plan
and [stack ownership](../orbyn-workflow/references/project-policy.md#stack-and-ownership) to place changes.

## Method

1. **Define the end state.** Write a checkable end state, exclusions and the largest unresolved risk.
2. **Inventory the units from current source,** not an estimated file count, before planning. Mark each as pending, active, verified, deferred by the user or blocked by a named dependency. Keep one task record rather than separate competing plans.
3. **Sequence by dependency and risk.** Use coherent units that can be inspected without leaving ambiguous ownership, and take the riskiest complete path first.
4. **Set up each unit.** Record its entry revision, expected artifact, authorized check, and reversible recovery point. Follow the user's verification scope. Use existing tools before building automation; create a small reusable helper when repetition or reliable checking justifies it.
5. **Execute each unit.** The lead states the hypothesis and throughput checkpoint, delegates substantial investigation/implementation with owned files, inspects the actual artifact and diff, and performs authorized verification.
6. **Recover from failure.** Preserve the failure and useful evidence, correct the disproven assumption and revise the hypothesis before retrying; repeat an unchanged failed attempt only with a new explanation. If a provider or operator step is unavailable, continue independent units and leave that step visibly unverified.
7. **Reconcile at the end.** Check the full inventory against actual files and check receipts. Close only units whose artifacts exist and whose required evidence was obtained. Report verified, unverified and blocked parts, including remaining work in the requested end state even if the local implementation is complete. Never silently reduce the requested outcome.

A service or API extraction unit includes shared schema, consumers, routing, contract, persisted state, the old handler and its retirement condition. Close it when all of those are done; a new handler alone leaves it open. Keep unfinished operator/deployment work visible in the report instead of moving it to a future-work paragraph and calling the migration complete.

## Delegation and records

Follow the [workflow lead contract](../orbyn-workflow/SKILL.md). Keep coupled contract/caller edits with one owner, isolate genuinely independent output paths, and stay within the resolved harness `max_children`. Route corrections to the same owner. A child executes its owned unit directly without delegation.

Use [show-me-your-work](../show-me-your-work/SKILL.md) for decisions that matter later.
