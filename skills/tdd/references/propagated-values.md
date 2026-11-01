# Propagated values and fallback selection

When repairing a previously ignored value, follow it through downstream presence,
truthiness, empty-result and precedence checks. Retaining a value can change which
fallback runs even when that fallback's code is unchanged. Choose assertions from
the documented contract before deciding whether this consequence is a defect.

Test a minimal input containing only the changed field, then a representative
combined-field input. Another field can independently select a branch and mask
the interaction. Where supported, distinguish explicit true, explicit false,
unset/null, empty and unmatched rules, with populated fallback values so branch
selection has an observable effect. These are relevant controls, not a required
cross-product for unrelated changes.

For example, a resolver may use defaults only when no recognized attribute is
defined. Retaining `warnOnChange: false` then suppresses defaults just as true
does; a test also supplying a label could have suppressed them before the fix.
Assert the complete resolved result and affected behavior against the unchanged
baseline and candidate. Preserve intended fallback semantics; document an expected
consequence or compatibility risk rather than silently broadening the repair.
