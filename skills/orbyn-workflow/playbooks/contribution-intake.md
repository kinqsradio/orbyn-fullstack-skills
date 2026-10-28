# Contribution intake

Use this playbook for an ordinary request to investigate or contribute to another
repository. The agent chooses the handoffs; the human need not invoke each skill.
Return a feasible, scoped next step, or continue an authorized implementation.
An intake or shortlist request alone stops before changing product code.

## Establish the target and authority

Resolve the actual Git root, upstream owner, primary clone, worktree, branch and
base revision. Inspect dirty files and existing output before changing anything.
Read root and applicable nested instructions, contribution docs and local skills
in place. The target's policy and stack govern the patch; the library's own
application conventions do not replace them. For nested clones, follow the
[workspace contract](../../orbyn-setup/references/repository-workspaces.md).

Record the requested end state: explanation, reproduction, local fix, submitted
PR or merge. Access to a repository is not publication authority. Select
[worktree/fork ownership](../../orbyn-worktree/SKILL.md) when isolation or delivery
is needed; reuse suitable owned work and preserve unrelated edits. Check actual
fork visibility and destination before publishing. Never promise a private
native fork of a public parent when the provider cannot support one.

## Check delivery feasibility when submission is the endpoint

For issue/report publication or updates, select the artifact and baseline/candidate
evidence using [publication guidance](../references/contribution-publication.md).
The requested endpoint governs the payload as well as the allowed external effect.


Before expensive implementation for a requested submitted PR/merge, inspect
available read-only account/repository permissions, fork/contribution restrictions,
and known submission-capacity limits through supported tools or existing error
receipts. Distinguish authentication, repository visibility, role and provider
capacity; access to source or a successful push does not prove PR creation will
be accepted. Some limits cannot be discovered in advance: record unknowns, not a
guarantee. Local-only work needs no online/account preflight, and an unavailable
check need not stop useful authorized local investigation.

Do not create a probe PR or close any existing PR merely to free capacity
without explicit authority. Do not switch accounts to evade a restriction or
bypass controls. A rejection warrants bounded
diagnostics based on its exact operation, account/target, status/message and new
evidence. A 403 or 404 alone does not establish one cause. Retry only a supported
transient hypothesis or a relevant changed condition; do not loop on a known
capacity/policy denial. Preserve the patch/evidence and distinguish local-ready
from submitted. An external blocker does not invalidate a sound reproduction or
justify a competing fix, invented submission or unrelated issue switch.

## Decide whether this contribution is useful

1. Read the actual issue and acceptance criteria. Check its current state,
   assignment/claim and linked work. Search open and recently closed PRs by issue
   link/number, symptom and relevant source area. Inspect a likely competing fix,
   not just its title. Note the observation time and repository identity.
2. Establish the checked-out baseline: does the issue describe this revision,
   version and supported platform? Trace the relevant source with
   [how](../../how/SKILL.md). Use the
   [reproduction contract](../../how/references/reproduction.md) for defects.
3. Check feasibility: affected owner, likely patch size, available environment,
   meaningful verification, review burden and compatibility. Read any applicable
   CLA/DCO or signing requirement; never accept legal terms for the user.
4. Prefer a small coherent patch that meets the target's contribution rules.
   Avoid unrelated formatting, vendoring this library or changing the project's
   agent instructions as an incidental part of a bug fix.

An assigned issue or competing PR is a coordination signal, not proof that all
work is forbidden or available. Report the overlap and continue source comparison
or another authorized slice; send claims/comments only with applicable user
authority. A shortlist
should expose feasibility and overlap so the user can choose. Do not silently
switch an explicitly selected issue to an unrelated one.

With no network or repository API access, use local issues/history if available
and label their age. Current issue availability, assignment and competing work
remain unknown. Continue useful local investigation; do not report a live search
that never happened or require online access for the local method itself.

## Establish value separately from correctness

Name the concrete benefit to the project and the evidence supporting it: a
reproduced supported bug, a maintainer-requested test/documentation gap, a useful
missing boundary or an evidenced maintenance problem. A self-authored issue records
a proposal; it is not independent user demand or maintainer acceptance. Green
checks establish only their covered behavior, not that the contribution is needed.
Do not require independent demand or advance maintainer approval for every genuine
bug fix, useful test or documentation correction; follow the project's actual rules.

Compare existing behavior and coverage before adding machinery. If the behavior is
intentional or already correct, or the proposed fixture duplicates a practical
existing boundary at disproportionate maintenance cost, report that result and
stop without a PR when appropriate. A mutation-sensitive test shows it detects
that mutation; it does not by itself establish missing coverage or project value.
Reassess value if reproduction changes the premise or a small patch grows into a
large fixture. Keep the useful investigation even when no patch is justified.

For example, an agent proposes a new harness for an exception path already covered
by a supported integration test. Demonstrating that the harness rejects a mutant
is insufficient: identify an uncovered contract and proportionate fixture, or
recommend no PR. Conversely, a reproduced crash on supported input can justify a
small correction without inventing a universal maintainer-approval gate.

A rejected value premise does not authorize new functionality, an unrelated issue
or resubmission of the same work under a different title. Return the finding and
stay within the user's selected scope.

## Hand off one bounded contribution

Use an existing issue/PR or concise response for these facts; no mandatory new log:

- Target/root/base, instruction owners, issue and current overlap evidence.
- Expected versus observed behavior and reproduction/source evidence limits.
- Smallest owned change, exclusions and compatibility risk.
- Allowed verification, test discovery and the requested delivery state.
- Next action or the one consequential missing decision.

For an authorized fix, continue through [bug fixing](bug-fix.md), appropriate
[language guidance](../../language-best-practices/SKILL.md), then
[PR delivery](opening-a-pr.md) only if requested. For an existing submitted PR,
use [bounded PR iteration](pr-iteration.md). See the
[worked contribution](../references/contribution-examples.md) for the boundaries.

The [source record](../references/contribution-sources.md) preserves reviewed
inspiration separately from the original skill licenses.
