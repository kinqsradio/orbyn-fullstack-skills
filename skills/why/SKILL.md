---
name: why
description: "Investigate design rationale, regressions and trade-offs using Git history and relevant authorized records; distinguish documented intent from inference."
---

# Why

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

Find the code anchor, symbols and introducing/changing commits with scoped
`git log`, `git blame` and diffs. Read linked ADRs, issues and PR discussions when
needed. Expand to available authorized records only to resolve a specific gap;
do not search all connected accounts or private chats by default.

Treat the user's proposed explanation as a hypothesis. Capture direct rationale,
contradictory evidence and plausible alternatives. Code establishes mechanics,
not necessarily motivation. An empty bounded search does not prove a record
never existed. Describe the searched boundary.

For substantial historical investigation, the lead delegates bounded evidence
questions to named Orbyn Investigators under the [workflow](../orbyn-workflow/SKILL.md),
then inspects their cited records and owns the explanation. Narrow questions and
children assigned a slice proceed directly. Do not create tickets or send messages
while investigating.
Return the supported explanation with sources, inference and unknowns. If work
will change the design, identify constraints to preserve and decisions to revisit.

## Separate rationale from mechanics

When a worker uses a lease instead of a process-local lock, inspect the introducing change and related recovery contract. Source can show that cross-process recovery is possible; only a linked rationale or other authorized record can establish why the original author selected it. Return both at their actual confidence.

## Operational method

Use the [local operating method](references/operating-method.md) for the execution
sequence, concrete failure case, expected result and stopping condition. It is
Orbyn-authored guidance; historical source notices remain in provenance.

## Recover the introducing decision

When last-touch blame misses origin, use scoped rename-following history and
symbol/string introduction search (`git log --follow` for a selected file and
pickaxe `-S`/`-G` for the relevant symbol), then inspect the introducing diff.
A later move/sync commit is not necessarily the decision or defect origin. Read
material discussion, parent/duplicate chains and finalized outcome before treating
an issue title or preview as rationale; a final reversal can supersede its proposal.
Bound investigation by the unresolved question rather than scanning all history.

For authorized operational records, distinguish a bounded empty query from missing
authentication, expired retention or unavailable history. Discover actual tool/schema,
select a relevant time/release/environment window and poll the same asynchronous
query identity instead of resubmitting costly scans. Preserve denominator, sampling,
refresh and instrumentation/schema changes before interpreting volume as adoption
or causality. Representative primary events support relevance; generated diagnoses
remain hypotheses. No connector installation, capture or cross-account search follows.
