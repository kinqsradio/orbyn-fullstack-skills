---
name: show-me-your-work
description: "Keep a compact decision and evidence trail for substantial migrations or unattended work that the user will review later; not for routine tasks already explained by Git, PR and CI."
---

# Show me your work

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.
Use the [task-record defaults](../orbyn-workflow/references/task-record.md).

Routine edits need no separate log when existing Git, PR and CI evidence suffices.
For long work, continuation or consequential decisions, the agent maintains a
compact checkpoint automatically, without the human requesting logging or filling
a template.

## Method

1. **Choose the record.** Reuse the existing project-owned task report or document. The optional single-writer [TSV helper](scripts/log.sh) is available when useful: `bash skills/show-me-your-work/scripts/log.sh <file> <phase> <decision> <why> <evidence> <result>`. If parallel work needs logs, each writer owns a separate file.
2. **Record meaningful decisions,** especially changes to ownership, compatibility, verification or delivery. Omit routine tool chatter.
3. **Write a useful checkpoint:** candidate revision, what changed, decision, reason, source/evidence, artifact/receipt and actual outcome. Distinguish prepared, attempted, failed, observed and externally delivered. An attempted command is not a completed check, and a command transcript without its terminal result does not establish success. Do not invent measurements or links.
4. **Correct with a superseding entry** when a conclusion changes, rather than deleting the failed attempt. Retain failures and unverified results.
5. **Reconcile before delivery.** Follow the evidence pointers, open the cited artifacts and reconcile the trail with the final candidate. Report missing receipts and unexecuted checks. The log is supporting evidence, not a substitute for inspecting the result or independent qualification.
6. **Summarize** the useful findings without copying the entire log into the reply.

For a schema cutover or rollout, record the candidate, the old-reader compatibility decision, the writer-cutover decision and fencing evidence, the batch outcome and observation, and the remaining operator action. Link to the actual artifact rather than copying private payloads. A later reviewer should be able to distinguish a planned check, a failed attempt and a completed observation.

## Where records live

Keep secrets, credentials and private payloads out of logs. Actual checkpoints and raw traces belong to the consumer, outside public skill sync and public library content. Follow its approved locations and retention policy; keep raw output ignored or in approved CI artifacts. Installing the template does not create a log folder or authorize publishing records. Only reviewed reusable methods and synthetic examples belong in the shared skill tree. Commit a report only within delivery scope, and link durable artifacts from a committed report only when that report is in publication scope.

## Handoffs and catch-ups

When a transfer or context-loss recovery needs structured validation, use the [versioned continuation contract](../orbyn-workflow/references/handoffs.md) in the same owning task record. Reconcile current HEAD, dirty work and user scope before reusing a completion claim. The optional offline checker catches stale revisions and inconsistent records; inspect actual evidence yourself. A concise status explanation or small task can skip the JSON packet.

For a catch-up, include every still-pending human decision in scope with weighed options, recommendation and material unknowns under [explanation and recaps](../orbyn-workflow/references/explanation-and-recaps.md). Sequential runs sharing one single-writer log identify their continuation boundary and verify inherited claims; do not count another run’s actions as your own.

The lead may assign a review subagent for a substantial independent concern under [coordination](../orbyn-workflow/references/project-policy.md#delegation-and-host-configuration); children reconcile their own trail directly. This skill does not authorize a separate chat.
