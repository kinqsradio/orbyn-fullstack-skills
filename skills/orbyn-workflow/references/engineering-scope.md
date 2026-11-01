# Match responsibility to the work

Junior, senior and staff are organization-specific roles, not separate skill
catalogs or quality settings. Keep correctness, authority, evidence and respectful
communication at every level. Choose scope from the task and the person's needs;
never infer their seniority or evaluate an employee from a code sample.

| Responsibility | Useful method and result |
| --- | --- |
| Bounded contribution / onboarding | Trace one entrypoint, locate local instructions/runner, complete a small vertical change, explain its invariant and evidence; name the next concrete question when blocked |
| Team-level ownership | Resolve ambiguity, coordinate the changed contracts, select relevant failure/control checks and take the feature through review and operational handoff |
| Cross-team / staff scope | Compare investment alternatives, settle ownership and interfaces with actual decision makers, pilot adoption, sequence independent releases and build capability others can maintain |

Use [how](../../how/SKILL.md), [language guidance](../../language-best-practices/SKILL.md)
and [test strategy](../../tdd/references/test-strategy.md) for execution; use
[planning strategy](../../orbyn-plan/references/technical-strategy.md) and
[large changes](../../architect/references/large-changes.md) for broader scope.
Do not turn an onboarding question into a rewrite, or describe a cross-team
migration as completed merely because one package compiles.

## Onboarding and review that transfer understanding

For an unfamiliar repository, establish a working local path with its documented
runner and a representative bounded change. Explain the nearest relevant owner,
inputs, output and one failure boundary. When coaching is requested, explain the
reason, a small example and a check the learner can interpret; avoid taking over
an exercise when the user asked for guidance. When implementation is requested,
complete it instead of assigning the human a chain of agent commands.

For ordinary review, inspect the actual diff and affected callers using the
feedback contract below. Automated changes still need meaningful review of the
changed contract. Use `interrogate` only for a requested adversarial challenge or
concrete unresolved risk.

Leave the rationale where the next maintainer needs it: existing code comments,
API docs, design decision or example. Do not copy private history into this public
library. A walkthrough by an agent is not independent human review or evidence of
learning. State what was checked and what the recipient must still validate.

## Actionable review feedback

Pin the repository, candidate and scope; inspect the relevant callers and guards.
A finding needs a supported trigger, consequence, violated contract and correction
direction, with observed execution distinguished from source-derived reasoning.
An untested path is an evidence gap until behavior or an explicit required-test
contract supports a defect. Ask a focused question when the decisive fact is
unknown, naming the observation that would resolve it.

Use the project's severity scheme to separate required fixes, scoped suggestions
and optional style. Confidence alone does not establish impact; personal style
does not block delivery. Discuss code and effects without judging its author.
Suggest a correction that preserves the contract; do not require a large redesign
when a local repair suffices. Keep unrelated improvements outside the patch.

Anchor a local finding to the smallest useful current line range. Put cross-cutting
risks and review limits in the summary. Describe one root cause once, with related
locations if useful; there is no comment quota, and no supported findings is a
valid result. State actual review/test coverage rather than implying every file
was inspected. A source review is not human approval, passing CI or production
qualification. Use the [PR feedback method](../playbooks/pr-iteration.md#deliver-line-anchored-feedback)
for current diff anchors, supported host surfaces and posting authority.

Synthetic example: a queue may yield between items, and its pending-work marker
prevents later submissions from reusing partial state. If a proposed early return
clears that marker, explain the interrupted-run trigger, unsafe reuse and required
marker lifetime; label an unexecuted trace source-derived. If the current guard
already preserves the marker, do not file that older allegation as a new defect.
Useful lasting rationale belongs in clearer code or a
[source comment](../../unslop/references/source-comments.md) when edits are authorized.

Reviewed inspiration, 27 October 2026:
[Google review comments](https://github.com/google/eng-practices/blob/3bb3ec25b3b0199f4940b1aa75f0ac5c5753301c/review/reviewer/comments.md).
This independently authored contract imports no upstream text or tooling.

Background, reviewed 25 October 2026:
[GitLab associate](https://handbook.gitlab.com/job-description-library/engineering/development/backend/associate/),
[senior](https://handbook.gitlab.com/job-description-library/engineering/development/backend/senior/),
[staff](https://handbook.gitlab.com/job-description-library/engineering/development/backend/staff/),
and [Google code review](https://abseil.io/resources/swe-book/html/ch09.html).
This is an independently authored scope guide, not certification of a job level.

For requested learning roadmaps, technical-document purpose and authored-work recaps, use [explanation and recaps](explanation-and-recaps.md).
