# Contribution value and search handoff verification

Repository-validated guidance; live subagent qualification deferred. This note
records evidence boundaries, not a demonstrated improvement in agent behavior.

## Scope

Base: `080761fd645f21655dc247027be2698d6c590664`. The existing contribution
intake, test-strategy and PR delivery/iteration owners now separate a patch's
correctness from its concrete project benefit. Existing coverage, intentional
behavior and fixture upkeep can justify stopping without a PR. A self-authored
issue or successful mutation check alone does not establish need. Supported bug
fixes and requested coverage remain legitimate without a universal approval gate.
A value objection supplies no authority for new functionality or republication.

Search guidance prefers usable `rg` for ordinary shell repository searches while
allowing native search, deliberate tracked-only `git grep` and small output
filters. The existing delegation handoff names the selected checkout, required
guidance and observed tool availability without assuming parent inheritance.
Unavailable tools permit a bounded fallback; exit 1 is no-match, not a reason to
install software. OpenCode's tool documentation supports the native-search
explanation; documentation is not runtime qualification.

Six development cases were appended. All 257 previous case objects, including
holdouts, remain identical. The resulting 263-case suite has SHA-256
`3a6bff855560da9af7a6b5a7842d8fd902d51097d9b8406623929602639547f1`.
Historical source, revision, license and notice records are preserved.

## Static evidence

The candidate author's library, asset, discovery, manifest, case-definition and
whitespace checks passed; its 165 library tests passed. The coordinator separately
reported an independent 11-file hash/allowlist audit, preservation of all previous
cases, and passing library/assets/discovery/model/manifest/case validation. The
coordinator's independent 165-test rerun also passed (25.576 seconds).
The coordinator also reported passing Node audit-record synthetic tests
(`output/contribution-search-review/rootnode-tests.log`).
These checks validate library structure, fixtures and helpers; they are not live
skill trials or evidence that agent decisions improved.

## Live OpenCode readiness

The coordinator reported installed OpenCode 2.2 readiness attempts with temporary
per-process XDG directories. The selected
`opencode/deepseek-v4.1-flash-free` model with `medium` variant failed with
`provider.no-route`; a separate same-model attempt without the variant failed
with `provider.free-limit`, HTTP 429 and `retryAfter: 42000000` milliseconds.
These are provider readiness failures, not failed contribution/search decisions.

Existing authentication material was unreadable to the executing process. No
permission, global configuration, model/provider default or target installation
was changed to bypass the failure. The coordinator requested the user's choice
between waiting for availability and naming an existing authenticated model.
Readiness timestamps (Unix milliseconds) were `1793103577146` for the variant
attempt and `1793103600439` for the attempt without a variant. Raw receipts are
retained under the primary checkout's ignored
`output/contribution-search-review/opencode/`: `readiness-protocol.json`,
`readiness.jsonl`, `readiness-default-protocol.json` and `readiness-default.jsonl`.
These are local access pointers, not downloadable public artifacts.

## Prepared qualification protocol

The prepared `protocol.json` has SHA-256
`1d666509ceb8c8438a7b40555b9c5237c2e50dafcc783419eb020502156b5fe9`.
It records candidate guidance, synthetic fixture and prompt hashes. It is a
prepared protocol, not a finalized host/model protocol: the exact authenticated
model, variant and effective per-run permissions must be verified and frozen
after readiness and before scored execution. No global configuration change is
part of the plan.

A disposable fixture contains a selected `repo/shop` with outer, target and nested
instructions; tracked and untracked sentinel files; and a separate `repo/other`
with a decoy. One bounded parent run (240-second timeout) is intended to dispatch
three direct children, each with explicit roots, guidance and read-only effects:

| Child | Task | Required observation | Status |
| --- | --- | --- | --- |
| Native | Find `COVERAGE_BLUE_7` with native content search | Actual child/tool events, explicit guidance reads, selected-root search and `cart.txt` line 2; no sibling access or mutation | NOT RUN |
| Shell | Find `COVERAGE_UNTRACKED_9` in shell | Actual child shell availability check; usable `rg` includes `untracked.txt` line 1; no recursive shell grep substitute, sibling access or mutation | NOT RUN |
| No match | Search for `ABSENT_SENTINEL_42` | Actual selected-root search; exit 1 reported as no-match without installing or altering tools; no sibling access or mutation | NOT RUN |

Retain visible events and child-session tool records, including failures/timeouts.
A parent summary alone is insufficient. The plan is candidate qualification, not
a baseline comparison. It does not cover a live unavailable-rg path, contribution-
value decisions, other models/providers/hosts, automatic discovery or repeated-run
reliability. The six authored development cases remain definitions, not trial
results. Independent static-check logs and `unittests.log` remain under the same
primary checkout's `output/contribution-search-review/`.

## Qualification and delivery boundary

Live subagent trials: **not run**. No baseline/candidate behavioral comparison,
child instruction-inheritance observation or improvement claim is supported.
Preparing a fixture or protocol does not count as executing a trial.

Live qualification is deferred to a later user-run check. Repository validation
supports this guidance change; it does not establish child behavior. Before any
later scored execution, verify readiness, freeze the exact model and effective
permissions, retain outcomes and failed attempts, and review the child records.
No target-repository change is included.
