# Contribution artifacts and publication evidence

Use when preparing or updating an upstream issue, fix preview, PR or delivery
handoff. Follow the target template and the user's requested purpose. This is a
content check within existing publication authority, not another approval stage.

## Select the artifact before selecting evidence

Identify the destination (repository and issue/PR), requested change, and whether
it explains an observed failure, proposes a repair, or verifies a submitted fix.
Do not assume that every useful local result belongs in every public artifact.

| Artifact | Default content | Conditional content |
| --- | --- | --- |
| Bug report | Supported failing input, expected/actual behavior, baseline version/revision, reproduction, impact, workaround and limits | Source diagnosis or proposed fix when requested or useful under the target's conventions; label it separately |
| Local fix preview | Baseline failure and candidate result with matched inputs, owned diff and unverified boundaries | Screenshots only when they explain the behavior; preview permission does not imply upload |
| Fix PR | Problem, correction, regression coverage, baseline/candidate results, exact tested revision and limits | Before/after captures and relation to the issue when relevant |
| Follow-up or handoff | Actual current state, changed facts, remaining gates and next action | Existing receipt updates when stale; no new tracker for a routine change |

A **bug issue reports the problem**: what the user did, expected versus actual
behavior on the affected version, minimal reproduction, impact and relevant
failure evidence. It should make sense even if no fix has been written. A failing
test, log or screenshot can demonstrate that problem; passing tests or corrected
output from a local patch are not the affected version’s observed behavior. Do
not lead the issue with “I fixed this,” the implementation diff or candidate
success merely because that work is available. Keep the title about the symptom.
Label a suspected cause as a hypothesis unless the evidence establishes it.

A **fix PR reviews the change**: connect the original problem to the correction,
explain the resulting behavior, relevant baseline/candidate validation, material
tradeoffs and remaining limits. Link the issue when available instead of copying
the complete investigation. Its title may describe the correction.

A separate proposed-fix section or before/after comparison may belong in an issue
when explicitly requested or expected by the target template. Keep the problem
and baseline reproduction primary, identify an unmerged candidate as such, and
do not imply acceptance, merge or release. This also applies to issue-only
screenshot updates: use the failing baseline by default and keep candidate success
for a requested fix discussion, local preview or PR.

## Scale the body to the review decision

Size an issue or PR description by the change, target template and reviewer’s
needed decision, not by the length of the investigation. Lead with the concrete
trigger/problem and resulting behavior. For an issue, include the smallest useful
reproduction, expected/actual result and material version/environment limits. For
a PR, explain the correction, actual validation and material risks or tradeoffs.
A small PR often needs one or two paragraphs plus validation. An issue of roughly
250–400 words can be useful for a bounded defect; that is an example, not a quota
or universal cap. Preserve required template fields, and use more space when a
complex migration or compatibility decision needs it.

Keep full source traces, experiment matrices, chronology, alternatives and process
receipts in existing supporting evidence unless they change that decision. Do not
copy the whole investigation into the body or create another mandatory report.
Link supporting material only when suitable and accessible to the recipient;
private or ignored local evidence must not be the only route to understanding or
reproducing a public issue. No automatic upload or publication is implied.

When shortening, remove repetition and incidental mechanics before removing a
consequential tradeoff, reproduction prerequisite, safety constraint or unverified
boundary. Before delivery, check that the reader can still understand the failure,
assess the correction and see the remaining risk. Concision is not a substitute
for evidence, and a complex change is not a reason to reproduce every receipt.

Synthetic contrasts (illustrations, not executed results):

- **Small parser defect, two artifacts:** Issue title: “Explicit zero is treated
  as missing.” Body: “On version 2.4 at baseline A, `parseCount({count: 0})` returns
  missing. Expected: zero. Passing an absent key still returns missing.”
  PR title: “Preserve explicit zero in count parsing.” Body: “Replace truthiness
  with key-presence checking. The zero assertion fails on A and passes on B;
  the absent-input control passes on both. Parser coverage only.” The issue
  reports the affected behavior; the PR describes the correction and its supplied
  validation. Neither needs the complete source-search history.
- **Mixed-writer migration:** Keep writer fencing, resumable backfill, cutover and
  recovery prerequisites, compatibility evidence and untested boundaries in the
  review body. If roll-forward was chosen because old writers cannot represent
  the new keys, retain that tradeoff when shortening. Put the full batch matrix
  and source trace in supporting evidence; allow a longer target-required body
  when reviewers need those migration decisions to assess safe delivery.

## Bind claims to their evidence

Screenshots are optional: use them only when necessary to explain or verify a
visual symptom, or when the user requests them. Prefer a concise reproduction,
assertion or log for nonvisual behavior; do not launch a UI or create captures
merely to decorate a report.

For consequential screenshots, tests and runtime observations, retain the source
revision or exact dirty patch, baseline/candidate identity, material environment,
fixture and observed boundary. A concise caption and existing receipt can supply
this; no mandatory metadata form is needed. Do not infer matched inputs merely
from a before/after pair or suggestive filenames. If fixture/build linkage is
missing, state that limit instead of claiming an equivalent comparison. A filename
or a successful screenshot capture does not establish which build ran. Use the reproduction owner's
[method](../../how/references/reproduction.md) for the actual checks.

Present the product version in the target's expected version field, followed by
the source SHA and build/channel. Keep host OS and diagnostic tool versions
separate. Source package version does not prove an installed binary's version.
When a bot disputes a version, verify the actual tested artifact and read its
message. Explain the evidence; do not invent a parser failure or change a version
merely to satisfy the bot. An unresolved classification stays unresolved.

After a rebase or source change, state which revision was actually tested. Inspect
changed contracts, dependencies, configuration and relevant callers to decide
which gates require rerunning under the target's rules. If evidence is reused,
state its basis and limit: it was not executed on the new head. Neither a clean
rebase nor green checks on an older head qualifies the current candidate by itself.

Before an authorized publication, read the final payload as the recipient: right
destination and purpose, supported claims, correctly labeled evidence and no
private context. Preserve unrelated existing discussion. After publication, read
back the actual contents and attachment references when supported. Upload success
alone does not prove the right image was attached or rendered; report the
observed check. Recover a partial update before retrying rather than duplicating it.

## Reconcile the existing delivery record

When a commit, push, PR or merge changes the task's state, reconcile its existing
owning receipt before handing off. Verify the intended commit/tree and remote ref;
record the actual PR identity/head and outstanding CI/review/merge gates. Retain
older evidence as historical and mark superseded status, rather than leaving
"local and uncommitted" as the current instruction after publication.

On pickup, a receipt is a lead, not authority over current Git or remote state.
Resolve contradictions using current source and authorized read-only checks. If
remote access is unavailable, distinguish verified local state from last-observed
remote state; do not invent a submitted PR or repeat a submission blindly.

Review requested, review unavailable (for example quota), completed review, CI
passed, merge permitted and merged are distinct states. Keep required gates open
when review could not run; an unavailable reviewer is not a code failure or approval.
