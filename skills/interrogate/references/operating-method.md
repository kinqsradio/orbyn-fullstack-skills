# Challenge a claim with a concrete counterexample

Freeze the candidate, intended behavior and review scope. Read its diff together with the callers and state/effect owners needed to evaluate the claim. Choose risks from the changed contract rather than a generic list of preferences.

For each suspected defect write initial state, actor, action/interleaving, observed or source-derived result and violated contract. Check whether a downstream guard or caller already prevents it. A rejected hypothesis is useful evidence; omit it from actionable findings after recording why it was dismissed.

A finding needs a current source location, practical impact, confidence and correction direction. Keep missing runtime evidence separate from a proven code defect. Rank lost data, authority and recovery consequences above style. Avoid prescribing a new abstraction unless the existing boundary cannot preserve the invariant.

For a value-propagation or configuration-resolution change, trace the retained
value through presence/truthiness guards, fallback selection, precedence and
affected consumers. Compare baseline and candidate with the changed field alone;
extra attributes may already select the same branch and hide the consequence.
Distinguish explicit false from absence where the contract does. Use the
[focused regression method](../../tdd/references/operating-method.md#propagated-values-and-fallback-selection)
for discriminating controls rather than requiring a generic exhaustive matrix.

Classify a changed result as an intended consequence supported by the contract,
a compatibility risk needing an owner decision, a concrete contract violation,
or missing evidence. A real behavior change and missing coverage do not alone
prove a new defect. Explain affected fallback values and user-visible effects;
do not prescribe changing fallback semantics merely to preserve accidental old
behavior. An authorized repair still needs a confirmed intended contract.

Return findings first, then checked assumptions and unverified scope. A review-only assignment edits no code. If a fix is authorized later, recheck the exact changed candidate rather than carrying the previous verdict forward automatically.
