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

## Pin the intent before the spec

A proof holds the code to its spec, so a wrong or weak spec gives a green check that
protects nothing. Settle intent with the person who owns the behavior first:

- **Ask both ways.** "Only X gets Y" and "X always gets Y" are different promises. The
  first alone is kept by code that refuses everyone. Ask which the user means; often
  it is both.
- **Map each clause to the request.** Keep a short intent map: each spec clause, the
  user's words it comes from, and clauses added to keep today's behavior (existing
  error codes, say), marked as such.
- **Write the "not promised" list.** Whether a call finishes, how fast, rate limits,
  anything nobody wrote down. A safety spec says nothing about these.
- **Explain before asking.** When a question depends on how the code works, explain
  that part in a sentence first, so the user can answer without opening the source.

Have someone other than the spec's author check it against the intent map before any
proof work: does it say what was asked, and does it promise more than a proof could
show? A spec the user has not agreed to is a draft.

## List what the proof trusts

Every proof rests on code it cannot see: databases, hashing and crypto libraries,
clocks, other crates or services. For each one:

1. Wrap it in one small function whose contract states exactly what the proof assumes.
2. Say what breaks if the assumption is wrong, by naming the spec clauses that rest on it.
3. Have the user accept it as its own decision, not as part of approving the whole spec.
4. Give it a test, planned before the proof work, that checks the assumed contract on
   the real dependency. A passing test is evidence, not proof; label it so.

Keep the list short and in one place. The guarantee is only as strong as its weakest
trusted piece, so name the ones most promises rest on.

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
   negative control is labelled as such. Preserve both outcomes. For a code-level
   spec with several clauses, plant one bug per clause, each aimed at that clause,
   and confirm the verifier rejects each on the clause it targets. A mutant that
   passes means that clause rules out nothing: strengthen or remove it, never keep it
   as decoration.
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

## Leave a project-local check

The generated skill belongs to the project. Write it only when the user asks for or approves a durable check, and put it in the project's existing skill path under [project verification](../../orbyn-skill-creator/references/project-verification.md); this library installs nothing into a target. Choose the target from the code: the promise whose break costs users most and that ordinary tests reach least, not the easiest model to turn green. Ask the user only what the code cannot show.

The generated skill must let a cold reader tell whether a change touches the covered code, run the check with one command in a time short enough to use on every relevant change, tell a modeling error from a real bug, and update the check when a change is intended. State the property and its harm in one plain sentence each, and tell a counterexample as short steps in the code's words. Record the covered files and functions and the commit at which the check was last confirmed; the next agent advances that commit only after confirming the check describes the code at the new one. If the check is a TLA+ model, point to the statechart method by name and copy none of its commands or paths, which change between releases. Follow the generated skill once as the next agent on a scratch change that breaks the property; until it catches the break it is a draft.

## Deliver and maintain

Return the property, tool rationale, command, actual result, negative control,
counterexample/replay, bounds and omissions. In a PR, write it as a short receipt,
one line per item ([short by default](../../unslop/references/short-by-default.md)):

```markdown
- Proved: <requirement> (<function>, <verifier and version>)
- Trusted and tested: <piece> (<test name, result>)
- Not promised: <what, such as completion or timing>
- Per-clause mutants: <n> of <n> rejected
```

The reviewer checks the receipt against the intent they agreed, not every generated
line. Once a proof runs in CI, tests that only re-check proved behavior can go; keep
the tests on the trusted pieces. Report deadlock and temporal results
separately from state invariants. A bounded pass covers this model/configuration,
not production scheduling, all deployments or the whole codebase.

Use the project's current verification owner. For a durable reusable check, the
[project verification method](../../orbyn-skill-creator/references/project-verification.md)
keeps a runnable local adapter and coverage record without changing shared-skill
ownership. The selected adaptation is recorded in the
[source record](verification-source.md).
