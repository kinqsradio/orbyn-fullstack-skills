# Live Codex contribution execution — 25 October 2026

Both conditions reproduced and fixed the synthetic defect, handled the review
feedback and eventually delivered correct local PR heads. The corrected guidance
also stopped publication after a controlled commit failure in both trials; the
baseline pushed the unchanged starting commit before recovering in both trials.
This supports an explicit commit-before-push gate, not a general code-quality or
model-performance claim.

## Completed matched study

Each condition ran twice through two stages: reproduce/fix/deliver, then inspect
paginated review feedback and update the same PR. These were eight actual Codex
calls with fresh context for each stage, real Python tests, commits and pushes
to local bare repositories. The PR provider was a controlled offline fixture;
there were no hosted GitHub PRs, external replies or merges in these trials.

| Executed evidence | Baseline | Corrected candidate |
| --- | --- | --- |
| Intended failing regression before source edit | 2/2 | 2/2 |
| Eventually correct fix and review behavior | 2/2 | 2/2 |
| Final local head = pushed head = successful required CI head | 2/2 | 2/2 |
| Preserved dirty files, instructions, target skill, tools and hooks | 2/2 | 2/2 |
| Stopped dependent push until the failed commit succeeded | 0/2 | 2/2 |
| Complete two-stage flow meeting every frozen criterion | 0/2 | 2/2 |
| Graded stage outcomes | 2 pass, 2 fail | 4 pass, 0 fail |

Both baseline failures are the first-stage delivery criterion. Their eventual
correct code and feedback responses still passed the executable behavior checks.
The later valid push does not erase an earlier task-branch push of the seed commit.
The remote's real reflog and captured commands establish that intermediate effect.

The feedback fixture returns three items across two pages. All four trials added
meaningful coverage for replacing a registration during emit while calling its
old disposer, declined global callable deduplication because distinct identities
are independent, and declined cleanup of unrelated local work. Final subject tests
failed against an API-compatible implementation retaining the stale-disposer bug,
with assertion failures and zero setup errors. Independent behavior checks also
verified latest replacement, safe/idempotent disposal, separate keys/topics and
the starting emit snapshot. Final subject suites selected seven or eight tests,
with no failures or skips; the two original controls remained intact.

## Frozen inputs and settings

- Baseline guidance: `5684ee576ba85d07be317ca91e9f3e02452f4993`.
- Corrected candidate guidance: `7e85145e303aed5aa5dc5585371cc9f259cfba69`.
- Primary-study fixture and case suite: `025c53eac1181840963d0a1ea95030d7499762ab`.
- Suite SHA-256: `e82f2d9adb5ce56f8340780a9f8f670844865689fc1fe7a426331f629032733e`.
- Protocol SHA-256: `4d11ab8d880025c02133c809cc5477c2c7bdaf6f24ef94795ac3b319ec5fb361`.
- Common seed commit: `da7e97aad04f19b9983663ff0694376a5d5793ca`.

The [declarative protocols](2026-10-25-contribution-execution-protocol.json)
include both studies, source inventories, settings, aggregate receipts and
reproduction/grading steps. Guidance snapshots exclude evaluation definitions,
lab assets and the controller helper. Actual prompt inventory exposed exactly
54 intended library skills plus the existing target-owned skill in both conditions.

Host: desktop Codex CLI `0.163.0-alpha.10.2`, model `gpt-6.1-sol`, medium effort,
requested default service tier, Fast/Ultrafast disabled. The server's effective
processing tier was not independently exposed. Runs used ephemeral isolated host
state, `workspace-write`, explicit trial-local writable paths, no browsing, apps,
plugins, memory or delegation, and a 300-second budget per stage. All eight scored
calls completed without timeout. The exact primary layout and one-time hook failure
were qualified by an actual write/commit/local-push/PR/CI probe before inference.

## Earlier blocked study and the correction

The first experiment used sibling linked worktrees, candidate `3d936ae1cc980d36f80619ca8665266d0ee60e95`
and fixture/suite `fcb6197f64ace68cc80ca68e0c3eb5fba72215dd`.
Its four first-stage calls all reproduced and corrected the defect and preserved
local work. The host denied linked-worktree Git index access despite the explicit
writable-path configuration. No owned commit or PR was produced, so all four
delivery outcomes remain unverified and the four dependent feedback calls were
not run. They are not silently scored as model failures or mixed into the table.

The primary-clone readiness probe had not qualified linked metadata access.
Three of those blocked attempts also pushed the unchanged seed after failed
stage/commit operations. This exposed a concrete workflow gap in command sequencing.
No alternate index, Git metadata path, sandbox relaxation or hook bypass was used
to rescue the trials. Their patches, errors and receipts remain preserved.

The next study used fresh primary clones, a controlled one-time commit failure,
recorded remote ref history, stronger development delivery criteria and composed
review coverage, all frozen before its calls. The essential gate was placed in
the workflow entrypoint as well as its PR reference before inference. An unused
preflight protocol/setup is retained separately. Earlier observations were not
regraded against the new criteria.

## Changes and evidence limits

The [workflow entrypoint](../../skills/orbyn-workflow/SKILL.md) and
[PR gate](../../skills/orbyn-workflow/playbooks/opening-a-pr.md#commit-and-push-gate)
now require a successful owned commit before dependent publication, checked command
exit status, bounded normal retry and verification of intended tree/remote head.
The [worktree skill](../../skills/orbyn-worktree/SKILL.md) requires capability
probes matching the intended checkout topology. The existing creator owner gains
the original, portable [execution lab and method](../../skills/orbyn-skill-creator/references/contribution-execution.md).
Seven deterministic calibration tests cover fixture behavior and managed-copy
packaging. Normal CI invokes no models or external accounts.

Local validation passed all 129 Python tests, all 65 bundled audit-record validator
fixture tests, library/assets/discovery/manifest checks and `git diff --check`.
These checks validate the library and helper contracts; the live results above
come from the separately captured model calls.

This is a two-repetition development comparison on one synthetic project, with
unblinded lead inspection and no independent or heldout qualification. Conditions
differ in more guidance than the single gate, so this is descriptive evidence,
not causal attribution or a statistical performance estimate. Hosted pagination,
webhooks, branch protection, remote review authority and real-project acceptance
remain unqualified. Claude was not tested.

Full visible captures, source/test snapshots, Git/provider evidence and grading
receipts remain in ignored local `output/contribution-execution-20261025/`, with
the second study under `primary-study/`. A verified local archive also preserves
the disposable clones, uncommitted patches and actual Git history. They are not
downloadable public artifacts.
This release keeps all 54 canonical owners, adds two development cases (113 total),
preserves prior cases/holdouts and upstream notices, and changes neither Orbyn's
consumer pin nor the deferred REA engine/source revision.
