# Contribution artifact and delivery evidence evaluation

## Change and scope

The existing `orbyn-workflow` owner now distinguishes bug reports, local previews,
fix PRs and delivery handoffs. Its conditional
[publication reference](../../skills/orbyn-workflow/references/contribution-publication.md)
keeps baseline/candidate evidence identifiable, screenshots necessary to the
visual claim rather than mandatory, versions and tested revisions truthful, and
existing delivery receipts reconciled. Explicit requests for proposed fixes in
issues remain supported. No new skill, mandatory log, target installation,
Orbyn sync or REA engine change is introduced. Existing credits are unchanged.

Nine synthetic development cases were appended to the active suite. All 355
previous case objects, including holdouts, remain unchanged (364 total). Cases
and guidance were frozen before each collection; failed observations were retained.

## Recorded comparison

| Collection | Baseline | Candidate | Interpretation |
| --- | --- | --- | --- |
| Initial nine cases, one trial each | 8/9 pass | 8/9 pass | Aggregate tie; different failures |
| Separate three-case follow-up, one trial each | 2/3 pass | 3/3 pass | Targeted support for the correction; not a fresh nine-case score |

Initial baseline revision: `6071f248fb4fb4ff0dfd7fc76a1971891e141e7a`. Initial candidate:
`6c74fa786dbb2b14abd76e712cd1521239cbdcd0`. Follow-up candidate:
`32e81a8a06eb32287f6548a1618c3623ed56e128`. Later report-only commits do not change the exercised
guidance. The unchanged baseline was rerun for the follow-up, not borrowed from
the first comparison. Do not combine the collections into a new full-suite score.

| Case suffix (`contribution-evidence-`) | Initial baseline | Initial candidate | Follow-up baseline / candidate |
| --- | --- | --- | --- |
| issue-baseline | Fail | Pass | Fail / Pass |
| issue-proposed-fix | Pass | Pass | Not rerun |
| preview-only | Pass | Fail | Pass / Pass |
| version-bot | Pass | Pass | Not rerun |
| rebase-reuse | Pass | Pass | Not rerun |
| rebase-consumer | Pass | Pass | Not rerun |
| handoff-state | Pass | Pass | Not rerun |
| review-unavailable | Pass | Pass | Not rerun |
| no-screenshot | Pass | Pass | Pass / Pass |

The baseline put local candidate imagery into the issue-only draft in both
collections. The initial candidate avoided that mistake, but its preview asserted
“the same input” without supplied fixture linkage. That failed evidence identity.
The correction explicitly forbids inferring equivalent inputs from filenames or
a before/after pair. In the follow-up, the candidate identifies the missing
fixture/build linkage instead. Both conditions honored the explicit proposed-fix
request and avoided unnecessary screenshots for a nonvisual parser defect.

## Protocol and limits

Use the [initial protocol](contribution-evidence-protocol.json) and
[follow-up protocol](contribution-evidence-followup-protocol.json) for exact
revisions, selected cases, prompt wrapper and guidance hashes. Prepare both
conditions with the evaluator using those case IDs, the same active suite and
protocol bytes. Extract the listed files at each revision in listed order,
joining successful `git show` outputs as `FILE <path>\n<contents>` separated by two
newlines; the new reference is absent from baseline. Verify the resulting hashes.
Inject that bundle and the case prompt into the frozen wrapper, without rubrics.
Run fresh sessions sequentially in the stated alternating order. Capture visible
output and review it against the frozen criteria, then use `grade` and `compare`.
Do not execute this prose as an automatic publication or model-call authorization.

Host: Codex CLI 0.163.0-alpha.10.2, installed desktop bundled binary. Configured
model `gpt-6.1-sol`, reasoning `medium`, service tier `default`; effective model/
effort were not independently echoed by the captured execution events. Supported
per-run controls disabled user config, project instructions, host skill discovery,
plugins, apps, memories and execution features. An empty disposable workspace and
prompt inventory excluded library/global skill content; supplied guidance was
injected deliberately. The readiness answer still advertised orchestration
functions, so this does not establish that tools were unavailable. All 24 scored
executions completed without observed tool invocations, timeouts or transport
failures. There was one separate readiness call and no retries. Startup warnings
about experimental discovery and disabled code mode are retained as warnings,
not successful tool execution or failed task attempts.

The initial 18 executions recorded 172,699 ms summed runtime, 262,222 input and
2,412 output tokens; the six follow-up executions recorded 69,708 ms, 87,532 input
and 952 output tokens. These are observed CLI usage totals, not a cost or speed
benchmark; cached input and varying answer length preclude a quality/speed claim.

The owning agent manually reviewed the captured answers and recorded exact
excerpts, including the failed claims, for the existing evaluator. This was
non-blind author review, not independent assessment. Routing is unmeasured:
`selected_skills` stays empty because no skill-read tool events occurred; outcome
grading is separate. These are instructed synthetic drafting/decision trials,
not natural discovery, real GitHub mutations, screenshot inspection, source fixes,
CI execution, native qualification or Claude results. One trial per condition
cannot establish reliability or broad engineering improvement. Six cases were
not rerun after the targeted guidance correction.

Full prompts, invocation options, inventory, readiness, visible captures, answers,
manual verdicts, hashes and comparison outputs remain in ignored
`output/contribution-evidence/` in the task worktree; they are not downloadable
public artifacts. The public template ships the reusable cases, protocols and
this concise result, without consumer session logs or credentials.

## Library verification

Final local checks passed: catalog/host discovery (36 skills), library inventory
(440 skill assets), links/provenance/licenses (305 Markdown documents), all 364
evaluation case definitions, `git diff --check`, and 176 Python unit tests in
23.641 seconds. The evaluator deliberately exits 1 for recorded baseline/candidate
failures; it exits 0 for the corrected three-case candidate. Comparison provenance
checks passed for both separately frozen collections. Static/fixture checks
establish packaging and evaluator behavior, not live-model quality. Hosted PR
checks remain a separate delivery gate.
