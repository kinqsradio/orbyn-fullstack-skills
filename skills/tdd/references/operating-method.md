# Demonstrate a regression at its real boundary

Freeze the observed defect, expected invariant and a practical authorized test boundary. Build one regression that exercises the actual production path. Assert state or externally meaningful behavior rather than private helper calls.

Run against the unchanged candidate first. Preserve the failure and verify that its cause is the reported contract violation, not a missing dependency or broken fixture. Implement the smallest coherent correction, then rerun the same case and directly affected controls.

For a stale version write, arrange an existing record and newer version, send the stale mutation, and assert both rejection and unchanged persisted data. An error-string snapshot alone misses a write that succeeds before returning an error. Include a legitimate current-version control when it distinguishes an overbroad rejection.

## Propagated values and fallback selection

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

If baseline execution is unavailable, record that limit explicitly. Do not call a newly passing test failing-before evidence. Refactor only after the meaningful signal is green; preserve useful contract tests rather than coupling them to the new implementation. Production databases and paid providers require their own applicable authority.
