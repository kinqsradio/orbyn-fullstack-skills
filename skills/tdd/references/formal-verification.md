# Verify a critical property

Use for an explicit verification request or a costly promise ordinary examples
rarely exercise. Work within authorized local scope. Start from actual code and
the strongest relevant user harm, not the easiest toy model to make green.
Use [statecharts](../../architect/references/statecharts.md) for a readable
explanation and [drift review](verification-drift.md) for an existing check.

## Let the property choose the tool

| Property | Candidate method and limit |
| --- | --- |
| Interleavings, retries, leases, migration phases | Small TLA+/TLC or another suitable model; explicit actors, domains and assumptions |
| Input-dependent implementation contract | Existing property-based tests or code-level verifier; exercise the actual implementation |
| Memory safety, overflow or all-input guarantee | Suitable language/code verifier; identify supported semantics and trusted assumptions |
| Every size or unbounded mathematical claim | Proof method when justified; a finite model run does not establish this |

Generated testing is useful evidence but is not formal proof. Prefer tools the
project can maintain. Detect existing versions first. No automatic global install,
provider setup or network download follows from reading this method. Missing
tools yield a precise blocked check and a retained model/command, not a pass.
Keep approved task-local tool versions, dependency locks/checksums and commands
reproducible; a renderer's dependencies and a checker's runtime are separate.

If the target chooses a separately reviewed pstack statechart compiler, pin its
source and qualify the actual runtime before use. At the reviewed revision in the
[source record](verification-source.md#review-of-compiler-era-guidance-27-october-2026),
direct invocation of `scripts/statechart.ts` accepts `--config`, `--view` and a
fresh `--out`, with explicit `JAVA` and `TLA2TOOLS` paths. Confirm Node supports
that TypeScript entrypoint; bypass setup wrappers that bootstrap dependencies.
Treat view modules as executable trusted code. Missing compiler or prerequisites
does not require an installation: use an existing suitable verifier, or report
the check blocked. Local compiler qualification does not make it a library
dependency or establish support for other runtimes/platforms.

The library now offers an [optional pinned offline compiler adapter](../../architect/references/statechart-compiler.md)
and [runnable leased-job example](../../architect/examples/leased-job/guide.md).
Doctor/parse/check/projection/render/replay remain separate evidence. Mixed
violation labels, hidden-edge visibility, parallel guards, lasso fidelity and
VIEW/SYMMETRY/constraint interpretation follow the architect's
[projection rules](../../architect/references/statecharts.md#projection-and-omission-guardrails).
Report an intentional terminal and disabled/unchecked deadlock detection separately;
a safety pass or terminal stutter cannot stand in for a checked temporal property.

## Establish a falsifiable check

1. State the property and user harm in plain words. Separate safety (a bad state
   never occurs), liveness (progress eventually occurs under stated assumptions),
   reachability and deadlock checks. A deliberately negated reachability query
   must be labelled expected-to-fail; do not count its counterexample as a defect.
2. Record covered files/functions and all relevant writers, source revision plus
   dirty-file digests, model/config digests, tools, exact command, finite domains,
   limits, fairness, environment assumptions and excluded behavior. Source line
   numbers help review but are insufficient identity on their own.
3. Tie each action and condition to source. Preserve real transaction/lock/await
   boundaries. A local mutex does not fence remote writers or other processes.
   For design-only checks, label the absence of implementation correspondence.
4. Run the original check and retain output, termination, effective configuration
   and counterexamples. A timeout, exhausted resource budget, parse failure,
   reduced unexplained bound or missing property is not a successful check.
   Give every invocation a distinct owned log and checker-state/output directory,
   even when sequential: timestamp defaults can collide within one second. For
   TLC, select a fresh `-metadir` per run. Check the chosen mode's capabilities:
   randomized simulation may refute a property but cannot establish exhaustive
   coverage; a depth cutoff may leave states unexplored; a mode without temporal
   checking cannot establish liveness. Keep unsupported checks blocked and read
   the actual property/configuration result, not just the process exit status.
5. In a disposable copy, remove the actual guard or reorder real steps that the
   property protects. Show that the check detects this broken variant, then
   restore the original and rerun. Do not merely flip a separate model flag while
   claiming to have validated detection of a product regression. A model-only
   negative control is labelled as such. Preserve both outcomes.
6. Replay a model counterexample against actual entry points where feasible,
   forcing ordering with barriers rather than timing guesses. Assert observable
   state/effects, including absence of rejected effects. Record which steps were
   exercised and which remain source inference. If a trace cannot occur, correct
   the model; do not weaken the intended rule to make it pass.

Never silently fix product code during a verification-only task. Report a current
violation with its harm, trace and source evidence. Separately authorized repair
uses the normal failing-before regression and implementation workflow.

### Worked example: report each property separately

The following is an illustrative receipt for the
[protected-host design](../../architect/references/statecharts.md#worked-example-an-overview-hides-protected-work),
not a report of executed checks. Replace each illustrative result with retained
tool evidence when running a real task. Record model/configuration digests,
source identity, checker version/command, termination and run directory once;
then report every requested property, including ones the selected mode omitted.

| Property ID | Illustrative model result | Scope or reason |
| --- | --- | --- |
| `NoProtectedPark` | Broken | Finite design with one worker/reaper and jobs in 0..1; observe → admit → park reaches protected parked work |
| `EventuallyFinished` | Not checked | Selected mode cannot check temporal properties; no liveness verdict follows from an invariant result or a path to completion |
| `DeadlockFree` | Not checked | Deadlock checking was disabled; absence of a reported deadlock is not a pass |

Record separately: **projection** omitted because the configured graph budget
was exceeded; **source correspondence** unverified because this is a design with
no implementation; **real-code replay** unavailable for the same reason;
**negative control** not run. None changes the broken model verdict or establishes
an implementation defect. A real implementation task must instead map the full
qualified action IDs to source and retain a replay or explain its blocker.

For a completed exhaustive run, “holds within stated bounds” requires evidence
that the requested property was actually checked over the configured finite
graph. A timeout, tool/parse error, unfinished exploration or unsupported mode
leaves the relevant result blocked or not checked, with the actual reason and
partial evidence retained. Record explored states/transitions when supplied,
configured domains and any cutoff separately; a count alone is not coverage.
Report projection validation failures and missing charts independently of checker
results. A compiler's chart or rerun thresholds are version-specific tool limits,
not universal safe model sizes or permission to reduce the requested scope.

## Deliver and maintain

Return the property, tool rationale, command, actual result, negative control,
counterexample/replay, bounds and omissions. Report deadlock and temporal results
separately from state invariants. A bounded pass covers this model/configuration,
not production scheduling, all deployments or the whole codebase.

Use the project's current verification owner. For a durable reusable check, the
[project verification method](../../orbyn-skill-creator/references/project-verification.md)
keeps a runnable local adapter and coverage record without changing shared-skill
ownership. The selected adaptation is recorded in the
[source record](verification-source.md).
