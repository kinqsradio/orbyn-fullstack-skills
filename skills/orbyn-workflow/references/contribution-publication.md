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

For an issue-only screenshot update, default to the reproduced baseline failure;
do not silently turn it into a fix announcement because candidate screenshots
exist. A proposed correction or before/after comparison may belong in an issue
when the user or target asks for it. Identify it as a candidate, preserve baseline
evidence, and do not imply maintainer acceptance or a merged repair.

## Bind claims to their evidence

Screenshots are optional: use them only when necessary to explain or verify a
visual symptom, or when the user requests them. Prefer a concise reproduction,
assertion or log for nonvisual behavior; do not launch a UI or create captures
merely to decorate a report.

For consequential screenshots, tests and runtime observations, retain the source
revision or exact dirty patch, baseline/candidate identity, material environment,
fixture and observed boundary. A concise caption and existing receipt can supply
this; no mandatory metadata form is needed. A filename or a successful screenshot
capture does not establish which build ran. Use the reproduction owner's
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
