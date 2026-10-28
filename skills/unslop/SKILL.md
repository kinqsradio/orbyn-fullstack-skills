---
name: unslop
description: "Edit agent prose and documentation for clear factual communication while preserving the requested voice and evidence."
---

# Unslop

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

Lead with the concrete result or action. Use familiar words and verbs, one main
idea per paragraph, and headings only when they help navigation. Remove filler,
repetition, inflated claims, forced contrasts and decorative formatting.

Preserve the user's writing style when editing their material. Preserve exact
names, measured results, caveats, attribution and uncertainty. Do not manufacture
metrics or remove evidence to make prose sound stronger. Code comments should
explain non-obvious constraints rather than narrate the next line.

Use [content design](../orbyn-content-design/SKILL.md) for product copy. Do not
rewrite user-authored product content as a side effect of UI simplification.
Read the edited passage as a whole; a checklist of forbidden words cannot prove
clear writing.

Use [social-content](../social-content/SKILL.md) for social post strategy, author
voice, platform adaptation and carousel copy; this skill supplies the prose pass.
Use [social-preview](../social-preview/SKILL.md) for rendered feed mockups and
attached visuals. Editing a caption does not require generating visual assets.

## Comments inside source

Prefer clear names and straightforward code for local mechanics. Preserve a
non-obvious invariant, ordering requirement, ownership boundary, compatibility
reason or deliberate tradeoff beside the code whose safe modification depends on
it. Explain the consequence of breaking the constraint; avoid narrating an obvious
assignment or using a comment to excuse unnecessary complexity.

For example, “Keep pending work visible so later submissions cannot reuse partial
state after an interrupted run” preserves a reason; “set the pending flag” merely
repeats the operation. Recheck nearby claims when behavior changes: correct stale
explanations and remove obsolete narration. Preserve legal notices, generated-code
warnings and useful safety/compatibility rationale under the project's conventions.
Do not apply blanket comment deletion or a required comment count.

Keep changing CI status and long experiment history in existing evidence/docs.
A link may supplement essential rationale, but should not replace it. Comments
are claims, not enforcement; critical behavior still needs the appropriate code
structure, assertion or regression. With authorized edits, move durable review
reasoning into clearer code or a source comment; review-only work changes neither.
Use the [review feedback contract](../orbyn-workflow/references/engineering-scope.md#actionable-review-feedback)
for findings and delivery authority.

Reviewed inspiration, 27 October 2026:
[Google review criteria for comments](https://github.com/google/eng-practices/blob/3bb3ec25b3b0199f4940b1aa75f0ac5c5753301c/review/reviewer/looking-for.md#comments).
This independently authored guidance imports no upstream text or tooling.

## Operational method

Use the [local operating method](references/operating-method.md) for the execution
sequence, concrete failure case, expected result and stopping condition. It is
Orbyn-authored guidance; historical source notices remain in provenance.

For a tutorial, how-to, reference or explanation, apply the conditional [document purpose method](../orbyn-workflow/references/explanation-and-recaps.md#technical-documents) before polishing sentences.
