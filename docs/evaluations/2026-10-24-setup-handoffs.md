# Codex setup and continuation trials, 24 October 2026

The final tested candidate passed 1/1 routing and 5/5 outcome cases versus 1/1
and 4/5 at baseline. The corrected recovery answer explicitly states crash and
power-loss limits. These are single-run development observations with unblinded
lead grading, not independent qualification or general model improvement.

## Frozen revisions and results

| Condition                       | Revision                                   | Routing | Outcomes |
| ------------------------------- | ------------------------------------------ | ------- | -------- |
| Released baseline               | `40d323c6007489e704bd60a6ea2eb97c6429dfac` | 1/1     | 4/5      |
| Initial candidate               | `40c0db2f932ae21a209eb54d8ea71b766d90ecb5` | 1/1     | 4/5      |
| Connected continuation/recovery | `c940db579a25a601f32d2e30b60ee4f719d3f510` | 1/1     | 4/5      |
| Final tested candidate          | `c2b91e81d4885beda1a356e25b1d05aa8b59db4c` | 1/1     | 5/5      |

The six cases cover prompt rewriting, a small Python task without a prompt/stack
selection detour, a held consumer pin, stale continuation, Cursor setup and failed
registration. The first five passed in all four conditions. Failed registration
initially missed the frozen criterion distinguishing exception rollback from
crash/power-loss guarantees; only the final tested candidate passed it. No rubric
was weakened, and failed attempts remain retained locally.

Source review also led to reporting preserved concurrent replacement paths in
installation errors and connecting `show-me-your-work` to the continuation
contract. Declared skill-read matches across all six cases were 3/6 at baseline
and 5/6 finally, separately from the routing-only score. The public-only outcome
read the release-handoff reference through the skill creator rather than loading
the expected upstream-review body; the artifact still met its outcome rubric.

## Reproducible protocol and retained evidence

The [declarative protocol](2026-10-24-setup-handoffs-protocol.json) contains the
original frozen protocol, synthetic fixture contents and hashes, case IDs,
revisions, task wrapper, snapshot exclusions and host invocation template.
Use the frozen suite and [evaluation guide](../../skills/orbyn-skill-creator/references/evaluations.md)
to prepare, capture and grade an explicitly authorized rerun. Host-specific paths
are placeholders; do not change global settings or execute model calls merely
because the protocol is present.

All 24 calls used Codex CLI `0.163.0-alpha.10.2`, `gpt-6.1-sol`/medium, requested
default service tier and disabled fast modes. Effective server tier was not
independently exposed. Each revision used six cases, one trial per case, the full
54-skill catalog, fresh read-only synthetic fixtures, a 240-second limit and at
most two concurrent calls. Global skills, user config, plugins, apps, memory,
hooks, delegation, browser and network search were disabled for subjects. All
calls completed without timeout. The lead inspected visible commands and answers;
no subject writes, tests or external effects were observed.

Full answers, JSONL captures, usage, command lists, prepared runs, grader receipts
and earlier failures remain in ignored local `output/improvements-20261024/live-evals/`.
The removed published-capture file was preserved byte-for-byte there with a
retention receipt. No downloadable CI artifact is claimed. The template's current
tree contains the summary and reproducible synthetic protocol, not per-run logs;
removing a file does not erase its earlier Git history.

## Evidence limits

The final candidate was corrected after development observations; no held-out or
blind test was performed. These response trials do not qualify implementation,
Cursor runtime discovery, Claude or offline-model behavior, rendering, production,
or cost/latency. Cursor files were supplied as planning context, not physical
fixture files; the Python case supplied no parser and correctly elicited missing
input rather than an invented edit. Filesystem behavior was checked separately.

At the tested revision, 116 helper tests and library checks passed for 54 skills,
235 managed files and 88 case definitions. Later lightweight-recording and
retention guidance received document/helper checks; these live trials were not
rerun and do not qualify those later instruction changes.

Public-library work only: the consumer pin remains held, REA stays deferred,
credits remain preserved and raw reference folders stay outside Git.
