# Live Codex contribution assessments — 25 October 2026

The new contribution guidance preserved sound answers and made the intended
owners easier to select in this bounded development study. It did **not** show an
outcome-quality gain over the released baseline. Both conditions passed 12 cases;
one original case was unverified because its input omitted the contract required
by its rubric. A separate clarified-case pair passed in both conditions.

## Revisions, observations and scope

| Study / condition | Guidance revision | Passed outcomes | Unverified outcomes | Expected-owner body read |
| --- | --- | --- | --- | --- |
| Initial baseline | `5684ee576ba85d07be317ca91e9f3e02452f4993` | 12/13 | 1/13 | 9/13 |
| Initial candidate | `13d58d1d571955a2aaba9197d083c49d880ae8fd` | 12/13 | 1/13 | 13/13 |
| Clarified-case baseline | `5684ee576ba85d07be317ca91e9f3e02452f4993` | 1/1 | 0/1 | 1/1 |
| Clarified-case candidate | `ecc1768f339ea7b554f76ad5d8bc45fbe381e949` | 1/1 | 0/1 | 1/1 |

There were 26 initial calls and two follow-up calls, one per case/condition, with
no scored-call errors or timeouts. The conditions used the same frozen prompts,
rubrics, fixture policy and capabilities. These are supplied-scenario Markdown
assessments: target commands, product edits, tests and account effects were
excluded. Read-only local guidance/metadata commands were observed; no subject
writes, tests, messages, publication or merge were observed.

All 13 initial cases are outcome tasks, not routing-only tasks. The last column
records whether commands actually read at least one expected canonical skill
body, with no forbidden owner. Reading a reference alone was not counted as a
body read. It is separate from answer quality. The baseline used other useful
owners for stale-head CI, partial review coverage, feedback disagreement and human
gates; those four answers passed their outcome criteria without the expected body
read. The candidate read the new workflow body in those cases. This supports a
more connected handoff observation, not a general capability or success-rate claim.

The cases cover stale issue availability, overlapping contributions, nested
target instructions and dirty work, reproduction scope, zero selected tests,
intermittent evidence, current-head checks, feedback pagination, disagreement,
draft/review gates, exhausted retries, optional checks and external-effect scope.
The [declarative protocols](2026-10-25-contribution-protocol.json) record exact
suite revisions/checksums, source inventories, fixtures and reproduction steps.

## Gap found and correction

The original `contribution-reproduction-only` prompt reported a double callback
but never supplied a contract requiring one callback. Its frozen `oracle`
criterion nevertheless required that expectation. Both answers retained evidence
limits; the candidate explicitly refused to infer a defect from the count alone.
That is appropriate contract discipline, not evidence of a skill failure.

The original oracle remains **unverified**, its other boundary criterion passed,
and all original observations are retained. The evaluator correctly refused a
complete aggregate comparison because both original runs contain an unverified
outcome. The table reports descriptive condition counts, not a completed 13-case
paired score. No original answer was silently regraded against a new suite.

The correction adds the target's one-callback-per-trigger/single-registration
contract to that development prompt. It leaves the rubric, other 110 cases and
all holdouts unchanged. A new suite hash and separate one-case protocol were
frozen before the two follow-up calls. Both then passed the unchanged oracle and
scope criteria. The evaluator's matched comparison for that pair is 1/1 versus
1/1. The follow-up is not combined with the original study into a claimed 13/13
new-suite result. Candidate guidance bytes excluding evaluation assets/scripts
are identical between `13d58d1` and `ecc1768`.

No contribution-method change was justified by these answer observations. The
public correction is to evaluation input and isolation guidance, with this
reviewable result record. Earlier licenses and source credits remain intact.

## Host readiness and isolation

The PATH CLI `0.133.0` failed a bounded readiness probe: it rejected the configured
model for this account. That error is retained; no scored trials used that host.
The already installed desktop CLI `0.163.0-alpha.10.2` then returned `READY` using
the same `gpt-6.1-sol` model, medium effort, requested default service tier and
disabled Fast/Ultrafast modes. Effective server processing tier was not exposed.
There was no model substitution, runtime install or global configuration edit.

Prompt-inventory preflight also caught global/system skills despite folder-only
disable overrides. Per-run overrides using actual advertised `SKILL.md` paths
and resolved locations removed them. Before scoring, both final prompt inventories
contained exactly the intended 54 local skill names, correct baseline/candidate
descriptions and no global/system/plugin skill roots. The contaminated inventories
were preparation observations, never scored trials.

Each call used a fresh ephemeral context and disposable Git root outside library
and consumer ancestor instructions. User configuration, plugins, apps, hooks,
memory, delegation and browsing were disabled; local host state was isolated.
The full local skill catalog was available. Source snapshots omitted evaluation
keys and executable helpers because the task allowed guidance reading only.
The original study alternated condition order by case with at most two concurrent
calls and a 180-second per-call limit. Follow-up used the same settings and bounds.

The [official non-interactive guide](https://developers.openai.com/codex/noninteractive)
supports ephemeral JSONL/read-only execution. Available flags and discovery
behavior were also checked against the installed host; flags alone were not
accepted as proof of isolation. Read-only is not a filesystem deny-read boundary:
fixture policy constrained reads, and the lead inspected actual visible commands.

## Evidence retention and limits

The lead inspected all 28 final artifacts and visible command results against
the frozen criteria. Grading was unblinded self-review, not independent review.
These were development cases with explicit scenario cues, one observation each;
the study cannot establish statistical equivalence, general improvement, complete
PR execution, reproduction-runner correctness, hosted CI behavior, native behavior,
Claude compatibility, deployment or cost/latency advantage. No heldout was tuned
or claimed. Observed skill-read matches do not qualify all 111 suite definitions.

Full answers, visible JSONL captures with reasoning items omitted, usage/duration,
prepared and graded runs, comparison receipts, readiness failures, contaminated
preflight inventories and the corrected follow-up remain under ignored local
`output/contribution-evals-20261025/`. Public content contains this summary and
declarative synthetic protocols, not per-run captures or credentials. A different
host/model or an execution-capable trial needs a fresh protocol/readiness check.

Public-library work only: Orbyn's consumer skills/pin are not synchronized, and
the REA engine/source upgrade remains deferred. Existing nested contribution
checkouts and unrelated local output are preserved.
