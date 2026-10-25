# Migration and engineering breadth follow-up — 25 October 2026

This follow-up evaluates the original 54-skill baseline against the revised,
uncommitted 34-skill candidate. It addresses the writer-fencing omission observed
in the [original 40-call comparison](2026-10-25-skill-consolidation.md) and samples
new onboarding, service, strategy, incident, preview and cleanup guidance.
It is not a rerun of the old cases or a comparison against the pre-fix 34-skill set.

## Method and evidence identity

The [reproduction package](2026-10-25-migration-followup-protocol.json) preserves
the frozen prompts, rubrics, fixtures, guidance inventories, SQLite oracle and
host settings. All cases are development cases, frozen before scored calls.
The lead author performed unblinded review; this is not independent review.

- Baseline: `4510c750f96af62a094e1193a473d6aad315e7ee`, 54 advertised skills.
- Revised candidate: uncommitted snapshot, 34 advertised skills; the same Git
  revision is only its ancestry anchor, not its content identity.
- Baseline guidance inventory: 271 files,
  `e8d3b28e37f6bdc16562ae1f8bd6526cb1280223449de0d5a179e5d057aaa8d5`.
- Revised candidate guidance inventory: 269 files,
  `1dcfea748335ce7245ba0c946201d80ab68736d606076bea3c4a5e3fbcd31ca5`.
- Frozen suite SHA256:
  `92183a7247f12e982f6fd70a1e3c4b9a3dcb2bf5b5835bdbdb2dc4f6317e6656`.
- Codex CLI `0.163.0-alpha.10.2`, `gpt-6.1-sol`, medium reasoning,
  `service_tier=default` requested; fast/ultrafast disabled. Effective backend
  service tier is not exposed. No claim of a verified standard-speed backend.
- Six migration cases, two repetitions, both conditions: 24 scored calls.
  Six breadth probes, one repetition, both conditions: 12 scored calls.
  At most two calls ran concurrently; 240-second per-call timeout; alternating
  pair order reversed for the second migration repetition.
- Fresh disposable checkout and ephemeral context for every call. Every actual
  prompt inventory was checked for exactly 54/34 names and no global or controller
  ancestry leakage. Authentication stayed in place; per-run overrides disabled
  unrelated configuration/tools without modifying user settings.
- One unscored exact-host readiness call. The immutable test runner and separate
  oracle were calibrated against the original defect and a corrected control.
  Visible outputs were captured; reasoning event content was discarded.

The distributed guidance excludes evaluation material and contribution-lab code.
Adding the new cases to the maintained evaluation suite after freezing did not
change any guidance bytes presented to subjects. The protocol and snapshots stay
immutable; later corrections must have a new identity and separate evidence.

## Results

All 36 scheduled calls completed without timeout; none were replaced. Whole-case
passes require every frozen criterion, so a missing control or handoff detail can
fail an otherwise useful answer. These are failure-sensitive task scores, not a
percentage measure of general engineering ability.

| New migration case | Baseline 54 | Revised 34 |
| --- | ---: | ---: |
| Direct SQL writer cutover | 0/2 | 2/2 |
| Paused lease writer | 0/2 | 2/2 |
| Unknown deployed/replay adoption | 0/2 | 2/2 |
| Partial conversion recovery | 0/2 | 1/2 |
| Actual SQLite admission repair | 2/2 | 2/2 |
| Private in-memory rename control | 2/2 | 2/2 |
| **Migration total** | **4/12** | **11/12** |

The baseline migration plans often had sound enforcement proposals but omitted
explicit old-writer rejection plus legitimate current-writer evidence. Its recovery
plans also lacked the required user/queue-health gate. The revised candidate
included the paired writer controls in every applicable plan. Its one failure was
recovery repetition 1: it did not explicitly gate resumption on user/queue health.
Repetition 2 tied user outcomes and replay disposition to reopening and passed.

All four actual SQLite repairs passed the separate oracle and final tests. Each had
an assertion failure on the original source before repair, and its final tests
failed again against the original blind-write implementation. Inspection confirmed
conditional SQL admission inside an owned transaction. Both versions kept the
private rename proportional; no durable migration ceremony was introduced.

| Breadth probe (one repetition) | Baseline 54 | Revised 34 |
| --- | --- | --- |
| Onboarding/review explanation | Fail | Fail |
| Service readiness | Fail | Fail |
| Cross-team platform adoption | Fail | Pass |
| Incident handoff | Fail | Pass |
| Portable HTML preview | Pass | Pass |
| Resource/worktree cleanup plan | Fail | Pass |
| **Breadth total** | **1/6** | **4/6** |

The breadth failures were specific omissions, not wholly incorrect answers:

- Both review explanations proposed exception cleanup checks but omitted a normal
  successful-path control.
- Both service plans covered capacity and recovery but omitted privacy/retention.
- Baseline adoption named delivery/support roles but left the investment decision
  owner unspecified.
- Baseline incident aftercare assigned prevention work without a causal timeline
  and verifiable corrective-action method.
- Baseline cleanup protected work and shared resources, but omitted the restart
  entrypoint requirement when stopping a server-dependent preview.

There were no candidate-only whole-case failures in these paired samples. This
supports improvement on the sampled criteria; it is not proof of noninferiority.

## Corrections and six-call development recheck

Command review showed that coaching selected `how`, bypassing the new workflow
method, and service readiness selected backend guidance without the architecture
reference. Three concise entrypoint corrections were made after the frozen round:
`how` now links coaching and asks for failure/normal controls; backend design now
hands service readiness to its operating contract including retention/diagnostics;
data migration now explicitly requires separate reopening and closure health gates.

The resulting uncommitted candidate has 269 guidance files and inventory hash
`1c3b3aac41ad9d9f2ed7b8cf23ae9ae9a7a2fb7de92a90884ff839453d48d18a`.
The [separate recheck protocol](2026-10-25-engineering-gap-recheck-protocol.json)
froze this new identity and the same three prompts/rubrics before six further calls.
Each condition ran once per case in a new checkout; another unscored readiness probe
confirmed the host. All six completed without timeout or replacement.

| Previously failed case | Fresh baseline 54 | Corrected 34 |
| --- | --- | --- |
| Partial conversion recovery | Fail | Pass |
| Onboarding/review explanation | Fail | Pass |
| Service readiness | Fail | Pass |
| **Recheck total** | **0/3** | **3/3** |

The corrected answers supplied distinct user/data/queue reopening and closure
gates, paired cleanup controls, and export retention/deletion with safe diagnostics.
The service answer selected architecture directly in this recheck; its pass cannot
be causally attributed to the backend link alone. This is an unblinded development
recheck on observed failures, not held-out generalization. Do not erase the earlier
failures, combine these denominators into a single final-snapshot score, or claim
the full original/breadth suite was rerun after these three edits.

Routing scores are recorded separately: migration 10/12 each, breadth 4/6 baseline
and 5/6 candidate, recheck 2/3 each. Frozen expectations missed valid `how` coaching
and `orbyn-plan` rename routes. The maintained cases now accept those owners and
no longer suggest adversarial `interrogate` for ordinary coaching. Frozen routing
scores and protocols were not rewritten. Active suite: 176 cases; this does not
mean 176 live cases ran.

## Browser observations and artifact lifecycle

Both subjects created real self-contained HTML with local simulated state and
honestly reported no rendering. After source scoring, the lead copied each exact
HTML to retained ignored `output/migration-followup-20261025/human-preview/` and
opened it through a task-owned loopback-only static server. The candidate tab was
retained for the human; the baseline inspection tab was temporary.

The lead exercised identical synthetic title/notes, first-save failure, keyboard
retry, success, reset, Tab traversal and reset during a pending save. Draft and
record identity survived failure/retry, and reset restored initial state. Saved
screenshots record candidate 571×988 and baseline 1280×720 host views. These unequal
views are observations, not a comparative visual score or a mobile/zoom matrix.
Source-only outcomes, rendered interaction, and human review remain distinct.

The retained folder contains unchanged HTML, screenshots, a browser receipt and
opening/restart notes. Both files open directly without a server. The task server
serves only that dedicated directory on loopback; its PID/session/port are recorded
locally. Retain it while needed for handoff, then stop only that owned process.
Preserve the complete preview/evidence outside the worktree and reopen it before
eligible worktree removal. The worktree remains active because changes and human
review are pending; no worktree, shared volume or foreign process was removed.

## Validation and decision

All 42 subject checkouts preserved guidance, discovery links, sentinels and allowed
file boundaries; none committed changes. Command review found no production,
publication, install, message or cleanup effects. Library checks validate 34 skills,
licenses/provenance, generated discovery, manifest, links and the active evaluation
suite. The 149 library tests pass. These checks are separate from live outcomes.

Keep this candidate local and uncommitted as requested. The sampled writer-fencing
gap and three later output gaps have positive follow-up evidence. Before broad
enterprise claims or a release decision, obtain independent review and exercise a
real multi-package repository, concurrent writer boundary, integrated frontend/API,
accessibility/native cases as applicable, and actual disposable environment teardown.


## What the probes can establish

The SQLite task repairs real code and runs real tests against a disposable local
database. The external oracle checks current admission, stale/future epoch and
revision rejection, unchanged rejected state, duplicate rejection and reopened
state. Lead inspection also checks the mutation's atomic predicate; subject tests
must fail on the original source before repair and again in a counterfactual copy.
This is not a concurrent fleet, direct SQL bypass or production-database qualification.

The HTML task creates an actual self-contained interactive artifact. Subjects have
no renderer and may not start servers; source outcomes and later lead browser
observations are separate. Agent interaction does not substitute for human usability
research, complete accessibility evaluation or real frontend/backend integration.

The remaining probes are plans and review drafts. They do not execute migrations,
rollouts, incidents, cross-team adoption or cleanup. One breadth repetition cannot
establish robustness. These cases do not qualify a Microsoft-, Xero- or Google-scale
codebase, every language/platform, or a person's engineering level. Passing this
sample cannot establish statistical equivalence or universal completeness.

Raw answers, visible command captures, inventories, receipts and review records
remain in ignored `output/migration-followup-20261025/` in the owning worktree.
They are retained local evidence, not downloadable public artifacts. The public
package contains only synthetic reproduction inputs and concise result reporting.
No commits, publication, consumer promotion, deployments or external messages.
