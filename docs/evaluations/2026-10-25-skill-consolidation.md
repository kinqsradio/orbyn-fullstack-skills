# Paired live consolidation trials — 25 October 2026

The 34-skill candidate passed 19 of 20 completed outcomes; the 54-skill baseline
passed 17 of 20. Both passed all executable repair, migration and small-edit trials.
However, one candidate migration-design answer omitted old-writer fencing while
its matched baseline answer included it. **Hold the commit pending a focused
follow-up on that omission.** This comparison does not establish zero capability
loss, statistical equivalence or qualification for an enterprise codebase.

## What ran

There were 40 scored live calls: 10 engineering task families, two repetitions,
and two conditions. Each call received a fresh synthetic checkout and ephemeral
context. Seven families assessed source-grounded analysis/design; two required
real Python source and test changes; one required a single TypeScript label edit.
The scenario mentions 60 packages, but the fixture is small: no 60-package
repository was actually built or migrated.

The [reproduction protocol](2026-10-25-skill-consolidation-protocol.json) contains
the exact synthetic inputs, frozen rubrics, guidance inventories, host settings,
submission order and executable oracles. These are development cases, not the
entire active 164-case suite and not a held-out evaluation. Full catalogs were
registered; the unchanged 14-skill core preset was not evaluated here.

- Baseline: commit `4510c750f96af62a094e1193a473d6aad315e7ee`, 54 entrypoints.
- Candidate: uncommitted `refactor/skill-consolidation` snapshot based on that
  commit, 34 entrypoints. Its snapshot checksum, not a candidate commit, identifies
  the tested bytes. No skill changes were made in response to these observations.
- Host: desktop Codex CLI `0.163.0-alpha.10.2`, model `gpt-6.1-sol`, medium effort,
  requested default service tier, fast and ultrafast modes disabled. The effective
  backend tier is not independently exposed. Same settings for both conditions.
- Read-only sandbox for analysis; workspace-write for the three edit families;
  240-second timeout; at most two calls active. Pair submission order alternated
  across cases and reversed on repetition two; scheduling was not randomized.
- Existing saved host authentication was used in place. User config, global skill
  discovery, memory, delegation, apps/plugins, web/browser and other listed
  optional capabilities were disabled per invocation. All 40 actual prompt
  inventories advertised exactly the intended 54 or 34 local skills, with no
  global skills or controller-checkout instruction ancestry.
- One unscored readiness call succeeded. The immutable fixture checker and both
  code oracles were calibrated before scored calls. Four known-good/known-bad
  oracle controls behaved as expected. No scored retries or timeouts occurred.

The lead agent reviewed the complete answers, visible actions and code evidence.
The lead also authored the candidate: this is **unblinded, non-independent
review**. Prose verdicts require judgment; evidence hashes prove capture identity,
not that the judgment is correct. Hidden reasoning was not retained.

## Results

Each cell is passed outcomes / completed outcomes under the frozen rubric. A
case fails when any required criterion fails; routing is measured separately.

| Task family | Baseline: 54 | Candidate: 34 |
| --- | ---: | ---: |
| Runtime impact and owner tracing | 2/2 | 2/2 |
| Staged cross-team contract design | 1/2 | 1/2 |
| CI scope, canary health and recovery | 0/2 | 2/2 |
| Current authorization after revocation | 2/2 | 2/2 |
| Web recovery, content and accessibility | 2/2 | 2/2 |
| Valid-state types and module simplification | 2/2 | 2/2 |
| Initiative choice, no-change and smaller options | 2/2 | 2/2 |
| Actual duplicate-registration repair | 2/2 | 2/2 |
| Actual resumable migration implementation | 2/2 | 2/2 |
| Narrow label edit and scope preservation | 2/2 | 2/2 |
| **Total** | **17/20** | **19/20** |

Sixteen matched pairs passed in both conditions. Three passed only in the
candidate; one passed only in the baseline. There were no unverified result slots.
Both conditions read an expected owner in 18/20 calls. The two tiny label edits
loaded no skill and still passed; that is appropriate proportional behavior,
not an engineering regression.

### Executable evidence

All eight substantive code calls passed separately executed behavioral oracles
and their final project tests. These oracles were authored by the lead and hidden
from subjects; they are independent of subject-generated tests, not independent
review by another person or agent.

- **Four registration repairs:** each recorded a real assertion failure with the
  original source hash before changing the owner. All seven final tests passed
  in each run. Final tests failed again against the original buggy source. Source
  and controls covered replacement, key/topic isolation, stale and repeated
  disposal, identical callback reuse and changes during a stable emit snapshot.
- **Four migrations:** all passed stable-ID ordering, bounded progress,
  deletion-before-resume, authoritative new-writer sessions, null conversion,
  field preservation, whole-batch validation and invalid-limit controls. Final
  suites passed 10/12 tests for baseline repetitions and 10/11 for candidate
  repetitions, including three pre-existing tests in each suite. Each generated
  suite rejected the supplied index-cursor/partial-mutation implementation with
  actual assertion failures. These are in-memory helpers, not durable databases
  or production cutovers.
- **Four label edits:** exact byte comparison confirmed only the requested string
  replacement. Subjects inspected the result and did not run tests.

Post-run audits found all 40 guidance snapshots and discovery links unchanged,
all unrelated sentinel files preserved, no out-of-scope fixture changes and no
subject commits. Visible commands and file-change events showed no scan, external
message, deployment, dependency installation or other prohibited effect. These
claims concern the captured local execution, not general future agent behavior.

### Retained failures

1. **Candidate, staged design, repetition 2 — writer boundary omitted.** The
   answer specified compatible readers, canonical writes, resumable batches,
   revision drift and retirement evidence, but did not specify fencing or stopping
   incompatible old writers. Event-route compatibility and eventual deployment
   verification do not explain how a bypassing legacy writer is prevented from
   restoring old data. The matched baseline explicitly fenced or stopped direct
   legacy writers. This fails the frozen `stages` criterion.

   The subject read `orbyn-data-migration/SKILL.md`, which already states this
   requirement twice; the candidate's other design repetition and both executable
   migrations respected the relevant boundaries. The observation demonstrates
   inconsistent application in one answer. It does not establish that consolidation
   caused the omission or that the underlying method was deleted.

2. **Baseline, staged design, repetition 1 — alternative comparison omitted.**
   Quantitative unknowns and phased delivery were present, but the answer did not
   compare a smaller/no-change transition. Rejecting independent conversions and
   uncontrolled dual writes addressed contract consistency rather than the
   requested smaller transition alternative. This fails `constraints`. The matched
   candidate rejected an atomic rename using released-consumer evidence. The
   baseline's second repetition explicitly rejected a simultaneous cutover and
   passed this criterion.

3. **Baseline, CI recovery, both repetitions — control comparison omitted.** Both
   answers stopped expansion and named queue health signals and observation
   windows, but omitted comparison against a current control/baseline. The second
   also lacked an explicit missing-telemetry stop condition. This fails `health`.
   Both candidate answers required a control comparison and blocked promotion
   without telemetry. Other baseline scope/recovery criteria passed.

A baseline design read also encountered a missing `.agents/docs/agents/stack.md`
path while following a relative policy pointer through discovery links. It
continued with available source evidence. This is a portability observation, not
an additional scored outcome failure.

### Observed resource usage

| Metric over 20 calls | Baseline | Candidate |
| --- | ---: | ---: |
| Median call wall time | 40.39 s | 39.09 s |
| Sum of call wall times | 801.07 s | 779.01 s |
| Reported input tokens | 1,366,824 | 1,308,937 |
| Reported cached input tokens (subset of input) | 1,121,920 | 1,077,632 |
| Reported output tokens | 27,707 | 27,486 |
| Input + output tokens | 1,394,531 | 1,336,423 |

Cached input is not added twice. These are reported usage and measured durations,
not billing estimates. Summed call times are not elapsed experiment time because
calls overlapped. Cache state, answer length, optional reads and backend scheduling
were not controlled; this small difference does not establish efficiency gains.

## Decision and next work

Keep the 34-skill candidate as the consolidation direction, but do not commit it
on a claim of no regression yet. This sample found no loss in the executable
behaviors tested, and it does not justify restoring 20 separate principle
entrypoints. It also does not test every retired principle or specialist.

Before committing:

1. Have a separate reviewer assess the writer-fencing omission and the strict
   alternative-comparison judgments from the preserved full answers. This report
   does not claim that review has happened.
2. Make the durable migration output contract harder to omit: the proposed design
   should identify active writer versions, the concrete compatibility/fencing
   mechanism, and the evidence required before conversion. Prefer a concise
   handoff between architecture and the existing migration owner over another
   skill or a blanket checklist for small tasks. This is a proposed refinement;
   the tested skill bytes remain unchanged.
3. Freeze a new candidate and run a separately reported focused comparison on
   unseen migration variants: an old worker continuing to write, a direct writer
   bypassing the API, unknown deployed versions, and failed recovery after
   partially converted data. Retain this failure and its denominator. Repeating
   until an answer passes would not establish reliability.
4. For claims about large-codebase capability, add actual multi-package execution:
   generated contracts and runtime registrations, dependency-ordered changes,
   intervening branch drift, resumable codemods and affected-test selection.
   Evaluate the core preset and other hosts separately. The current synthetic
   source analysis cannot qualify those workflows.

## Identity and evidence retention

- Original frozen protocol SHA-256:
  `73b9701936eba8d1a042acff7747f6ccb239c8445d9793350ef142bbf42041c4`.
- Frozen 10-case suite SHA-256:
  `6ce865903cbb5b042cc504d5d6d7400aac9647ec054ab9c5bcaf115551a9801c`.
- Baseline guidance inventory SHA-256:
  `e8d3b28e37f6bdc16562ae1f8bd6526cb1280223449de0d5a179e5d057aaa8d5`.
- Candidate guidance inventory SHA-256:
  `44c9bf3adfe0895d09239dd32ffa61bd359c4d3b4569af90801621ab006acea0`.

The local ignored directory `output/consolidation-trials-20261025/` retains
snapshots, preflight inventories, visible transcripts, source/test artifacts,
check receipts, counterfactual failures, review notes, evaluator run/grade records
and the paired comparison. It is not a public downloadable artifact. Raw output
and machine-specific host paths are not part of this report's publication scope.
The public JSON is a declarative reproduction package assembled after the run;
it includes the original frozen protocol, not a replacement for its checksum.

The existing evaluator requires a 40-character revision. Both run records retain
the baseline ancestry anchor; the shared frozen protocol separately binds each
guidance inventory. The comparison's candidate revision field must therefore not
be interpreted as a committed 34-skill version. The evaluator was used unchanged,
with this frozen development suite and the baseline catalog as the superset for
validating observed skill names. It reported baseline 17 pass / 3 fail and
candidate 19 pass / 1 fail, with zero unverified outcomes.

This work remains local and uncommitted. No push, PR, merge, consumer pin change,
release or independent review is implied. Browser/native behavior, live provider
integration, real organizational scale, performance under production load and
held-out generalization remain unverified.

Final documentation checks passed: `python3.13 scripts/check-library.py` validated
34 skills, provenance/licenses, 213 Markdown documents, links, host assets, presets,
evaluation cases and the manifest; `git diff --check` passed. Fixture and inventory
hashes in the public protocol match the frozen inputs. All candidate managed and
subject-guidance bytes still match the pre-trial freeze. The primary checkout
remains clean at the baseline commit. The earlier 149-test library receipt is
retained in the work record; this documentation-only closeout did not rerun it.
