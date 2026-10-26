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
