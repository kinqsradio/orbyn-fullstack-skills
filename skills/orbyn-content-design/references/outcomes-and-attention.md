# Factual outcomes and useful attention

Use for agent/job results, daily review, routine outputs and control labels.
Read the actual domain status, artifact and effect receipts; this reference owns
presentation, not a new backend state machine. Keep product vocabulary and map
states explicitly. Missing outcome evidence remains unknown, even if a worker
exited successfully. Use [tool effects](../../orbyn-ai-application/references/tool-effects.md)
for authority, uncertain writes and reconciliation.

## A run ending is not a goal being met

| Evidence available | Example visible wording | Useful next action |
| --- | --- | --- |
| Required artifact and agreed checks support the goal | Completed · Draft and references ready | Open result; keep unchecked deployment/publication separate |
| A useful artifact exists but a required part is missing | Partial · Draft ready; two sources unavailable | Open draft, inspect missing work, retry that part |
| Execution cannot produce the required result | Failed · Could not read the source | Correct access or retry; retain any useful partial output |
| Current work needs a specific decision/input | Waiting for you · Choose the destination | Show the actual choice and scope; no generic approval loop |
| Work stopped before a verified outcome | Interrupted · Output retained; completion unverified | Inspect retained work, reconcile effects, resume if supported |
| Request accepted but no matching outcome receipt arrived | Outcome unknown · Checking whether the change applied | Reconcile; avoid duplicate writes or a false success badge |

These are synthetic labels, not a required enum. A provider error must not coexist
with a goal-level “Completed” claim merely because the orchestration process ended.
A result can be partial and the run failed: show both facts where useful. “3 of 5
sources checked” is evidence; an invented percentage or blanket “All done” is not.
Link the resulting artifact and relevant sources near the result, including scope,
version or unavailable source where it affects interpretation. Put diagnostic logs
behind detail; do not require a transcript to discover the outcome.

## Group routine results around the decision

Present recurring outputs by goal/routine/project with a latest result and accessible
run history. A successful no-change check normally needs no new interruptive alert;
a failed check or newly actionable result may. Group repeat reminders for the same
source decision, retaining severity, freshness and the unresolved action. Do not
merge separate owners, permissions or decisions merely because titles match.
Deduplication needs actual event/operation identity; fewer visible cards do not
prove delivery is deduplicated. [Notification identity](../../orbyn-ui-design/references/async-state.md#notification-identity)
owns attempts, stale events and surface lifetime.

Keep durable decisions/review reachable after a toast is dismissed or notifications
are muted. Suppress unchanged routine success, not newly blocking failure, changed
approval consequences or missing evidence. Follow the project's attention policy;
quiet behavior is not permission to disable accessible state feedback or hide a
material failure. A daily brief summarizes decisions and linked work; a calendar
agenda lists time-bound entries. Do not rename them interchangeably. Account/tool
integrations also differ from contextual related-object links.

## Controls say what they actually affect

| Control | Scope to explain at the decision | Do not imply |
| --- | --- | --- |
| Pause routine | Future admission/scheduling paused; state what happens to active work | Every running job stopped |
| Stop run | This job's stop requested, then confirmed/unknown outcome and retained effects | A request acknowledgment rolls back committed work |
| Revoke access | Specified grant removed; show any remaining capabilities and uncertain in-flight effects | Existing outputs deleted or all remote execution undone |
| Mute notifications | Attention channel/routine quieted; results remain in review | Execution paused or authority revoked |

Use the implementation's supported semantics; disable unsupported controls with a
useful reason. Never invent resume, rollback or revocation guarantees. Preserve
upfront bounded authorization for autonomous work: ask only for an unresolved
required fact or effect outside the current grant, and continue independent
permitted work. Ordinary reversible commands do not acquire mandatory previews
or repeat approvals through this policy. [Effect scope](../../orbyn-ai-application/references/tool-effects.md)
owns authorization and budgets; visible copy reflects that contract.

[Worked example](../examples/routine-review.md) exercises partial/unknown outcomes,
quiet repeat results and the four control scopes without importing product data.
These are independently authored presentation decisions informed by the pinned
[workspace reference review](../../orbyn-ui-design/references/workspace-composition.md#reviewed-inspiration-and-limits),
not proof of either reference product's runtime reliability.
