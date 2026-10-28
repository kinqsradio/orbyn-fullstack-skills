# Worked contribution decisions

All repositories, revisions and outputs below are synthetic. They illustrate the
method, not a run of React, a hosted PR or a measured model evaluation. Use
[intake](../playbooks/contribution-intake.md),
[reproduction](../../how/references/reproduction.md) and
[iteration](../playbooks/pr-iteration.md) for the actual task.

## Local framework defect with uncertain issue availability

Request: “Fix issue 81 in the framework checkout; keep it local and add a
regression.” The target is `repo/widget-core`, not the skills library. Its own
instructions require source tests and exclude generated output. There is unrelated
dirty documentation. Network is unavailable; an issue snapshot predates checkout
revision `A`. Current assignment and competing PRs are unknown.

The agent preserves the dirty documentation and reads the framework's instructions
and test configuration. It traces a repeated-registration defect in source rather
than installing an application framework or REA. Intake records the stale issue
snapshot and unknown live availability, then continues the authorized local fix.
It creates no public claim or PR. A later publication decision needs fresh overlap
evidence and the requested destination.

## A green command that selected nothing

At baseline `A`, a synthetic test filter exits zero with `0 tests selected`.
This is missing evidence, not a successful baseline. The agent reads runner
configuration and discovers that development and production variants use different
selectors. The supported development selector finds one test; it fails because
two registrations produce two callbacks rather than the required one. An import
failure would not establish that contract.

At candidate `B`, the same assertion, fixture and development selector find one
test and pass. A nearby single-registration control also passes. Production-mode
execution is unavailable, so the report names it as unverified. The patch does not
change the test assertion or claim all framework modes passed. If the request had
only been to reproduce, the agent would stop at baseline evidence and the minimal
fixture, before editing production code.

## Intermittent failure with a useful limit

A disposable worker fixture loses a callback in 3 of 12 runs with the same seed
and scheduler configuration. That supports an intermittent observation. It does
not establish deterministic failure or a reliable rate estimate. Source tracing
points to cancellation ownership; a controlled cancellation case distinguishes
that hypothesis from slow I/O. Production replay is excluded, so the agent keeps
its source/fixture evidence and does not repeat real writes to improve a count.

## Review moved on while CI was green

PR `team/widget-core#19` initially points to `B`; its required tests pass. A review
thread from `A` says duplicate callbacks still occur. The agent reads every page
of threads and traces the current `B` implementation: the duplicate path is fixed,
but a cancellation path is still supported by the comment's scenario. It corrects
that path at `C`, keeps unrelated style advice out of scope, and records the
unresolved explanation locally because the user authorized code pushes but no
replies. Resolving the thread is a separate action.

The success at `B` is stale for `C`. At `C`, a required runner times out; one
permitted retry after a documented runner outage also times out. The chosen
two-attempt budget is exhausted. An optional platform lane legitimately skipped
under repository policy. The result is “pushed `C`; required CI unavailable;
optional skip explained,” with the failure receipts preserved. No merge occurs.

If required checks later succeed for `C`, the agent rechecks the head, base and
feedback. A draft or missing maintainer approval remains a separate gate. Only an
authorized merge with current satisfied rules reaches “merged”; a completed local
fix or empty check list never substitutes for that state.

## Issue, preview, PR and pickup

In synthetic `widget-core`, revision `A` drops an inherited timeout when a named
rule sets only a label. The user requests an issue description and screenshot.
The agent has `baseline-failure.png` from `A` and `candidate-success.png` from local
patch `B`. It follows [publication guidance](contribution-publication.md): the
issue shows the failing baseline with its configuration and scope. It keeps the
candidate capture for the requested local preview or a later authorized fix PR.
It does not upload either image when the user has requested preview only.

A different user explicitly requests a suggested fix in the issue. The agent can
include `B` as an unmerged candidate, separately from `A`'s observed failure and
without claiming acceptance. A universal ban on fixes in issues would be wrong.

The baseline is a source build of version 2.4.0 at `A`. A version bot requests
2.3.1. The agent verifies the source/build identity and presents version 2.4.0
first, with revision and build limits. It does not claim to know why the bot
misclassified the report or pretend an installed release was tested.

When PR delivery is authorized, the agent publishes the owned diff and matching
before/after results. Tests ran on `B`; the PR is subsequently rebased to `C`.
If inspection finds a changed timeout consumer, it reruns the affected check
before reporting current-head validation. If the rebase only changes unrelated
documentation and policy permits reuse, it explains that basis and explicitly
states tests ran on `B`, not `C`.

The existing receipt still says "uncommitted, no PR". The agent verifies local
commit and remote head `C`, reads back the submitted PR, and updates that receipt:
submitted at `C`; tests on `B`; relevant checks pending; automated review unavailable
due to quota. It preserves the baseline results as history. A new session picks
up those remaining gates instead of reopening the PR or treating quota as review
approval. Without remote access, it records the last observation as such.
