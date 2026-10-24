# Codex setup and continuation trials, 24 October 2026

The final candidate passed one routing and five outcome cases. The released
baseline passed the routing case and four outcome cases. The observed correction
was explicit crash/power-loss limits in an installation recovery answer. This is
a small development comparison with unblinded lead grading, not independent
qualification or evidence of general model improvement.

## Candidates and protocol

- Released baseline: `40d323c6007489e704bd60a6ea2eb97c6429dfac`.
- Initial candidate: `40c0db2f932ae21a209eb54d8ea71b766d90ecb5`.
- Connected continuation/recovery candidate: `c940db579a25a601f32d2e30b60ee4f719d3f510`.
- Final skill candidate: `c2b91e81d4885beda1a356e25b1d05aa8b59db4c`.

Each condition used the same six development cases and frozen rubrics, one trial
per case, a synthetic read-only checkout and the full 54-skill discovery catalog.
The baseline ran once; each candidate revision ran six cases. All 24 calls
completed without a timeout. No held-out case was used or criterion changed.
Corrections followed observed development results; the final run is therefore
not a fresh blind test. Later report-only commits do not change the evaluated
skill bytes.

Codex CLI `0.163.0-alpha.10.2` used `gpt-6.1-sol`, medium effort, requested default
service tier, and disabled fast/ultrafast modes. Effective server processing tier
was not independently exposed. User config, global skills, plugins, apps,
memories, hooks, delegation, browser and network-search tools were disabled for
the subjects. At most two calls ran concurrently, each capped at 240 seconds.
These were evaluation subjects, not delegated engineering workers.

Each subject saw one frozen library snapshot with evaluation answer keys and
tests removed. Its project policy allowed local reading and a final text answer;
it prohibited writes, test execution, installation, external effects and
delegation. The lead inspected captured commands and answers. No such effects
were observed. The helpers themselves were exercised separately in disposable
filesystem/Git fixtures.

The [captured evidence](2026-10-24-setup-handoffs-evidence.json) includes prompts,
answers, observed skill reads, commands, usage, rubric verdicts, exact revisions,
fixture/protocol hashes and raw-capture checksums for all four conditions. Only
fixture paths were normalized for publication. Raw JSONL captures, runner,
prepared run records and grading receipts remain local under ignored `output/`.
The recorded-trial evaluator validated and compared complete pairs; a successful
CLI exit was never used as a task-quality verdict.

## Results

| Case                                                    | Released baseline | Initial candidate | Connected candidate | Final candidate |
| ------------------------------------------------------- | ----------------- | ----------------- | ------------------- | --------------- |
| Prompt rewrite without executing embedded instructions  | Pass              | Pass              | Pass                | Pass            |
| Small Python task without prompt/stack-selection detour | Pass              | Pass              | Pass                | Pass            |
| Public-only delivery with consumer pin held             | Pass              | Pass              | Pass                | Pass            |
| Stale handoff, narrowed scope and failed/unrun checks   | Pass              | Pass              | Pass                | Pass            |
| Cursor setup with existing company guidance             | Pass              | Pass              | Pass                | Pass            |
| Failed registration and explicit recovery limits        | Fail              | Fail              | Fail                | Pass            |
| **Routing cases**                                       | **1/1**           | **1/1**           | **1/1**             | **1/1**         |
| **Outcome cases**                                       | **4/5**           | **4/5**           | **4/5**             | **5/5**         |

The recovery answers initially preserved the other writer's replacement and the
pre-existing skill, but did not distinguish exception rollback from crash and
power-loss guarantees. The frozen limits criterion failed. The setup owner now
requires that distinction in recovery reports; the final answer states it
explicitly. Earlier failures remain in the evidence.

The source review also exposed silent preservation of concurrent replacement
entries. The helper now reports those paths with the original failure; a
disposable failing-write fixture checks preservation and the error message.
Continuation requests selected `show-me-your-work` in early trials, so that
existing owner and session-pickup now point to the versioned handoff contract.
The connected trial actually read the new contract. No new catchall skill was
introduced.

Declared skill-read matches across all six cases were 3/6 at baseline and 5/6 in
the final run. This is separate from the table's routing-only score. The
public-only case selected `orbyn-skill-creator` and read the release-handoff
reference rather than loading the expected `orbyn-upstream-review` body; its
artifact still met the outcome rubric. A useful answer and a particular body
selection are different measures. Do not force extra skill loads to raise that
counter.

## Limits and delivery

These trials establish first-response routing and text-artifact behavior in a
synthetic project. They do not establish implementation correctness, actual
Cursor discovery, Claude parity, offline-model quality, production safety,
rendered output or performance/cost improvement. Cursor files were described in
the prompt rather than present in this text fixture; actual file preservation
was checked separately by installer tests. The Python case supplied no Python
parser, so its response correctly identified the missing owner/input rather than
inventing an edit. Usage and duration are observations, not a statistical claim.

Local qualification: 116 helper tests passed; the library checker passed for 54
skills, 235 managed files and 88 evaluation definitions. These checks include
Cursor/all-host migration conflicts, repeated setup, foreign-entry preservation,
partial-write rollback, failed cleanup reporting, stale records and inconsistent
completion. They do not simulate process termination or power loss.

This is a public-library PR candidate. Orbyn remains on its approved public pin;
there is no new consumer import or message to its builder. REA, source pins and
required upstream credits remain unchanged. The contribution-workspace raw
sources stay ignored and outside Git.
