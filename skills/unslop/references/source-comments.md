# Source comments

Use this when writing, reviewing or editing comments inside source code.

Prefer clear names and straightforward code for local mechanics. Keep a non-obvious
invariant, ordering requirement, ownership boundary, compatibility reason or
deliberate tradeoff beside the code whose safe modification depends on it. Explain
the consequence of breaking the constraint. Leave out narration of an obvious
assignment, and do not use a comment to excuse unnecessary complexity.

“Keep pending work visible so later submissions cannot reuse partial state after an
interrupted run” preserves a reason; “set the pending flag” merely repeats the
operation.

- Recheck nearby claims when behavior changes: correct stale explanations and remove
  obsolete narration.
- Preserve legal notices, generated-code warnings and useful safety/compatibility
  rationale under the project's conventions.
- Do not apply blanket comment deletion or a required comment count.
- Keep changing CI status and long experiment history in existing evidence/docs.
- A link may supplement essential rationale; it does not replace it.
- Comments are claims, not enforcement. Critical behavior still needs the
  appropriate code structure, assertion or regression.

With authorized edits, move durable review reasoning into clearer code or a source
comment; review-only work changes neither. Use the
[review feedback contract](../../orbyn-workflow/references/engineering-scope.md#actionable-review-feedback)
for findings and delivery authority.

Reviewed inspiration, 27 October 2026:
[Google review criteria for comments](https://github.com/google/eng-practices/blob/3bb3ec25b3b0199f4940b1aa75f0ac5c5753301c/review/reviewer/looking-for.md#comments).
This independently authored guidance imports no upstream text or tooling.
