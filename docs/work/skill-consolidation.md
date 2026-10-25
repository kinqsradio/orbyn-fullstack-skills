# Engineering skill consolidation — 25 October 2026

Implementation baseline: `4510c750f96af62a094e1193a473d6aad315e7ee` (54 skills).
Target: 34 discoverable skills with 20 maintained principle references. Core remains
14; this change does not promote a consumer pin, alter model settings or publish.

## Disposition and preservation

Each retiring entrypoint retains its decision, example and check under its owner.
The owner exposes the essential rule; deep methods load only when relevant.
Source records and unchanged MIT notices move with the methods. Installer aliases
map old selections to owners; old direct host invocations are not promised aliases.
Both-host known discovery links are migrated; foreign content remains untouched.

| Retired discovery name | Execution owner | Preserved behavior |
| --- | --- | --- |
| `principle-boundary-discipline` | `orbyn-backend-design` | [Maintained method](../../skills/orbyn-backend-design/references/principles/boundary-discipline.md) |
| `principle-build-the-lever` | `orbyn-workflow` | [Maintained method](../../skills/orbyn-workflow/references/principles/build-the-lever.md) |
| `principle-encode-lessons-in-structure` | `architect` | [Maintained method](../../skills/architect/references/principles/encode-lessons-in-structure.md) |
| `principle-exhaust-the-design-space` | `architect` | [Maintained method](../../skills/architect/references/principles/exhaust-the-design-space.md) |
| `principle-experience-first` | `orbyn-ui-design` | [Maintained method](../../skills/orbyn-ui-design/references/principles/experience-first.md) |
| `principle-fix-root-causes` | `how` | [Maintained method](../../skills/how/references/principles/fix-root-causes.md) |
| `principle-foundational-thinking` | `architect` | [Maintained method](../../skills/architect/references/principles/foundational-thinking.md) |
| `principle-guard-the-context-window` | `how` | [Maintained method](../../skills/how/references/principles/guard-the-context-window.md) |
| `principle-laziness-protocol` | `architect` | [Maintained method](../../skills/architect/references/principles/laziness-protocol.md) |
| `principle-make-operations-idempotent` | `orbyn-backend-design` | [Maintained method](../../skills/orbyn-backend-design/references/principles/make-operations-idempotent.md) |
| `principle-migrate-callers-then-delete-legacy-apis` | `architect` | [Maintained method](../../skills/architect/references/principles/migrate-callers-then-delete-legacy-apis.md) |
| `principle-minimize-reader-load` | `architect` | [Maintained method](../../skills/architect/references/principles/minimize-reader-load.md) |
| `principle-never-block-on-the-human` | `orbyn-plan` | [Maintained method](../../skills/orbyn-plan/references/principles/never-block-on-the-human.md) |
| `principle-outcome-oriented-execution` | `orbyn-workflow` | [Maintained method](../../skills/orbyn-workflow/references/principles/outcome-oriented-execution.md) |
| `principle-prove-it-works` | `orbyn-workflow` | [Maintained method](../../skills/orbyn-workflow/references/principles/prove-it-works.md) |
| `principle-redesign-from-first-principles` | `architect` | [Maintained method](../../skills/architect/references/principles/redesign-from-first-principles.md) |
| `principle-separate-before-serializing-shared-state` | `orbyn-workflow` | [Maintained method](../../skills/orbyn-workflow/references/principles/separate-before-serializing-shared-state.md) |
| `principle-sequence-verifiable-units` | `orbyn-plan` | [Maintained method](../../skills/orbyn-plan/references/principles/sequence-verifiable-units.md) |
| `principle-subtract-before-you-add` | `architect` | [Maintained method](../../skills/architect/references/principles/subtract-before-you-add.md) |
| `principle-type-system-discipline` | `language-best-practices` | [Maintained method](../../skills/language-best-practices/references/principles/type-system-discipline.md) |

The other 34 entrypoints remain. This includes `why`, `arena`, `reflect`,
`automate-me`, `unslop`, all five REA specialists and both social specialists.
`figure-it-out` and `show-me-your-work` remain distinct pending paired behavior
trials; 32 is an experiment, not this implementation's target. Preset changes are
also deferred so routing consolidation and selection changes can be evaluated separately.

## Coupled implementation sequence

One writer owns catalog, discovery, provenance, link repair and distribution checks:
these files share an inventory and cannot be safely regenerated independently.
First close portable dependencies, then consolidate principles and strengthen
existing engineering owners. Validate copied exports, retirement behavior, routing
case structure, licenses and the whole library. Review the actual diff last.
The current host cannot guarantee the repository's standard-speed child settings;
work proceeds directly, with no independent-review claim.

## Engineering capability additions

- Bounded source/build/runtime discovery and a task-local impact map (`how`).
- Problem and outcome framing, verifiable sequencing (`orbyn-plan`).
- Organizational ownership, quantitative design constraints and staged API changes
  (`architect`); durable writers and backfills (`orbyn-data-migration`).
- Graph-aware affected verification and health-driven rollout/recovery (`orbyn-ci-design`).
- Consumer-specific UI, content and security examples; proportional regression checks.

## Evidence and remaining experiments

The original 54-skill case suite is frozen under the creator's `evals/baselines/`.
New development cases exercise preserved rules and large-codebase failure modes.
Structural checks and disposable installation tests establish packaging behavior;
they do not establish equivalent model behavior or enterprise-scale qualification.
Future paired trials must pin baseline/candidate, host/model/effort, fixture,
criteria and attempts; compare outcome quality and routing separately. Use a new
isolated holdout for generalization. Keep the two proposed workflow merges and
core-preset substitutions separate experiments. No live trial is implied by a
prepared case or passing validator.

## Initial local validation receipt (before live trials)

Validated with the existing Python 3.13 interpreter on 25 October 2026. The shell's
default Python is below the library's 3.11 minimum and was not used for qualification.

- Both-host discovery regeneration and checks: 34 canonical entrypoints, with
  the 20 retired names removed from known owned links.
- Library and agent-asset checks: pass; 266 managed files, 212 Markdown documents,
  licenses/provenance, dependency closure, source hashes, presets and routing metadata.
- `python3.13 -m unittest discover -s tests -v`: **149 tests passed**. Includes
  full skills-only copies, missing/unexported dependencies, immutable-source guards,
  both-host retirement, dry-run/idempotence and existing foreign-content protection.
- Evaluation validation: **164 cases** (134 existing unchanged, 30 new development
  cases). The 54-skill baseline is byte-identical to the original suite; its SHA-256
  is `744d9724f0a8719bc0689ebade403d2452c8ffa0a8f19d47c8b5d7fdaa3659e6`.
  Candidate suite SHA-256:
  `e3c1d5272614d888a77554e7fe3bec57866476f7c6aab1bc4978208bb6c53a72`.
- All 20 original principle license byte sequences are preserved. Preset definitions
  and model registry bytes are unchanged. Diff whitespace checks pass.

At this initial checkpoint, implementation was local on
`refactor/skill-consolidation`, based on the baseline above. No live model trial
or independent review had been performed. Those checks established structure and
helper behavior; they did not qualify live outcomes.


## Paired live development trial receipt

The [40-call live comparison](../evaluations/2026-10-25-skill-consolidation.md)
measured 17/20 passing outcomes for the 54-skill baseline and 19/20 for the
uncommitted 34-skill snapshot. Both passed every executable repair, migration and
small-edit trial. One candidate migration design omitted old-writer fencing; its
matched baseline included it. The report retains this candidate-only failure and
three baseline failures under the frozen rubric.

Recommendation: hold the commit pending focused migration follow-up. The result
supports continued consolidation but does not establish zero capability loss.
The lead's review was unblinded and not independent. Raw captures remain ignored;
the report and synthetic reproduction protocol are reviewable documentation. No
skill bytes were revised in response to trial results, and no commit, push, merge
or consumer promotion occurred.

## Writer boundary, engineering breadth and lifecycle follow-up

The [follow-up report](../evaluations/2026-10-25-migration-followup.md) preserves
42 additional calls separately from the original 40. The catalog remains 34.
New methods cover enforced writer cutover, service readiness, technical investment,
coaching, incident handoff, human-preview artifacts and resource retention/cleanup.
Three observed output gaps received concise owning-entrypoint corrections and a
separate six-call development recheck. See the [capability map](engineering-capability-gaps.md)
for coverage and remaining large-repository/native/operational evidence gaps.
At that follow-up checkpoint, all work remained local and uncommitted. The earlier hold checkpoint and failed
receipts remain historical evidence; no broad enterprise qualification is claimed.

## Subsequent delivery scope

The later request authorizes a PR for human review after independent review and
new executable trials. Selected Hallmark methods are integrated into the existing
UI owner with pinned provenance and its original MIT notice. The prior hold and
scores remain historical records; they do not describe the final delivery state.
