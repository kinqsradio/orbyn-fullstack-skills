# PR delivery

For any new branch, follow the consuming project's naming policy and the
local [branch guidance](../../orbyn-worktree/SKILL.md#sibling-location-and-names).
Use a neutral purpose-based name, never an agent/vendor/tool/model prefix or
suffix. Preserve an existing branch when continuing work; do not rename a shared
remote branch without an explicit request.

Follow [local branch and fork ownership](../../orbyn-worktree/SKILL.md) before
publishing. Reuse the task branch; keep delegate branches local. For a company
upstream, prefer an approved permitted private personal contribution fork when supported, with a stable
name such as `Orbyn-contributions`, rather than spawning company-remote branches.
Verify account, upstream relationship, actual visibility and exact push destination.
If a public-parent native fork cannot be private, keep work local/private until
public PR publication is explicitly authorized; a private standalone backup is not
a native upstream PR source. Follow the owning policy for that transition.
If no permitted delivery path exists, preserve the local patch and report the
blocker; never publish private company code into a public fork or silently push
to the company remote instead.

Use [delivery feasibility](contribution-intake.md#check-delivery-feasibility-when-submission-is-the-endpoint)
for a requested submitted endpoint before expensive work; unknown capacity remains
unknown, and a rejected submission needs evidence-led diagnostics, not probe PRs.

Confirm PR creation is part of the requested delivery. Inspect the exact owned diff, checks and target branch. Exclude unrelated files and secrets. Write a [proportionate body](../references/contribution-publication.md#scale-the-body-to-the-review-decision) with actual evidence, material tradeoffs and limits, create the requested PR and attach it when the host supports attachments. Merge or publish only within authorization. No automatic babysitting job or separate session.

Use the parent [workflow](../SKILL.md) and repository scope.
Use [publication evidence](../references/contribution-publication.md) for issue/PR
content, tested revisions, readback and reconciliation of an existing delivery
receipt. A bug issue describes the affected behavior and reproduction; the fix PR
describes the correction and validation. Keep candidate success out of the issue
by default unless a proposed-fix discussion is requested or required by the target.


## State the benefit before publication

Use the [contribution value decision](contribution-intake.md#establish-value-separately-from-correctness)
to explain what this exact diff improves, why existing behavior/coverage is
insufficient, and the relevant verification. A self-filed issue, passing suite or
successful mutant rejection alone does not establish the need for a PR. Keep the
body proportionate; no new mandatory proposal document is required. Revisit a
changed premise or excessive fixture burden before publishing. A sound finding
that needs no patch can be the completed result.

## Commit and push gate

Verification, staging, commit, push and PR/CI actions are dependent steps. Stop
dependent actions when a prerequisite fails. Use checked return codes or `&&`
for a shell sequence; separators such as `;` can push the old HEAD after a failed
commit and return the later command's success. A final zero exit code does not
establish that the earlier commit succeeded.

Before pushing, verify the successful owned commit, its tree/diff and actual
HEAD against the validated source/tests. Preserve unrelated index/worktree data;
never use broad staging or commit unrelated files to obtain a clean status.
After pushing, verify the remote ref matches that intended commit before opening
the PR or accepting CI evidence. A pushed baseline is not a delivered fix.

A transient hook or transport failure needs an identified cause and bounded
permitted retry. Do not skip hooks, change the Git index/metadata location,
disable controls or use an alternate execution path to bypass a host denial.
Preserve the local patch and report the exact blocked dependency when the
required operation remains unavailable.

For an upstream contribution, start with [intake](contribution-intake.md) to check
the target instructions, issue overlap and reproduction. Once a PR exists, use
[bounded iteration](pr-iteration.md) for feedback, current-head checks and honest
delivery gates. PR creation alone does not authorize comments, merge or a monitor.

## Disclose how it was built

Where the target uses this library's template, fill in the Agent disclosure section from
what actually ran: tools, exact model IDs, effort and what a person decided. Add a new
`authoring` entry in `provenance.json` for each changed library skill. Follow the target's
own PR template and policy where it has one. Fill these in from the record of the work,
and never guess. In this library, review is requested automatically once the section is
complete and CI is green.

## State how to test, the risk and how to undo it

Every PR says, in a line each, using the target's own template fields when it has them:

- **How to test:** the command, page or steps a reviewer can repeat, and what they show.
- **Risk:** `low`, `medium` or `high`, set by what the change can break, never by who
  wrote it. Low: docs, tests, isolated internals, behind a flag. Medium: ordinary
  behavior change with tests. High: data, money, auth, security, migrations, public
  APIs, CI or release workflows, or anything hard to undo. Name who or what is affected.
- **How to undo:** revert the merge commit, turn off a flag, or the exact steps when a
  plain revert is not enough (data written, a migration, a published release).

Some paths always need a person, whatever the risk level: the target's CODEOWNERS and
sensitive paths such as auth, billing, CI workflows and release. Follow the target's
rules for how many approvals each level needs. An agent's review or approval never
fills a slot that calls for a human, and an approval covers only the commit it saw.
Prefer small, reversible changes: when undo is hard, say so and ask for a human review
instead of a quick approval.

## When three rounds do not resolve it

When the task has PR authority and a review or fix loop ends its third round with
a finding still open, push the work and open it, or keep it, as a **draft** PR. Do
not leave it only in chat, and do not drop it. The description lists each open
finding, what each round tried, and the failing check or reviewer verdict. Never
mark that PR ready for review and never merge it; the PR gate ignores drafts. The
user decides: fix it, give a hint and allow more rounds, or close it. Without PR
authority, report the same three items in chat and keep the branch local.

## Merge only on the user's instruction

Merge when the user says to, never because checks went green. Confirm every required
check passed on the exact head you tested, and merge with that head pinned (for
example `gh pr merge --squash --match-head-commit <sha>`). If a review rule blocks a
PR the user authored and owns, and the repository lets its owner bypass that rule,
use the bypass on the user's instruction (`--admin` on GitHub). Never use a bypass to
skip a failing or missing check, or for someone else's PR.

## Make the review path explicit

For a substantial diff, point reviewers first to the core behavior, then wiring,
then generated/mechanical edits. Trace one tricky input through old and new code
when that explains a consequential difference; label unexecuted traces accordingly.
A small PR needs no new canvas or document. For an expressly authorized history-only
rewrite, capture the pre-rewrite tree and compare the post-rewrite tree; unexpected
content changes need review and checks. This does not authorize rewriting others'
history, staging dirty unrelated files or force-pushing.

At the requested delivery endpoint, reconcile the task/issue's actual PR identity
and independent source/resource states, then make the [closeout decision](../../orbyn-worktree/references/task-closeout.md).
Verified commit/push and a published PR do not imply merged work or permission to
remove its checkout, evidence or running preview. Keep private recovery notes local.
