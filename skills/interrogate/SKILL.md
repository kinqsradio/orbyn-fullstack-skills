---
name: interrogate
description: "Challenge a specified design, patch or claim for concrete correctness, ownership and evidence gaps. Use for adversarial review, not every routine edit."
---

# Interrogate

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

## Method

1. **Freeze the candidate,** intended contract and review scope. Read its diff with the affected callers and the state/effect owners needed to evaluate the claim, using the [review criteria](../orbyn-workflow/references/project-policy.md#verification-and-review).
2. **Choose risks from the changed contract,** not a generic list of preferences. Look for scenarios that falsify the claim, especially lost authority, stale state, partial failures, concurrency, cleanup and incomplete verification.
3. **Write each suspected defect as a scenario:** initial state, actor, action/interleaving, observed or source-derived result and violated contract. Check whether a downstream guard or caller already prevents it. A rejected hypothesis is useful evidence: record why it was dismissed and leave it out of the actionable findings.
4. **Deduplicate and independently check** the findings. Classify them as concrete defects, evidence gaps, optional improvements or dismissed claims.
5. **Rank** lost data, authority and recovery consequences above style. Every actionable item needs a current source location, scenario, practical impact, confidence and correction direction. Prescribe a new abstraction only when the existing boundary cannot preserve the invariant.
6. **Return findings first,** then checked assumptions and unverified scope, with a supported verdict and its limitations.

For an approval change, ask whether a revoked user or stale client can still apply it and whether a retry duplicates the effect. Return a concrete reproducing state and the affected owner. Keep missing runtime evidence separate from a proven code defect: missing native evidence is an evidence gap, and it is not automatically a source-code defect.

## Review-only limits

A review-only assignment edits no code; do not auto-apply changes. If a fix is authorized later, recheck the exact changed candidate rather than carrying the previous verdict forward.

The lead may use an independent in-task reviewer for a distinct unresolved risk under [coordination](../orbyn-workflow/references/project-policy.md#delegation-and-host-configuration), within the task's shared child limit. Assigned reviewers inspect their candidate directly without further delegation, and follow assigned read-only limits and the model policy. Neither multiple models nor a majority vote establishes correctness.

## Record falsification receipts

For each consequential challenged claim, retain the pinned candidate, input/trigger, expected and observed result, actual command or source trace, disposition and next check. Re-run supported executable findings at the same candidate when permitted; a fabricated final state or a test that always fails is not adversarial evidence. Keep source-proven unsafe paths actionable with their evidence labeled even when execution is blocked. Compare baseline and head/reachability before attributing a preexisting defect to the patch; newly exposed or copied unsafe behavior still matters.

## Value and fallback changes

For a value-propagation or configuration-resolution change, trace the retained value through presence/truthiness guards, fallback selection, precedence and affected consumers. Compare baseline and candidate with the changed field alone, because extra attributes may already select the same branch and hide the consequence. Distinguish explicit false from absence where the contract does. Use the [focused regression method](../tdd/references/propagated-values.md) for discriminating controls rather than requiring a generic exhaustive matrix.

Classify a changed result as an intended consequence supported by the contract, a compatibility risk needing an owner decision, a concrete contract violation, or missing evidence. A real behavior change and missing coverage do not alone prove a new defect. Explain affected fallback values and user-visible effects; do not prescribe changing fallback semantics merely to preserve accidental old behavior. An authorized repair still needs a confirmed intended contract.

## Module refactors

Inspect what callers must know, which complexity is hidden, whether the seam reflects actual variation, and whether behavior checks survive the internal reorganization. Identify a concrete caller or failure scenario; a preferred vocabulary or file count is not a finding.
