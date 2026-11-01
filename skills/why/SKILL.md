---
name: why
description: "Investigate design rationale, regressions and trade-offs using Git history and relevant authorized records; distinguish documented intent from inference."
---

# Why

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

## Method

1. **Anchor the question** in the changed code, symbol or behavior. Treat the user's proposed explanation as a hypothesis.
2. **Locate introducing and corrective commits** with scoped `git log`, `git blame` and diffs. Read the relevant diff and surrounding source, because line attribution alone does not establish intent.
3. **Read linked ADRs, issues, PR discussions and design records** only to answer the current question. Expand to other available authorized records only to resolve a specific gap. Do not search all connected accounts or private chats by default.
4. **Record direct rationale, contrary evidence, plausible alternatives and inference separately.** Code establishes mechanics, not necessarily motivation. A later comment can describe current policy without proving why the original implementation was chosen.
5. **Return the supported explanation** with sources, inference and unknowns. If work will change the design, name the constraints to preserve and the decisions to revisit. Describe the searched boundary: an empty bounded search means no rationale was found in that scope, and does not prove no record ever existed.

Take a worker that uses a lease instead of a process-local lock. Inspect the introducing change and related recovery contract. Source can establish cross-process expiry and recovery behavior; only a linked rationale or other authorized record can establish why the original author selected it. A linked design note may show crash-recovery motivation. If that note is absent, report the mechanism as confirmed and the motivation as inferred, with the searched history boundary.

## Investigation limits

Do not create tickets or issues, message authors or send other messages while investigating or merely to complete a historical explanation.

For substantial historical investigation, the lead delegates bounded evidence questions to named Orbyn Investigators under the [workflow](../orbyn-workflow/SKILL.md), then inspects their cited records and owns the explanation. Narrow questions and children assigned a slice proceed directly.

## Recover the introducing decision

When last-touch blame misses the origin, use scoped rename-following history and symbol/string introduction search (`git log --follow` for a selected file and pickaxe `-S`/`-G` for the relevant symbol), then inspect the introducing diff. Treat a later move/sync commit as a possible carrier rather than the decision or defect origin. Read material discussion, parent/duplicate chains and the finalized outcome before treating an issue title or preview as rationale; a final reversal can supersede its proposal. Bound the investigation by the unresolved question rather than scanning all history.

## Authorized operational records

- Distinguish a bounded empty query from missing authentication, expired retention or unavailable history.
- Discover the actual tool/schema, select a relevant time/release/environment window and poll the same asynchronous query identity instead of resubmitting costly scans.
- Preserve denominator, sampling, refresh and instrumentation/schema changes before interpreting volume as adoption or causality.
- Representative primary events support relevance; generated diagnoses remain hypotheses.
- No connector installation, capture or cross-account search follows.
